---
doc_type: feature-acceptance
feature: mux-backend-contract
status: accepted
reviewer_id: "019f89b3-7b81-7571-8be7-8431d1545a27"
updated_at: "2026-07-22"
---

# mux-backend-contract Acceptance

## Acceptance Checks

- pass：contract module 定义 `MuxNamespaceRef`、`MuxPaneRef`、`MuxCapabilities`、`MuxCommandError`，且不依赖 tmux implementation module。
- pass：`MuxBackend` 由 namespace/window/pane io/presentation/logging/diagnostics 小协议组合，public protocol 不暴露 `_tmux_run(args)`。
- pass：`FakeMuxBackend` 以 namespace/window/pane 状态机和 `event_log` 覆盖 lifecycle、layout、io、presentation、logging、capabilities 与 failure injection。
- pass：leakage inventory 已记录当前 `_tmux_run` / tmux argv 泄漏点。
- pass：核心验证命令已通过，feature checklist 已更新为 `done`，goal iterations 已记录验证证据。

## Evidence

- Terminal acceptance Task agent: `019f89b3-7b81-7571-8be7-8431d1545a27`。
- Focused re-evaluation verdict: `pass`。
- Functional acceptance report: `.codestable/goals/2026-07-22-mux-backend-contract/functional-acceptance.md`。

## Delivery Record

`mux-backend-contract` 已接受。roadmap item 已写回 `done`，epic goal-state feature status 已写回 `accepted`。
