---
name: pdf-vlm-extract
description: "Use when 扫描版PDF要提取文字+图表。转Markdown供下游学习。"
version: 1.3.0
source: https://github.com/liushuishengcai/pdf-vlm-extract
tags: [pdf, vlm, skill, ai-agent, qwen-vl, markdown, book-extraction]
compatibility: [hermes, chatgpt, claude, qwen, custom-agents]
---

# PDF VLM Extract Skill

> **通用 AI Agent 技能**：可被任何支持自定义工具/技能的 Agent 调用。
> 仓库：https://github.com/liushuishengcai/pdf-vlm-extract

## 触发条件

当 Agent 收到以下任务时，应加载本 Skill：

- 用户提供扫描版 PDF（`pymupdf page.get_text()` 返回空）需要提取文字/图表内容
- 下游流程（知识库、蒸馏、分析）拿到的是扫描 PDF
- 纯 OCR 会丢失图表语义（K线图、表格、示意图变碎片文字）

**用户偏好（2026-08 明确）**：凡是分析 PDF，先用本流程提取成 Markdown 保存到相应目录，再让下游 skill 调用。不要用纯 OCR。

## 方案选型结论（已实测 2026-08，跨 3 个平台 16 个模型）

| 方案 | 结论 |
|------|------|
| ✅ **ALI 百炼 qwen3.8-max（默认）** | 综合最佳：图表语义描述最详细、点位/时间戳/盘口数字全、无幻觉。推理模型，reasoning_tokens 占用 max_tokens 预算，必须设 8192 |
| ✅ Nous Portal claude-opus-4.7 | 精度最高（博文标题+时间戳+批注全文全读准），26s/页，速度快 |
| ✅ Nous Portal kimi-k3 | 图表描述最详尽（点位链、圈注、时间戳全还原），74s/页 |
| ✅ SiliconFlow Kimi-K2.7-Code | 简洁稳健不编造，18s/页最快（SiliconFlow 内） |
| ✅ SiliconFlow Qwen3-VL-32B-Instruct/Thinking | 详细但盘口简略；Thinking 结构最规范 |
| ✅ SiliconFlow GLM-4.5V | 极简要点式，21s/页，无幻觉 |
| ✅ 任意 OpenAI 兼容端点 | v1.1.0 起支持 `--base-url`/`--api-key` 直连（阿里/SiliconFlow/Nous Portal/OpenAI/本地） |
| ❌ 纯 OCR (RapidOCR) | 图表区输出碎片乱序文字，不可用于图表密集书籍 |
| ❌ GPT-4V / Claude（旧版） | 中文图表理解弱于千问，成本更高 |

## 模型实测对比（2026-08-11，两本书 8 页 × 16 模型）

### 速度与 token 消耗（单页）

| 模型 | 平台 | 耗时/页 | tokens/页 | 速度 |
|------|------|------|------|------|
| muse-spark-1.2 | Nous | 16s | ~4.6K | 🥇 最快 |
| gpt-5.6-terra | Nous | 13s | ~3.4K | 🥇 |
| gemini-3.6-flash | Nous | 20s | ~5.1K | 🥈 |
| claude-opus-4.7 | Nous | 26s | ~3.7K | 🥉 |
| grok-4.5 | Nous | 34s | ~3.9K | 4 |
| gpt-5.6-terra-pro | Nous | 38s | **~21K** 🔥 | 5（最贵，6倍） |
| GLM-4.5V | SiliconFlow | 21s | ~1K | 🥈 |
| Kimi-K2.7-Code | SiliconFlow | 18s | ~1K | 🥇 |
| Qwen3-VL-32B-Thinking | SiliconFlow | 39s | ~2K | 中 |
| Qwen3-VL-32B-Instruct | SiliconFlow | 52s | ~1.5K | 慢 |
| qwen3-vl-plus | ALI | 12s | ~2K | 🥇 最快 |
| **qwen3.8-max** | ALI/Nous | **69-120s** | 7-8K | 最慢 |
| doubao-seed-2.0-lite | Nous | 49s | ~4.9K | 中 |
| gpt-5.6-sol | Nous | 56s | ~4.8K | 慢 |

