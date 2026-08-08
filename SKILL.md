---
name: pdf-vlm-extract
description: "Use when 扫描版PDF要提取文字+图表。转Markdown供下游学习。"
version: 1.0.0
tags: [pdf, vlm, ocr-alternative, qwen3.8-max, markdown, book-extraction]
---

# PDF VLM 智能提取（扫描版 PDF → Markdown，文字+图表语义）

## 触发条件

- 用户提供扫描版 PDF（`pymupdf page.get_text()` 返回空）需要 agent 学习/分析
- book2skill / llm-wiki ingest 等下游流程拿到的是扫描 PDF
- 纯 OCR（RapidOCR）会丢失图表语义（K线图、表格结构、示意图变碎片文字）时

**用户偏好（2026-08 明确）**：凡是分析 PDF，先用本流程提取成 Markdown 保存到相应目录，再让下游 skill 调用。不要用纯 OCR。

## 方案选型结论（已实测）

| 方案 | 结论 |
|------|------|
| ✅ ALI qwen3.8-max（默认） | 视觉理解质量最高，图表语义描述详细。推理模型，reasoning_tokens 占用 max_tokens 预算，必须设 8192 |
| ✅ ALI qwen3.6-flash | 备选，便宜快，描述略简 |
| ✅ SiliconFlow Qwen/Qwen3-VL-32B-Instruct | ALI 额度用完时的备选，OpenAI 兼容接口 |
| ❌ 纯 OCR (RapidOCR) | 图表区输出碎片乱序文字，不可用于图表密集书籍 |
| ❌ 直接发原图 PNG | 3MB+ base64 会超时；必须压缩成 JPEG（宽≤1100, q=85，约 200-300KB） |

## 执行步骤

### 1. 确认是扫描版

```python
import pymupdf
doc = pymupdf.open("book.pdf")
print(len(doc), repr(doc[10].get_text().strip()[:100]))
# 文字层 < 50 字符 → 走本流程
```

### 2. 跑批处理脚本（断点续传，可后台）

```bash
python scripts/pdf_vlm_extract.py "E:\下载\book.pdf"
# 可选: -o out_dir --model qwen3.8-max --pages 0-20（先小样验证）
```

- 环境变量 `HERMES_CUSTOM_ALI_API_KEY` 必须存在（Hermes 环境自带）
- 输出：`<pdf同目录>/<pdf名>_vlm/page_001.md ... + full_text.md`（合并版，带 `<!-- PAGE N -->` 锚点）
- 失败的页记录在 `failed.txt`，重跑脚本自动补漏（已完成的页 skip）
- 速度参考：qwen3.8-max 约 40-50秒/页 → 394页 ≈ 4.5小时，**务必 terminal(background=true, notify_on_complete=true)**

### 3. 交给下游

把 `full_text.md` 路径给 book2skill / llm-wiki ingest 等。下游需要图表细节时，可按 `<!-- PAGE N -->` 锚点回查单页 md。

## Pitfalls

- **图片必须压缩**：200DPI 渲染 → PIL resize 到宽≤1100 → JPEG q85。原图 PNG（3MB+ base64）必然超时
- **max_tokens 必须 ≥ 8192**：qwen3.8-max 是推理模型，reasoning_tokens 计入 max_tokens 预算，给小了正文会被截断
- **temperature 0.1**：转录任务要低温
- **端点不是 dashscope.aliyuncs.com**：是 `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`（阿里云 MaaS 套餐端点）
- qwen3.7-max / glm-5.2 / deepseek-v4-pro 不支持视觉理解，别用
- 空白页/章节扉页会提取出很少内容，属正常，不要当失败处理
- **Windows bash 环境**：`-o` 参数必须传 Windows 原生路径（`E:\项目\...`），不能传 MSYS 路径（`/e/项目/...`）——Python 会把它解析成 `C:\e\项目\...` 并悄悄新建错误目录

## 验证记录

- 2026-08-08：《龙头主力操盘术》(394页纯扫描版) 第5/6/7/25页验证，K线图+盘口数据+正文均正确转 Markdown，图表语义（圈注、形态、论点）完整。断点续传验证通过。
