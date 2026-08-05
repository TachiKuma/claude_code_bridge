---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "10"
nature: security
severity: P2
confidence: low
recommended_action: cs-issue
---

# Finding 10：`_redacted_argv` 脱敏逻辑依赖对 argv 布局的隐含假设

## 位置

`cli.py:1403-1412`

## 证据

```python
def _redacted_argv(operation: str, command: list[str]) -> list[str]:
    if operation != "send_text":
        return list(command)
    redacted = list(command)
    if "--session" in redacted:
        session_index = redacted.index("--session")
        redacted = list(redacted[:session_index - 1]) + ["<redacted>", "--session", redacted[session_index + 1]]
    elif redacted:
        redacted[-1] = "<redacted>"
    return redacted
```

## 问题

脱敏逻辑假设 `send_text` 操作的命令格式为 `["herdr", "pane", "run", pane_id, text_content, "--session", session_name]`。当 `--session` 存在时，脱敏 `session_index - 1` 位置的元素（即 text_content）。

在以下场景会失效：如果 `--session` 是命令的第一个或第二个参数（`session_index` 为 0 或 1），`session_index - 1` 会产生负索引从列表末尾倒数——截断错误位置。例如 `["herdr", "--session", "demo", "pane", "run", "p1", "secret"]` → `session_index=1` → `redacted[:0]` 为空，导致 pane_id 和 text 全部丢失，只剩 `["--session", "demo"]`。

当前 `_json_command` 和 `_command` 方法总是将 `--session` 追加在命令末尾，所以不会触发此问题——但依赖的是调用方的隐式约定，而非脱敏函数自身的防御性。

## 影响

低——当前所有调用路径下 `--session` 均在命令末尾，不会触发。仅在未来新增调用路径或 Herdr CLI 参数顺序变化时有风险。

## 修复方向

改为按语义位置脱敏（识别 `pane run` 后的第二个参数为 text 内容），而非依赖 `--session` 的相对位置。
