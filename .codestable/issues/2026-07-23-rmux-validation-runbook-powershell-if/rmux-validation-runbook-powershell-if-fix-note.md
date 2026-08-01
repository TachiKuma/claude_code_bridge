---
doc_type: issue-fix
issue: 2026-07-23-rmux-validation-runbook-powershell-if
status: confirmed
path: fast-track
fix_date: 2026-07-23
tags:
  - windows
  - powershell
  - rmux
  - validation
---

# rmux validation runbook PowerShell if 修复记录

## 问题描述

用户在 native Windows 上运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\rmux-windows-validation-runbook.ps1" -ProjectRoot "$env:TEMP\ccb-rmux-validation" -AskCaseKind fake_provider -Json
```

脚本在构造 scenario result 时失败：

```text
if : 无法将“if”项识别为 cmdlet、函数、脚本文件或可运行程序的名称。
scripts/rmux-windows-validation-runbook.ps1:358
```

## 根因

`scripts/rmux-windows-validation-runbook.ps1` 使用了 PowerShell 不支持的内联 `if (...) { ... } else { ... }` 表达式作为函数参数。PowerShell 将它解析为命令调用，运行时查找名为 `if` 的命令并失败。

复现继续推进后还暴露两个 runbook 证据采集问题：

- runbook 没有把已有 rmux route approval / capability fixture 初始化到临时 smoke project，导致 `ccb-start` 报 `rmux backend requested but route approval is missing`。
- cleanup endpoint residue 扫描把 `lease.json`、`keeper.json` 和日志文件当作 endpoint residue，导致真实 runtime failure 被误报为 `test_design_failure`。

## 修复方案

- 新增 `Select-Classification` helper，替代 8 处内联 `if` 参数表达式。
- 在 `Initialize-SmokeProject` 中复用现有 route approval fixture 初始化模式，复制 approval report、route decision summary 和 capability report 到临时项目。
- 收窄 cleanup endpoint residue 扫描，只把 endpoint/socket 命名文件计入 endpoint residue；token 文件仍由 `*token*.json` 独立扫描。

## 改动文件

- `scripts/rmux-windows-validation-runbook.ps1`

## 验证结果

- `rg -n "\(if \(" "scripts/rmux-windows-validation-runbook.ps1"`：无匹配。
- PowerShell AST parse：passed。
- `python -B -m pytest -q "test/test_rmux_windows_validation_matrix.py" "test/test_rmux_windows_validation_scope_guard.py" -p no:cacheprovider`：`25 passed`。
- 用户同款 runbook 命令可执行到矩阵报告阶段，不再出现 PowerShell `if` 命令错误。
- 修复 route approval 后，`rmux backend requested but route approval is missing` 不再出现。
- 修复 cleanup endpoint 分类后，报告中 `test_design_failure=0`，剩余失败为真实 runtime `system_failure`。

## 遗留风险

当前 runbook 仍返回 exit `1`，但原因已经是实际 Rmux backend/runtime failure：

```text
rmux set_pane_user_option failed: can't find pane: %0
```

这不是本次 PowerShell runbook 语法/证据采集问题的修复范围，应作为后续 Rmux backend runtime issue 处理。
