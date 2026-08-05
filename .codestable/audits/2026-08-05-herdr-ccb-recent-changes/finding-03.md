---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "03"
nature: bug
severity: P1
confidence: medium
recommended_action: cs-issue
---

# Finding 03：`_attach_namespace` 前台附着错误分类粗糙

## 位置

`cli.py:758-772`

## 证据

```python
command = [executable, "session", "attach", session_name]
try:
    self._run_fn(command, check=True)
except (OSError, subprocess.SubprocessError) as exc:
    detail = f"Herdr foreground attach failed for session {session_name!r}"
    if isinstance(exc, subprocess.CalledProcessError):
        detail = (exc.stderr or exc.stdout or detail).strip() or detail
    raise MuxCommandErrorV2(
        category=_command_error_category(detail, expect_json=False),
        ...
    ) from exc
```

## 问题

`_command_error_category(detail, expect_json=False)` 在 `expect_json=False` 时始终返回 `"command-failed"`（除非 detail 包含 not-found 等关键词）。但 `herdr session attach` 失败可能的原因很广：

- **session 不存在** → 应当返回 `"not-found"`
- **session 已在其他位置附着** → 应当返回有意义分类
- **连接超时 / permission denied** → 不同类别

当前 stderr 文本被用作 `_command_error_category` 的输入——依赖于 Herdr CLI 在 stderr 中输出包含 `"not found"` 等关键词的可读文字。但若 Herdr 输出的是 JSON 错误（如 `{"error": {"code": "not_found"}}`），`_command_error_category` 会命中 `"not_found" in lowered`（行 1380），正确分类。但若 Herdr 返回的 stderr 是简短错误码或空字符串，分类将 fallback 到 `"command-failed"`，上游 caller 可能无法正确重试或回退。

## 影响

中等——`herdr session attach` 的非零退出码会被泛化归类为 `command-failed`，阻止上游做准确的状态判断和重试策略。

## 修复方向

尝试解析 stderr 为 JSON，从结构化错误中提取分类；或至少将 `"attach"` 和 `"session"` 关键词纳入分类判断。
