---
doc_type: feature-design-review
feature: 2026-07-19-rmux-route-approval
status: passed
review_state: passed
review_reason: ""
reviewer_id: ""
reviewed: 2026-07-19
round: 2
---

# rmux-route-approval feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-design.md`
- Checklist: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap-review.md`、`.codestable/reference/approval-conventions.md`、`.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-design.md`
- Code facts checked: `lib/terminal_runtime/backend_selection.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: subagent `019f7af2-fbf6-7ee0-bf0e-fa007eac16a1`、subagent `019f7af9-075c-7d52-b7ef-bb5a267c10b5`
- Raw output: round 1 建议 `changes-requested`，无 blocking，提出 3 条 important、1 条 nit、1 条 suggestion；主 agent 修订 design/checklist 后，round 2 复核 verdict 为 `passed`，上一轮 4 个重点 finding 均关闭，未发现 blocking / important / nit。
- Merge policy: 主 agent 已逐条核验 reviewer findings；有仓库事实支撑的 finding 已合并到本报告，修订证据见 Focused Closure。
- Gate effect: independent review completed and merge verified；允许进入 `cs-epic` 子 feature 批量流程。

## 2. Design Summary

- Goal: 将 `rmux-capability-gate` 的 Windows capability report 转为可恢复、可审计的 owner route decision：continue / pause / reselect。
- Key contracts: `probe_status=completed` 不等于 route approved；route approval 必须依赖唯一 canonical capability report ref、blocking gaps 和 owner approval evidence。
- Steps: 5 步，覆盖 report discovery、gap summary、decision surface、owner decision persistence、acceptance 回写。
- Checks: 10 项，覆盖 Windows evidence fail-closed、required gap 暴露、workaround 风险授权、approval ref 可恢复、parent handoff、production code 不触碰和 downstream constraints 记录。
- Baseline / validation: checklist YAML、roadmap items YAML、人工 capability report/artifact review。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] FDR-001 route summary 可显式包含 `report_ref`、`report_hash`、`artifact_index_hash`、`decision_status`、`owner_confirmation_id`。
  - Evidence: design 已定义 route decision schema 和 parent handoff，但这些 hash 字段不是本 feature 当前必须的生产 schema。
  - Impact: 不阻塞 design；后续 `backend-resolver-opt-in-contract` design review 可更容易核验没有读错 approval ref。

### learning

- RMR-001 / RMR-002 已从“当前 feature 验证未来 downstream design 已消费”收敛为“当前 feature 记录 downstream hard constraints 与目标 item 映射”；实际消费留给对应 downstream feature design/review gate。
- capability report discovery 已改为 authority 优先级：capability-gate acceptance canonical ref、owner 明确选择 ref、drafts 中唯一 completed Windows report；多个候选或 artifact 不可反查时 fail-closed 为 `paused`。
- paused / reselect 已通过 `parent_handoff` 区分 “decision made” 与 “route approved”，避免 parent epic 误解锁下游 Rmux implementation item。

### praise

- capability report 与 route approval 分离清楚，避免把 probe completed 自动升级成路线批准。
- design 明确本 feature 不改 `backend_selection.py`、不新增 `RmuxBackend`、不新增 production transport adapter，边界克制。

## 4. User Review Focus

- 用户需要重点拍板：route decision 的三种互斥结果 continue / pause / reselect，以及 required workaround 风险是否可接受。
- implement 需要重点遵守：只能读取唯一 canonical capability report ref；不得按“最新文件”猜测；缺 Windows evidence、多个候选、artifact index 不可反查都只能 `paused`。
- code review / QA / acceptance 需要重点复核：approval group 是否只覆盖实际需要的 named decisions；paused/reselect 是否写清 `parent_handoff` 且没有解锁后续 Rmux implementation。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 到 AC-006，并映射 S1 到 S5 | none |
| DoD Contract | pass | E | design §3.4 定义 design / implementation / acceptance DoD、validation commands 和 required artifacts | none |
| Steps and checks traceability | pass | E | checklist steps/checks 可追溯到 design §2.4、§3.1、§3.3、§3.4 | none |
| Roadmap contract compliance | pass | E/C | roadmap 要求 route approval 明确继续、暂停或重新选型；design 不把 probe completed 当成 route approved | none |
| Module interface design | n/a | E | 本 feature 是 CodeStable 决策 gate，不新增 production module/interface | none |
| Validation and artifacts | pass | E | checklist 定义 CMD-001、CMD-002、CMD-003 与 required artifacts | none |

Summary: E=6, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- capability gate 当前仍是 `in-progress`，本 design 只能定义 route approval gate，不能证明 Rmux Windows 能力事实。
- route decision 的真实 outcome 依赖后续 capability report 和 owner approval；实现阶段必须 fail-closed，不能用示例数据替代。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child design batch；本 feature design 保持 `draft`，等待所有子 feature design-review passed 后统一 owner 确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004
- Attributed delta: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-design.md` 与 `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml`
- Verification: second independent reviewer `019f7af9-075c-7d52-b7ef-bb5a267c10b5` 复核通过；`validate-yaml.py` 校验 checklist 与 roadmap items 均通过。
- Classification: 修订改变了验收语义与决策恢复语义，因此已按完整独立复审处理；round 2 未发现 blocking / important / nit。
