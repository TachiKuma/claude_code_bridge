---
doc_type: feature-review
feature: 2026-07-19-rmux-route-approval
status: passed
reviewer: subagent
reviewed: 2026-07-22
round: 1
lane_a_state: completed
lane_a_ref: "019f8592-77cb-7af3-8d05-fd357e278604"
lane_a_reason: "independent Task agent reviewer returned changes-requested findings"
lane_b_state: unavailable
lane_b_ref: ""
lane_b_reason: "ocr llm test timed out during parent cs-epic recovery; optional lane B unavailable for this round"
---

# rmux-route-approval 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-design.md`
- Checklist: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-dod-results.json`
- Implementation evidence: `approval-report.md`、`rmux-route-decision-summary.yaml`、report/artifact verifier 输出
- Diff basis: 当前工作区 diff
- Review mode: initial
- Baseline dirty files: none outside this goal driver scope

### Independent Review

- Detection: 父 `cs-epic` 会话具备可见 Task agent/spawn 接口；已启动环节 A。
- 环节 A 独立隔离 Task agent: completed，ref `019f8592-77cb-7af3-8d05-fd357e278604`。
- 环节 B OCR CLI: unavailable；`ocr llm test` 在父会话超时，按协议不阻塞环节 A。
- Merge policy: 独立 reviewer findings 已逐条本地核验并合并；OCR 未完成不阻塞 gate。
- Gate effect: 存在 blocking findings，需 review-fix 后再做 closure。

## 2. Diff Summary

- 新增：`.codestable/features/2026-07-19-rmux-route-approval/approval-report.md`、`rmux-route-decision-summary.yaml`、implementation gate/evidence artifacts、本报告。
- 修改：`rmux-route-approval-checklist.yaml`、`.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml`。
- 删除：none。
- 未跟踪 / staged：新增 CodeStable feature artifacts，未 staged。
- 风险热点：route decision authority、下游 implementation 解锁条件。

## 3. Adversarial Pass

- 假设的生产 bug：route approval 误把旧 `blocking_gaps=7` 的 report 覆盖成 approved，导致下游跳过能力事实。
- 主动攻击过的反例：旧 canonical report hash 和 gap 列表是否仍保留；新 full-backend report 是否为 Windows、`probe_status=completed`、`blocking_gaps=[]`；approval ref 是否在 feature unit 内可恢复；是否改动 production backend。
- 结果：本地主线程核对未发现这些问题，但由于缺独立 reviewer，本报告不定稿通过。

## 4. Findings

### blocking

- [x] REV-001 `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-decision-summary.yaml` 在 review / QA / acceptance 完成前写入 `parent_handoff.downstream_unlocked: true`。
  - Evidence: 独立 reviewer 指出 `rmux-route-approval-acceptance.md` 尚不存在，roadmap item 仍是 `in-progress`，而 design 将 item done 与 downstream unlock 放在 acceptance 回写阶段。
  - Impact: 下游 admission 如果消费 summary，会在 route gate 未闭合时被错误解锁。
  - Expected fix scope: 保留 `route_approved: true`，但在 acceptance 前把 `downstream_unlocked` 置为 `false`，或要求 downstream consumer 同时检查 acceptance artifact / items done。
  - Closure: 已在 review-fix 中把 `downstream_unlocked` 改为 `false`，`next_action` 改为等待 review / QA / acceptance / item done。

- [x] REV-002 `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-dod-results.json` 缺少核心 DoD `CMD-003` 的可机读执行 / 核验证据。
  - Evidence: checklist 声明 `manual capability report and artifacts review` 是 core 且 `fix-or-block`，但 DoD results 只记录 CMD-001/CMD-002；approval report 只有文本声明。
  - Impact: 最核心风险“缺证据误批准 / artifact_index 不可反查”无法由 gate 证据证明，测试会假阳性 passed。
  - Expected fix scope: 补 verifier evidence，记录新旧 report hash、`probe_status/platform/blocking_gaps`、artifact index 条目存在性与 hash 校验、live evidence 存在性。
  - Closure: 已新增 `rmux-route-approval-cmd003-results.json`，并把 CMD-003 纳入 `rmux-route-approval-dod-results.json` 与 evidence pack。

### important

- [x] REV-003 `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-decision-summary.yaml` 将 workaround 风险写为 `not-applicable`，但 fresh report 仍存在 required capability 的 accepted workaround。
  - Evidence: `attach-session`、`refresh-client`、`kill-server`、`attach_reattach` 依赖 live foreground attach / live client commands evidence。
  - Impact: 下游只读 machine summary 时会把“通过 accepted live evidence/workaround 闭合”误读为“完全无 workaround 风险”。
  - Closure: 已改为 `workaround_risk_decision: accepted-via-full-backend-live-evidence`，新增 `accepted_workarounds` 列表，并同步 `approval-report.md#rmux-workaround-risk`。

