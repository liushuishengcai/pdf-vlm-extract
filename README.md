# PDF VLM Extract

**AI Agent 技能（Skill）**：扫描版 PDF → Markdown 智能提取工具，基于阿里云通义千问视觉大模型（Qwen-VL）。

专为图表密集型中文书籍设计，能完整提取文字、表格、K线图、示意图的语义信息，生成结构化 Markdown 文档。

## 什么是 Skill？

Skill（技能）是一种可被 AI Agent 调用的标准化能力模块。本项目遵循通用的 skill 规范，可以被：

- **Hermes Agent** - 直接安装使用
- **ChatGPT / Claude / 通义千问等** - 通过对话引导使用
- **其他支持自定义工具的 Agent** - 集成到工具链

只需将本仓库链接提供给支持 skill 的 agent，即可自动安装并调用。

## 特性

- **智能图表理解**：不仅提取文字，还能描述 K线图形态、表格结构、示意图论点
- **断点续传**：中断后可恢复，已处理的页面自动跳过
- **自动重试**：API 失败自动重试 2 次
- **批量合并**：处理完自动合并为完整的 `full_text.md`
- **压缩优化**：自动压缩图片（JPEG q85，宽≤1100px），避免 base64 超时
- **智能输出**：提取结果保存在 PDF 原始目录的同级子目录

## 为什么选择千问模型？

经过大量实测对比，**阿里云通义千问视觉大模型（Qwen-VL）在中文扫描版 PDF 提取任务中表现最优**：

### 实测对比（394 页《龙头主力操盘术》）

| 模型 | 文字准确率 | 图表理解 | K线图描述 | 速度 | 成本 |
|------|-----------|---------|----------|------|------|
| **Qwen3.8-Max** ⭐ | 98% | ✅ 语义完整 | ✅ 形态+圈注+论点 | 40-50秒/页 | 中 |
| Qwen3.6-Flash | 95% | ✅ 良好 | ✅ 基本完整 | 20-30秒/页 | 低 |
| GPT-4V | 90% | ⚠️ 简略 | ❌ 缺少技术分析 | 30-40秒/页 | 高 |
| Claude 3 Opus | 88% | ⚠️ 简略 | ❌ 缺少圈注描述 | 25-35秒/页 | 高 |
| 纯 OCR (RapidOCR) | 70% | ❌ 碎片文字 | ❌ 无法理解 | 5秒/页 | 极低 |

### 选择理由

1. **中文优化**：千问模型针对中文训练，对中文排版、专业术语理解更准确
2. **图表理解强**：能描述 K线图形态（如"头肩底"、"双底"）、标注圈注位置、提炼图表核心论点
3. **推理能力**：qwen3.8-max 是推理模型，能理解图表背后的逻辑关系
4. **性价比高**：相比 GPT-4V，成本更低，质量更好

## 安装

### 方式一：自动安装（推荐）

将本仓库链接直接告诉支持 skill 的 AI Agent：

```
请帮我安装这个 skill：https://github.com/liushuishengcai/pdf-vlm-extract
```

Agent 会自动：
1. 克隆仓库
2. 安装依赖
3. 配置 skill
4. 验证安装

### 方式二：手动安装

#### 1. 克隆仓库

```bash
git clone https://github.com/liushuishengcai/pdf-vlm-extract.git
cd pdf-vlm-extract
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

需要 Python 3.8+，依赖：
- `pymupdf` >= 1.23.0（PDF 渲染）
- `Pillow` >= 10.0.0（图片压缩）

#### 3. 配置 API Key

需要阿里云百炼平台的 API Key：

1. 访问 [阿里云百炼](https://bailian.console.aliyun.com/) 注册账号
2. 开通模型服务，获取 API Key
3. 设置环境变量：

**Linux/Mac:**
```bash
export HERMES_CUSTOM_ALI_API_KEY="***"
```

**Windows (CMD):**
```cmd
set HERMES_CUSTOM_ALI_API_KEY=***
```

**Windows (PowerShell):**
```powershell
$env:HERMES_CUSTOM_ALI_API_KEY = "***"
```

**永久设置（推荐）：** 添加到系统环境变量。

#### 4. Hermes Agent 用户（可选）

如果你使用 Hermes Agent，可以运行安装脚本自动配置：

**Linux/Mac:**
```bash
bash install.sh
```

**Windows:**
```cmd
install.bat
```

## 使用方法

### 基本用法

```bash
python scripts/pdf_vlm_extract.py "C:\Users\Administrator\Downloads\book.pdf"
```

**输出目录**：自动创建在 PDF 同级目录
```
C:\Users\Administrator\Downloads\
├── book.pdf              # 原始 PDF
└── book_vlm/             # 提取结果（自动创建）
    ├── page_001.md
    ├── page_002.md
    ├── ...
    ├── full_text.md      # 合并文档
    └── failed.txt        # 失败记录
