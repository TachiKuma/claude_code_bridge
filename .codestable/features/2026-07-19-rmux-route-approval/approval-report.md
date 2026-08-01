---
doc_type: approval-report
unit: .codestable/features/2026-07-19-rmux-route-approval
status: pending
reason: review-authorization
approvals:
  rmux-route: approved
  rmux-workaround-risk: approved
  code-review-local-only: pending
approval_groups:
  route-approval:
    status: approved
    confirmation_id: rmux-route-approval-2026-07-22-windows-rmux-native-backend
    decisions:
      - rmux-route
      - rmux-workaround-risk
created_at: 2026-07-22
---

# Approval Report

## Decision History

- 2026-07-20：`rmux-capability-gate` acceptance 记录的 canonical report 为 `.codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T094438Z-4728/capability-report.json`，结果是 `rmux 0.8.0`、`probe_status=completed`、`blocking_gaps=7`。该报告只证明 capability gate 已完成，不批准 Rmux 路线。
- 2026-07-21：owner 将工作重心转为让 Rmux 成为完整基座，并创建/推进 `windows-rmux-full-backend` goal，目标是重做 stdio-aware lifecycle runner、foreground attach runner、logical EOF 映射并重跑完整 gate。
- 2026-07-21：`windows-rmux-full-backend` 功能验收通过，fresh report `.codestable/goals/2026-07-21-windows-rmux-full-backend/evidence/rmux-full-gate/run-20260721T144322Z-15036/capability-report.json` 记录 `rmux 0.9.0`、`probe_status=completed`、`blocking_gaps=[]`。该结果闭合旧 route gate 的 required gaps；其中 `attach-session`、`refresh-client`、`kill-server`、`attach_reattach` 仍依赖已接受 live evidence / workaround，本 feature 将 route 与 workaround 风险一起记录为 approved。
- 2026-07-22：当前 `/goal` driver 已完成 route decision implementation gates，但宿主工具面没有暴露可见 Task agent/spawn 接口，无法启动 gate 必需的独立 reviewer。记录 `code-review-local-only` 为 pending；未经 owner 明确批准，不降级为 self review。

## Decision Needed

是否批准本 feature 的本地只读 review 降级。

## Why Now

`backend-resolver-opt-in-contract` 以及后续 Rmux implementation item 只能依赖 `rmux-route-approval`，不能直接依赖原始 probe completed。当前必须把 capability facts、后续 full-backend 验收和 owner 方向收敛为一个可恢复的 route decision。

## Context

本 feature 不修改 production 代码。它只把路线决策落盘为 feature unit 内的 named approval 和 route decision summary。

关键证据：

- 旧 canonical capability report：`.codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T094438Z-4728/capability-report.json`
- 旧 report SHA256：`912675c22835a067f5a62d43537f3c0fc8ba80891be16e998d304d34b9da0b42`
- 旧 report 结论：`blocking_gaps=7`，包括 attach/reattach、capture fidelity、Ctrl-C/Ctrl-D 等 required partial gaps。
- 新 full-backend report：`.codestable/goals/2026-07-21-windows-rmux-full-backend/evidence/rmux-full-gate/run-20260721T144322Z-15036/capability-report.json`
- 新 report SHA256：`6abb86655af5ac61d69f4e2e06cd6f22feae526d4af3fa9b6fc67dea9af9296d`
- 新 report 结论：`blocking_gaps=[]`，并由 `functional-acceptance.md` 记录 Task agent verdict `pass`。
- 新 report accepted workaround：`attach-session`、`refresh-client`、`kill-server`、`attach_reattach` 依赖 live foreground attach / live client commands evidence；这些不是当前 route blocker，但必须传递给下游 validation。
- Implementation gates：`scope-gate`、`dod-runner`、`evidence-pack` 均 passed；`CMD-003` 的 report/artifact review 已用只读 verifier 核对，并落盘到 `rmux-route-approval-cmd003-results.json`。
- Review blocker：当前 Codex 工具面没有可见 Task agent/spawn 工具；OCR CLI 可用，但本轮 diff 全在 `.codestable/`，按协议不能替代独立 Task agent review。

## Options

- Continue Rmux route：基于 fresh `rmux 0.9.0` full-backend report 和功能验收继续后续 implementation item。
- Pause route：保留旧 canonical report 的 7 个 gaps，返回 capability gate 补证据。
- Reselect backend：放弃当前 Rmux 路线，返回 roadmap planning/update。
- Approve local review fallback：批准 `code-review-local-only`，允许主线程做本地只读 review 并在 report 中写 `reviewer: self`。
- Reject local review fallback：不批准降级；改用具备可见 Task agent 的会话重跑 review gate。

## Recommendation

路线选择为 Continue Rmux route。当前待决策项建议优先选择具备可见 Task agent 的会话重跑 review；若 owner 接受本轮 `.codestable` 治理产物的低风险属性，可批准 `code-review-local-only` 做本地只读 review fallback。

## Risks And Tradeoffs

- `windows-rmux-full-backend` 是后续 goal 产物，不是最初 `rmux-capability-gate` acceptance report；本报告显式保留旧 report hash 和 gap 列表，避免历史事实被覆盖。
- full-backend 验收仍记录非交互 `attach-session`、`refresh-client`、`kill-server` 依赖 live evidence 的 residual risk；这些不是当前 route blocker，但必须在下游 backend/core/validation feature 中继续解释。
- 本地 review fallback 会降低 gate 独立性；即使批准，也只能覆盖本 feature 的 `.codestable` route decision 产物，不应作为后续生产代码 feature 的默认降级。
- 本 approval 只批准继续 Rmux route，不批准 remote push、merge、release、deploy 或生产切换。

## Non-Automatic Actions

本 approval 不自动执行 git commit、git push、merge、release、deploy、publish、production cutover，也不改变 upstream 仓库状态。

## After You Answer

已经记录 `approval-report.md#rmux-route` 为 approved。若批准本地 review fallback，把 `approvals.code-review-local-only` 改为 `approved` 并恢复 review；否则在具备可见 Task agent 的会话中重跑 `cs-code-review`。
