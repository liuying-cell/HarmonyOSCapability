# 版本与事实源

## 当前核查基线

2026-11-23 本机实测：

- `devecocli 1.3.12`
- `deveco 0.2.5`

这是本机验证基线。需要核对工具链时，运行 `python scripts/doctor.py --format json`。

已记录的命令变化见 [DevEco CLI 1.3.12 命令参考](devecocli-1.3.12-current.md)，来源和许可证见 [Upstream Sources](upstream-sources.md)。

## 事实源优先级

1. 当前 `devecocli <command> --help`
2. 当前已安装离线文档
3. 当前 CLI / SDK 的实际输出
4. 本文件的版本摘要
5. 历史手册和旧快照

发生冲突时，采用优先级更高的来源，并在结果中说明差异。

## 已知版本边界

- `deveco-code` 的依赖树可能携带不同于顶层 `devecocli` 的 CLI 版本。
- 判断命令能力时以 PATH 中实际命中的顶层 `devecocli --version` 为准。
- `run --apply`、`--hotreload`、`--hotreload-apply` 依赖本机 Studio/CLI 组合；执行前先看当前 `run --help`。
- `testing` 依赖独立安装的 DevEco Testing 或 `DEVECO_TESTING_HOME`。
- `docs` 命令可能提示存在新文档版本；是否更新由当前任务和用户意图决定。

## 漂移检查

```powershell
python scripts/doctor.py --format json
python scripts/validate_skill.py --format json
```

更新 CLI 或知识库后，重跑：

```powershell
devecocli --help
devecocli build --help
devecocli run --help
devecocli check --help
devecocli docs --help
devecocli ui --help
devecocli design2arkts --help
```

只更新实际发生变化的工作流，不把完整帮助重新复制到 `SKILL.md`。