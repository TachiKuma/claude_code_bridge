---
doc_type: leakage-inventory
feature: 2026-07-19-tmux-backend-contract-adapter
roadmap: windows-rmux-native-backend
roadmap_item: tmux-backend-contract-adapter
status: active
updated_at: 2026-07-22
---

# tmux-backend-contract-adapter 泄漏点 Inventory

## Scope

本 inventory 记录本 feature 后 `_tmux_run` / tmux argv 的迁移状态。目标不是删除 tmux implementation 内部 primitive，而是阻止上层继续把 `_tmux_run(args)` 当作 public backend 能力。

## 已迁移的代表性 seam

- `lib/terminal_runtime/tmux_mux_backend.py` 新增 `TmuxMuxBackendAdapter`，把 refs、capabilities、namespace lifecycle、window layout/reflow、pane io/presentation/logging 和 diagnostics 映射到 `MuxBackend` 语义。
- `lib/terminal_runtime/layouts_root.py` 在传入 mux backend 时通过 `namespace_ref()`、`create_session()`、`session_alive()`、`session_root_pane()` 分配 detached root pane；旧 `TmuxBackend` 仍走 `_tmux_run` fallback。
- `lib/ccbd/services/project_namespace_runtime/backend.py` 的 `prepare_server()`、`ensure_server_policy()`、`create_session()`、`list_windows()`、`create_window()`、`kill_window()`、`session_alive()`、`window_root_pane()`、`select_window()`、`wait_for_root_pane()` 已支持 mux backend 语义路径。
- `lib/cli/services/runtime_launch_runtime/tmux_panes.py` 的 detached server policy 与 detached pane creation 已支持 mux backend 语义路径。
- `lib/ccbd/services/project_namespace_runtime/agent_window_reflow.py` 已支持无 `_tmux_run` 的 mux reflow ops：pane 几何观测通过 `describe_window_panes()`，layout 应用通过 `reflow_window()`，视觉顺序调整通过 `swap_pane()`。

## 保留在 tmux implementation 内部的 primitive

- `lib/terminal_runtime/tmux_backend.py` 的 `_tmux_run()` 仍是 tmux adapter 的 backend-local primitive。
- `lib/terminal_runtime/tmux_backend_runtime/actions.py`、`services.py`、`tmux_backend_control.py`、`tmux_logs.py`、`tmux_respawn.py` 仍可在 tmux implementation 内部直接消费 `_tmux_run`。
- `lib/terminal_runtime/tmux_mux_backend.py` 内部调用 `_backend._tmux_run()` 只作为 adapter 私有实现，不进入 `MuxBackend` protocol。

## 剩余上层泄漏点

- `lib/ccbd/services/project_namespace_runtime/move_patch_agents.py`：仍通过 `_tmux_run` 执行 `move-pane` 和 placeholder cleanup。
- `lib/ccbd/services/project_namespace_runtime/remove_patch_agents.py`：仍通过 `_tmux_run` 执行 `select-window`、`select-layout`、`kill-pane`。
- `lib/ccbd/services/project_namespace_runtime/additive_patch_agents.py`：仍通过 `_tmux_run` 执行 `select-layout -E`。
- `lib/ccbd/services/project_namespace_runtime/additive_patch_windows.py`：仍通过 `_tmux_run` 执行 `respawn-pane`。
- `lib/ccbd/services/project_namespace_runtime/materialize_topology.py`：仍有多处 `respawn-pane`、layout、pane/window 操作直接依赖 `_tmux_run`。
- `lib/cli/services/start_foreground.py`：foreground attach 仍直接使用 tmux/rmux 命令分支。
- `provider_backends/*` 的 provider-specific launcher/session runtime 仍读取或调用 tmux-specific runtime 字段与 `_tmux_run`。
- `lib/cli/services/runtime_launch_runtime/tmux_panes.py` 的旧 `TmuxBackend` fallback 仍保留 `_tmux_run`，用于兼容当前 tmux 默认路径。

## Gate

- `MuxBackend` public protocol 仍不包含 `_tmux_run(args)`。
- 本 feature 没有新增 `RmuxBackend` production module 或 Rmux CLI/SDK 调用。
- 后续迁移应优先消除上层 `getattr(backend, "_tmux_run", None)` 能力检查，改为检查 `MuxBackend` 小协议或更窄的语义方法。
