---
doc_type: goal
goal: rmux-daemon-ownership-boundary
status: active
---

# rmux-daemon-ownership-boundary

## Objective

继续 windows-rmux-native-backend epic 中的 `rmux-daemon-ownership-boundary`，定义并实现 Rmux daemon discovery、start、health、crash、cleanup 的 ownership 和 diagnostics evidence，推进到可见 Task agent review 与功能验收完成。

## Starting Point

- `provider-runtime-backend-session-contract` 已提交：`5c4a808e feat: add provider runtime backend session contract`。
- Roadmap item `rmux-daemon-ownership-boundary` 当前为 `in-progress`。
- Feature design、design-review、checklist 已存在，design-review passed。
- 代码尚未实现 `RmuxDaemonRef`、`RmuxDaemonEvidence`、`RmuxCleanupPlan` contract、cleanup scope policy、`backend_daemon_*` diagnostics projection 和 focused tests。

## Acceptance Criteria

- 新增 Rmux daemon evidence contract，覆盖 discovery source、daemon ref、endpoint、health、crash reason、cleanup scope 和 diagnostics。
- start_result 成功/失败 evidence 覆盖 endpoint、version、capability status、`unreachable|crashed` 映射，且不改变 ccbd owner / lease generation。
- Rmux daemon pid / endpoint 不得成为 ccbd lease holder 或 lifecycle owner。
- cleanup plan 默认 namespace/project scope，shared daemon 默认 `daemon_action=leave_running`；daemon-wide cleanup 只有 explicit force 才允许，并记录 force reason diagnostics。
- `backend_daemon_*` diagnostics 不覆盖 ccbd `daemon_*`、namespace `namespace_*` 或 `tmux_socket_path` 字段。
- Rmux daemon crashed/unreachable 只降级 backend diagnostics，不自动标记 ccbd unhealthy。
- CMD-001 到 CMD-005 通过，并通过可见 Task agent review 与功能验收。

## Non-Goals

- 不实现 RmuxBackend core、send/capture/logging、layout、foreground attach、Rmux IPC 或 named pipe ACL。
- 不启动真实 Rmux daemon，不调用 Rmux CLI/SDK。
- 不修改 ccbd control-plane transport。
- 不把 Rmux daemon 作为 ccbd lease holder、keeper 或 runtime registry owner。
- 不删除或改写现有 tmux cleanup history。

## Decisions And Assumptions

- 本 feature 是 contract/evidence 层，不是 Rmux backend core 实现。
- ccbd authority 继续由 `OwnershipGuard`、lease、keeper lifecycle 和 namespace state 管理；Rmux daemon evidence 只能作为 backend diagnostics。
- 方案深度按长期维护 contract 处理：使用 typed helpers 和 deterministic tests，不使用占位 schema 或仅文档声明。

## Current State

Goal 已创建，尚未开始 implementation iteration。

## Next Action

实现 `terminal_runtime/rmux_daemon_contract.py`，补 daemon evidence、cleanup plan、diagnostics projection 与 focused tests。
