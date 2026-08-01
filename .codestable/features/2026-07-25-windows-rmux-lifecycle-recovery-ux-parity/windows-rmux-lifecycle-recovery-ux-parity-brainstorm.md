---
doc_type: feature-brainstorm
feature: 2026-07-25-windows-rmux-lifecycle-recovery-ux-parity
status: confirmed
summary: Windows/rmux lifecycle recovery UX parity 采用 UX continuity first，crash 场景以可证伪 diagnostics 和 degraded evidence 为通过基础
tags: [windows, rmux, wezterm, lifecycle, recovery, diagnostics, parity, evidence]
---

# Windows Rmux Lifecycle Recovery UX Parity Brainstorm

> Stage 0 | 2026-07-27 | 下一步：cs-feat（由主入口选择 lane）

## 想做什么、为什么

当前 roadmap 要求 `windows-rmux-lifecycle-recovery-ux-parity` 在 design 前单独完成 `$cs-brainstorm`。这个 item 的真实问题不是“再实现一套 supervision/recovery”，而是 Windows/rmux/WezTerm 日用生命周期里，用户关闭/重开 WezTerm、重新 attach、执行 kill，或遇到 pane/provider/rmux daemon 异常时，系统是否能给出可观察、可诊断、可恢复或明确 degraded 的路径。

已有 baseline 已经 accepted：

- `rmux-supervision-recovery` 已把 namespace、pane、process/job、daemon evidence 纳入 supervision ledger，并定义 shared daemon degraded、owned daemon recover 等边界。
- `ccbd-rmux-namespace-lifecycle` 已把 namespace state、foreground attach、kill、doctor、ping 和 project view 统一到 canonical namespace projection。
- `ccbd-windows-full-chain-smoke` 已证明 native Windows true-host 下 start / ping / doctor / ask / kill 的最小链路和 cleanup evidence。
- `rmux-windows-validation-matrix` 已提供 true-host matrix、manual transcript parser、failure classification 和 cleanup/residue evidence。

因此本 item 的增量应放在 UX continuity 和 lifecycle evidence：把 attach/reconnect、terminal closed survival、kill cleanup、pane/provider/rmux daemon crash 后的用户可见恢复或 degraded diagnostics 做成可证伪的 transcript/report，而不是无证据扩大底层 recovery policy。

## 考虑过的方向

### 方向 A：UX continuity first

- 描述：优先覆盖用户日用生命周期连续性：关闭 WezTerm 不等于 kill project，重新 `ccb` attach 能回到正确 namespace/pane，`ccb kill` 能清干净；crash 场景消费已有 supervision 能力，能恢复则记录恢复证据，不能恢复则明确 degraded diagnostics 和下一步。
- 价值：贴合 roadmap 的 UX parity 目标，复用已 accepted 的 recovery / namespace / validation baseline，避免重做底层 authority。
- 代价：不会默认把所有 crash 都变成自动恢复；部分 crash 可能以 `partial` / degraded 形式通过。
- 结论：选定。

### 方向 B：recovery automation first

- 描述：以增强 pane/provider/daemon 自动恢复策略为核心，围绕 crash 后自动恢复体验设计。
- 价值：如果当前 supervision 仍有真实恢复缺口，用户可能获得更强自动恢复能力。
- 代价：会扩大到 `lib/ccbd/supervision/*` 的 recovery policy 和 daemon ownership 决策，容易重做 `rmux-supervision-recovery`，也可能误杀 shared daemon。
- 结论：否决第一版默认方向；只有 lifecycle evidence 证明具体恢复缺口时，才纳入最小 production 修复。

### 方向 C：evidence/runbook first

- 描述：完全不碰生产恢复逻辑，只建立 lifecycle transcript、residue report、diagnostics projection 和 UX evidence JSON。
- 价值：范围最稳，能快速形成支持性证据。
- 代价：如果 `reattach` 或 `kill cleanup` 存在真实日用缺口，单纯 runbook 不足以形成 UX parity。
- 结论：不作为默认方向；作为 UX continuity first 的保守 fallback。

## 已敲定的设计点

- 已确认：本 item 采用 **UX continuity first**。
- 已确认：crash 场景的第一版通过标准是 **诊断可证伪即可通过**：每类 crash 至少要有 transcript、residue report、diagnostics ref、failure class 和 residual risk；可恢复则记录恢复，不可恢复也可以用 `partial` / degraded 表达。
- 已确认：关闭 WezTerm 不等于 kill project；terminal closed survival 必须能证明 namespace/provider/rmux state 的预期存活或明确 degraded。
- 已确认：重新 `ccb` attach 必须证明能回到正确 namespace/pane；pane identity 和 output/capture 的依赖由已 passed design-review 的 parent items 提供设计前置，不在本 item 重做。
- 已确认：`ccb kill` 验收必须覆盖 ccbd endpoint、TCP token、rmux namespace/session、provider/job/process residue。
- 已确认：pane/provider/rmux daemon crash 消费 `rmux-supervision-recovery` 的 accepted baseline；shared daemon 不自动 kill/restart/refresh，owned/project daemon 才允许按已有 evidence 恢复。
- 已确认：本 item 必须产出 `evidence/windows-rmux-ux-parity-evidence.json`，且 `parity_dimension=lifecycle_recovery`。
- 已确认：本 item 不提升 support tier，不修改 npm/install/release gate；supportability feature 之后消费本 item evidence。
- 已确认：owner 已批准本 brainstorm 结论，并允许进入 feature design。

## 选定方向与遗留问题

选定方向是 `windows-rmux-lifecycle-recovery-ux-parity`：建立 Windows/rmux/WezTerm lifecycle recovery UX parity evidence，证明 terminal closed、reattach、kill cleanup 和 crash/degraded 场景在用户日用路径上可观察、可诊断、可恢复或明确 degraded。

核心行为：

- 生成 lifecycle transcript + residue report，覆盖 `reattach`、`terminal_closed`、`kill_cleanup`、`pane_crash`、`provider_crash`、`rmux_daemon_crash`。
- 每个 scenario 记录 start state、action、expected observable、verdict、cleanup residue、diagnostics ref、failure class 和 residual risks。
- 生成 roadmap §4.1 `WindowsRmuxUxParityEvidence`，固定 `parity_dimension=lifecycle_recovery`。
- 对 crash 场景：自动恢复不是硬性 full-pass 前提；诊断必须可证伪，degraded 必须有用户可见说明和下一步建议。

明显不做：

- 不默认重构 `rmux-supervision-recovery` 或 daemon ownership policy。
- 不重做 namespace lifecycle、full-chain smoke 或 validation matrix。
- 不把真实 provider auth/quota failure 归为 rmux/system failure。
- 不把 pane identity/layout 或 output/capture 的契约重新设计一遍；本 item 消费它们的 design evidence。
- 不修改 support tier、install.ps1、npm gate、release guard 或外部文档承诺。

遗留给 design 的问题：

- lifecycle report 是否作为细粒度 JSON，例如 `evidence/lifecycle-recovery-report.json`，再由 `windows-rmux-ux-parity-evidence.json` 汇总引用。
- native Windows + WezTerm live evidence 缺失时，哪些 scenario 可 `blocked`，哪些只能 `partial`。
- `terminal_closed` 的 transcript 应如何可靠区分“关闭 GUI 宿主”与“kill project”。
- crash scenario 的 diagnostics ref 应消费 doctor、ping、project view、diagnostics bundle 中哪一个作为 canonical ref。
