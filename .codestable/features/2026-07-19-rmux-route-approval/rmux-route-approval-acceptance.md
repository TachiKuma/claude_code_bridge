---
doc_type: feature-acceptance
feature: 2026-07-19-rmux-route-approval
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: approval-report.md#goal-acceptance
accepted: 2026-07-22
round: 1
---

# rmux-route-approval 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：2026-07-22
> 关联方案 doc：`.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-design.md`

## 1. 接口契约核对

**接口示例逐项核对**：

- [x] route decision summary 示例：`decision_id/status/capability_report/blocking_gaps/owner_decision_ref/parent_handoff/downstream_constraints` 均已落盘到 `rmux-route-decision-summary.yaml`。
- [x] canonical approval ref：`approval-report.md#rmux-route` 为 approved，`approval-report.md#rmux-workaround-risk` 为 approved，可由 feature unit 恢复。
- [x] capability report authority：selected report 指向 `windows-rmux-full-backend` fresh report；旧 `rmux-capability-gate` report 保留在 `superseded_reports`，未被覆盖。

**名词层"现状 -> 变化"逐项核对**：

- [x] `capability report`：从旧 `rmux 0.8.0` canonical report 过渡为 selected `rmux 0.9.0` fresh report，并保留旧 report facts。
- [x] `route decision`：已从 pending decision surface 固化为 approved route decision。
- [x] `route approved`：`parent_handoff.route_approved=true`，且 acceptance 后 `downstream_unlocked=true`。
- [x] `route paused` / `reselect required`：本轮未选择；summary 通过 `next_route=continue` 明确不走 pause/reselect。

**流程图核对**：

- [x] locate/validate report：CMD-003 verifier 复核 selected/superseded report hash、platform、probe_status、blocking_gaps。
- [x] derive gaps：selected report `blocking_gaps=[]`，superseded report gaps 保留为历史事实。
- [x] owner approval / record summary：`approval-report.md` 与 `rmux-route-decision-summary.yaml` 均已落盘。

## 2. 行为与决策核对

**需求摘要逐项验证**：

- [x] 定位并验证 capability report：selected report 存在，SHA256 为 `6abb86655af5ac61d69f4e2e06cd6f22feae526d4af3fa9b6fc67dea9af9296d`。
- [x] 机械判定 required blocking gaps：selected report `blocking_gaps_count=0`；旧 report `blocking_gaps_count=7` 仅作为 superseded evidence。
- [x] route decision surface：`approval-report.md` 包含 options、recommendation、tradeoffs、evidence、consequence、next action。
- [x] canonical approval ref：`approval-report.md#rmux-route` approved；workaround risk 同 feature unit approved。
- [x] 知识回写候选：已登记在 summary 与本报告第 5/8/9 节，不在 acceptance 阶段直接写 ADR/docs。

**明确不做逐项核对**：

- [x] 未运行新的 Rmux probe；只消费已有 fresh full-backend report。
- [x] 未修改 `lib/terminal_runtime/backend_selection.py`。
- [x] 未新增 production `RmuxBackend`、transport seam、TCP adapter 或 provider session 迁移。
- [x] 未把 `probe_status=completed` 单独解释为 approved；route approval 由 approval report + summary + acceptance 回写共同闭合。
- [x] 未自动执行 git commit、push、release 或 production cutover。

**关键决策落地**：

- [x] CodeStable 决策 gate：本 feature 仅写 `.codestable` governance artifacts，不新增 production API。
- [x] Workaround 风险：不写成 `not-applicable`；改为 `accepted-via-full-backend-live-evidence` 并传递给 downstream constraints。
- [x] Downstream unlock：review/QA/acceptance 前保持 false；本 acceptance 后改为 true。

**挂载点反向核对（可卸载性）**：

- [x] `approval-report.md`：删除后 route approval 不可恢复，符合 design。
- [x] `rmux-route-approval-acceptance.md`：删除后验收证据消失，符合 design。
- [x] `windows-rmux-native-backend-items.yaml`：`rmux-route-approval` 已从 `in-progress` 机械回写为 `done`。
- [x] 反向核查：当前 production code 无 diff；所有新增/修改均在 feature unit 与 roadmap state 范围内。
- [x] 拔除沙盘推演：移除本 feature unit 会失去 route authority，不会留下 production runtime 分支。

## 3. 验收场景核对

- [x] **AC-001** capability report 缺失或 `probe_status != completed` 不得批准。
  - 证据来源：CMD-003 verifier / QA-001。
  - 结果：通过；selected report 是 Windows completed report，缺证据路径未被使用。
- [x] **AC-002** required unsupported gap 必须出现在 decision surface。
  - 证据来源：route summary / approval report / QA-002。
  - 结果：通过；旧 7 gaps 保留为 superseded facts，selected report无 blocking gaps。
- [x] **AC-003** partial/workaround 风险必须明确接受。
  - 证据来源：`approval-report.md#rmux-workaround-risk` / QA-003。
  - 结果：通过；accepted workaround 列表与 downstream risk 已落盘。
- [x] **AC-004** approved route 可恢复。
  - 证据来源：`approval-report.md#rmux-route`、route summary。
  - 结果：通过。