### nit

- [ ] REV-004 `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml` implementation steps 已 done，但 checks 仍为 pending。
  - Evidence: steps 与 checks 的状态语义不同。
  - Impact: 人读状态可能误解；不阻塞 review-fix，因为 checks 在后续 QA / acceptance 中闭合。

### suggestion

- [x] REV-005 scope gate evidence 初始只列出 4 个 changed files，未覆盖 generated gate/evidence artifacts。
  - Closure: 已同步 `rmux-route-approval-scope-gate-results.json` 与 evidence pack 的 changed_files，列入本轮生成产物。

### learning

- route approval 应同时保留旧 capability report 的 gap facts 和新 full-backend report 的闭合证据，避免审计时丢失路线变化原因。

### praise

none

## 5. Test And QA Focus

- QA 必须复核 `rmux-route-decision-summary.yaml` 的 selected report、hash、`blocking_gaps=[]`、accepted workaround 列表和 `parent_handoff.downstream_unlocked=false` 是否一致；acceptance 才能改为 true。
- QA 必须复核旧 `rmux 0.8.0` report 的 7 个 gaps 没有被删除，而是标记为 superseded。
- Evidence pack residual risks / gate warnings：provider signals skipped；OCR lane unavailable；本 feature 不改 production 代码。
- 建议新增或加强的测试：none，当前为 CodeStable 治理产物。
- 不能靠 review 完全确认的点：未重放 live foreground/client evidence，交给 QA / acceptance 复核。

## 6. Residual Risk

- 未重放 live foreground/client evidence，只确认 fresh report 与 functional acceptance 引用了这些 evidence；QA / acceptance 必须重点复核 accepted workaround 场景。

## 7. Verdict

- Status: passed
- Next: Goal feature 进入 QA。

## 8. Focused Closure

- Closed findings: REV-001, REV-002, REV-003, REV-005
- Attributed delta: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-decision-summary.yaml`、`approval-report.md`、`rmux-route-approval-cmd003-results.json`、`rmux-route-approval-dod-results.json`、`rmux-route-approval-evidence-pack.md`、`rmux-route-approval-scope-gate-results.json`、`rmux-route-approval-evidence-pack-results.json`
- Targeted verification:
  - `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-decision-summary.yaml" --yaml-only` → passed
  - `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml" --yaml-only` → passed
  - `python -m json.tool` on `rmux-route-approval-cmd003-results.json`, `rmux-route-approval-dod-results.json`, `rmux-route-approval-scope-gate-results.json`, `rmux-route-approval-evidence-pack-results.json` → passed
  - read-only CMD-003 verifier summary: selected report `rmux 0.9.0` / Windows / completed / `blocking_gaps=0` / 67 artifact files checked with no missing or hash mismatch; superseded report `rmux 0.8.0` / Windows / completed / `blocking_gaps=7` / 53 artifact files checked with no missing or hash mismatch; live foreground/client evidence files exist.
- Classification: closure-only governance artifact fix；未修改 production 代码、公开 runtime 契约、安全、数据、并发或架构实现。`downstream_unlocked=false` 收紧 admission，CMD-003 evidence 只增加可审计证据。
