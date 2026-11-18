---
name: harmonyos-capabilities
description: Develop, build, run, debug, test, and document-search HarmonyOS NEXT applications with DevEco CLI and DevEco Code, including ArkTS, ArkUI, emulators, devices, UI automation, signing, and offline documentation. Use when the task concerns HarmonyOS tooling or APIs rather than generic TypeScript or Android development.
metadata:
  short-description: 鸿蒙应用开发、构建、调试与文档检索
---

# 鸿蒙能力（HarmonyOS Capabilities）

为 Codex 提供 HarmonyOS NEXT、ArkTS 与 ArkUI 开发中的工具定位、文档检索、命令规范和已知坑点。技能是操作指南，不替代本机工具；执行前先确认 CLI、DevEco Studio、SDK、设备与知识库的实际状态。

当前验证基线（2026-11-18）：

- `@deveco/deveco-code` 0.2.5，命令为 `deveco`
- `@deveco/deveco-cli` 1.3.12，命令为 `devecocli`
- `@deveco/deveco-cli-knowledgebase` 1.3.12
- `deveco-code` 0.2.5 的内部依赖曾钉在 CLI 1.3.4；始终以 PATH 中顶层 `devecocli --version` 为准

## 环境检查

执行会改变工程或设备状态的命令前，先做最小检查：

```powershell
devecocli --version
deveco --version
devecocli <command> --help
python scripts/search_kb.py --help
```

命令行为和参数以当前 `devecocli <command> --help` 为准。不要根据旧版参考虚构参数，也不要假装已经完成构建、安装或设备验证。

## 任务路由

- 查询已验证的命令、参数与新增能力：读 [references/devecocli-1.3.12-current.md](references/devecocli-1.3.12-current.md)。
- 查询本机真实命令和参数：执行 `devecocli <command> --help`。运行时帮助优先于本技能中的版本快照。
- 需要检索离线文档：按 [references/knowledge-base.md](references/knowledge-base.md) 使用 `scripts/search_kb.py`。
- 核对来源、版本和许可证边界：读 [references/upstream-sources.md](references/upstream-sources.md)。

按需读取；不要把事实性快照当作比当前 CLI 帮助更新的来源。

## DevEco CLI 1.3.12

顶层帮助包含 19 个主要命令，以及 `help [command]` 元命令：

| 命令 | 用途 |
|---|---|
| `build` | 调用 hvigor 构建工程或模块 |
| `run` | 构建、安装并在设备上运行 |
| `update` | 更新 DevEco CLI |
| `device` | 管理已连接设备 |
| `emulator` | 管理模拟器和模拟场景 |
| `auth` | 登录、登出、状态和团队操作 |
| `skills` | 管理 HarmonyOS skills |
| `plugin` | 管理白名单 Agent 插件 |
| `log` | 获取设备应用日志 |
| `create` | 从模板创建工程 |
| `init` | 安装内置技能或配置 deveco-mcp |
| `serve` | 启动辅助协议服务 |
| `docs` | 搜索、读取、列出目录和更新文档 |
| `ui` | 检查并操作设备 UI |
| `check` | 运行 lint、ArkTS 或兼容性检查 |
| `signature` | 生成签名配置 |
| `design2arkts` / `d2a` | 设计稿解析、Skill 管理、ArkUI 页面导入导出 |
| `verify` | 在设备上执行 UI 验证 |
| `testing` | 调用 DevEco Testing CLI |

关键新能力：

- `check` 子命令为 `lint`、`arkts`、`compat`；`check arkts` 专门检查 `.ets` 源码。
- `docs` 子命令为 `search`、`read`、`catalog`、`update`。
- `init` 支持 `--agent`、`--project`、`--path`、`--skill`、`--mcp`、`--with-homegraph` 和 `--force`。
- `run` 支持 `--apply`、`--hotreload [action]`、`--hotreload-apply`、`--debug-line` 等模式。
- `plugin` 支持 `list`、`install`、`update`、`uninstall`。
- `design2arkts` 覆盖设计解析、页面导入、预览、诊断、视觉评分、HDS 迁移和 React/JSX 转 ArkUI。
- `verify` 支持自然语言测试计划、设备验证、截图、日志、初始化视觉模型和 `appanalyzer`。
- `testing` 依赖独立安装的 DevEco Testing 或 `DEVECO_TESTING_HOME`；未安装时会明确报错。

`arkts_knowledge_search` 和 `check_ets_files` 不是官方命令名。知识检索使用 `devecocli docs search`；ArkTS 检查使用 `check arkts`，DevEco Code Linter 使用 `check lint`。

## 离线知识库

知识库现由 `@deveco/deveco-cli-knowledgebase` 独立分发，不再依赖旧素材目录。当前实测：

