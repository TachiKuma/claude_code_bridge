---
doc_type: audit-finding
audit: 2026-07-25-windows-rmux-native-backend
finding_id: "bug-01"
nature: bug
severity: P1
confidence: high
suggested_action: cs-issue
status: open
---

# Finding 01：Windows additive patch 忽略 rmux respawn 后的规范 pane id

## 速答

`additive_patch_windows` 在新工具 pane 和 sidebar pane respawn 后只把返回值当布尔值使用；rmux 适配层可能返回规范化后的 replacement pane id，后续 identity 和 created_panes 仍写旧 pane id，可能导致新增窗口/工具 pane 的运行时归属证据落到错误 pane。

## 关键证据

- `lib/ccbd/services/project_namespace_runtime/backend.py:527` — `replacement = respawn(...)` 后会读取返回值。
- `lib/ccbd/services/project_namespace_runtime/backend.py:529` — `replacement_pane_id.startswith('%')` 时进入 replacement 分支。
- `lib/ccbd/services/project_namespace_runtime/backend.py:531` — rmux 分支返回 `_canonical_mux_pane_id(...)`，即返回值可以是规范 pane id 字符串，而不只是 `True/False`。
- `lib/ccbd/services/project_namespace_runtime/materialize_topology.py:786` — 相邻路径显式读取 `replacement_text` 并在 `startswith('%')` 时更新 `pane_id`。
- `lib/ccbd/services/project_namespace_runtime/additive_patch_windows.py:307` — 新工具 pane 路径只执行 `if not respawn_pane(...)`，没有保存 replacement。
- `lib/ccbd/services/project_namespace_runtime/additive_patch_windows.py:319` — 随后仍 `_append_unique(created_panes, pane_id)`，记录旧 pane id。
- `lib/ccbd/services/project_namespace_runtime/additive_patch_windows.py:419` — sidebar 路径同样只把 `respawn_pane(...)` 当布尔值，成功即 `return`，不传播 replacement。

## 影响

触发条件是 Windows/rmux 下 additive patch 使用 `%0` 这类 index alias 或 rmux 返回 replacement pane id。后续 `apply_pane_identity`、`created_panes` 和 patch diagnostics 可能继续引用旧 id，进而影响 supervision、reload 后续补丁和用户可见的 pane 归属信息。

## 修复方向

让 `additive_patch_windows` 与 `materialize_topology` 使用同一套 replacement 处理逻辑：捕获 `respawn_pane()` 返回值，若是 `%...` 则更新本地 `pane_id` 后再写 identity 和 created_panes。

## 建议动作

`cs-issue`，因为这是已定位的行为错误，修复范围集中且应补一条 rmux replacement additive patch 回归测试。
