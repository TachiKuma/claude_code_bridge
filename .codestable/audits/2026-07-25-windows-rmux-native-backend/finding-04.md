---
doc_type: audit-finding
audit: 2026-07-25-windows-rmux-native-backend
finding_id: "maintainability-04"
nature: maintainability
severity: P2
confidence: medium
suggested_action: cs-refactor
status: open
---

# Finding 04：PowerShell export 转译用裸分号切分，边界条件会破坏 provider 命令

## 速答

Windows rmux provider command wrapper 会把 POSIX `export`/`unset` 转成 PowerShell 语句，但当前实现先对整条命令做 `split(';')`，没有解析引号；含分号的 quoted env 值或命令参数会被拆坏，维护成本和边界风险偏高。

## 关键证据

- `lib/terminal_runtime/rmux_backend_runtime/panes.py:107` — rmux respawn 会调用 `_wrapped_provider_command(...)` 包装 provider 命令。
- `lib/terminal_runtime/rmux_backend_runtime/panes.py:371` — wrapper 来自 `_log_command_builder`。
- `lib/terminal_runtime/windows_shell_log_builder.py:178` — PowerShell shell family 下会调用 `_translate_posix_exports_for_powershell(body)`。
- `lib/terminal_runtime/windows_shell_log_builder.py:363` — `_translate_posix_exports_for_powershell(command)` 负责转译整条命令。
- `lib/terminal_runtime/windows_shell_log_builder.py:364` — `str(command or '').split(';')` 会无条件按分号拆分，不区分引号内外。
- `lib/terminal_runtime/windows_shell_log_builder.py:381` — 每段再交给 `shlex.split(...)`，此时引用结构已经可能被上一步破坏。
- `test/test_terminal_runtime_windows_shell_log_builder.py:102`、`test/test_terminal_runtime_windows_shell_log_builder.py:121`、`test/test_terminal_runtime_windows_shell_log_builder.py:139` — 现有测试覆盖简单分号分隔，但没有覆盖 quoted 分号。

## 影响

典型命令如 `export NOTE='a;b'; codex`、`python -c "print('a;b')"` 在 PowerShell wrapper 下会被拆成错误片段，轻则保留未转译的 `export` 导致 Windows 原生命令失败，重则改变传给 provider 的参数。该问题只在 Windows rmux 使用 PowerShell wrapper 时暴露。

## 修复方向

用一个最小 shell 分段器替换裸 `split(';')`，至少保证单引号、双引号和转义场景不被错误切分；同时补 quoted semicolon 的单元测试。

## 建议动作

`cs-refactor`，因为核心问题是自定义命令转译器的解析边界，需要小范围重构并补测试。
