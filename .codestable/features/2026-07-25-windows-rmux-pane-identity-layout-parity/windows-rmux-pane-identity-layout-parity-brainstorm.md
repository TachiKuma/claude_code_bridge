---
doc_type: feature-brainstorm
feature: 2026-07-25-windows-rmux-pane-identity-layout-parity
status: confirmed
summary: Windows/rmux pane identity/layout parity 先建立身份快照、绑定恢复和冲突诊断契约，不默认重写 layout/canonicalization
tags: [windows, rmux, wezterm, pane, identity, layout, canonicalization, parity, evidence]
---

# Windows Rmux Pane Identity Layout Parity Brainstorm

> Stage 0 | 2026-07-25 | 下一步：cs-feat（由主入口选择 lane）

## 想做什么、为什么

当前 roadmap 要求 `windows-rmux-pane-identity-layout-parity` 在 design 前单独完成 `$cs-brainstorm`。这个 item 的真实问题不是“再修一次 pane id”，而是 Windows/rmux 下 pane 身份、layout 重建、agent-pane 绑定在 split、respawn、reattach 后不能漂移；一旦出现 identity conflict，系统必须可诊断并 fail closed。

已有代码已经提供部分基础：

- `lib/terminal_runtime/rmux_backend_runtime/targets.py` 有 `canonical_pane_id()` / `canonical_pane_target()`，会用 `list-panes` / `display-message` 尝试把 `%N` index alias 解析成真实 pane id。
- `lib/terminal_runtime/rmux_backend_runtime/panes.py::split_pane()` 已处理 split 返回 index alias 和已有 pane id 冲突，并会在必要时从窗口 pane 列表重新解析。
- `lib/ccbd/services/project_namespace_runtime/backend.py` 仍有一套 `_canonical_mux_pane_id()` 适配逻辑，说明 canonicalization 存在重复/分散风险。
- roadmap §4.4 已定义目标 contract：`WindowsRmuxPaneIdentitySnapshot`，包含 `pane_id`、`pane_index`、`ccb_role`、`ccb_agent_id`、`canonicalization_source`。

本轮讨论收敛为 identity evidence + contract first：先把身份快照、绑定恢复和冲突诊断变成可重复证据；不默认大重构 layout authority 或重写 split/canonicalization。

## 考虑过的方向

### 方向 A：identity evidence + contract first

- 先建立 `WindowsRmuxPaneIdentitySnapshot` 证据，覆盖 exact pane id、index alias fallback、layout_state、runtime_authority 等 canonicalization source。
- 把 agent-pane binding 恢复和 identity conflict diagnostics 作为验收核心。
- 只在证据证明重复 canonicalization helper 导致真实漂移时，才把收敛 helper 纳入 design 的实现步骤。
- 价值：复用现有 `targets.py` / `panes.py` / project namespace adapter 的基础能力，避免把 layout、namespace、recovery 和 diagnostics 一次性绑成大重构。
- 代价：第一版更偏证据和契约，若发现真实漂移仍需在 design 中补实现闭环。
- 结论：选定。

### 方向 B：统一 canonicalization 重构优先

- 直接把 `targets.py` 与 `project_namespace_runtime/backend.py` 的 canonicalization 逻辑收敛到单一 helper，再补测试和证据。
- 价值：能尽早消除重复逻辑。
- 代价：当前还没有新的证据证明重复逻辑已经导致所有场景漂移；直接重构会扩大到 ccbd namespace、layout materialize 和 recovery 调用面。
- 结论：否决第一版默认方向；保留为证据触发后的候选实现步骤。

### 方向 C：layout authority 重建优先

- 把 layout state、agent registry、runtime authority 统一成新的 layout/pane identity authority。
- 价值：长期上更整洁，也能为 lifecycle recovery 铺路。
- 代价：范围明显超过当前 item，会吞掉后续 lifecycle/recovery feature；容易把 identity bug、layout bug、crash recovery bug 混在一起归因。
- 结论：否决本 item 第一版。

## 已敲定的设计点

- 已确认：本 item 采用 **identity evidence + contract first**，不默认重写 layout/canonicalization。
- 已确认：核心证据是 pane identity snapshot，而不是仅靠 split/list-panes 单测通过。
- 已确认：snapshot 至少记录 `backend_impl=rmux`、`session_name`、`window_name`、`pane_id`、`pane_index`、`ccb_role`、`ccb_agent_id`、`canonicalization_source`。
- 已确认：`canonicalization_source` 至少覆盖 `exact_pane_id`、`index_alias`、`layout_state`、`runtime_authority` 或等价枚举；index alias 只能作为 fallback，且必须记录来源。
- 已确认：agent-pane binding 恢复是核心验收点；split、respawn、reattach 后必须能证明 agent 与 pane 仍能重新关联。
- 已确认：identity conflict diagnostics 必须 fail closed；不得把同一 agent 绑定到多个 active pane，也不得把多个 active panes 归给同一 canonical identity。
- 已确认：复用 `rmux-backend-core`、`ccbd-rmux-namespace-lifecycle` 和现有 `targets.py` / `panes.py` 的 canonicalization、split alias、layout materialize 基础能力，只补 UX parity contract、binding 恢复和 conflict diagnostics。
- 已确认：owner 已批准本 brainstorm 结论，并允许进入 feature design。

## 选定方向与遗留问题

选定方向是 `windows-rmux-pane-identity-layout-parity`：建立 Windows/rmux pane identity/layout parity evidence，证明 pane identity、layout snapshot、agent-pane binding 在 split、respawn、reattach 后稳定，且冲突有可诊断 fail-closed 行为。

核心行为：

- 生成可重复的 identity/layout parity snapshot 与 UX evidence JSON，覆盖 exact pane id、index alias fallback、layout state、runtime authority。
- 验证 agent-pane binding 在 split、respawn、reattach 后可恢复。
- 验证 identity conflict 能进入 diagnostics，不会静默绑定错误 pane。

明显不做：

- 不默认重写 layout authority。
- 不默认把 `targets.py` 与 `project_namespace_runtime/backend.py` 合并；只有证据证明重复逻辑导致真实漂移时才设计收敛步骤。
- 不把 lifecycle crash recovery 纳入本 item；crash 后恢复路径留给 `windows-rmux-lifecycle-recovery-ux-parity`。
- 不把 WezTerm GUI focus/鼠标策略纳入本 item；普通 pane GUI-native 由 interaction feature 负责。

遗留给 design 的问题：

- `WindowsRmuxPaneIdentitySnapshot` 是否需要额外字段记录 `window_layout_ref`、`runtime_ref` 或 `diagnostics_ref`。
- conflict diagnostics 的机器可读 schema 是否复用 roadmap §4.1 `artifacts/residual_risks`，还是增加细粒度 identity report。
- 如果 parent `windows-rmux-wezterm-native-interaction-parity` 尚未 accepted，design 如何限制 implementation 只推进 headless identity/layout lanes。
