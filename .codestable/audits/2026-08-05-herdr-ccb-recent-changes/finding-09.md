---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "09"
nature: security
severity: P1
confidence: medium
recommended_action: cs-issue
---

# Finding 09：错误 detail 中的 restore_token 可能在异常链中泄露到日志

## 位置

`cli.py:135-148`, `cli.py:120-176`

## 证据

`_create_session` 中 workspace 回验逻辑（行 140-148）：

```python
if not any(
    str(item.get("workspace_id") or "").strip() == namespace_id
    for item in self._workspaces(session_name=session_name)
):
    raise self._failed(
        "create_session",
        f"Herdr workspace {namespace_id!r} was not found after creation",
        session_name=session_name,
    )
```

返回的 `restore_token`（行 173）形如 `ccb-herdr-avaprintdesigner-source-dev::w1`——这本身不是 secret。但在其他操作中，`_failed` 的 `detail` 可能包含敏感信息。

更关键的：`_command_error_category`（行 1376-1386）基于 `detail` 文本判断分类，而 `detail` 来自 Herdr CLI 的 stderr。如果 Herdr 在错误输出中包含 token 类参数（Herdr CLI 自身目前不涉及 token，但未来可能变化），这些内容会被包装到 `MuxCommandErrorV2.detail` 中，随后传播到上层日志。

## 影响

中等——目前 Herdr CLI 的错误输出不包含敏感信息，但当前代码没有防护机制。一旦上游 Herdr CLI 改变错误输出格式，可能引入信息泄露。

## 修复方向

在 `_command_evidence` 和 `_failed` 方法中增加对 restore_token 模式（`*::*`）的脱敏处理；或在 MuxCommandErrorV2 构造时通用脱敏 detail 字符串。