**token 消耗规律**：推理模型（qwen3.8-max、terra-pro）思考 token 计入输出/输入，单页可达 21K（terra-pro），是普通模型的 4-6 倍。选型时若按量计费，**优先 muse-spark / gemini-flash / Kimi-K2.7 / qwen3-vl-plus**；要精度优先 claude-opus-4.7 / qwen3.8-max。

### 精度实测（缠论108课 第5/14页 大图 + 龙头操盘术 25-30页）

| 模型 | 正文转录 | 图注 | 点位/细节 | 幻觉情况 |
|------|------|------|------|------|
| **claude-opus-4.7** | ✅ | ✅ 带日期 | 🥇 最全（998→6124→1664 全点位+博文时间戳） | 无 |
| **qwen3.8-max**（ALI/Nous） | ✅ | ✅ 规范 | 🥇 最全（点位链+时间戳+盘口数字） | 无 |
| **kimi-k3** | ✅ | ✅ 最详细 | 🥇 详尽（点位+圈注+时间戳） | 无 |
| gemini-3.6-flash | ⚠️ 偶错字 | ✅ | 详细 | 博文标题 2 处幻觉 |
| doubao-seed-2.0-lite | ✅ | ⚠️ 模板化 | 详细 | 无 |
| muse-spark-1.2 | ✅ | ❌ 正文当图注 | 中 | 无 |
| gpt-5.6-terra / terra-pro | ✅ | ❌ 写"无" | 中 | 无 |
| grok-4.5 | ✅ | ❌ 写"无" | 中 | 输出包 ```markdown 代码块 |
| Kimi-K2.7-Code | ✅ | ✅ | 简洁概括 | 无（保守不编造） |
| GLM-4.5V | ✅ | ✅ | 极简要点 | 无 |
| **gpt-5.6-sol** | ⚠️ 错字 | ❌ | ❌ | 🔥 **严重幻觉：把上证指数认成纳斯达克指数、编造1995年历史** |
| **Qwen3-Omni-30B-A3B** | ❌ | ❌ | ❌ | 🔥 **编造整篇正文**（转录任务禁用） |

**结论**：
- 精度首选：**claude-opus-4.7**（Nous）/ **qwen3.8-max**（ALI，默认）
- 速度省钱：**muse-spark-1.2** / **gemini-3.6-flash** / **Kimi-K2.7-Code** / **qwen3-vl-plus**
- 禁用：**gpt-5.6-sol**（幻觉重灾区）、**Qwen3-Omni**（编造正文）
- 非视觉模型（勿用）：GLM-5.2、MiniMax-M2.5、LongCat-2.0、Ling-flash-2.0、qwen3.7-max、deepseek-v4-pro

## 平台接入

### 阿里云百炼（默认）

```bash
# 端点：阿里云百炼控制台 → API-KEY 管理 → 获取专属 endpoint（形如 https://<workspace-id>.cn-beijing.maas.aliyuncs.com/compatible-mode/v1）
# 模型名：qwen3.8-max（推荐）、qwen3-vl-plus（快）、qwen3-vl-flash、qwen-vl-max、qwen3.6-flash
```

**注意**：百炼模型名**全小写**（`qwen3-vl-plus`，写成 `Qwen3-VL-Plus` 会 404）。可用 `GET /models` 列出全部 236 个可用模型。

### SiliconFlow

```bash
# 端点
https://api.siliconflow.cn/v1
# 模型名（带厂商前缀）：moonshotai/Kimi-K2.7-Code、Qwen/Qwen3-VL-32B-Instruct、zai-org/GLM-4.5V
# API Key 通常在环境变量 SILICONFLOW_API_KEY
```

### Nous Portal（OAuth 订阅制）

```bash
# 端点（凭据存于 Hermes auth.json: providers.nous）
https://inference-api.nousresearch.com/v1
# 认证：Bearer token（OAuth device_code，约1小时过期，过期需 hermes auth 重新登录）
# 模型名（带厂商前缀）：openai/gpt-5.6-terra、anthropic/claude-opus-4.7、moonshotai/kimi-k3、qwen/qwen3.8-max、google/gemini-3.6-flash、x-ai/grok-4.5、meta/muse-spark-1.2 等 356 个
```

**Nous Portal 注意事项**：
- **必须带浏览器 User-Agent 头**，否则 Cloudflare 拦截返回 `HTTP 403 error 1010`
- 模型名大小写敏感，`doubao-seed-2.1-pro` 不存在（只有 `bytedance-seed/seed-2.0-lite/mini`）
- gpt-5.6-terra-pro 是推理模型，单页 token 消耗 ~21K，成本是其他模型 6 倍

## 配置管理（URL / API Key / 模型）

**配置文件**：`~/.pdf-vlm-extract.json`（Windows 即 `C:\Users\<用户名>\.pdf-vlm-extract.json`），保存 `base_url` / `api_key` / `model` 三项。

### 首次使用（Agent 必做）

执行提取任务前，先检查配置是否存在：

```bash
python scripts/pdf_vlm_extract.py --show-config
```

- 若显示三项已设置 → 直接进入执行流程
- 若显示 `(未设置)` → **必须先用 clarify 工具问用户**，一次性问清三件事：
  1. **API 端点 URL**（如阿里云百炼、OpenAI、SiliconFlow、Nous Portal、本地部署等；用户不确定时可给默认阿里云百炼端点）
  2. **API Key**（敏感信息，拿到后写入配置即可，不用回显）
  3. **模型名称**（如 `qwen3.8-max`、`qwen3-vl-plus`、`moonshotai/Kimi-K2.7-Code`、`openai/gpt-5.6-terra` 等；用户不确定时默认 `qwen3.8-max`）

  用户回答后执行：

  ```bash
  python scripts/pdf_vlm_extract.py --configure
  # 交互式依次输入 URL → API Key → 模型（回车可用默认值）
  ```

  也可用管道一次性传入（Agent 自动化场景）：
  ```bash
  printf '%s\n' '<url>' '<api_key>' '<model>' | python scripts/pdf_vlm_extract.py --configure
  ```

  配置保存后即可正常提取。

### 切换模型（用户随时一句话）

- 用户说"换模型 / 切到 xx 模型 / 用 xx 提取" → 执行：

  ```bash
  python scripts/pdf_vlm_extract.py --set-model <新模型名>
  # 只改 model，URL 和 Key 保留
  ```

- 用户只想本次用某模型、不改配置 → 正常执行时加 `--model` 参数即可（临时覆盖，不保存）
- 用户想改 URL 或 Key → 重新跑 `--configure`（会显示当前值，回车保留，输入新值覆盖）
- 随时可查当前配置：`--show-config`（API Key 自动打码，安全）

### 参数优先级（重要）

命令行参数（`--model` / `--base-url` / `--api-key`）**>** 配置文件 **>** 环境变量 `HERMES_CUSTOM_ALI_API_KEY` **>** 默认值（阿里云 qwen3.8-max）。

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
#   --model qwen3.8-max   本次临时指定模型（不写配置；写配置用 --set-model）
#   --base-url <url>      本次临时指定 API 端点（不写配置）
#   --api-key <key>       本次临时指定 API Key（不写配置）
#   --pages 0-20          页码范围（0起始）：0-20 区间 / 5 单页 / 4,13 逗号列表
#   --configure           交互式配置 URL/API Key/模型（首次使用）
#   --show-config         查看当前配置
#   --set-model <name>    切换模型（保留 URL/Key，写入配置）
```