- `docs.zip` 54.5 MB，42,568 个条目，13,836 个 Markdown 文档
- `index.zip` 11.9 MB，含 `search.db`、词表和同义词
- SQLite 索引使用 FTS5 虚表 `segments_fts`
- 路径使用自动探测，不假设知识库永远位于固定位置

脚本按以下顺序自动探测：

1. `DEVECO_CLI_DOCS` / `DEVECO_CLI_INDEX`
2. `DEVECO_CLI_ROOT` 指定的 npm 根
3. 常见全局 npm 与本地 `node_modules`

快速检索：

```powershell
python scripts/search_kb.py -k "RelationalStore"
python scripts/search_kb.py -k "页面" "Page" --mode both
python scripts/search_kb.py -k "ArkTS" --docs-path "<PATH>/docs.zip" --index-path "<PATH>/index.zip"
```

ZIP 模式按 Markdown 正文检索。SQLite 模式优先用 FTS5 `MATCH`，再用自动识别的文本列做 `LIKE` 兜底。不要恢复旧脚本中硬编码的 `content/text/body/title` 列名白名单。

## Agent 暴露层

DevEco Code 0.2.5 当前提供 5 个开发工具：`build_project`、`start_app`、`hdc_log`、`verify_ui`、`switch_cwd`。原来的内置 `arkts_check` 已移除，ArkTS 检查改由 `devecocli check arkts` 承担。

内置技能体系已重整。已知当前名称包括 `hmos-arkui-develop-skill`、`deveco-create-project`、`arkts-runtime-fix`、`hmos-design-to-arkts` 和 `customize-deveco`；旧名称 `arkts-grammar-standards` 与 `arkts-error-fixes` 不应继续使用。实际安装列表以当前 DevEco Code 和 `devecocli init` 资源为准。

`hmos-design-to-arkts` 支持 Pixso、Figma 和 MasterGo，提供 Fast / Full 工作流；Full 模式包含多轮视觉校准。对应的 CLI 入口是 `devecocli design2arkts` 或 `d2a`。

这些工具名称不表示当前 Codex 会话一定连接了同名工具。先检查实际工具与 CLI，必要时通过 `devecocli` 执行等价流程。

Goal 模式按“需求分析 → 架构设计 → 任务分解 → 代码实现 → 功能验证”交付，并可在工程内生成 `.specs/spec.md`、`plan.md`、`tasks.md`。没有模拟器或真机时，必须把结果明确限定为编译、lint 或静态检查。

## 操作约束

1. 构建、部署、签名、插件安装和设备清理会改变本机或设备状态，只作为当前任务的一部分执行。
2. 先读取 `build-profile.json5`、`oh-package.json5`、`module.json5` 和签名配置，再决定 SDK、产品、模块与设备参数。
3. 失败时先读取真实错误和退出码；不要在环境问题未定位时进行多次大范围重试。
4. `run --hotreload` 会启动 daemon；调试结束必须执行 `--hotreload stop` 或终止后台进程。
5. `check lint` 与 `check arkts` 是不同检查入口，报告时不要混称。
6. `docs search`、本地 `search_kb.py` 和普通文件搜索的覆盖范围不同，说明证据来源。
7. 报告结果时区分“命令成功”“编译通过”“静态检查通过”“设备运行成功”“UI 验证完成”。
8. ArkTS 代码不要调用已移除的 `arkts_check` 工具，使用 `devecocli check arkts`。

## Known Pitfalls

1. 官方文档的 `DEVECO_HOME` 与 CLI 实际读取的 `DEVECO_CLI_STUDIO_PATH`、`DEVECO_CLI_CLT_PATH` 不是同一层配置。
2. `deveco-code` 的依赖树可能继续携带旧 CLI；命令版本以顶层 `devecocli --version` 为准。
3. `run --apply` 与热重载仍有 DevEco Studio 6.1.1 门槛；执行前检查本机 Studio。
4. 知识库升级后路径和 schema 可能变化；使用环境变量显式覆盖比硬编码路径可靠。
5. `testing` 需要 DevEco Testing。当前未安装时，不要把它报告为技能或 CLI 损坏。
6. `raw.gitcode.com` 的 `.html` 能返回误导性 403 或 SPA 200；需要 API 时使用 v5 API 的 `download_url`。

## 推荐工作流

1. 识别任务属于文档查询、代码实现、构建、运行、UI 验证、测试或 Agent 集成。
2. 检查顶层 CLI、Code、知识库和项目配置。
3. 查询当前命令帮助与最少但足够的参考文档。
4. 先做 lint / ArkTS / 兼容性检查，再构建，再按可用设备执行运行或 UI 验证。
5. 交付时列出实际执行的命令、验证层级、未执行项和环境阻塞。
