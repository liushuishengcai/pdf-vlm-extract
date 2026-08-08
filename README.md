# PDF VLM Extract

扫描版 PDF → Markdown 智能提取工具，基于阿里云通义千问视觉大模型（Qwen-VL）。

专为图表密集型中文书籍设计，能完整提取文字、表格、K线图、示意图的语义信息，生成结构化 Markdown 文档。

## 特性

- **智能图表理解**：不仅提取文字，还能描述 K线图形态、表格结构、示意图论点
- **断点续传**：中断后可恢复，已处理的页面自动跳过
- **自动重试**：API 失败自动重试 2 次
- **批量合并**：处理完自动合并为完整的 `full_text.md`
- **压缩优化**：自动压缩图片（JPEG q85，宽≤1100px），避免 base64 超时

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

需要 Python 3.8+，依赖：
- `pymupdf` >= 1.23.0（PDF 渲染）
- `Pillow` >= 10.0.0（图片压缩）

### 2. 配置 API Key

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
$env:HERMES_CUSTOM_ALI_API_KEY = "sk-***"
```

**永久设置（推荐）：** 添加到系统环境变量。

## 使用方法

### 基本用法

```bash
python scripts/pdf_vlm_extract.py "E:\下载\book.pdf"
```

输出目录默认创建在 PDF 同级目录：`E:\下载\book_vlm\`

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

## 与纯 OCR 的对比

| 方案 | 文字 | 图表 | 速度 | 成本 |
|------|------|------|------|------|
| **本工具（VLM）** | ✅ 准确 | ✅ 语义描述 | 慢 | 较高 |
| 纯 OCR（RapidOCR） | ⚠️ 可能乱序 | ❌ 碎片文字 | 快 | 低 |

**结论**：图表密集的书籍必须用 VLM，纯文字书籍用 OCR 即可。

## Hermes Skill 集成

本项目源自 [Hermes Agent](https://hermes-agent.nousresearch.com/) 的 `pdf-vlm-extract` skill。

如果你使用 Hermes，可以快速安装：

**Linux/Mac:**
```bash
bash install.sh
```

**Windows:**
```cmd
install.bat
```

安装后在 Hermes 中直接说"提取这个 PDF"即可自动调用。

## 开发背景

本项目从实际生产环境提炼：
- 2026-08-08：成功处理 394 页《龙头主力操盘术》（纯扫描版，含大量 K线图）
- 验证了断点续传、失败重试、图表语义提取的可靠性
- 从 Hermes skill 独立为开源项目

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 贡献

欢迎提 Issue 和 PR！

## 致谢

- [阿里云百炼](https://bailian.console.aliyun.com/) - 提供 Qwen-VL 模型服务
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF 处理库
- [Hermes Agent](https://hermes-agent.nousresearch.com/) - 原始 skill 来源
