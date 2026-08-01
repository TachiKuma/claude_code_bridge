---
doc_type: goal
goal: sidebar-kill-project-click-e2e
status: complete
---

# sidebar-kill-project-click-e2e Goal

## Objective

完成 `sidebar-kill-project-click-e2e` 的诊断闭环与终端验收，确认当前 Windows + WezTerm + rmux 下 sidebar `x` KillProject 点击不能作为 mouse parity pass，且内部 KillProject 路径已有可复核证据。

## Starting Point

- Root-cause split: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/root-cause-review-and-feature-split.md`
- Split child: `sidebar-kill-project-click-e2e`
- 关联 settings 诊断：
  - `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-review.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/windows-rmux-ux-parity-evidence.json`
- 当前事实：
  - root-cause split 将该 child 标为 `failed`，下一步是 `design_diagnostic_feature`。
  - Rust TUI 内部已有 `header_action_at` / `handle_mouse_down` / `run_ccb_kill_with_program` 测试覆盖。
  - 真实前台 mouse route 仍受 rmux 坐标缺失与 `send-keys -M` 不透传限制，不能把 `x` click 写成 e2e pass。

## Acceptance Criteria

- 功能验收确认 Rust sidebar 内部 `x` hit-test 会返回 `ExitAction::KillProject`，且 `ccb kill` 子进程路径已有测试证据。
- 功能验收确认真实前台 click e2e 仍不能宣称通过，因为 rmux `send-keys -M` 未进入 Rust/crossterm mouse event，且普通 root binding 没有 settings/x 所需坐标或等价谓词。
- 功能验收确认本 goal 未新增 broad sidebar-left-click fallback，未把 `x` click 映射为不精确 kill 行为，也未执行真实项目 kill。
- 功能验收确认 evidence JSON 投影为 `evidence_status=blocked`、`failure_class=unsupported_capability`、`parity_dimension=foreground_interaction`。
- 功能验收确认本 goal complete 只代表 `sidebar-kill-project-click-e2e` 诊断闭环完成，不代表 epic 其他 child 完成。

## Non-Goals

- 不实现新的 rmux 或 WezTerm precise x-click route。
- 不执行真实 `ccb kill` 或关闭当前项目。
- 不修改运行时代码或测试代码。
- 不执行 git commit、push、merge、release 或 deploy。

## Decisions And Assumptions

- 用户通过 `$codestable:cs-goal sidebar-kill-project-click-e2e` 要求推进该 split child。
- 本 goal 采用 evidence-first 深度：先证明当前能力边界和已有内部路径，避免写 broad fallback。
- 如果未来 rmux / WezTerm 提供 precise x-click route，应另开 feature 实现并重新 review / QA。

## Current State

`state.yaml` 当前为 `complete`，`current_iteration=1`。Task agent 功能验收已通过，最终 iteration 已引用 `functional-acceptance.md`。

## Next Action

Goal 已完成。后续 epic 应把该 child 视为诊断闭环完成、前台 x-click parity 仍为 `blocked/unsupported_capability`；不得解读为真实 x click 已通过。
