# Design2ArkTS

用于设计稿、Figma/Pixso/MasterGo 页面、ArkUI 导入和视觉校准。

## 先读内置工作流

Design2ArkTS 自带完整工作流。不要凭记忆重写流程：

```powershell
devecocli design2arkts workflow
```

输出中的 `instructionPath` 和 `integrationPath` 必须先读，然后只加载当前 stage 需要的文件。

## 环境检查

```powershell
devecocli design2arkts doctor --output json
devecocli design2arkts skills
python scripts/project_snapshot.py --format json
```

确认：

- 当前工程可发现
- Design2ArkTS 运行时与引擎校验通过
- source MCP / Figma / Pixso 配置可用
- 导出的目标模块存在
- 设备可用（仅当需要 preview、run 或 visual check）

## 标准阶段

1. `resolve`：保存本地输入或获取设计快照。
2. `inspect`：检查输入、资源和分析覆盖率。
3. `export`：从已验证快照导出 ArkUI 页面。
4. `resources`：准备图片、字体等资源。
5. `verify`：验证产物和显式请求的检查。

只执行当前任务需要的阶段，不要无目的跑全流程。

## 验证

```powershell
devecocli design2arkts verify --run "<run-id>" --page-name "<page>" --checks arkts,lint,build,run,visual --module entry --device "<serial>"
```

`--checks` 只执行列出的项。没有列出 run/visual 时，不得报告运行或视觉验证完成。

## 边界

- 纯视觉复刻且不需要工具链构建/运行/调试时，交给视觉复刻技能。
- 需要工程集成、构建或设备验证时，由本技能接手。
- 不修改引擎校验、不覆盖 source 配置、不自动安装私有 Skill。
- 视觉评分只能作为证据之一，不能替代构建、运行和用户可观察行为。