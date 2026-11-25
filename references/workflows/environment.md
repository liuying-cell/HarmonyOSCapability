# 环境与工程预检

用于 Build、Run、日志、UI、签名和 Design2ArkTS 前的环境确认。

## 快速探测

```powershell
python scripts/doctor.py --format json
python scripts/project_snapshot.py --format json
devecocli --version
deveco --version
```

只有在需要判断具体参数时才执行：

```powershell
devecocli <command> --help
```

## 读取顺序

1. 顶层 `devecocli --version` 决定当前命令能力。
2. 顶层 `deveco --version` 决定 DevEco Code 侧能力。
3. `devecocli <command> --help` 决定参数和子命令。
4. 已安装的离线文档决定 API 语义。
5. 版本快照只用于解释历史差异，不得覆盖运行时事实。

## 工程信息

`project_snapshot.py` 汇总：

- 根目录 `build-profile.json5`
- 根目录 `oh-package.json5`
- `AppScope/app.json5` 中的 bundleName 和应用版本
- product、build mode、SDK 版本和签名配置名
- module 路径、target 和 applyToProducts
- `module.json5` 中的 ability、deviceTypes、pages 和权限

脚本内置解析支持常见配置格式。遇到无法读取的 JSON5 时，直接检查对应配置文件；环境已有 `json5` 模块时脚本会尝试使用。

先根据这些信息决定 `--product`、`--module`、`--build-mode`、`--ability` 和 `--bundle-name`，不要猜测。

## 环境变量

- `DEVECO_CLI_STUDIO_PATH`：DevEco CLI 查找 Studio。
- `DEVECO_CLI_CLT_PATH`：Command Line Tools 根目录。
- `DEVECO_CLI_DOCS` / `DEVECO_CLI_INDEX`：显式指定离线文档与索引。
- `DEVECO_CLI_ROOT`：指定 npm 包根目录。
- `DEVECO_TESTING_HOME`：DevEco Testing 安装位置。
- `DEVECO_HOME`：官方文档常见配置，但不等于 CLI 实际读取的所有路径。

环境变量存在不代表路径有效；检查实际可执行文件和目标目录。

## 禁止自动执行

- 不自动执行 `devecocli update`。
- 不自动安装或更新插件。
- 不自动接受模拟器许可证。
- 不自动下载大体积系统镜像。
- 不自动覆盖已有签名材料。

## 停止条件

以下情况停止改动并报告：

- `devecocli` 或 `deveco` 不存在，且任务依赖对应能力。
- 工程配置无法解析或 product/module 不存在。
- SDK、Studio 或 CLT 版本不满足命令要求。
- 文档与索引缺失，但任务要求具体 API 结论。
- 设备侧需要用户登录、许可证确认或交互安装。