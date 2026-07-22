---
doc_type: goal-functional-acceptance
goal: "windows-shell-log-builder"
status: pass
reviewer_id: "019f8a4e-4b58-7491-aeea-de3d9a395cf5"
final_iteration: "iterations/003.md"
---

# windows-shell-log-builder 功能验收

## Reviewer

- Task agent role: Acceptance
- Task agent id: `019f8a4e-4b58-7491-aeea-de3d9a395cf5`
- 运行方式：可见 Task agent 只读功能验收，不修改仓库文件。
- 生命周期：验收结果已消费，agent 已关闭；关闭时 previous_status 为 completed/pass。

## Scope

验收 `.codestable/goals/2026-07-22-windows-shell-log-builder/goal.md` 中记录的 owner-level acceptance criteria：集中 Windows shell/log command builder、shell resolution diagnostic、provider wrapper、pipe-pane log command、stderr redirection 与 clipboard pipe command，并保持 tmux 调用层行为不漂移。

## Acceptance Checks

- pass：builder 暴露 `wrap_provider_command(cmd, cwd)`、`build_pipe_log_command(log_path)`、`append_stderr_redirection(cmd, stderr_log_path)` 等能力，且旧 `tmux_respawn.py` 作为兼容 facade 转调 builder。
- pass：Windows shell resolution 覆盖 env override、tmux default-shell、process shell 与 pwsh / PowerShell / cmd fallback，并记录 shell、flags、source、candidate availability 与 fallback reason。
- pass：`TmuxRespawnService` 已消费 `wrap_provider_command_fn` 注入点；存在 wrapper 时优先调用，不再走 legacy `resolve_shell_fn` / `build_shell_command_fn` 路径。
- pass：`TmuxPaneLogManager` 通过 builder 注入构造 `pipe-pane` log command，调用层不再拼 `tee -a` 或平台 shell 字符串。
- pass：`append_stderr_redirection()` 按 shell family 分支；PowerShell 使用 script block append，cmd 使用 cmd path quoting，POSIX 保留 shlex quoting。
- pass：`backend.py` 与 `runtime_launch_runtime/tmux_panes.py` 不再复制 `_CLIPBOARD_PIPE_COMMAND = "sh -lc ..."`，clipboard policy 通过 builder helper 复用。
- pass：fresh focused pytest、YAML 校验、`rg` leakage guard 与 `git diff --check` 均通过。

## Functional Evidence

- `lib/terminal_runtime/windows_shell_log_builder.py` 提供 `ShellResolution`、`WindowsCommandBuilder`、`DefaultWindowsShellLogBuilder`、`build_windows_shell_log_builder()` 与 shell/log/clipboard helpers。
- `lib/terminal_runtime/tmux_respawn_service.py` 通过 `wrap_provider_command_fn` 注入消费 builder wrapper，测试覆盖 stderr append 后再 wrapper，且 legacy shell 函数不会被调用。
- `lib/terminal_runtime/tmux_backend_runtime/services.py` 装配 `command_builder.wrap_provider_command` 与 pipe log builder。
- `lib/terminal_runtime/tmux_logs.py` 与 `lib/terminal_runtime/tmux_server_policy.py` 只消费 builder 输出，业务层不新增 Windows shell branching。
- `test/test_terminal_runtime_windows_shell_log_builder.py` 覆盖 shell resolution、provider wrapper、PowerShell/cmd/POSIX stderr redirection、Windows pipe log command 与 clipboard helper。
- functional acceptance agent 首轮返回 changes requested：B1 为 respawn service 未消费 `wrap_provider_command()`，B2 为 stderr redirection 无条件使用 `2>>`。
- focused revalidation：Task agent `019f8a4e-4b58-7491-aeea-de3d9a395cf5` 返回 `verdict: pass`，确认 B1/B2 closed，且无剩余 blocking finding。

## Verification

- `git diff --check` -> clean。
- `python -m pytest -q "test/test_terminal_runtime_windows_shell_log_builder.py"` -> `12 passed`。
- `python -m pytest -q "test/test_terminal_runtime_tmux_respawn.py" "test/test_terminal_runtime_tmux_respawn_service.py" "test/test_terminal_runtime_tmux_logs.py"` -> `18 passed`。
- `python -m pytest -q "test/test_v2_project_namespace_backend.py" "test/test_v2_project_namespace_state.py" "test/test_v2_runtime_launch.py" -k "clipboard or copy-pipe or set-clipboard"` -> `10 passed, 139 deselected`。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-windows-shell-log-builder/windows-shell-log-builder-checklist.yaml" --yaml-only` -> passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` -> passed。
- `rg -n "sh -lc|tee -a|powershell\\.exe|pwsh|cmd /" "lib/ccbd/services/project_namespace_runtime/backend.py" "lib/cli/services/runtime_launch_runtime/tmux_panes.py" "lib/terminal_runtime/tmux_logs.py"` -> no matches。

## Verdict

`pass`。

## Residual Risks

- 当前证据主要来自 Windows 开发环境上的 focused unit/contract tests 与调用层 leakage guard；未跑真实 Rmux backend 或跨平台 tmux full matrix。
- `clipboard_pipe_command()` 仍保留 POSIX-oriented copy-mode policy 作为现有 tmux 行为兼容，Windows backend 后续应在 `rmux-send-capture-logging` / `rmux-backend-core` 中消费本 builder 边界，而不是在调用层新拼 shell。

## Delivery Record

本功能验收对应 final iteration：`.codestable/goals/2026-07-22-windows-shell-log-builder/iterations/003.md`。`windows-shell-log-builder` 可进入 accepted/done 写回，epic 下一项为 `windows-job-object-runtime-evidence`。
