---
doc_type: goal
goal: windows-shell-log-builder
status: complete
---

# windows-shell-log-builder

## Objective

继续 `windows-rmux-native-backend` epic 中的 `windows-shell-log-builder`，建立 Windows shell command builder、pipe/log command builder、stderr redirection 和默认 shell 诊断，并保持现有 tmux 行为不漂移。

## Starting Point

`windows-shell-log-builder` 的 design / checklist / design-review 已存在，但 runtime 侧仍把 shell/log 语义分散在 `tmux_respawn.py`、`tmux_logs.py`、`tmux_server_policy.py`、`backend.py` 和 `runtime_launch_runtime/tmux_panes.py`。

## Acceptance Criteria

- builder 暴露 `wrap_provider_command(cmd, cwd)`、`build_pipe_log_command(log_path)`、`append_stderr_redirection(cmd, stderr_log_path)`。
- Windows shell resolution 记录 `shell`、`flags`、`source`、`candidate availability`、`fallback reason`，并由 `resolve_shell()` helper 返回。
- `TmuxRespawnService` 与 `TmuxPaneLogManager` 通过 builder / 注入消费 command，不在业务层拼 shell/log 字符串。
- `backend.py` 与 `runtime_launch_runtime/tmux_panes.py` 不再复制 `_CLIPBOARD_PIPE_COMMAND = "sh -lc ..."`。
- Windows `pipe-pane` log command 不使用 `tee -a`，stderr redirection 不假设 POSIX `2>>`。
- focused pytest、`rg` guard 与 roadmap/items 回写通过。

## Non-Goals

- 不实现 `RmuxBackend`、`rmux_*` production module、provider session schema、ccbd transport、job object 或 process liveness 变更。
- 不改变 `pane_placeholder_argv` / `pane_placeholder_cmd` 语义。
- 不把 provider completion 解析或 capture 语义改成日志构造逻辑。
- 不新增 caller 级 `if is_windows()` shell branching。
- 不执行 git push、merge、release、deploy 或生产变更。

## Decisions And Assumptions

- 这是一条 runtime boundary seam，shell 选择、stderr redirection、pipe log、clipboard pipe command 都应集中到 builder 边界。
- 现有 tmux 行为保持不漂移，Unix 兼容字符串只能留在 builder / tests 里。
- `resolve_shell()` 需要可诊断，而不是只返回 shell 字符串。

## Current State

当前实现入口仍是 tmux-specific helper，且 clipboard command 在两个业务模块里重复定义。feature 设计和 checklist 已经给出明确 contract，下一步是落实现与回归测试。

## Next Action

实现 Windows shell/log command builder，并把 respawn / log / clipboard 调用层收口到 builder 边界。
