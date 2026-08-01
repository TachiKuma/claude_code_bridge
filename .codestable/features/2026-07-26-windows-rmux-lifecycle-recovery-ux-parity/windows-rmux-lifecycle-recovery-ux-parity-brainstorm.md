---
doc_type: feature-brainstorm
feature: 2026-07-26-windows-rmux-lifecycle-recovery-ux-parity
status: confirmed
summary: Windows/rmux lifecycle recovery UX parity 先建立可证伪 transcript、residue report 和 diagnostics evidence，不默认重写 supervision
tags: [windows, rmux, wezterm, lifecycle, recovery, diagnostics, parity, evidence]
---

# Windows Rmux Lifecycle Recovery UX Parity Brainstorm

> Stage 0 | 2026-07-26 | 下一步：cs-feat（由主入口选择 lane）

## 想做什么、为什么

当前 roadmap 要求 `windows-rmux-lifecycle-recovery-ux-parity` 在 design 前单独完成 `$cs-brainstorm`。这个 item 的真实问题不是“再做一套 crash recovery”，而是 Windows/rmux/WezTerm 在真实日用生命周期里，用户能否看懂系统状态、重新 attach、安全 kill，并在 pane / provider / rmux daemon 异常时看到明确恢复路径或 degraded diagnostics。

已有 `windows-rmux-native-backend` baseline 已经覆盖底层系统能力：

- `rmux-supervision-recovery` 已 accepted，证明 runtime authority / supervision evidence ledger 能区分 pane、process/job、namespace、daemon evidence，并把 recovery action 投影到 project view、ping、doctor 和 diagnostics。
- `ccbd-windows-full-chain-smoke` 已 accepted，证明 native Windows true-host 下 `ccb -> ccbd -> rmux` start / ping / doctor / ask / kill 走真实 control plane，且 cleanup evidence 覆盖 ccbd endpoint、TCP token、rmux namespace/session 和 owned process residue。
- `rmux-windows-validation-matrix` 已 accepted，提供 fake / provider_blackbox / windows_true_host / manual_transcript lanes，且把 provider failure 与 system failure 分离。

因此，本 item 的增量应落在 UX lifecycle evidence：把 reattach、关闭 WezTerm、kill cleanup、pane/provider/rmux daemon crash 变成可证伪 transcript + residue report + diagnostics ref。只有证据显示某条路径体验断裂，design 才把它转成最小实现修复。

## 考虑过的方向

### 方向 A：UX lifecycle evidence first

- 先建立 lifecycle UX transcript、residue report、diagnostics evidence 和 `lifecycle_recovery` parity JSON。
- 覆盖 `reattach`、`terminal_closed`、`kill_cleanup`、`pane_crash`、`provider_crash`、`rmux_daemon_crash` 六类场景。
- 复用 `rmux-supervision-recovery`、`ccbd-windows-full-chain-smoke`、`rmux-windows-validation-matrix` baseline，不默认改 supervision / validation matrix / provider parser。
- 价值：能把“底层能恢复”和“用户能理解并继续工作”分开证明，避免把 lifecycle UX parity 扩成第二轮底层架构重写。
- 代价：如果 transcript 证明某条路径 broken，design 仍需要把缺口转成实现任务，不能只补报告。
- 结论：选定。owner 已选择该方向并批准进入 design。

### 方向 B：恢复优先

- 直接强化 attach / reconnect / crash recovery 行为，证据跟随实现。
- 价值：若已知某条路径 broken，会更快进入代码修复。
- 代价：当前 roadmap 依赖项已经提供 accepted supervision 和 full-chain evidence；没有新的 UX transcript 前直接改 recovery 容易重做底层能力，并把真实 provider failure、rmux/system failure、test design failure 混在一起。
- 结论：否决第一版默认方向；保留为证据触发后的最小修复路径。

### 方向 C：诊断优先

