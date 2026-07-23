---
doc_type: approval-report
unit: ".codestable/goals/2026-07-23-ccbd-rmux-namespace-lifecycle"
status: pending
reason: blocker
approvals: {}
approval_groups: {}
created_at: "2026-07-23"
---

# Approval Report

## Decision Needed

需要 owner 选择如何处理当前 goal 的终端 gate 阻塞：本会话没有可见独立 Task agent 能力，无法按 `cs-goal` 规则完成独立 code review 和 functional acceptance。

## Why Now

本轮 implementation 与测试已经推进到可 review 状态，但 `cs-goal` 明确要求完成前必须由可见 Task agent 做独立 review 与功能验收。当前工具面检查结果为空，主线程不能静默用本地自审替代。

## Context

- 已完成 Iteration 001：namespace_ref state bridge、Rmux foreground attach capability、controller/backend factory、destroy/kill namespace 基础闭环。
- 已完成 Iteration 002：`project_focus`、`layout_status`、`project_clear`、`project_restart` 的 Rmux/canonical reader 覆盖与 unsupported 安全降级。
- 已通过相关 pytest 回归与 Rmux CLI 拼接 guard。
- 未完成：独立 code review、独立 functional acceptance、`functional-acceptance.md`、final iteration、feature checklist/QA/acceptance/roadmap 最终回写。

## Options

1. 推荐：在具备可见 Task agent 的环境中恢复该 goal。
   - 影响：保持 `cs-goal` 完整 gate，不降低验收标准。
   - 恢复动作：重新执行 `$codestable:cs-goal ccbd-rmux-namespace-lifecycle`，并确保会话提供可见 Task agent / review / acceptance 能力。

2. 暂停并保持 blocked。
   - 影响：代码和测试改动保留，goal 不标记 complete。
   - 恢复动作：之后补齐 Task agent 能力再继续。

3. 明确批准 local review fallback 仅用于 code review。
   - 影响：只能覆盖 review agent 不可用，不能覆盖 functional acceptance 不可用；goal 仍不能 complete。
   - 需要命名授权：`approval-report.md#goal-local-review`，并在 `approvals.goal-local-review` 记录为 `approved` 后才能消费。

## Recommendation

选择选项 1。这个 goal 的验收标准本身要求独立 review 和独立功能验收，降级会破坏完成定义；当前代码证据可以恢复，不需要为了本轮结束而降低 gate。

## Risks And Tradeoffs

- 保持 blocked 的代价是当前改动不会被 CodeStable 标记为 complete。
- 本地自审的代价是破坏 `cs-goal` completion contract，并可能遗漏跨入口行为问题。
- 只批准 local review fallback 仍无法完成 functional acceptance，因为 acceptance gate 不允许 self/local 替代。

## Non-Automatic Actions

不会自动执行 git commit、merge、push、部署或修改长期验收规则。不会把 `state.yaml.status` 改成 `complete`，除非后续真的写入 passing `functional-acceptance.md` 且 final iteration 双向引用完成。

## After You Answer

- 如果提供可见 Task agent 能力：恢复 goal，先做独立 code review，再做功能验收。
- 如果选择保持 blocked：保留当前 `state.yaml.status: blocked`，后续可安全重试。
- 如果只批准 local review fallback：更新本文件命名授权后可执行 local code review，但仍需可见 acceptance agent 才能 complete。
