#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""扫描版 PDF -> VLM 智能 Markdown 提取（文字+图表语义）

用法:
  python pdf_vlm_extract.py "E:\\下载\\book.pdf"
  python pdf_vlm_extract.py book.pdf --model gpt-4o --api-key sk-xxx --base-url https://api.openai.com/v1
  python pdf_vlm_extract.py book.pdf --model qwen3.8-max --pages 0-20

特性: 断点续传(已有 page 文件跳过)、失败重试、完成后自动合并 full_text.md
支持: 任何 OpenAI 兼容接口的 VLM 模型（阿里云、OpenAI、SiliconFlow、本地部署等）
"""
import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.request

import pymupdf
from PIL import Image

DEFAULT_MODEL = 'qwen3.8-max'
DEFAULT_BASE_URL = 'https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1'
DEFAULT_API_KEY_ENV = 'HERMES_CUSTOM_ALI_API_KEY'

PROMPT = '''这是一本中文书籍的扫描页面。请将其完整转录为 Markdown：
1. 正文文字：逐字转录，保留段落结构
2. 标题：用 # ## ### 标记层级
3. 表格：转成 Markdown 表格
4. 图表（K线图/走势图/示意图/插图）：先用一行 【图注：原文图注】，再用 【图表描述：...】 详细描述：图表类型、标的或对象、时间范围（若有）、关键形态、圈注标记位置、该图想说明的核心论点
5. 软件截图的盘口/数据栏：概括为 【盘口数据：...】 一句话，不要逐条罗列
6. 忽略页眉页脚中的页码和书名
只输出 Markdown 内容本身，不要任何额外解释。'''


def page_image_bytes(doc, idx, dpi=200, max_w=1100, quality=85):
    """渲染页面并压缩为 JPEG（大图 base64 会导致 API 超时）"""
    pix = doc[idx].get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    w, h = img.size
    if w > max_w:
        img = img.resize((max_w, int(h * max_w / w)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=quality)
    return buf.getvalue()


def call_vlm(b64, model, base_url, api_key, timeout=300):
    payload = {
        'model': model,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
                {'type': 'text', 'text': PROMPT},
            ],
        }],
        'max_tokens': 8192,
        'temperature': 0.1,
    }
    req = urllib.request.Request(
        f'{base_url}/chat/completions',
        data=json.dumps(payload).encode(),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    return data['choices'][0]['message']['content']


def extract_page(doc, idx, out_dir, model, base_url, api_key, retries=2):
    out = os.path.join(out_dir, f'page_{idx + 1:03d}.md')
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return 'skip'
    try:
        b64 = base64.b64encode(page_image_bytes(doc, idx)).decode()
    except Exception as e:
        record_fail(out_dir, idx, f'render: {e}')
        return 'fail'
    for attempt in range(retries + 1):
        try:
            text = call_vlm(b64, model, base_url, api_key)
            if text.strip():
                with open(out, 'w', encoding='utf-8') as f:
                    f.write(text)
                return 'ok'
        except Exception as e:
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
            else:
                record_fail(out_dir, idx, str(e))
    return 'fail'


def record_fail(out_dir, idx, err):
    with open(os.path.join(out_dir, 'failed.txt'), 'a', encoding='utf-8') as f:
        f.write(f'{idx + 1}\t{err}\n')


def merge(out_dir):
    """扫描目录中所有 page_*.md 按页码合并为 full_text.md"""
    import re
    files = [f for f in os.listdir(out_dir) if re.match(r'page_\d+\.md$', f)]
    files.sort()
    parts = []
    for fname in files:
        page_no = int(re.search(r'\d+', fname).group())
        with open(os.path.join(out_dir, fname), encoding='utf-8') as f:
            parts.append(f'<!-- PAGE {page_no} -->\n\n' + f.read().strip())
    merged = '\n\n---\n\n'.join(parts)
    out = os.path.join(out_dir, 'full_text.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(merged)
    return out, len(files), len(merged)


def main():
    ap = argparse.ArgumentParser(description='扫描版PDF -> VLM Markdown（支持任意 OpenAI 兼容接口）')
    ap.add_argument('pdf', help='PDF 文件路径')
    ap.add_argument('-o', '--output', help='输出目录（默认: <pdf同目录>/<pdf名>_vlm/）')
    ap.add_argument('--model', default=DEFAULT_MODEL, help=f'模型名称（默认: {DEFAULT_MODEL}）')
    ap.add_argument('--base-url', default=None, help=f'API 端点（默认: 阿里云千问端点）')
    ap.add_argument('--api-key', default=None, help=f'API Key（也可通过环境变量 {DEFAULT_API_KEY_ENV} 设置）')
    ap.add_argument('--pages', help='页码范围(0起始)，如 0-20 或单页 5')
    args = ap.parse_args()

    # 解析 base_url
    base_url = args.base_url or DEFAULT_BASE_URL

    # 解析 api_key：命令行参数 > 环境变量
    api_key = args.api_key or os.environ.get(DEFAULT_API_KEY_ENV)
    if not api_key:
        sys.exit(f'缺少 API Key。请通过 --api-key 参数或环境变量 {DEFAULT_API_KEY_ENV} 提供。')

    doc = pymupdf.open(args.pdf)
    n = len(doc)
    if args.pages:
        if '-' in args.pages:
            a, b = map(int, args.pages.split('-'))
            idxs = list(range(a, min(b + 1, n)))
        else:
            idxs = [int(args.pages)]
    else:
        idxs = list(range(n))

    if args.output:
        out_dir = args.output
    else:
        base = os.path.splitext(os.path.basename(args.pdf))[0]
        out_dir = os.path.join(os.path.dirname(os.path.abspath(args.pdf)), base + '_vlm')
    os.makedirs(out_dir, exist_ok=True)

    print(f'PDF: {args.pdf} ({n}页) | 处理 {len(idxs)} 页 | 模型: {args.model}')
    print(f'API: {base_url} | 输出: {out_dir}')
    t0 = time.time()
    counts = {'ok': 0, 'skip': 0, 'fail': 0}
    for k, idx in enumerate(idxs):
        r = extract_page(doc, idx, out_dir, args.model, base_url, api_key)
        counts[r] += 1
        if r != 'skip':
            elapsed = time.time() - t0
            speed = elapsed / (counts['ok'] + counts['fail'])
            eta = speed * (len(idxs) - k - 1)
            print(f'[{k + 1}/{len(idxs)}] page_{idx + 1:03d} {r} | 已用{elapsed / 60:.1f}min ETA {eta / 60:.1f}min', flush=True)

    merged_path, n_files, n_chars = merge(out_dir)
    print(f'\n完成: ok={counts["ok"]} skip={counts["skip"]} fail={counts["fail"]}')
    print(f'合并: {merged_path} ({n_files}页, {n_chars}字符)')
    if counts['fail']:
        print(f'失败页记录在 {os.path.join(out_dir, "failed.txt")}，重跑本脚本即可自动补漏')


if __name__ == '__main__':
    main()
