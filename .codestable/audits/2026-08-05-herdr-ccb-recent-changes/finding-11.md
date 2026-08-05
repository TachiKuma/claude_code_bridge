---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "11"
nature: performance
severity: P2
confidence: medium
recommended_action: cs-refactor
---

# Finding 11：`_logical_workspaces` 在 create→ensure→list 链路中重复查询 workspaces

## 位置

`cli.py:120-176` (`_create_session`), `cli.py:221-354` (`_ensure_window`), `cli.py:198-219` (`_list_windows`), `cli.py:803-847` (`_logical_workspaces`)

## 证据

CCB 的典型启动调用链：`create_session` → `ensure_window` × N → `list_windows`。

每个操作都独立调用 `_logical_workspaces`，而 `_logical_workspaces` 内部每次都执行：
1. `self._workspaces()` — Herdr CLI `workspace list` 调用
2. `self._panes()` — Herdr CLI `pane list` 调用（全量 pane 列表）

以 2 个 agent 为例，调用链为：
- `create_session`: 1 次 workspaces + 1 次 panes
- `ensure_window` × 3 (main + 2 agents): 3 次 workspaces + 3 次 panes
- `list_windows`: 1 次 workspaces + 1 次 panes

共计 **5 次 workspaces + 5 次 panes** Herdr CLI 调用。每次调用都是独立的子进程 fork + JSON 解析。尤其在 `_start_server` 的重试循环中（行 1064 最多 10 次重试），更放大了调用次数。

## 影响

低——Herdr CLI 子进程调用开销小（< 50ms/次），且 CCB 启动不属于热路径。但在 Herdr 负载高或 session 内 workspace/pane 数量大时（>100），累积延迟可能明显。

## 修复方向

在 session 生命周期内缓存 `_workspaces()` 和 `_panes()` 结果（100-200ms TTL），或为批量操作（create_session + N × ensure_window）提供一次传入 workspace/panes 快照的批量接口。
