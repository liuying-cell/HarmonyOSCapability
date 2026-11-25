# 设备、日志与 UI 验证

用于连接设备、启动应用、诊断崩溃和进行 UI 自动化。

## 设备发现

```powershell
devecocli device list --format json
devecocli emulator list --format json
devecocli device view --format json
```

多设备时必须显式传 `--device`。设备名称和 serial 以当前命令输出为准，不要从旧记录复制。

## 模拟器

```powershell
devecocli emulator list --format json
devecocli emulator start "<name>"
devecocli emulator license view
```

以下操作会改变本机状态，只在当前任务需要且用户意图明确时执行：

```powershell
devecocli emulator license accept
devecocli emulator image download --device-type phone --os-version "<version>"
```

许可证未接受或镜像缺失时，报告为环境阻塞。不要循环重试，也不要自动接受协议。

## 日志

```powershell
devecocli log --device "<serial>" --bundle-name "<bundle>" --tail 2000
devecocli log --device "<serial>" --bundle-name "<bundle>" --crash --format json
devecocli log --device "<serial>" --bundle-name "<bundle>" --level E --from 5m
```

先限定设备和 bundle，再按时间、级别或关键词收窄。不要无过滤拉取无限日志。

## UI 检查

```powershell
devecocli ui layout --device "<serial>" --format json --mode simplified
devecocli ui find "text=Login,type=Button" --device "<serial>" --format json
devecocli ui click --device "<serial>" --selector "text=Login,type=Button"
devecocli ui screenshot --device "<serial>" --path "work/screenshots"
```

操作前先确认目标节点在当前屏幕内。`layout` 默认只返回屏幕节点；目标不可见时使用 `scrollsearch` 或先滚动。

常用 selector：

- `text=Login`
- `text*=Log`
- `type=Button`
- `text=Login,type=Button`
- `id=<id>`
- `xpath=...`

含逗号、方括号或引号的值需要加引号，必要时使用 `base64=`。

## 自动验证

```powershell
devecocli verify --bundle-name "<bundle>" --device "<serial>" --test-plan "打开应用，进入设置，确认版本号可见"
devecocli verify screenshot --id "<verification-id>" --path "work/screenshots"
devecocli verify log --id "<verification-id>"
```

自然语言测试计划必须包含可观察的预期结果。视觉模型未配置时先执行 `devecocli verify init`，并把它作为状态变更告知用户。

## 完成标准

- L4：应用已安装并成功启动。
- L5：关键操作、预期结果、截图或 layout 证据齐全。
- 断言失败时保留失败步骤、实际画面和日志；不要把“界面能打开”当作测试通过。