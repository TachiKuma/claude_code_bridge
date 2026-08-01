---
doc_type: feature-review
feature: windows-shell-log-builder
status: passed
reviewer_id: "019f8a4e-4b58-7491-aeea-de3d9a395cf5"
updated_at: "2026-07-22"
---

# windows-shell-log-builder Review

## Scope

审查 `windows-shell-log-builder` 的 implementation diff、builder contract、respawn/log/clipboard wiring、stderr redirection shell semantics，以及调用层 Unix-only / Windows shell 字符串泄漏风险。

## Reviewer

- 功能验收 Task agent：`019f8a4e-4b58-7491-aeea-de3d9a395cf5`
- 运行方式：可见只读 Task agent；首轮验收发现 blocking issue，focused revalidation 后 verdict 为 pass。
- 生命周期：结果已消费，agent 已关闭。

## Findings

首轮验收发现 2 项 blocking 问题：

- B1：`TmuxRespawnService` 未消费 `wrap_provider_command()`，实现仍可能绕过 builder wrapper contract。
- B2：`append_stderr_redirection()` 无条件使用 `2>>`，不满足 PowerShell/cmd/POSIX shell family 分支要求。

## Closure

Focused revalidation verdict: `pass`。

closure reviewer 确认：

- `TmuxRespawnService` 现在有 `wrap_provider_command_fn` 注入点，并在存在时优先调用 wrapper，不再走 legacy `resolve_shell_fn` / `build_shell_command_fn` 路径。
- 生产装配已注入 `command_builder.wrap_provider_command`。
- `append_stderr_redirection()` 已按 PowerShell、cmd、POSIX 分支。
- 新增测试覆盖 stderr append 后再 wrapper、legacy shell functions 不被调用，以及 PowerShell/cmd/POSIX redirection。
- `git diff --check`、focused pytest、YAML 与 leakage guard 均通过。

## Residual Risks

- 本次 review 聚焦 `windows-shell-log-builder` 的 shell/log boundary，未扩展到 Rmux backend production 实现；该部分属于后续 feature。
- `clipboard_pipe_command()` 保留当前 tmux copy-mode policy 兼容，后续 Rmux 路径仍需通过 builder 边界消费。
