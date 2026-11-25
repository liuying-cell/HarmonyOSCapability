# ArkTS / ArkUI 代码检查

用于修改 `.ets` / `.ts` 代码后的静态检查，不替代构建和运行。

## 先判断检查入口

| 入口 | 用途 |
|---|---|
| `devecocli check arkts [files...]` | 检查 `.ets` 源码的 ArkTS 规则 |
| `devecocli check lint [path]` | DevEco Code Linter，检查 TS/ArkTS 代码 |
| `devecocli check compat` | 检查 SDK 版本兼容性 |

三个入口结果不可混称。

## 标准流程

1. 运行工程快照，确认模块和目标 SDK：

```powershell
python scripts/project_snapshot.py --format json
```

2. 对改动文件先做 ArkTS 检查：

```powershell
devecocli check arkts path/to/File.ets
```

3. 需要项目级 Linter 时：

```powershell
devecocli check lint path/to/file-or-directory --format json
```

4. 需要兼容性检查时先列版本：

```powershell
devecocli check compat versions --format json
devecocli check compat --source-version "<source>" --target-version "<target>" --format json
```

5. 修复后重跑同一检查。通过后再进入 build。

## 修复规则

- 先读完整错误、文件、行号和规则名。
- 只改与当前错误相关的代码，不顺带重构。
- `--fix` 只用于目标任务且改动范围可控时；运行后检查 diff。
- 错误来自 SDK 缺失、项目配置或工具环境时，先走环境流程，不修改业务代码。
- 同一错误两次修复无进展时停止，输出错误原文和最小复现。

## 完成标准

- L2：目标检查通过，且报告实际命令和范围。
- 只修改代码但未检查时保持 L1。
- 静态检查通过不等于 build 通过，更不等于设备运行成功。