# Upstream Sources

本技能只保留经过整理的决策信息和必要的检索工具，不复制上游完整手册。发布前或排查版本问题时核对以下来源。

| 组件 | 验证版本 | 上游 |
|---|---|---|
| DevEco CLI | 1.3.12 | [GitCode](https://gitcode.com/openharmony-sig/deveco-cli) / [npm](https://www.npmjs.com/package/@deveco/deveco-cli) |
| DevEco Code | 0.2.5 | [GitCode](https://gitcode.com/openharmony-sig/deveco-code) / [npm](https://www.npmjs.com/package/@deveco/deveco-code) |
| DevEco Studio | 推荐 6.1+ | [Huawei Developer](https://developer.huawei.com/consumer/cn/deveco-studio/) |
| Offline knowledge base | 1.3.12 | `@deveco/deveco-cli-knowledgebase` npm 包 |

## Source policy

1. 当前 CLI 行为以 `devecocli <command> --help` 和实际退出码为准。
2. `references/devecocli-1.3.12-current.md` 是 2026-11-18 的验证快照，不是永久规范。
3. 上游手册和离线文档不在本仓库中重新分发；由用户安装上游 npm 包。
4. 提交行为差异时，提供版本、操作系统、命令和脱敏后的错误输出。

