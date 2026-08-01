---
doc_type: goal
goal: ccbd-rmux-namespace-lifecycle
status: active
---

# ccbd-rmux-namespace-lifecycle

## Objective

将已验收的 `RmuxBackend` 接入 `ccbd` 的 project namespace lifecycle，完成 `ensure`、layout projection、foreground attach 和 `ccb kill` 的用户可见闭环。

## Starting Point

`ccbd-rmux-namespace-lifecycle` 的 design、design-review 和 checklist 已完成并通过。roadmap item 已挂起，等待继续实现。当前代码仍以 tmux 语义主导，`ProjectNamespaceController`、`ensure_context`、`start_foreground.py`、`destroy.py`、`project_view/service.py`、`project_clear.py`、`project_restart.py` 等入口还在不同程度上把 tmux socket/session 当成 authority。

## Acceptance Criteria

- namespace state、ping、doctor、startup、kill report 写 canonical `namespace_ref`、`namespace_backend_impl`、`namespace_ipc_kind`、`namespace_ipc_ref`、`namespace_session_name`，并保留旧 tmux aliases。
- `ProjectNamespaceController` 通过 backend resolver / factory 消费 `ProjectNamespaceBackend`。
- `ensure`、`reflow`、layout projection 通过 backend interface materialize namespace，不在调用层直接拼 `tmux` / `rmux` CLI。
- foreground attach 在 Rmux 路径调用已批准的 attach capability / adapter，不在 `start_foreground.py` 里直接拼 `tmux attach-session`。
- `ccb kill` 保持 remote stop、local prepare evidence/registry、backend `kill_namespace`、daemon diagnostics、final PID/orphan/report cleanup 的顺序。
- `project_view`、`start_flow/runtime binding`、`health assessment`、`slot replacement`、`project_clear/restart`、`layout_status`、`doctor`、`ping` 读取 canonical namespace projection。
- scope guard 证明不修改 provider parser、accelerator、process liveness、supervision/recovery，也不在 ccbd/cli 调用层直接拼 rmux/tmux CLI。
- 独立 Task agent code review passed，独立 Task agent 功能验收 passed，feature checklist/review/QA/acceptance/roadmap/final iteration 全部回写。

## Non-Goals

- 不实现 `RmuxBackend` core / send / capture / logging。
- 不实现 supervision/recovery、pane/provider crash 恢复或 full-chain smoke。
- 不修改 provider completion parser、accelerator transport、process liveness。
- 不把 Rmux 设为默认后端，不改 opt-in / route approval 语义。

## Decisions And Assumptions

- Namespace state 采用 canonical-first；旧 tmux aliases 只作兼容，不再作为 Rmux authority。
- foreground attach 的能力边界归属前序已批准的 attach contract / adapter，本 goal 只消费，不扩接口。
- kill 需要保留现有 finalize 清理语义，Rmux daemon 只作为 evidence，不作为项目 authority。
- 需要在实现中同步更新测试、scope guard、goal iteration 和最终功能验收产物。

## Current State

Goal 已创建，尚未开始实现。

## Next Action

先补齐 namespace_ref/state bridge 和 controller 接线，再推进 ensure、attach、kill 与跨切读者。