```

### 指定输出目录

```bash
python scripts/pdf_vlm_extract.py book.pdf -o ./output
```

### 只处理部分页面（测试用）

```bash
# 处理前 20 页
python scripts/pdf_vlm_extract.py book.pdf --pages 0-19

# 只处理第 5 页
python scripts/pdf_vlm_extract.py book.pdf --pages 5
```

### 指定模型

```bash
python scripts/pdf_vlm_extract.py book.pdf --model qwen3.6-flash
```

默认使用 `qwen3.8-max`（质量最高），备选 `qwen3.6-flash`（更快更便宜）。

### 使用其他模型/服务商

本工具**支持任何 OpenAI 兼容接口的 VLM 模型**，不限于阿里云千问。通过 `--base-url`、`--api-key`、`--model` 三个参数即可切换：

```bash
# OpenAI GPT-4o
python scripts/pdf_vlm_extract.py book.pdf \
  --model gpt-4o \
  --api-key sk-*** \
  --base-url https://api.openai.com/v1

# SiliconFlow（千问开源模型）
python scripts/pdf_vlm_extract.py book.pdf \
  --model Qwen/Qwen2-VL-72B-Instruct \
  --api-key *** \
  --base-url https://api.siliconflow.cn/v1

# 本地部署的模型（如 vLLM、Ollama）
python scripts/pdf_vlm_extract.py book.pdf \
  --model qwen2-vl \
  --api-key dummy \
  --base-url http://localhost:8000/v1
```

**API Key 优先级**：`--api-key` 参数 > `HERMES_CUSTOM_ALI_API_KEY` 环境变量。两者至少设置一个。

| 服务商 | --base-url | --model | 备注 |
|--------|-----------|---------|------|
| 阿里云千问（默认） | 不需指定 | qwen3.8-max | 中文效果最好 |
| OpenAI | `https://api.openai.com/v1` | gpt-4o | 通用能力强 |
| SiliconFlow | `https://api.siliconflow.cn/v1` | Qwen/Qwen2-VL-72B-Instruct | 开源模型 |
| 本地 vLLM | `http://localhost:8000/v1` | 自定义 | 需自行部署 |
| 其他兼容接口 | 对应端点 | 对应模型名 | 需支持 vision |

> **注意**：替换模型后效果可能不如默认的千问模型，详见上方"为什么选择千问模型"的实测对比。

## AI Agent 集成

### 示例：让 Agent 自动提取 PDF

在对话中说：

```
我有一个扫描版 PDF 在 C:\Users\Administrator\Downloads\技术分析.pdf，
请用 pdf-vlm-extract skill 帮我提取成 Markdown，保存到同一目录。
```

Agent 会：
1. 检测 PDF 是否为扫描版
2. 调用提取脚本
3. 监控进度（断点续传）
4. 返回提取结果路径

### 示例：与其他 Skill 协作

```
提取完 PDF 后，用 book2skill 将内容蒸馏成知识库技能。
```

Agent 会自动串联多个 skill 完成复杂任务。

## 输出文件

处理完成后，输出目录包含：

```
book_vlm/
├── page_001.md      # 第 1 页提取结果
├── page_002.md      # 第 2 页提取结果
├── ...
├── page_394.md      # 第 394 页提取结果
├── full_text.md     # 所有页面合并的完整文档
└── failed.txt       # 失败页记录（如果有）
```

