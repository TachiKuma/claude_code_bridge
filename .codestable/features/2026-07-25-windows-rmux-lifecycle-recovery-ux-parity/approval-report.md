---
doc_type: approval-report
unit: .codestable/features/2026-07-25-windows-rmux-lifecycle-recovery-ux-parity
status: approved
reason: interview
approvals:
  design-admission: approved
approval_groups: {}
created_at: 2026-07-25
---

# Approval Report

## Decision History

- 2026-07-27：owner 回复“批准”，批准 `approval-report.md#design-admission`，授权 `windows-rmux-lifecycle-recovery-ux-parity` 按 UX continuity first 与“crash 诊断可证伪即可通过”的 brainstorm 结论进入 feature design。

## Decision Needed

是否批准 `windows-rmux-lifecycle-recovery-ux-parity` 按本次 brainstorm 收敛方向进入 feature design。

命名授权：`approval-report.md#design-admission`

## Why Now

`windows-rmux-ux-parity-hardening` epic 的 child batch 当前停在该 item 的 per-item `$cs-brainstorm` gate。只有 owner 明确批准本 item 的 brainstorm 结论并允许进入 design 后，才能把 roadmap item 更新为 `brainstorm_status: confirmed` / `design_admission: admitted`，并由 `cs-feat` 起草 design。

## Context

已选定方向：

- 主轴：UX continuity first。
- crash 通过标准：诊断可证伪即可通过。

这意味着本 feature 不以“增强所有自动恢复策略”为默认目标，而是把用户日用生命周期路径做成可观察、可诊断、可恢复或明确 degraded 的证据闭环。

设计应复用以下 accepted baseline，不默认重做：

- `.codestable/features/2026-07-20-rmux-supervision-recovery/rmux-supervision-recovery-acceptance.md`
- `.codestable/features/2026-07-20-ccbd-rmux-namespace-lifecycle/ccbd-rmux-namespace-lifecycle-acceptance.md`
- `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-acceptance.md`
- `.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-acceptance.md`

## Options

### Option A: 批准进入 design（推荐）

按 UX continuity first 进入 `cs-feat` design。design 覆盖 terminal closed survival、reattach、kill cleanup、pane/provider/rmux daemon crash 的 transcript、residue report、diagnostics ref、failure class 和 `lifecycle_recovery` UX parity evidence。

### Option B: 继续 brainstorm

暂不进入 design，继续讨论自动恢复范围、crash pass 标准、诊断 schema 或和 supportability 的边界。

### Option C: 改成 recovery automation first

推翻当前收敛方向，把重点改为增强自动恢复策略。该选项会扩大到 supervision/recovery policy，范围和风险更高。

## Recommendation

选择 Option A。当前 epic 里 identity 和 capture 依赖已经 design-review passed，旧 supervision / namespace / validation baseline 也已 accepted；本 item 的增量应放在日用 UX lifecycle evidence 和 degraded diagnostics，不应无证据重做底层 recovery。

## Risks And Tradeoffs

- crash 场景可以通过 `partial` / `degraded` 形式验收，但必须有 transcript、diagnostics ref 和 residual risk，不能口头通过。
- 如果 design 发现真实恢复路径缺口，可以把最小 production 修复纳入当前 feature；但不默认重构 supervision/recovery。
- native Windows + WezTerm + rmux live evidence 不可用时，full pass 必须 fail closed 或降级为 partial/blocked。

## Non-Automatic Actions

本批准不包含 git commit、push、merge、release、publish、deploy、npm 发布、修改 support tier、生产环境操作或任何远端操作。

## After You Answer

- 若 owner 明确回复“批准”“确认”或“继续”，则记录 `approval-report.md#design-admission: approved`，落盘 confirmed feature brainstorm，更新 roadmap items.yaml 的该 item admission 字段，然后在当前 run 继续加载 `cs-feat` design。
- 若 owner 选择继续讨论，则保持 pending，不更新 roadmap item。
- 若 owner 改选 recovery automation first，则更新 brainstorm 方向后重新请求 design admission。
