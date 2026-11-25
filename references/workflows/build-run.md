# 构建、打包与运行

用于新工程、编译、打包、安装和启动。UI 验证转到 `device-log-ui.md`。

## 工程上下文

先执行：

```powershell
python scripts/project_snapshot.py --format json
```

确认：

- `product`
- `module` 与 `target`
- `buildModeSet`
- `compatibleSdkVersion` / `targetSdkVersion`
- `bundleName`
- 签名配置
- 默认 ability 和 `mainElement`

## 新工程

```powershell
devecocli create --app-name MyApp --project-path ./MyApp --api-level 23
```

需要多设备类型时显式传 `--device-types`。创建后读取生成的工程配置，再执行检查或构建。

## 构建

```powershell
devecocli build
devecocli build --product default --build-mode debug
devecocli build --modules entry
devecocli build --modules entry@default
```

清理输出：

```powershell
devecocli build clean --modules entry
```

## 运行

```powershell
devecocli run --device "<name-or-serial>" --module entry
devecocli run --device "<name-or-serial>" --module entry --ability EntryAbility
```

只在明确需要部署既有产物时使用 `--skip-build`。不要用它替代正常构建验证。

## 增量与热重载

```powershell
devecocli run --hotreload
devecocli run --apply "<file-under-.hvigor>"
devecocli run --hotreload-apply "<file-under-.hvigor>"
devecocli run --hotreload stop
```

结束热重载后必须执行 `stop`。修改状态逻辑或原生能力时，不假设热重载已经覆盖全部变化；关键路径重新完整构建和启动。

## 失败分流

| 症状 | 第一动作 | 禁止 |
|---|---|---|
| product/build mode not found | 回读 `build-profile.json5` | 不要猜参数 |
| no entry / multiple entry modules | 显式指定 module/target | 不要改工程结构试错 |
| install sign info inconsistent | 确认签名是否变化。需要卸载时先说明应用数据可能被清除并取得用户同意 | 不要直接覆盖证书 |
| Not logged in | 说明需要 `devecocli auth login` | 不要伪造登录状态 |
| no active device | 检查 device/emulator | 不要报告运行成功 |
| 构建错误重复出现 | 保留退出码和错误原文 | 不要无范围清缓存或连续重试 |

## 完成标准

- L3：build 命令退出码为 0，并报告 product/module/build mode。
- L4：安装和启动均由实际命令与设备状态支持。
- 没有设备或启动失败时，只报告到 L3。