# 离线鸿蒙知识库（Offline HarmonyOS Knowledge Base）

本技能的离线检索能力来自 DevEco CLI 生态分发的两份压缩包：`docs.zip`（Markdown 文档正文）和 `index.zip`（SQLite 检索索引及词表）。技能通过 `scripts/search_kb.py` 直接读取 zip，不把知识库复制到技能目录。

2026-11-18 的验证基线为 `@deveco/deveco-cli-knowledgebase` 1.3.12。知识库的条目数、体积和 SQLite schema 会随版本变化，因此脚本不依赖固定统计值或固定表结构。

**资源定位**：脚本按以下顺序自动探测：

1. 环境变量 `DEVECO_CLI_DOCS` / `DEVECO_CLI_INDEX`
2. `DEVECO_CLI_ROOT` 指定的 npm 根
3. npm 全局安装根和当前工作区的 `node_modules`
4. 常见平台安装位置，例如 `%APPDATA%\npm\node_modules`、`/usr/local/lib/node_modules` 和 Homebrew 路径

候选 npm 根下会查找以下布局，独立知识库包优先于旧版随包资源：

1. `@deveco/deveco-cli-knowledgebase/`
2. `@deveco/deveco-cli/node_modules/@deveco/deveco-cli-knowledgebase/`
3. `@deveco/deveco-cli/`（旧版随包布局）
4. `@deveco/deveco-code/node_modules/@deveco/deveco-cli-common/`（旧依赖布局）
5. `@deveco/deveco-code/node_modules/@deveco/deveco-cli/`（旧依赖布局）

无法自动定位时，显式设置环境变量或传参，不要在脚本中写死个人机器路径。

## 一、docs.zip —— 文档正文库
鸿蒙开发的正文知识源。新版 13,836 个 Markdown 文档，分 guides / harmonyos-references / release-notes / faq / best-practices / changelogs 六类（详见上表）。`search_kb.py --mode zip` 在全部 `.md` 内做关键词（支持中文）检索，返回命中文件路径与上下文片段。

## 二、index.zip —— 检索索引库
- `search.db`：SQLite 全文索引，indexVersion 1.9.1；新版 22,801 个切分片段（旧版 23,568）
- `harmonyos-terms.txt`：**488 条鸿蒙专有词条**（如 AbilityStage、ArkTS、ArkUI、RelationalStore、Ability、FA 模型等）
- `harmonyos-synonyms.json`：中英同义词表（如 `页面/page/Page`、`数据库/database/RelationalStore`），这是中文"页面"能命中英文 "Page" 的关键
- `harmonyos-stopwords.txt`：领域停用词
- 用途：更高效的全文检索。`search_kb.py --mode sqlite` 解压 `search.db` 到临时目录后检索，实现为两路：① 检测 FTS5 虚表（实际库有 `segments_fts`，列 `search_text`）用 `MATCH` 做真全文检索；② 对其余表按 `PRAGMA table_info` 声明类型自动识别文本列（documents.doc_title、segments.lead_text/search_text/section_title）做 LIKE 兜底。两路结果按 (表,rowid) 去重。旧版脚本曾用硬编码列名白名单（content/text/body/title…），与实际 schema 无一匹配导致零输出，已废弃。

## 三、检索脚本用法
```
python scripts/search_kb.py -k "RelationalStore"
python scripts/search_kb.py -k "页面" "Page" --mode both --max-files 20
python scripts/search_kb.py -k "ArkTS" --docs-path "D:/path/docs.zip" --index-path "D:/path/index.zip"
```
参数：
- `-k/--keyword`：关键词，可多个（空格分隔），必填
- `--docs-path`：docs.zip 路径，默认自动探测（见上）；可用环境变量 `DEVECO_CLI_DOCS` 指定
- `--index-path`：index.zip 路径，默认自动探测；可用环境变量 `DEVECO_CLI_INDEX` 指定
- `--mode`：`zip`（默认）| `sqlite` | `both`
- `--limit`：每个文件命中行展示上限，默认 3
- `--max-files`：展示文件数上限，默认 15
- `--context`：命中行上下文行数，默认 1

> 若资源迁移，用 `--docs-path` / `--index-path` 指向新位置即可，无需改动技能其它部分。

## 四、注意事项
- `docs.zip` 内文件名含中文，脚本按 `utf-8 → gbk → gb18030` 顺序回退解码。
- `search.db` 的表结构随 devecocli 版本演进，脚本对文本列按声明类型自动识别（不依赖固定列名/表名白名单），并对 FTS5 虚表优先用 MATCH。schema 变化时仍可能需要微调类型判定。
- **版本对应**：本文件验证于 deveco-code 0.2.5 / deveco-cli 1.3.12 环境。依赖树中可能同时存在旧版知识库，脚本优先选择独立 `deveco-cli-knowledgebase` 包。
- 升级 deveco-cli 后知识库路径可能再次变动，届时用 `DEVECO_CLI_DOCS` / `DEVECO_CLI_INDEX` 或 `--docs-path` / `--index-path` 指定即可。
