---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "08"
nature: maintainability
severity: P2
confidence: low
recommended_action: cs-refactor
---

# Finding 08：`_server_status_running` 新增嵌套 `server` 状态路径，引入兼容逻辑但未标 deprecated

## 位置

`cli.py:1184-1189`

## 证据

```python
server = payload.get("server")
status = server if isinstance(server, Mapping) else payload
return bool(status.get("running") is True or status.get("status") == "running")
```

## 问题

`herdr status server --json` 的 JSON 输出格式有两种已知形态：
- 扁平：`{"status": "running", "running": true, ...}`
- 嵌套：`{"server": {"status": "running", "running": true}, ...}`

该改动添加了对嵌套格式的支持——这是正确的。但代码没有标注：
1. 哪种格式是 Herdr 的当前/未来稳定格式
2. 旧格式何时可以移除

当 Herdr 后续版本统一为一种格式时，维护者需要回溯判断哪条路径可以安全删除——而当前代码没有提供这个上下文。

## 影响

低——功能正确，只是技术债务。未来重构时容易保留死代码。

## 修复方向

加注释标注格式来源和 deprecation 计划：
```python
# Herdr 0.7.5: {"status":"running",...}
# Herdr 0.8+:   {"server":{"status":"running",...}}  (nested)
server = payload.get("server")
status = server if isinstance(server, Mapping) else payload
```
