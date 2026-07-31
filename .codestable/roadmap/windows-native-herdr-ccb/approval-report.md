---
doc_type: approval-report
unit: .codestable/roadmap/windows-native-herdr-ccb
status: approved
reason: review-authorization
approvals:
  roadmap-review: approved
  roadmap-plan: approved
approval_groups: {}
created_at: 2026-07-31
---

# Approval Report

## Decision History

- 2026-07-31：owner 回复“批准”，批准 `approval-report.md#roadmap-review` 与 `approval-report.md#roadmap-plan`，授权将 `windows-native-herdr-ccb` roadmap 从 `draft` 改为 `active` 并进入后续 child design batch。

## Decision Needed

已批准 `windows-native-herdr-ccb` epic 规划进入后续 child design batch。该批准覆盖两项可机械核验的命名决策：

- `approval-report.md#roadmap-review`：确认已接受独立 roadmap review 的 `passed` 结论。
- `approval-report.md#roadmap-plan`：授权将 roadmap 从 `draft` 标记为 `active`，并按 items DAG 继续生成各 child feature design。

## Why Now

`cs-epic` 已恢复到 `ConfirmRoadmap` checkpoint：roadmap review 已 `passed`，但 roadmap 仍是 `draft`。根据 epic 状态机，未经 owner 明确批准，不得把规划标记为 active，也不得进入 child design batch。

## Context

当前 epic 目标是基于 Herdr 建立 Native Windows x64 CCB public workflow parity 路线。Roadmap 已拆为 11 个 child feature，覆盖 Windows x64 / CCB `v8.5.2` 基线、Herdr socket spike、mux backend contract V2、Herdr backend client、ccbd namespace、provider runtime、bounded recovery、用户可见面、release surface、validation matrix 与 supportability projection。

独立 reviewer `019fb3a9-e22f-7d23-83dd-88137f91832c` 已给出 `review_state: passed`，并确认 blocking 为 none。已修复的 important findings 包括 `watch` 覆盖粒度、baseline gate 与 release surface 边界、spike 对 `kill_pane` / provider CLI dry run 的覆盖；nit 为 validation evidence workflow key 收紧。

## Options

- Approved: 批准 `roadmap-review` 与 `roadmap-plan`，允许将 roadmap 标记为 `active` 并进入 child design batch。
- Rejected: 不批准当前 roadmap，停留在 planning/review 修订阶段。

## Recommendation

Approved。当前 roadmap 已通过独立 review，边界清晰：CCB 继续拥有 control plane / provider runtime / completion / recovery / support projection 权威，Herdr 只作为 Native Windows terminal primitive；且最小闭环先由 `herdr-backend-contract-spike` 事实验证后再投入正式 adapter，符合 KISS 与 YAGNI。

## Risks And Tradeoffs

- 批准 roadmap 不代表批准实现、QA、acceptance 或 commit；它只允许进入 child design batch。
- Herdr socket API、Windows beta 缺口和 Native Windows x64 真机验证仍是后续 feature design / QA 的硬 gate。
- 当前工作区与 CCB `v8.5.2` 基线不一致的风险仍需由 `windows-x64-v852-baseline-gate` 在首个 child feature 中处理。

## Non-Automatic Actions

本批准不会自动执行 implementation、acceptance、git commit、push、merge、release、publish、deploy、promotion、production cutover、npm 发布或任何远端状态变更。

后续所有 child feature design 仍需要独立 design-review；全部 child design-review passed 后，还会再次停下请求统一确认所有 design。Goal execution 与本地 scoped commit 也会在 goal package 阶段单独请求授权。

## After You Answer

Owner 已批准。下一步按 `workflow-next epic` 进入 child design batch。