- 不追求自动恢复，先确保每个异常都有清晰 doctor / diagnostics / fallback 指引。
- 价值：范围最稳，能快速补用户可理解性。
- 代价：lifecycle parity 不只是错误解释；reattach、terminal close、kill cleanup 这些日用闭环仍要有真实 transcript 证据。
- 结论：不作为默认方向；diagnostics 是方向 A 的必备输出，而不是单独替代品。

## 已敲定的设计点

- 已确认：本 item 采用 **UX lifecycle evidence first**。
- 已确认：第一版不默认重写 supervision / recovery 底层，不重做 full-chain smoke，不修改 provider parser。
- 已确认：核心场景至少覆盖：
  - `reattach`：关闭或重开 WezTerm 后，`ccb` 能重新进入同一项目上下文。
  - `terminal_closed`：关闭 WezTerm 不等同于 `ccb kill`，namespace / provider lifecycle 必须可解释。
  - `kill_cleanup`：用户触发 kill 后，ccbd endpoint、TCP token、rmux namespace/session、provider/job/process residue 都有证据。
  - `pane_crash`：pane 异常后恢复或 degraded diagnostics 可见。
  - `provider_crash`：provider process death 与 pane death 分开归因，不把 provider failure 算作 rmux/system failure。
  - `rmux_daemon_crash`：shared / owned daemon 语义按 ownership evidence 解释，允许 degraded 但必须有下一步建议。
- 已确认：每个场景输出应投影为 `WindowsRmuxLifecycleUxReport` 或等价机器可读 report，包含 `scenario`、`start_state`、`action`、`expected_observable`、`verdict`、`cleanup_residue`、`diagnostics_ref`。
- 已确认：最终必须产出 `evidence/windows-rmux-ux-parity-evidence.json`，且 `parity_dimension=lifecycle_recovery`。
- 已确认：真实 provider auth / quota failure 不归为 Windows/rmux lifecycle failure；应按 provider lane / provider_failure 隔离。
- 已确认：没有 native Windows + WezTerm 前台证据时不得写 full pass；应记录 partial / blocked 与 residual risk。
- 已确认：owner 已批准本 brainstorm 结论，并允许进入 feature design。

## 选定方向与遗留问题

选定方向是 `windows-rmux-lifecycle-recovery-ux-parity`：建立 Windows/rmux/WezTerm lifecycle recovery UX parity evidence，证明用户在 reattach、terminal close、kill cleanup、pane/provider/rmux daemon crash 场景下能继续工作，或能看到明确 degraded diagnostics 与下一步建议。

核心行为：

- 生成可重复 lifecycle transcript 和 residue report。
- 验证关闭 WezTerm 与 kill project 的语义边界。
- 验证 reattach 能恢复用户上下文，而不只是后台进程仍存活。
- 验证 crash / degraded 场景有 diagnostics ref 和用户可理解的 next action。
- 产出 roadmap §4.1 `WindowsRmuxUxParityEvidence`，固定 `parity_dimension=lifecycle_recovery`。

明显不做：

- 不默认重写 `rmux-supervision-recovery` 已 accepted 的 supervision / recovery ledger。
- 不重做 `ccbd-windows-full-chain-smoke` 的 start / ask / kill 基础链路证明。
- 不扩大到 support tier / docs / installer projection；这些由 `windows-rmux-supportability-parity-contract` 收口。
- 不把真实 provider 凭证、quota、外部服务异常归为 rmux lifecycle failure。
- 不发布 npm、不 push/tag/release、不做生产环境动作。

遗留给 design 的问题：

- lifecycle transcript 是否复用 `rmux-windows-validation-matrix` manual transcript schema，还是新建更细的 UX lifecycle report 并由 parity evidence JSON 引用。
- `terminal_closed` 的可重复证据如何在自动化和手工 WezTerm 前台之间分层；没有 GUI 前台时应如何标记 partial / blocked。
- crash 场景第一版是否全部要求 live destructive smoke，还是允许 fake evidence + manual degraded transcript 分层。
- `kill_cleanup` 的 residue schema 是否直接复用 full-chain smoke cleanup evidence，还是补充用户可读 diagnostics summary 字段。
