---
doc_type: approval-report
unit: .codestable/roadmap/windows-rmux-ux-parity-hardening
status: approved
reason: review-authorization
approvals:
  global-codestable-brainstorm-gate-tooling: approved
  roadmap-review: approved
  roadmap-plan: approved
  all-child-designs: approved
  goal-acceptance: approved
  goal-commits: approved
approval_groups:
  child-designs:
    status: approved
    confirmation_id: child-designs-2026-07-26-windows-rmux-ux-parity-hardening
    decisions:
      all-child-designs: approved
  goal-execution:
    status: approved
    confirmation_id: goal-execution-2026-07-26-windows-rmux-ux-parity-hardening
    decisions:
      - goal-acceptance
      - goal-commits
created_at: 2026-07-25
---

# Approval Report

## Decision History

- 2026-07-25：owner 在对话中回复“确认”，批准 `approval-report.md#global-codestable-brainstorm-gate-tooling`，授权修改本机全局 CodeStable workflow/tooling 以机械执行 per-item `$cs-brainstorm` design admission gate。
- 2026-07-25：owner 在 roadmap review passed 后回复“批准”，批准 `approval-report.md#roadmap-review` 与 `approval-report.md#roadmap-plan`，授权将 `windows-rmux-ux-parity-hardening` roadmap 从 `draft` 改为 `active` 并进入后续 child design batch；后续每个 pending child 仍必须先通过 `$cs-brainstorm` gate。
- 2026-07-26：owner 在所有 child design-review 均 passed 后回复“确认”，批准 `approval-report.md#all-child-designs`，授权将 `windows-rmux-ux-parity-hardening` 下 6 个已审查通过的 child feature design 统一标记为 `status: approved`。
- 2026-07-26：owner 回复“确认授权 Goal execution”，批准 `approval-report.md#goal-acceptance` 与 `approval-report.md#goal-commits`，授权本 epic 进入 goal package 派发阶段。

## Decision Needed

是否授权启动本 epic 的 Goal execution。该授权一次性覆盖两项可机械核验的命名决策：

- `approval-report.md#goal-acceptance`：允许 goal driver 在每个 feature 证据通过后执行 acceptance。
- `approval-report.md#goal-commits`：允许 goal driver 在每个 feature accepted 后做本地 scoped commit。

## Why Now

`cs-epic` 在所有未 dropped child feature 的 design-review 均 passed 后，需要一个可恢复的统一 owner approval，才能从 child design batch 进入 goal package 阶段。

Goal package 已生成时必须先停在本授权门；未经批准不得派发 driver，不得执行 acceptance，不得自动 commit。

## Context

所有未 dropped child feature 都已有 design、checklist 和 `status: passed` 的 design-review。2026-07-26 的批量确认只批准这些设计进入后续 goal package / implementation planning，不批准 implementation 结果、QA、acceptance、commit、push、merge、release、publish、deploy 或生产环境操作。

Goal execution 会按 `goal-state.yaml` 的 6 个 feature 顺序推进 implementation、独立 code review、QA、acceptance 和每个 feature 的本地 scoped commit。任何 remote push、merge、release、publish、deploy、promotion 或 production cutover 仍不包含在本授权中。

## Options

- Approved: proceed from child design batch to goal package using the 6 reviewed child designs.
- Rejected: keep the epic at child design confirmation gate and revise designs before goal package.
- Approve Goal execution: 授权 `approval_groups.goal-execution`，同时批准 `goal-acceptance` 和 `goal-commits`。
- Reject Goal execution: 保留 goal package 作为 handoff 材料，不派发 driver，不执行 acceptance / commit。

## Recommendation

Approved。当前 6 个 child design 已通过独立 review，且最后一个 supportability design 已对齐 canonical `support_tier`、5 upstream DAG、`rmux_supportability` consumer seam 与低档位 `install_entry` 规则。

## Risks And Tradeoffs

- 批准 design 不代表实现已正确；实现、code review、QA 和 acceptance 仍需各自证据。
- 当前批准不放宽 implementation dependency gate：依赖必须达到 `done` 才能进入实现。
- Goal execution 和本地 scoped commit 仍需要后续单独授权。

## Non-Automatic Actions

本 design 批量确认不包含 git commit、push、merge、release、publish、deploy、npm 发布、生产环境操作或远端状态变更。

若后续明确批准 Goal execution，`goal-commits` 只授权本 roadmap 每个 feature accepted 后的本地 scoped commit；仍不授权 remote push、merge、publish、release、deploy、promotion、production cutover 或修改上游仓库状态。

## After You Answer

Goal execution 已获得 owner 批准；下一步按 Goal driver 规则派发或打印 `/goal`。
