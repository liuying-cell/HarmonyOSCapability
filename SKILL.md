---
name: harmonyos-capabilities
description: >-
  Use for HarmonyOS NEXT work that needs the local DevEco toolchain: project
  inspection, ArkTS/ArkUI changes, checks, build/run, logs, UI testing,
  signatures, and HarmonyOS docs. Trigger on HarmonyOS, 鸿蒙, DevEco, ArkTS,
  ArkUI, devecocli, or deveco. Do not use for generic TypeScript/Android work
  or pure visual replication without build/run/debug; defer that to the
  visual-replica skill.
metadata:
  short-description: 鸿蒙应用开发、构建、调试与文档检索
---

# 鸿蒙能力（HarmonyOS Capabilities）

先按任务类型选择工作流，只读取对应的参考文档。涉及本机工具链时，先核对实际环境。

## 核心不变量

1. 命令参数以运行时 `devecocli <command> --help` 为最高事实源；快照和手册只作兜底。
2. 未实际执行的步骤不得报告为成功。编译、静态检查、安装、启动、UI 验证是不同证据层级。
3. 同一故障在同一层最多尝试两次；第二次仍无新增信息时停止，输出真实错误、缺失条件和下一步。
4. 更新 CLI、安装插件、生成签名、接受许可证、下载镜像属于状态变更，只在当前任务确有需要时执行。
5. 使用 `run --hotreload` 后必须执行 `run --hotreload stop` 或终止对应后台进程。
6. `docs search`、本地 `search_kb.py` 和普通文件搜索覆盖范围不同；说明实际使用的来源。
7. 纯视觉复刻且无需构建、运行或调试时，优先使用会话可用的视觉复刻技能。未安装时按原任务范围处理。

## 最小预检

代码修改、构建、运行、日志或 UI 任务，先执行：

```powershell
python scripts/doctor.py --project "<project>" --format json
python scripts/project_snapshot.py --project "<project>" --format json
```

示例从 Skill 根目录运行，将 `<project>` 替换为项目路径。日志和设备任务按需采集工程快照。仅查询文档时直接走检索流程，路径或工具不可用时再用 `doctor.py` 诊断。命令参数不确定时执行：

```powershell
devecocli <command> --help
```

## 任务路由

| 用户意图 | 首先做什么 | 读取 | 完成证据 |
|---|---|---|---|
| 查 API、ArkTS/ArkUI 用法、版本差异 | 搜当前文档，再读完整正文 | [docs-search.md](references/workflows/docs-search.md) | 文档 ID / 路径与结论 |
| 修改 ArkTS/ArkUI 代码并做静态检查 | 读工程配置，改最小范围，先跑目标检查 | [code-check.md](references/workflows/code-check.md) | L2 |
| 构建、打包、新工程 | 确认 product、module、build mode、签名 | [build-run.md](references/workflows/build-run.md) | L3 |
| 安装、启动、崩溃与日志 | 确认设备和 bundle，复现后读日志 | [device-log-ui.md](references/workflows/device-log-ui.md) | L4 |
| UI 自动化、截图、界面验证 | 先拿 layout/find，再执行操作和断言 | [device-log-ui.md](references/workflows/device-log-ui.md) | L5 |
| 设计稿转 ArkUI、页面导入 | 先读 CLI 自带完整工作流并 inspect | [design2arkts.md](references/workflows/design2arkts.md) | 检查/构建/视觉证据 |
| DevEco Agent 工具、Skill、MCP、插件 | 先确认当前会话实际可用的工具 | [agent-integration.md](references/workflows/agent-integration.md) | 配置或命令证据 |
| 环境、SDK、CLI、知识库异常 | 运行 doctor，检查版本和路径 | [environment.md](references/workflows/environment.md) | 探测结果与阻塞项 |
| 版本兼容性判断 | 以运行时帮助和本机版本为准 | [versions.md](references/versions.md) | 版本与命令来源 |

离线知识库的具体检索方式和 JSON 输出见 [knowledge-base.md](references/knowledge-base.md)。

## 证据等级

```text
L0 未执行
L1 代码已修改
L2 lint / ArkTS / compat 检查通过
L3 build 通过
L4 安装并启动成功
L5 日志、UI 或测试验证完成
```

没有连接设备时，最多报告到 L3，并明确“未运行、未验证 UI”。设备存在但应用未启动时，不得报告 L4。

## 交付格式

```text
任务：
修改：
执行命令：
证据等级：
未验证项：
环境阻塞：
```

## 禁止事项

- 不要调用已移除的 `arkts_check`；ArkTS 静态检查使用 `devecocli check arkts`。
- 不要把 `check lint`、`check arkts`、`check compat` 混为一谈。
- 不要在没有设备时声称 `run`、日志或 UI 验证成功。
- 不要自动接受模拟器许可证、下载大体积镜像或覆盖签名配置。
- 不要把旧版命令手册当作当前参数来源；先运行当前 `--help`。
- 不要因为文档搜索提示可更新，就自动执行 `devecocli docs update`。