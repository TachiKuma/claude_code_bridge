---
doc_type: feature-acceptance
feature: tmux-backend-contract-adapter
status: accepted
reviewer_id: "019f89ea-98dc-7d52-ad37-2af7f6ab7e24"
updated_at: "2026-07-22"
---

# tmux-backend-contract-adapter Acceptance

## Acceptance Checks

- pass：implementation admission 已确认 `mux-backend-contract` item `done`，contract module、fake backend、`MuxCommandError` 与 capability protocols 可导入。
- pass：`TmuxMuxBackendAdapter` 作为生产 adapter 暴露 `backend_impl=tmux`、namespace/pane refs、capabilities 与稳定 ipc evidence。
- pass：tmux/transient/permission/unsupported/subprocess/returncode failure 归一到 `MuxCommandError.category` 并保留 evidence。
- pass：旧 `TmuxBackend` public methods 兼容；默认 tmux backend factory 已包装 adapter，同时旧 `create_auto_layout()` 路径保持不漂移。
- pass：layout root、ccbd namespace backend、runtime launch detached pane/server policy、agent window reflow 已迁移到 mux-facing seam。
- pass：public `MuxBackend` protocol 不包含 `_tmux_run(args)`；剩余泄漏点已 inventory 化。
- pass：核心验证命令已通过或记录既有 baseline，feature checklist 已全量 `done`。

## Evidence

- Terminal acceptance Task agent：`019f89ea-98dc-7d52-ad37-2af7f6ab7e24`。
- Focused closure review Task agent：`019f89e4-8462-7262-8257-0f0d88733685`。
- Functional acceptance report：`.codestable/goals/2026-07-22-tmux-backend-contract-adapter/functional-acceptance.md`。
- Final iteration：`.codestable/goals/2026-07-22-tmux-backend-contract-adapter/iterations/003.md`。
- Fresh verification：`python -m pytest -q test/test_tmux_mux_backend_adapter.py test/test_agent_window_reflow.py test/test_cli_runtime_launch_tmux_panes.py test/test_backend_selection_diagnostics.py test/test_terminal_runtime_backend_selection.py test/test_v2_project_namespace_backend.py`，83 passed。

## Delivery Record

`tmux-backend-contract-adapter` 已接受。roadmap item 已写回 `done`，epic goal-state feature status 已写回 `accepted`，下一项 handoff 指向 `windows-namespace-ipc-schema`。