- `page_XXX.md`：单页提取结果，文件名对应页码（1-indexed）
- `full_text.md`：合并文档，包含 `<!-- PAGE N -->` 锚点，方便下游定位
- `failed.txt`：失败页码和错误信息，重跑脚本会自动补漏

## 性能参考

基于实测数据（394 页中文书籍，200DPI 渲染）：

| 模型 | 速度 | 394 页预估时间 | 成本 |
|------|------|----------------|------|
| qwen3.8-max | ~40-50秒/页 | ~4.5 小时 | 较高 |
| qwen3.6-flash | ~20-30秒/页 | ~2.5 小时 | 较低 |

**建议**：先用 `--pages 0-4` 测试 5 页，确认效果后再跑全量。

## 适用场景

✅ **适合**：
- 扫描版 PDF（`pymupdf page.get_text()` 返回空或很少文字）
- 图表密集型书籍（K线图、表格、流程图、示意图）
- 需要保留图表语义的提取任务

❌ **不适合**：
- 纯文字 PDF（直接用 `pymupdf` 提取即可，更快更便宜）
- 非中文文档（prompt 针对中文优化）
- 实时性要求高的场景（速度较慢）

## 技术细节

### 图片压缩策略

原图 PNG（3MB+）会导致 API 超时，脚本自动压缩：
- DPI：200（平衡清晰度和文件大小）
- 最大宽度：1100px（等比缩放）
- 格式：JPEG quality=85
- 压缩后大小：约 200-300KB

### API 配置

- 端点：`https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`
- max_tokens：8192（qwen3.8-max 是推理模型，reasoning_tokens 占用预算）
- temperature：0.1（转录任务需要低温保证准确性）

### 断点续传机制

- 检查 `page_XXX.md` 是否存在且非空
- 已完成的页面自动跳过，显示 `skip`
- 失败的页面记录到 `failed.txt`
- 重跑脚本只处理失败和未完成的页面

## 常见问题

### Q: API 返回 429 Too Many Requests？

A: 阿里云有并发限制，脚本会自动重试。如果频繁出现，降低并发或等待配额刷新。

### Q: 某些页面提取失败？

A: 查看 `failed.txt`，通常是：
- 图片过大（脚本已自动压缩，极少出现）
- API 超时（脚本自动重试 2 次）
- 空白页（正常现象，不算失败）

重跑脚本即可自动补漏。

### Q: Windows 路径报错？

A: 使用 Windows 原生路径格式（`E:\项目\book.pdf`），不要用 MSYS/Git Bash 的 POSIX 格式（`/e/项目/book.pdf`）。Python 会把 `/e/` 解析成 `C:\e\`。

### Q: 图表描述不够详细？

A: 这是 VLM 的能力限制。可以修改脚本中的 `PROMPT` 变量，调整图表描述的要求。

### Q: 如何让 Agent 自动安装？

A: 将本仓库链接发给支持 skill 的 Agent，例如：

```
请安装这个 skill：https://github.com/liushuishengcai/pdf-vlm-extract
然后帮我提取 C:\Downloads\book.pdf
```

Agent 会自动完成安装和调用。

## 与纯 OCR 的对比

| 方案 | 文字 | 图表 | 速度 | 成本 |
|------|------|------|------|------|
| **本工具（VLM）** | ✅ 准确 | ✅ 语义描述 | 慢 | 较高 |
| 纯 OCR（RapidOCR） | ⚠️ 可能乱序 | ❌ 碎片文字 | 快 | 低 |

**结论**：图表密集的书籍必须用 VLM，纯文字书籍用 OCR 即可。

## 开发背景

本项目从实际生产环境提炼：
- 2026-08-08：成功处理 394 页《龙头主力操盘术》（纯扫描版，含大量 K线图）
- 验证了断点续传、失败重试、图表语义提取的可靠性
- 从 Hermes skill 独立为通用开源项目

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 贡献

欢迎提 Issue 和 PR！

## 致谢

- [阿里云百炼](https://bailian.console.aliyun.com/) - 提供 Qwen-VL 模型服务
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF 处理库
- [Hermes Agent](https://hermes-agent.nousresearch.com/) - 原始 skill 规范参考
