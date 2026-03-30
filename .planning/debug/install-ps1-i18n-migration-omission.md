---
status: fixing
trigger: "Investigate issue: install-ps1-i18n-migration-omission"
created: 2026-03-31T00:49:51.8372770+08:00
updated: 2026-03-31T00:51:04.5392879+08:00
---

## Current Focus

hypothesis: Phase 06 对 install.ps1 的 i18n 迁移为部分完成，验收只统计 install.* key 数量和 Write-Warning 是否清零，未覆盖剩余 Write-Host/Read-Host 字面量，导致文档误报完成。
test: 为 install.ps1 剩余用户可见字面量补充 install.* 消息键并替换为 Get-Msg，然后重新扫描确认仅剩空行输出和参数化/命令注入内容。
expecting: 修复后，install.ps1 中用户可见输出均经 Get-Msg；静态扫描不再出现残留英文提示字面量。
next_action: 编辑 install.ps1，补齐消息字典并替换剩余硬编码输出

## Symptoms

expected: install.ps1 should route user-visible installer output through Get-Msg / install.* keys, matching Phase 06 docs and avoiding hardcoded English output.
actual: Static scan shows many remaining hardcoded Write-Host / Read-Host strings, including Python checks, backend confirmation, install completion, skills install status, WezTerm prompts, and uninstall output.
errors: Evidence from `rg -n 'Write-(Host|Error)|Read-Host' install.ps1` includes lines 212-223, 230-248, 260-268, 432-440, 447-492, 509-599, 617-625, 658-829, 840-928, 938-1043 still using literal text.
reproduction: In repo root, run `rg -n 'Write-(Host|Error)|Read-Host' install.ps1` and inspect remaining literal strings not wrapped by Get-Msg.
started: Phase 06 summary claims install.ps1 migration complete on 2026-03-31, but current file still has migration omissions.

## Eliminated

## Evidence

- timestamp: 2026-03-31T00:51:04.5392879+08:00
  checked: .planning/phases/06-ccb-i18n/06-06-SUMMARY.md
  found: 文档声明 install.ps1 已完成 installer message dictionary 扩展，并用 `rg -o '"install\.'` 与 `Write-Warning=0` 作为验证。
  implication: Phase 06 的完成判定依赖计数型静态检查，没有直接验证剩余 Write-Host/Read-Host 字面量。

- timestamp: 2026-03-31T00:51:04.5392879+08:00
  checked: .planning/phases/06-ccb-i18n/06-06-PLAN.md / 06-CONTEXT.md
  found: 计划和上下文都要求 install.ps1 所有用户可见字符串迁移到 Get-Msg/install.*，并明确协议字符串只作为参数注入。
  implication: 当前残留硬编码输出与 Phase 06 的既定需求直接冲突，属于漏迁移而非需求变更。

- timestamp: 2026-03-31T00:51:04.5392879+08:00
  checked: install.ps1
  found: Get-Msg 字典已扩展，但多个函数仍保留大量字面量输出，分布于 Python 检查、Windows/WSL 确认、安装完成、技能安装、WezTerm 配置和卸载路径。
  implication: 根因是迁移只覆盖部分代码路径，且后续自检没有扫描残留用户文案。

## Resolution

root_cause: Phase 06 的 install.ps1 i18n 迁移遗漏了多段用户可见输出；自检只统计 install.* key 与 Write-Warning 清零，没有验证剩余 Write-Host/Read-Host 字面量，导致遗漏未被发现。
fix: 在 install.ps1 中为剩余用户可见输出补充 install.* 消息键，并把相关 Write-Host/Read-Host 全部改为 Get-Msg 调用，保留命令/路径/协议字符串作为参数注入。
verification:
files_changed: []
