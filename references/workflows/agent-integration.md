# DevEco Agent 集成

用于 DevEco Code 的工具、Skill、MCP、插件和 Goal 模式。

## 先确认真实能力

当前会话可能没有连接 DevEco Code 的同名工具。先检查会话工具，再检查 CLI：

```powershell
devecocli --version
deveco --version
devecocli init --help
devecocli plugin --help
devecocli skills --help
```

CLI 可用时，优先通过等效 `devecocli` 流程完成任务，不要因为缺少某个 Agent 工具就停止。

## 已知开发工具

常见工具包括：

- `build_project`
- `start_app`
- `hdc_log`
- `verify_ui`
- `switch_cwd`

内置 `arkts_check` 已移除，ArkTS 检查使用 `devecocli check arkts`。

## 安装与配置

```powershell
devecocli init --skill
devecocli init --mcp
devecocli init --mcp --with-homegraph
devecocli init --path "<target>" --skill
devecocli plugin list
devecocli skills list -l
devecocli skills find arkui
```

`init`、`plugin install`、`skills add` 会改变 Agent 或工程配置，只在用户明确要求时执行。覆盖现有内容时先确认 `--force` 的影响。

## 内置设计能力

常见技能名称包括：

- `hmos-arkui-develop-skill`
- `deveco-create-project`
- `arkts-runtime-fix`
- `hmos-design-to-arkts`
- `customize-deveco`

旧名称 `arkts-grammar-standards`、`arkts-error-fixes` 不要继续使用。实际安装列表以当前 `devecocli init`、`skills list` 和会话工具为准。

## Goal 模式

用户明确要求 SDD / Goal 模式时，再按“需求分析 → 架构设计 → 任务分解 → 代码实现 → 功能验证”推进。没有设备时，把验证限定为静态检查或构建。

## 边界

- 不自动安装、更新或卸载插件。
- 不把 UI 展示名称当作已连接工具。
- 不把 Skill 指导当作执行证据。
- 不绕过当前 CLI 和真实工程状态。