**API Key 来源优先级**：`--api-key` 参数 > 配置文件 `~/.pdf-vlm-extract.json` > 环境变量 `HERMES_CUSTOM_ALI_API_KEY`。首次使用无配置时脚本会提示先运行 `--configure`。

**输出**（默认在 PDF 原始目录的同级子目录）：
- `<pdf同目录>/<pdf名>_vlm/page_001.md ... page_N.md` — 单页提取
- `<pdf同目录>/<pdf名>_vlm/full_text.md` — 合并文档，带 `<!-- PAGE N -->` 锚点
- `<pdf同目录>/<pdf名>_vlm/failed.txt` — 失败页记录（重跑自动补漏）

### 3. 交付结果

将 `full_text.md` 路径返回给用户或传递给下游 Skill（book2skill / llm-wiki ingest）。下游需要图表细节时，可按 `<!-- PAGE N -->` 锚点回查单页 md。

## Pitfalls（Agent 必读）

- **图片必须压缩**：脚本已自动处理（200DPI → resize 宽≤1100 → JPEG q85），原图 PNG 3MB+ base64 必然超时
- **max_tokens ≥ 8192**：qwen3.8-max 等推理模型，reasoning_tokens 计入预算，给小了正文会被截断
- **temperature 0.1**：转录任务要低温保证准确性
- **模型名大小写敏感**：阿里百炼用小写（`qwen3-vl-plus`），大写会 404；SiliconFlow/Nous 带厂商前缀（`Qwen/...`、`openai/...`）
- **Nous Portal 必须带浏览器 UA 头**，否则 Cloudflare 403 error 1010；token 约 1 小时过期
- **Windows 路径**：必须传原生格式（`E:\项目\...`），不能传 MSYS 路径（`/e/项目/...`）——Python 会解析成 `C:\e\项目\...` 并悄悄新建错误目录
- **空白页/章节扉页**：提取出很少内容属正常，不要当失败处理
- **长时间任务**：qwen3.8-max 实测约 1-2 分钟/页，394页 ≈ 7-13 小时，**务必后台运行**（terminal background=true, notify_on_complete=true）
- **幻觉模型禁用**：gpt-5.6-sol（编造指数名称/历史）、Qwen3-Omni（编造整篇正文）、gpt-4v 旧版
- **非视觉模型勿用**：GLM-5.2、MiniMax-M2.5、LongCat-2.0、Ling-flash-2.0、qwen3.7-max、deepseek-v4-pro（API 会报 not a VLM）
- **断点续传**：已完成的页自动 skip，失败页记录 failed.txt，重跑自动补漏

