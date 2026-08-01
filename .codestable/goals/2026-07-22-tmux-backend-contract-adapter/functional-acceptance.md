---
doc_type: goal-functional-acceptance
goal: "tmux-backend-contract-adapter"
status: pass
reviewer_id: "019f89ea-98dc-7d52-ad37-2af7f6ab7e24"
final_iteration: "iterations/003.md"
---

# tmux-backend-contract-adapter 功能验收

## Reviewer

- Task agent role: Acceptance
- Task agent id: `019f89ea-98dc-7d52-ad37-2af7f6ab7e24`
- 运行方式：只读功能验收，不修改仓库文件。
- 生命周期：验收结果已消费，agent 已关闭。

## Scope

验收 `.codestable/goals/2026-07-22-tmux-backend-contract-adapter/goal.md` 中记录的 owner-level acceptance criteria：实现 `TmuxBackend` 到 `MuxBackend` 的生产 adapter、错误归一、旧 public method 兼容、代表性调用 seam 迁移、状态产物回写，并保持当前 tmux 路径行为不漂移。

## Acceptance Checks

- pass：implementation admission 已确认 `mux-backend-contract` roadmap item 为 `done`，contract module、fake backend、`MuxCommandError` 与 capability protocols 可导入。
- pass：`TmuxMuxBackendAdapter` 暴露 `backend_impl="tmux"`，可生成 `MuxNamespaceRef` / `MuxPaneRef`，并提供 `MuxCapabilities` 与稳定 socket path/name/default ipc evidence。
- pass：tmux failure、transient、permission、unsupported、subprocess timeout / called process / returncode failure 归一为 `MuxCommandError.category`，且保留 command、returncode、stdout、stderr、timeout、socket 等 evidence。
- pass：旧 `TmuxBackend` public methods 保持兼容；`send_text`、`is_alive`、`kill_pane`、`activate`、`create_pane`、`split_pane`、capture/title/user-option/style/logging 等 facade 仍可直接调用。
- pass：`layouts_root`、ccbd project namespace backend、runtime launch detached pane/server policy、agent window reflow 已迁移到 mux-facing seam，并保留旧 `_tmux_run` fallback。
- pass：public `MuxBackend` protocol 不包含 `_tmux_run(args)`；剩余上层 `_tmux_run` 泄漏点已记录到 feature inventory。
- pass：核心验证命令已刷新，feature/roadmap 状态产物在 final iteration 中完成写回。

## Functional Evidence

- `lib/terminal_runtime/tmux_mux_backend.py` 包含 `TmuxMuxBackendAdapter`，覆盖 namespace lifecycle、window layout/reflow、pane io/presentation/logging、diagnostics 与旧 facade。
- `lib/terminal_runtime/api.py` 的默认 tmux factory 返回 `TmuxMuxBackendAdapter(TmuxBackend(...))`；`create_auto_layout()` 仍显式使用旧 `TmuxBackend`，避免旧 layout 路径漂移。
- `lib/terminal_runtime/layouts_root.py`、`lib/ccbd/services/project_namespace_runtime/backend.py`、`lib/cli/services/runtime_launch_runtime/tmux_panes.py`、`lib/ccbd/services/project_namespace_runtime/agent_window_reflow.py` 均有 mux-facing 分支。
- `test/test_tmux_mux_backend_adapter.py` 覆盖 refs、ipc evidence、错误映射、session root、runtime launch mux path 与默认 backend factory。
- `test/test_mux_backend_contract.py` 覆盖 public protocol 不暴露 `_tmux_run`。
- fresh verification：`python -m pytest -q test/test_tmux_mux_backend_adapter.py test/test_agent_window_reflow.py test/test_cli_runtime_launch_tmux_panes.py test/test_backend_selection_diagnostics.py test/test_terminal_runtime_backend_selection.py test/test_v2_project_namespace_backend.py`，结果 `83 passed`。
- focused closure review agent `019f89e4-8462-7262-8257-0f0d88733685` verdict 为 `pass`，确认 iteration 001 的 8 项 blocking findings 已关闭，且无新 blocking/high/medium。

## Verdict

`pass`。

## Residual Risks

- 未跑真实 Linux、macOS、WSL tmux 全平台矩阵；当前证据为 Windows 开发环境上的 fake/contract/调用 seam 回归。
- `CMD-005` 对 `test/test_v2_runtime_launch.py` 与 `test/test_ccbd_start_runtime_layout.py` 的抽样仍有既有 baseline failure，已记录为 Codex runtime bootstrap artifacts 与 legacy explicit session archive，不作为本 adapter 阻塞。
- 剩余 `_tmux_run` 上层泄漏点已 inventory 化，但未在本 feature 全量迁移，符合本 goal non-goal 与代表性迁移边界。

## Delivery Record

本功能验收对应 final iteration：`.codestable/goals/2026-07-22-tmux-backend-contract-adapter/iterations/003.md`。`tmux-backend-contract-adapter` 可进入 accepted/done 写回。