- [x] **AC-005** route approved 后 item done 并解锁下游。
  - 证据来源：items.yaml diff、route summary。
  - 结果：通过；`rmux-route-approval` 为 `done`，`downstream_unlocked=true`。
- [x] **AC-006** paused/reselect 不解锁实现。
  - 证据来源：本轮 `next_route=continue`，非 pause/reselect；QA 已验证 acceptance 前 lock。
  - 结果：通过；不适用路径未被错误激活。

**review 报告重点复核**：

- [x] `downstream_unlocked=false` 在 review/QA/acceptance 前成立，acceptance 后才改 true。
- [x] CMD-003 evidence 已落盘并被 QA 复核。
- [x] accepted workaround 风险已在 summary、QA 和本报告中保留。
- [x] scope gate 覆盖 generated artifacts；acceptance 后重新生成 gate evidence。

**QA 报告重点复核**：

- [x] 验证证据来源：`rmux-route-approval-qa.md`。
- [x] QA 报告覆盖 design 关键场景、DoD commands、review QA focus、evidence pack residual risks。
- [x] Feature 性质为 non-functional，替代证据合理。
- [x] failed / blocked 项为 none。
- [x] residual-risk 不承载当前 route approval 核心缺口；它只要求下游继续消费 accepted workaround 风险。

## 4. 术语一致性

- `route approval` / `route approved`：仅作为 roadmap / CodeStable governance 术语使用，无 production runtime 同名概念冲突。
- `capability report`：沿用 capability gate / full-backend evidence 语义。
- `psmux`：本 feature 未修改旧 docs；route 决策说明 Rmux 是当前 active route，旧 psmux superseded 标记留给 domain/docs-neat。
- 禁用范围：未新增 `RmuxBackend` production 类或 backend resolver runtime 字段。

## 5. 领域影响盘点

- [x] 候选：Rmux 作为旧 psmux 方向的当前候选实现已被 route-approved。建议后续走 `cs-domain` 写 ADR 或 CONTEXT 术语；本 acceptance 不直接代写。
- [x] 候选：capability gate 历史应区分旧 `rmux 0.8.0` gaps 与 fresh `rmux 0.9.0` full-backend pass。建议后续 `cs-keep` / `cs-domain` 归档。
- [x] 候选：TCP loopback transport 仍由 `ccbd-windows-tcp-loopback-transport` owning feature 决策，本 feature 不抢写 ADR。

## 6. requirement delta / clarification 回写

- Frontmatter `requirement` 为空。
- 本 feature 不新增用户可见 runtime 能力，只记录 epic 内 route governance 决策。
- 结论：无 requirement 影响；不需要 owner-approved req delta。

## 7. roadmap 回写

- [x] `roadmap=windows-rmux-native-backend` 与 `roadmap_item=rmux-route-approval` 成对存在。
- [x] `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 中 `rmux-route-approval` 已由 `in-progress` 改为 `done`。
- [x] `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md` 第 5 节对应条目已改为 `accepted`，并记录 selected report / superseded gaps / accepted workaround 风险传递。
- [x] route summary 的 `parent_handoff.downstream_unlocked` 已在 acceptance 后改为 `true`。

## 8. attention.md 候选盘点

- 本 feature 未暴露每个 feature 都会反复踩的本地环境 / 命令陷阱。
- 不建议写入 `.codestable/attention.md`。

## 9. 遗留

- 后续优化点：下游 `backend-resolver-opt-in-contract` 必须消费 `approval-report.md#rmux-route`，缺失或 rejected 时 fail fast。
- 已知限制：accepted workaround 风险仍需后续 `rmux-backend-core`、`rmux-send-capture-logging`、`ccbd-windows-full-chain-smoke` 用真实 Windows evidence 继续闭合。
- 实现阶段顺手发现：`dod-contract-gate` 只识别 `Required Artifacts:` ASCII 冒号；本轮已做非语义 design 格式修复。

## 10. 最终审计

- 验证证据来源：`rmux-route-approval-qa.md`。
- Evidence sources：`rmux-route-approval-evidence-pack.md` / `rmux-route-approval-dod-results.json` / `rmux-route-approval-scope-gate-results.json` / `rmux-route-approval-acceptance-dod-gate-results.json`。
- Inline Verification Matrix：不适用；Goal 模式已有 QA 报告。
- 聚合命令：
  - `validate-yaml` checklist / route summary / items.yaml -> exit 0。
  - `python -m json.tool` gate and DoD JSON -> exit 0。
  - CMD-003 read-only verifier -> exit 0。
  - `codestable-dod-contract-gate.py --stage acceptance` -> exit 0。
  - `codestable-workflow-next.py feature --require-implementation-ready --json` -> exit 0。
- 场景复核：re-verified 7 / trust-prior-verify 0。
- 交付物复核：approval report、route summary、QA、acceptance、gate JSON、checklist、items.yaml、roadmap markdown 均已落盘。
- 完整工作区复核：当前改动均归因于本 feature / roadmap goal-state；无 staged diff。
- diff 清洁度：通过；未新增 production code、debug 输出、临时 TODO、注释掉代码或 dead imports。
- 知识沉淀出口：domain / docs-neat / keep 候选已在第 5/9 节登记；attention 无候选。
- 结论：通过。
