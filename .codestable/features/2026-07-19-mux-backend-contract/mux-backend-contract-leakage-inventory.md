---
doc_type: leakage-inventory
feature: 2026-07-19-mux-backend-contract
roadmap: windows-rmux-native-backend
roadmap_item: mux-backend-contract
status: active
updated_at: 2026-07-22
---

# mux-backend-contract 泄漏点 Inventory

## Scope

本 inventory 记录当前 `_tmux_run` / tmux argv / tmux-specific 字段的真实泄漏点，作为后续 `tmux-backend-contract-adapter` 的迁移输入。本 feature 只建立 backend-neutral contract 与 fake backend，不迁移这些调用点。

## Contract Gate

- 新 public contract 位于 `lib/terminal_runtime/mux_backend_contract.py`。
- `MuxBackend` 由 `NamespaceLifecycle`、`WindowLayout`、`PaneIO`、`PanePresentation`、`PaneLogging`、`DiagnosticsCapability` 组合。
- 新 public protocol 不包含 `_tmux_run(args)`。
- `command` / `ipc_ref` / `detail` / `evidence` 只作为 `MuxCommandError` 诊断字段保留，不作为调用层协议。

## Leakage Groups

### terminal_runtime layout root

- `lib/terminal_runtime/layouts_models.py`: `TmuxLayoutBackend` protocol 仍声明 `_tmux_run(...)`，是旧 layout seam 的主要泄漏。
- `lib/terminal_runtime/layouts_root.py`: detached root session 直接执行 `new-session`、`list-panes`。

后续迁移目标：用 `NamespaceLifecycle.create_session()`、`WindowLayout.window_root_pane()` 和 `PaneIO` 语义替换。

### terminal_runtime tmux backend internals

- `lib/terminal_runtime/tmux_backend.py`: `TmuxBackend._tmux_run()` 是 tmux-family adapter 的 backend-local primitive，应保留为 adapter 内部实现，不向新 public contract 泄漏。
- `lib/terminal_runtime/tmux_backend_runtime/actions.py`: 直接执行 `select-pane`、`attach`、`send-keys`、`has-session`、`kill-session`、`new-session`、`list-panes`。
- `lib/terminal_runtime/tmux_backend_runtime/services.py`: 将 `_tmux_run` 注入 pane/log/respawn 服务。
- `lib/terminal_runtime/tmux_backend_control.py`: `kill_tmux_pane()` 直接执行 `kill-pane`。
- `lib/terminal_runtime/tmux_logs.py`: `pipe-pane` 和 `tee -a` 是 tmux + Unix shell logging seam。
- `lib/terminal_runtime/tmux_respawn.py`: `respawn-pane` argv 构造是 tmux primitive。

后续迁移目标：这些文件属于 tmux adapter 内部，可继续消费 `_tmux_run`，但上层调用方应通过 `PaneIO`、`PaneLogging`、`PanePresentation`、`NamespaceLifecycle`。

### ccbd project namespace backend

- `lib/ccbd/services/project_namespace_runtime/backend.py`: `_tmux_run_ready()`、`_tmux_run_once()`、`_tmux_run_checked()` 以及 `kill-server`、`new-session`、`list-windows`、`select-window` 等直接 tmux 命令。
- `lib/ccbd/services/project_namespace_runtime/controller.py`: namespace backend factory 仍以 `TmuxBackend(socket_name/socket_path)` 为核心。
- `lib/ccbd/services/project_namespace_runtime/models.py`、`records.py`、`ensure_context.py`、`ensure_state.py`: `tmux_socket_path` / `tmux_session_name` 仍是 authoritative 字段。

后续迁移目标：引入 `MuxNamespaceRef` 和 namespace capabilities；旧 tmux 字段保留兼容别名。

### agent reflow / move / remove / materialize

- `lib/ccbd/services/project_namespace_runtime/agent_window_reflow.py`: 通过 `_tmux_run` 执行 `select-layout`、`swap-pane`。
- `lib/ccbd/services/project_namespace_runtime/move_patch_agents.py`: 通过 `_tmux_run` 执行 `move-pane` 和 placeholder cleanup。
- `lib/ccbd/services/project_namespace_runtime/remove_patch_agents.py`: 通过 `_tmux_run` 执行 `select-window`、`select-layout`、`kill-pane`。
- `lib/ccbd/services/project_namespace_runtime/additive_patch_agents.py`: 通过 `_tmux_run` 执行 `select-layout -E`。
- `lib/ccbd/services/project_namespace_runtime/additive_patch_windows.py`: 通过 `_tmux_run` 执行 `respawn-pane`。
- `lib/ccbd/services/project_namespace_runtime/materialize_topology.py`: 多处通过 `_tmux_run` 执行 `respawn-pane`、layout、pane/window 操作。

后续迁移目标：`reflow_window()` 是 canonical window reflow seam；`select_layout()` 只能作为低阶 adapter primitive。`split_pane()` 使用 `right` / `bottom` 语义 literal，不泄漏 tmux `-h` / `-v`。

### runtime launch

- `lib/cli/services/runtime_launch_runtime/tmux_panes.py`: 启动路径直接设置 tmux server/window options、环境变量、`new-session`、`list-panes`、`kill-pane`。
- `lib/cli/services/runtime_launch_runtime/tmux_runtime.py`: 仍围绕 tmux runtime launch 命名和返回模型组织。

后续迁移目标：将 server policy、session create、pane listing、pane cleanup 迁移到 `NamespaceLifecycle`、`WindowLayout`、`PaneIO`。

### foreground attach

- `lib/cli/services/start_foreground.py`: tmux path 直接调用 `attach-session`、`list-clients`、`refresh-client`、`has-session`、`select-window`；rmux path 已有 direct command fallback。

后续迁移目标：通过 `NamespaceLifecycle.attach_namespace()` 表达前台 attach，backend-local command 只留在 adapter。

### pane log helpers

- `lib/terminal_runtime/tmux_logs.py`、`lib/terminal_runtime/pane_logs_runtime/*`: 当前 logging 仍以 tmux pane id 和 `pipe-pane` 为核心。

后续迁移目标：调用层改依赖 `PaneLogging.ensure_pane_log()` / `pane_log_path()`，Windows shell/log builder 后续处理 backend-local logging 语义。

## Migration Notes

- 当前 feature 不改变上述调用行为；旧 tmux 默认路径必须保持不变。
- 后续 adapter feature 应优先替换调用层 `getattr(backend, "_tmux_run", None)` 检查，因为它把 backend 能力误建模为私有方法存在性。
- 任何新增 mux 调用不得再以 `_tmux_run(args)` 作为 public seam。