## 安装说明（供 Agent 自动执行）

```bash
git clone https://github.com/liushuishengcai/pdf-vlm-extract.git
cd pdf-vlm-extract
pip install -r requirements.txt
```

## 验证记录

- 2026-08-08：《龙头主力操盘术》(394页纯扫描版) 第5/6/7/25页验证，K线图+盘口数据+正文均正确转 Markdown，图表语义（圈注、形态、论点）完整。断点续传验证通过。
- 2026-08-10：v1.2.0 新增配置管理（`--configure` / `--show-config` / `--set-model`，配置文件 `~/.pdf-vlm-extract.json`），首次使用问答引导 + 随时切换模型。隔离环境全流程测试通过（配置写入、Key 打码、模型切换保留 URL/Key、缺 Key 引导提示）。
- 2026-08-11：v1.3.0 跨平台 16 模型实测（阿里百炼 2 + SiliconFlow 6 + Nous Portal 10），两本扫描书 8 页验证：claude-opus-4.7 / kimi-k3 / qwen3.8-max 精度最高；muse-spark-1.2 / gemini-3.6-flash / Kimi-K2.7-Code 速度最快；gpt-5.6-sol 与 Qwen3-Omni 有严重幻觉禁用；`--pages` 新增逗号列表支持（4,13）。
