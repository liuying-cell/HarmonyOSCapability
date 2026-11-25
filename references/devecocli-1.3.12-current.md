# DevEco CLI 1.3.12 当前命令参考

核查日期：2026-11-18  
实测版本：`devecocli 1.3.12`、`deveco 0.2.5`

本文件记录 2026-11-18 实测的 CLI 帮助、关键变化和常见操作边界。参数冲突时，以本机 `devecocli <command> --help` 为准；升级 CLI 后应重新核查本文件。

## 目录

- [顶层命令](#顶层命令)
- [1.3.2 快照后的主要变化](#132-快照后的主要变化)
- [稳定命令](#稳定命令)
- [环境与版本注意事项](#环境与版本注意事项)

## 顶层命令

`devecocli --help` 列出以下 19 个主要命令，以及 `help [command]` 元命令：

| 命令 | 用途 |
|---|---|
| `build` | 构建 HarmonyOS 工程 |
| `run` | 构建并在已连接设备或模拟器上运行 |
| `update` | 更新 DevEco CLI |
| `device` | 管理已连接设备 |
| `emulator` | 管理模拟器和场景参数 |
| `auth` | 登录、登出、状态和团队操作 |
| `skills` | 管理 HarmonyOS skills |
| `plugin` | 管理白名单 AI Agent 插件 |
| `log` | 获取设备应用日志 |
| `create` | 创建 HarmonyOS 工程 |
| `init` | 安装内置 skills 或配置 deveco-mcp |
| `serve` | 启动辅助协议服务 |
| `docs` | 搜索、读取、列出和更新文档 |
| `ui` | 检查并操作设备 UI |
| `check` | 运行 DevEco 项目检查 |
| `signature` | 生成应用签名 |
| `design2arkts` / `d2a` | 设计解析、Skill 管理和 ArkUI 页面导入导出 |
| `verify` | 在设备上运行 UI 验证 |
| `testing` | 透传 DevEco Testing CLI |

## 1.3.2 快照后的主要变化

### 新增顶层命令

#### `plugin`

管理白名单 AI Agent 插件：

- `plugin list`：列出白名单插件及已下载版本
- `plugin install <name>`：为检测到的 Agent 安装插件
- `plugin update <name>`：更新插件
- `plugin uninstall <name>`：运行插件卸载钩子

#### `design2arkts` / `d2a`

设计到 ArkUI 工作流，常用子命令：

- `workflow`：读取当前 Agent 的内置完整工作流
- `resolve`：保存本地输入或从已配置 MCP 获取设计快照
- `export` / `import`：导出或导入 ArkUI 页面
- `inspect`：验证输入和资源，报告覆盖范围
- `preview`：截取当前设备画面
- `register` / `registry` / `skills`：管理项目私有 Skill
- `doctor` / `configure` / `mcp`：诊断和配置项目
- `recognize` / `score` / `scoring-workflow`：识别与视觉校准
- `resources` / `verify` / `report`：资源准备、验证和报告
- `arkui2hds`、`react-to-arkui`、`solution-design`：迁移与方案准备

通用参数：

- `--project <path>`
- `--directory <design2arkts|d2a|design2arkui>`
- `--output <text|json>`

#### `verify`

在已连接设备上执行 UI 验证：

- `--test-plan <plan>`：自然语言步骤和预期结果
- `--bundle-name <name>`
- `--device <name|serial>`
- `--no-fresh-start`
- `verify init`：配置视觉模型
- `verify log`：按 ID 获取验证日志
- `verify screenshot`：按 ID 保存截图
- `verify appanalyzer`：执行应用和元服务健康检查

#### `testing`

将后续参数原样传给 DevEco Testing CLI。该命令要求安装 DevEco Testing，或设置 `DEVECO_TESTING_HOME`。未安装时 CLI 会直接报告环境缺失。

### 新增或变化的重要子命令

#### `check`

当前子命令：

- `check lint [path]`：DevEco Code Linter，检查 TS/ArkTS
- `check arkts [files...]`：直接检查 `.ets` 源码
- `check compat [files...]`：按文件、模块或工程扫描 SDK 兼容性

`lint` 和 `arkts` 不能混为一谈。`arkts_knowledge_search`、`check_ets_files` 不是当前官方命令。

#### `docs`

当前子命令：

- `docs search <keywords...>`
- `docs read <documentId>`
- `docs catalog`
- `docs update`

`docs update` 会更新兼容版本的文档。迁移知识库后，优先用 `DEVECO_CLI_DOCS`、`DEVECO_CLI_INDEX` 或显式路径，而不是修改脚本常量。

#### `init`

当前选项：

- `--agent <agents>`：逗号分隔的 Agent 列表；省略时安装到可用 Agent
- `--project <path>`：项目根目录
- `--path <path>`：直接安装目录，不能和 `--project` 或 `--agent` 同用
- `--skill`：安装全部内置 skills
- `--mcp`：只配置 deveco-mcp
- `--with-homegraph`：配置 HomeGraph MCP 并安装 homegraph CLI
- `-f, --force`：替换既有 Skill 或 MCP 配置

#### `run`

关键选项：

- `--module <modules...>`
- `--device <device>`
- `--product <product>`
- `--build-mode <debug|release>`
- `--ability <ability>`
- `--uninstall`
- `--skip-build`
- `--apply <fileName>`：通过 quickfix 增量部署并重启
- `--hotreload [action]`：启动热重载模式；`stop` 停止 hvigor daemon
- `--hotreload-apply <fileName>`：不重启应用，热编译并 quickfix
- `--debug-line`：向 hvigor 传递 `debugLine=true`

热重载结束必须停止后台 daemon。修改 `@State` 等状态逻辑后，不应假设热重载已经应用。

## 稳定命令

`build`、`device`、`emulator`、`ui`、`log`、`create`、`signature`、`auth`、`skills`、`serve` 和 `update` 的参数会随版本变化。本仓库不复制上游手册，执行前按以下顺序确认：

```powershell
devecocli <command> --help
devecocli <command> <subcommand> --help
```

常用入口：

- 构建：`devecocli build --help`
- 运行：`devecocli run --help`
- 设备与模拟器：`devecocli device --help`、`devecocli emulator --help`
- 静态检查：`devecocli check lint --help`、`devecocli check arkts --help`
- UI 检查与验证：`devecocli ui --help`、`devecocli verify --help`
- 日志：`devecocli log --help`

执行构建或部署前，先读取工程根目录的 `build-profile.json5`、`oh-package.json5`、模块 `module.json5` 和签名配置。

## 环境与版本注意事项

- 顶层 `devecocli` 为 1.3.12。
- `deveco-code` 0.2.5 的依赖仍钉在 `@deveco/deveco-cli` 1.3.4。
- 不要根据嵌套依赖版本判断实际执行的 CLI。
- 用 `where.exe devecocli`、`devecocli --version` 或 `Get-Command devecocli` 确认 PATH 命中位置。
