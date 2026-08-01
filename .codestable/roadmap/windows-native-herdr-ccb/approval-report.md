---
doc_type: approval-report
unit: .codestable/roadmap/windows-native-herdr-ccb
status: approved
reason: goal-execution
approvals:
  roadmap-review: approved
  roadmap-plan: approved
  all-feature-designs: approved
  goal-acceptance: approved
  goal-commits: approved
approval_groups:
  child-designs:
    status: approved
    confirmation_id: child-designs-2026-08-01-windows-native-herdr-ccb
    decisions:
      all-feature-designs: approved
  goal-execution:
    status: approved
    confirmation_id: goal-execution-2026-08-01-windows-native-herdr-ccb
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
- 2026-08-01：owner 通过 `/goal` 启动指令确认 Goal execution，批准 `approval_groups.goal-execution`，同一 confirmation id `goal-execution-2026-08-01-windows-native-herdr-ccb` 覆盖 `approval-report.md#goal-acceptance` 与 `approval-report.md#goal-commits`。
- 2026-08-01：goal driver 执行到 feature 4 `herdr-backend-client` 时，发现其 design 的仓库事实假设在分支 `codestable/windows-native-herdr-ccb-v852-source` 不成立（rmux_backend analog 与 `test/test_rmux_backend_core.py` 不存在、factory 仅 tmux），触发 handoff。owner 指示经 cs-epic/cs-feat 修订该 child design + checklist（对齐真实树、修 CMD-005、明确 factory 接线），已由独立 Task agent design-review **round 4 passed**。该 design 已从 `approved` 重开为 `draft`，`all-feature-designs` 对 `herdr-backend-client` 一项待 owner 再确认；其余 10 个 child design 的 approved 不变。
- 2026-08-01：owner 回复“确认”，批准修订后的 `herdr-backend-client` design + checklist，标记其 `status: approved`，授权清除 goal-state handoff 恢复 `ready-to-dispatch`，由 goal driver 从 `current_feature_index=3` 续跑 feature 4。既有 `goal-execution`/`goal-commits` 授权不变，仍不含 push。

## Decision Needed

none

## Why Now

Goal execution authorization 已落盘。`goal-state.yaml` 必须使用同一 confirmation id 同步为 `ready-to-dispatch`。

## Context

当前 epic 目标是基于 Herdr 建立 Native Windows x64 CCB public workflow parity 路线。Roadmap 已拆为 11 个 child feature，覆盖 Windows x64 / CCB `v8.5.2` 基线、Herdr socket spike、mux backend contract V2、Herdr backend client、ccbd namespace、provider runtime、bounded recovery、用户可见面、release surface、validation matrix 与 supportability projection。

以下 child feature design-review 已重新通过，且已在本 report 中 batch-approved。Goal package 已按同一顺序落盘并获得 Goal execution authorization：

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
- Approve Goal execution: 已授权 `approval_groups.goal-execution`，同时批准 `goal-acceptance` 和 `goal-commits`。
- Reject Goal execution: 保留 goal package 作为 handoff 材料，不派发 driver，不执行 acceptance / commit。

## Recommendation

Proceed with Goal execution。当前 11 个 child design 均已 approved，goal package 与授权均已落盘；implementation、review、QA、acceptance 和 scoped commit 仍由 goal protocol 的 gate 逐项控制。

## Risks And Tradeoffs

- 批准 design 不代表实现已经完成，也不代表 acceptance、QA、commit 或 release 已授权。
- 后续 implementation 仍必须按 DAG 和每个 child checklist 执行；batch approval 只放行 goal package，不放宽实现依赖。
- Native Windows x64 真机验证、Herdr API 事实、docs/doctor guard、release surface gate 和 support projection artifact 仍是 implementation / QA / acceptance 的硬证据。
- Goal execution 会允许本地 scoped commit；每个 feature accepted 后仍必须机械复核 `goal-commits` authorization，且不包含 push。

## Non-Automatic Actions

本 Goal execution 授权只允许本 roadmap 下每个 feature accepted 后的本地 scoped commit。

不会自动执行 remote push、merge、release、publish、deploy、promotion、production cutover、npm 发布、远端 API 调用或任何生产状态变更。

## After You Answer

按 Goal driver 规则继续执行 `goal-state.yaml` 中的 feature loop。
