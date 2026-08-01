# Windows rmux Git Bash 弹窗修复记录

## 根因

Windows + rmux 下，项目 UI 状态栏会把 `ccb-git.sh` 和 `ccb-status.sh` 渲染进 tmux `#()` 命令。rmux 周期执行状态栏命令时会通过 Git Bash 启动 `.sh` 脚本，形成短暂 `git-bash.exe` / `git-cmd.exe` 弹窗。`ccb-border.sh` 和 resize hook 同样依赖 `run-shell`，属于同类风险。

## 改动

- `lib/cli/services/tmux_ui_runtime/service.py`：Windows + `backend_impl=rmux` 时保留静态 tmux UI 选项，但禁用外部 shell 状态脚本、border hook 和 resize shell hook。
- `test/test_v2_tmux_ui.py`：新增 Windows/rmux 断言，确保渲染结果不包含 `ccb-git.sh`、`ccb-status.sh`、`ccb-border.sh`、`#()` 或 `run-shell`。

## 验证

- `pytest test/test_v2_tmux_ui.py::test_apply_project_tmux_ui_sets_session_theme_and_hook_from_current_install_root test/test_v2_tmux_ui.py::test_windows_rmux_project_ui_avoids_shell_status_commands test/test_tmux_identity.py`：12 passed。
- `python -m compileall -q lib/cli/services/tmux_ui_runtime/service.py`：通过。
- `git diff --check`：通过。
- 真实项目 `D:/C#Project/GitHub/CodeStable` 重新运行源码版启动命令后，`doctor` 显示 `ccbd_health: healthy`、`backend_selection_backend_impl: rmux`。
- 新 rmux session 的 `status-left/status-right` 不再包含 `#()`，`show-hooks` 为空；连续采样未发现新的 `ccb-git.sh` / `ccb-status.sh` / `ccb-border.sh` Git Bash 进程。

## 遗留风险

Windows/rmux 下状态栏 Git 分支和 ccbd 状态指示暂时显示为静态 `-`。这是为避免外部 shell 弹窗的最小修复；如果后续需要恢复动态信息，应改为 rmux 原生隐藏执行或非 shell 的 Windows 运行路径。
