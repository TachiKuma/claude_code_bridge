---
doc_type: approval-report
unit: .codestable/roadmap/windows-native-herdr-ccb
status: approved
reason: all-feature-designs
approvals:
  roadmap-review: approved
  roadmap-plan: approved
  all-feature-designs: approved
  goal-acceptance: pending
  goal-commits: pending
approval_groups:
  child-designs:
    status: approved
    confirmation_id: child-designs-2026-08-01-windows-native-herdr-ccb
    decisions:
      all-feature-designs: approved
  goal-execution:
    status: pending
    confirmation_id: ""
    decisions:
      - goal-acceptance
      - goal-commits
created_at: 2026-07-31
---

# Approval Report

## Decision History

- 2026-07-31：owner 回复“批准”，批准 `approval-report.md#roadmap-review` 与 `approval-report.md#roadmap-plan`，授权将 `windows-native-herdr-ccb` roadmap 从 `draft` 改为 `active` 并进入后续 child design batch。
- 2026-07-31：owner 确认 draft requirement `.codestable/requirements/native-windows-ccb-via-herdr.md`，要求基于 Herdr 全能力 parity 达到 Windows x64 CCB supported；旧的 roadmap review 与 child design-review 已被该 requirement update 取代，需要重新独立审查。
- 2026-07-31：owner 回复“确认”，批准修订后的 `windows-native-herdr-ccb` roadmap，授权将 roadmap 从 `draft` 改回 `active`，并进入 child design-review 重审。
- 2026-08-01：owner 回复“所有 child design统一确认batch-approved”，批准 `approval-report.md#all-feature-designs`，授权将 `windows-native-herdr-ccb` 下 11 个已审查通过的 child feature design 统一标记为 `status: approved`。

## Decision Needed

是否授权启动本 epic 的 Goal execution。该授权一次性覆盖两项可机械核验的命名决策：

- `approval-report.md#goal-acceptance`：允许 goal driver 在每个 feature 证据通过后执行 acceptance。
- `approval-report.md#goal-commits`：允许 goal driver 在每个 feature accepted 后做本地 scoped commit。

## Why Now

`workflow-next epic` 在所有 child design 已 approved 且 goal package 已落盘后，要求 Goal execution authorization，才能派发 goal driver。

## Context

当前 epic 目标是基于 Herdr 建立 Native Windows x64 CCB public workflow parity 路线。Roadmap 已拆为 11 个 child feature，覆盖 Windows x64 / CCB `v8.5.2` 基线、Herdr socket spike、mux backend contract V2、Herdr backend client、ccbd namespace、provider runtime、bounded recovery、用户可见面、release surface、validation matrix 与 supportability projection。

以下 child feature design-review 已重新通过，且已在本 report 中 batch-approved。Goal package 已按同一顺序落盘，等待 Goal execution authorization：

- `windows-x64-v852-baseline-gate`
- `herdr-backend-contract-spike`
- `mux-backend-contract-herdr-v2`
- `herdr-backend-client`
- `ccbd-herdr-namespace-lifecycle`
- `provider-runtime-on-herdr`
- `herdr-bounded-recovery-boundary`
- `herdr-user-surfaces-parity`
- `windows-x64-release-surface`
- `native-windows-public-workflow-validation-matrix`
- `herdr-supportability-projection`

## Options

- Approved: 批准所有已通过独立 review 的 child design，允许进入 goal package 阶段。
- Rejected: 停留在 child design confirmation gate，并指出需要重审或修订的 child design。
- Approve Goal execution: 授权 `approval_groups.goal-execution`，同时批准 `goal-acceptance` 和 `goal-commits`。
- Reject Goal execution: 保留 goal package 作为 handoff 材料，不派发 driver，不执行 acceptance / commit。

## Recommendation

Approve Goal execution。当前 11 个 child design 均已 approved，goal package 已落盘；implementation、review、QA、acceptance 和 scoped commit 仍由 goal protocol 的 gate 逐项控制。

## Risks And Tradeoffs

- 批准 design 不代表实现已经完成，也不代表 acceptance、QA、commit 或 release 已授权。
- 后续 implementation 仍必须按 DAG 和每个 child checklist 执行；batch approval 只放行 goal package，不放宽实现依赖。
- Native Windows x64 真机验证、Herdr API 事实、docs/doctor guard、release surface gate 和 support projection artifact 仍是 implementation / QA / acceptance 的硬证据。
- Goal execution 会允许本地 scoped commit；每个 feature accepted 后仍必须机械复核 `goal-commits` authorization，且不包含 push。

## Non-Automatic Actions

本 Goal execution 授权若获批准，只允许本 roadmap 下每个 feature accepted 后的本地 scoped commit。

不会自动执行 remote push、merge、release、publish、deploy、promotion、production cutover、npm 发布、远端 API 调用或任何生产状态变更。

## After You Answer

如果 owner 明确批准 Goal execution，将原子更新 `approval_groups.goal-execution`、`goal-acceptance`、`goal-commits` 和 `goal-state.yaml`，然后按 Goal driver 规则派发或打印 `/goal` 指令。
