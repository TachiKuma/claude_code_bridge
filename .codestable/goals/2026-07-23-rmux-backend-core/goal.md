---
doc_type: goal
goal: rmux-backend-core
status: active
---

# rmux-backend-core Goal

## Objective

完成 `rmux-backend-core`：在 `MuxBackend` 契约下提供独立的 `RmuxBackend` production core adapter，覆盖 capability guard、command client seam、namespace/window、pane、presentation/title/user-option/style core operation、错误 evidence 和 tmux/Rmux import 边界。

## Starting Point

`rmux-daemon-ownership-boundary` 已提交。`rmux-backend-core` 的 design、design-review 和 checklist 已存在，roadmap item 为 `in-progress`。

当前代码中 `lib/terminal_runtime/rmux_backend.py` 仍继承 `PsmuxBackend` / `TmuxBackend`，并包含 `send_key`、`capture-pane`、foreground attach 相关行为；这与本 feature 的 core-only 边界冲突，需要替换为独立 core adapter。

## Acceptance Criteria

- `RmuxBackend` 不再继承或导入 `TmuxBackend` / `PsmuxBackend`，只通过 Rmux command client seam 执行 Rmux。
- capability report 缺失或 required command unsupported 时 fail-fast，抛 `MuxCommandError(category="unsupported")`，且不 fallback 到 tmux。
- namespace/window/pane/presentation core operations 返回 backend-neutral refs / records。
- command failure、malformed output、not-found、unreachable、permission 等错误有结构化 evidence。
- core 不实现 send/capture/logging/provider completion parser，不接 ccbd lifecycle 或 foreground attach。
- CMD-001 到 CMD-005 通过，并完成可见 Task agent review 与功能验收。

## Non-Goals

- 不实现 `rmux-send-capture-logging`。
- 不接入 `ccbd-rmux-namespace-lifecycle`、foreground attach 或 full-chain smoke。
- 不修改 ccbd control-plane transport。
- 不把 Rmux daemon 当成 ccbd authority。

## Decisions And Assumptions

- 采用 feature design 的分层：`rmux_backend.py` 作为 public entry，`rmux_backend_runtime/` 承载 client、capabilities、errors、namespace、panes、presentation。
- 方案深度选择 production core adapter，而不是沿用旧 psmux/tmux shim；这是长期维护的 core boundary，不能用 tmux clone 继续扩散。
- 测试用 fake Rmux command client，不依赖真实 Rmux。

## Current State

Goal active，尚未实现。

## Next Action

实现 RmuxBackend core adapter 和 focused tests。
