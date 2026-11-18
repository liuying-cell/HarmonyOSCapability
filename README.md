# HarmonyOS Capability Skill

面向 Codex 的 HarmonyOS NEXT 开发技能，集中整理 DevEco CLI、DevEco Code、ArkTS、ArkUI、设备调试、UI 验证和离线文档检索中真正影响操作决策的信息。

这是一个社区项目，不是华为、HarmonyOS 或 OpenHarmony 官方项目。

## 能力范围

- 识别当前 HarmonyOS 工程、SDK、模块、设备和签名状态。
- 使用 `devecocli` 完成创建、检查、构建、运行、日志、UI 检查和设备验证。
- 区分 lint、ArkTS 检查、编译、设备运行与 UI 验证等不同完成层级。
- 检索 DevEco CLI 分发的离线 HarmonyOS Markdown 文档与 SQLite 索引。
- 避免已废弃的工具名、旧版本参数和硬编码知识库路径。

这个技能不会替用户安装 DevEco Studio、SDK、HarmonyOS 设备驱动或签名材料，也不会把静态检查结果冒充为真机验证结果。

## 兼容基线

| 组件 | 2026-11-18 验证版本 | 说明 |
|---|---|---|
| Codex Skills | `SKILL.md` + `agents/openai.yaml` | 支持 `$harmonyos-capabilities` 调用 |
| Node.js | 22 或更高 | DevEco CLI 与 DevEco Code 的前置条件 |
| DevEco CLI | 1.3.12 | 命令为 `devecocli` |
| DevEco Code | 0.2.5 | 命令为 `deveco` |
| DevEco Studio | 推荐 6.1 或更高 | 构建、模拟器和真机运行依赖 Studio 工具链 |

DevEco 工具更新较快，版本差异应优先以本机 `devecocli <command> --help` 为准。

## 安装

### Windows

```powershell
git clone https://github.com/liuying-cell/HarmonyOSCapability.git "$env:USERPROFILE\.codex\skills\harmonyos-capabilities"
```

### macOS / Linux

```bash
git clone https://github.com/liuying-cell/HarmonyOSCapability.git "$HOME/.codex/skills/harmonyos-capabilities"
```

目标目录必须名为 `harmonyos-capabilities`，并且直接包含 `SKILL.md`。安装后重新打开 Codex 或新建一个线程，让技能目录重新加载。

更新已安装技能：

```powershell
git -C "$env:USERPROFILE\.codex\skills\harmonyos-capabilities" pull --ff-only
```

## 使用

显式调用：

```text
$harmonyos-capabilities 检查当前鸿蒙工程的环境、模块配置和可用设备，然后执行 ArkTS 检查。不要部署。
```

离线文档检索示例：

```powershell
python scripts/search_kb.py -k "RelationalStore"
python scripts/search_kb.py -k "页面" "Page" --mode both
python scripts/search_kb.py -k "ArkTS" --docs-path "<PATH>/docs.zip" --index-path "<PATH>/index.zip"
```

知识库通常随 DevEco CLI 生态安装。若脚本找不到资源，先运行：

```powershell
npm list -g --depth=1 @deveco/deveco-cli @deveco/deveco-cli-knowledgebase
npm root -g
```

也可以通过 `DEVECO_CLI_DOCS`、`DEVECO_CLI_INDEX` 或 `DEVECO_CLI_ROOT` 显式指定位置。

## 安全边界

- 构建、安装、签名、设备清理和插件安装会改变本机或设备状态，应由当前任务明确授权。
- 执行前检查 `build-profile.json5`、`oh-package.json5`、模块 `module.json5` 和签名配置。
- `run --hotreload` 会启动后台 daemon，调试结束必须停止。
- 没有设备时必须把结果限定为编译、lint 或静态检查，不能声称已完成运行或 UI 验证。

## 仓库结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── devecocli-1.3.12-current.md
│   ├── knowledge-base.md
│   └── upstream-sources.md
├── scripts/search_kb.py
├── tests/
└── .github/workflows/validate.yml
```

本仓库不携带 DevEco CLI 二进制、HarmonyOS SDK、`docs.zip` 或 `index.zip`。离线文档由用户本机安装的上游包提供。

## 开发与验证

```powershell
python -m unittest discover -s tests -v
python -m py_compile scripts/search_kb.py
python -X utf8 scripts/search_kb.py --help
```

发布技能前还建议运行 Codex `skill-creator` 提供的 `quick_validate.py`。

欢迎通过 Issue 报告版本变化、命令失效或文档与运行时不一致。提交修复时请附上 `devecocli --version`、`deveco --version` 和实际命令输出中的非敏感部分。

## 许可证与声明

本仓库原创整合内容采用 MIT 许可证。涉及 DevEco CLI 与 DevEco Code 的上游事实、名称和材料遵循其 MIT 许可证，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

HarmonyOS、DevEco 和 ArkTS 等名称及商标归其各自权利人所有。本项目与华为、OpenHarmony 或 DevEco 官方团队无隶属或背书关系。

