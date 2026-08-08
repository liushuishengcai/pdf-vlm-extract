---
name: pdf-vlm-extract
description: "AI Agent Skill: 扫描版PDF智能提取为Markdown（文字+图表语义），基于阿里云千问VLM视觉大模型。"
version: 1.1.0
source: https://github.com/liushuishengcai/pdf-vlm-extract
tags: [pdf, vlm, skill, ai-agent, qwen-vl, markdown, book-extraction]
compatibility: [hermes, chatgpt, claude, qwen, custom-agents]
---

# PDF VLM Extract Skill

> **通用 AI Agent 技能**：可被任何支持自定义工具/技能的 Agent 调用。
> 仓库：https://github.com/liushuishengcai/pdf-vlm-extract

## 触发条件

当 Agent 收到以下任务时，应加载本 Skill：

- 用户提供扫描版 PDF 需要提取文字/图表内容
- 下游流程（知识库、蒸馏、分析）拿到的是扫描 PDF
- 纯 OCR 会丢失图表语义（K线图、表格、示意图变碎片文字）

## 执行流程

### 1. 确认是扫描版

```python
import pymupdf
doc = pymupdf.open(pdf_path)
text = doc[10].get_text().strip()[:100]
# 文字层 < 50 字符 → 走本 Skill
```

### 2. 执行提取脚本

```bash
python scripts/pdf_vlm_extract.py "<pdf_path>"
# 可选参数:
#   -o <output_dir>       指定输出目录（默认: <pdf同目录>/<pdf名>_vlm/）
#   --model qwen3.8-max   模型选择（默认 qwen3.8-max，备选 qwen3.6-flash）
#   --pages 0-20          页码范围（0起始），用于先小样验证
```

**环境变量**：需要 `HERMES_CUSTOM_ALI_API_KEY`（阿里云百炼 API Key）

**输出**（默认在 PDF 原始目录的同级子目录）：
- `<pdf同目录>/<pdf名>_vlm/page_001.md ... page_N.md` — 单页提取
- `<pdf同目录>/<pdf名>_vlm/full_text.md` — 合并文档，带 `<!-- PAGE N -->` 锚点
- `<pdf同目录>/<pdf名>_vlm/failed.txt` — 失败页记录（重跑自动补漏）

### 3. 交付结果

将 `full_text.md` 路径返回给用户或传递给下游 Skill。

## 模型选择（已实测验证）

| 模型 | 结论 |
|------|------|
| ✅ **qwen3.8-max**（默认） | 质量最高，推理模型，reasoning_tokens 占用 max_tokens 预算，必须设 8192 |
| ✅ qwen3.6-flash | 更快更便宜，描述略简，适合大批量 |
| ❌ 纯 OCR (RapidOCR) | 图表区输出碎片乱序文字，不可用于图表密集书籍 |
| ❌ GPT-4V / Claude | 中文图表理解弱于千问，成本更高 |

**为什么选千问**：经过 394 页中文技术书籍实测，千问-VL 在中文排版理解、K线图形态描述、图表语义提炼方面显著优于 GPT-4V 和 Claude，且成本更低。

## Pitfalls（Agent 必读）

- **图片必须压缩**：脚本已自动处理（200DPI → resize 宽≤1100 → JPEG q85）
- **max_tokens ≥ 8192**：qwen3.8-max 是推理模型，reasoning_tokens 计入预算
- **temperature 0.1**：转录任务要低温保证准确性
- **端点**：`https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`（不是 dashscope.aliyuncs.com）
- **Windows 路径**：必须传原生格式（`E:\项目\...`），不能传 MSYS 路径（`/e/项目/...`）
- **空白页**：提取出很少内容属正常，不要当失败处理
- **长时间任务**：394页约 4.5 小时，建议后台运行

## 安装说明（供 Agent 自动执行）

```bash
git clone https://github.com/liushuishengcai/pdf-vlm-extract.git
cd pdf-vlm-extract
pip install -r requirements.txt
```

安装完成后，Agent 即可调用 `scripts/pdf_vlm_extract.py` 执行提取任务。

## 验证记录

- 2026-08-08：《龙头主力操盘术》(394页纯扫描版) 全量提取，K线图+盘口数据+正文均正确，断点续传验证通过。
