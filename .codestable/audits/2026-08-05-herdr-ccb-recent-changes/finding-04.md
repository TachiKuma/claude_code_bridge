---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "04"
nature: bug
severity: P2
confidence: medium
recommended_action: cs-issue
---

# Finding 04：`_logical_workspaces` 依赖 pane token metadata，新创建的 workspace 可能尚未被 report-metadata 写入

## 位置

`cli.py:803-847`, `cli.py:120-176`

## 证据

`_create_session` 中（行 120-176）：
1. 创建 workspace → 获得 `namespace_id`
2. 通过 `self._workspaces()` 检查 workspace 是否已存在
3. 调用 `self._report_workspace_metadata()` 和 `self._report_pane_metadata()` 写入 token 标记

但 `_logical_workspaces`（行 803-847）筛选 workspace 的依据是 pane token：
```python
if (
    workspace_id
    and str(tokens.get(_ROOT_PANE_TOKEN) or "").strip() == "1"
    and str(tokens.get(_NAMESPACE_TOKEN) or "").strip() == namespace_anchor
):
    roots_by_workspace.setdefault(workspace_id, pane)
```

## 问题

存在竞态窗口：`report-metadata` 命令是异步方式执行的（通过 Herdr IPC），但 `_logical_workspaces` 通过 `pane list` 返回的 token 键值查询。如果在 `report_workspace_metadata`/`report_pane_metadata` 执行完成但 token 尚未传播到 `pane list` 返回结果之前调用 `_logical_workspaces`，会返回空列表。

这个场景在测试中可能不触发（因为 mock 同步返回），但真实环境中 `report-metadata` 是写入操作，未必立即对读操作可见。

`_create_session` 中新增的 `_workspaces()` 回验（行 140-148）部分缓解了此问题——至少确认 workspace 创建成功。但后续的 `ensure_window`、`list_windows` 等操作需通过 `_logical_workspaces` 筛选，仍受此窗口影响。

## 影响

低——触发概率受 Herdr 内部实现细节影响，在生产环境中不太常见。仅在 `pane list` token 传播延迟 > 代码执行间隔时触发。

## 修复方向

`_create_session` 后可选执行一次短等待/重试，确保 metadata 已传播；或在 `_logical_workspaces` 的筛选逻辑中增加从 `workspace list` 直接匹配的回退路径。
