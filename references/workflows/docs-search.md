# 文档与 API 检索

用于 HarmonyOS API、ArkTS/ArkUI 用法、版本差异、错误码和最佳实践查询。

## 查询流程

1. 提取精确符号或概念：类名、接口名、模块名、错误码、中文主题。
2. 先搜索目录，再搜索关键词：

```powershell
devecocli docs catalog --format json
devecocli docs search RelationalStore --format json --limit 10
devecocli docs search "关系型数据库" --catalog harmonyos-references --format json
```

3. 用搜索返回的 `documentId` 读取完整正文：

```powershell
devecocli docs read "<documentId>"
```

4. 正文过长或需要本地检索时使用：

```powershell
python scripts/search_kb.py -k RelationalStore --mode both --format json
python scripts/search_kb.py -k "页面" "Page" --mode both --format json
```

## 搜索策略

- 先搜精确英文符号，再搜中文名称或同义词。
- API 查询优先限定 `harmonyos-references`；教程和最佳实践使用对应 catalog。
- 搜索结果只有 snippet，不足以支撑结论时必须 `docs read`。
- 同时涉及 ArkTS 与 C API 时分别核对，不要混用签名和错误码。
- 以工程 `compatibleSdkVersion` / `targetSdkVersion` 判断 API 是否可用。
- 涉及废弃、替代或版本门槛时，必须读到正文中的版本说明。

## 引用要求

回答中保留至少一种可核验来源：

- `documentId`
- 本地文档路径
- 文档标题和 catalog

不要只写“官方文档说”。不要凭记忆补齐未检索到的参数、返回值或错误码。

## 边界

- 文档查询不触发 build、run 或工程修改。
- 搜索提示存在新文档版本时，不自动执行 `docs update`。
- 文档与运行时行为冲突时，以本机 CLI/SDK 实际行为为准，并说明差异。
- 找不到文档时，明确报告检索词、catalog 和未命中，不要编造结论。