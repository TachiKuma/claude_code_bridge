---
doc_type: feature-design-review
feature: 2026-07-31-herdr-backend-contract-spike
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb63a-9fae-7de2-8b15-29467ae705b4
reviewed: 2026-07-31
round: 2
---

# herdr-backend-contract-spike feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap-review.md`、`.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`、`.codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md`
- Code facts checked: `lib/terminal_runtime/mux_backend_contract.py`、`lib/terminal_runtime/backend_resolver.py`、`test/test_mux_backend_contract.py`、`test/test_terminal_runtime_backend_selection.py`、`test/test_v2_project_namespace_backend.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fb633-111e-7983-b3e9-b7c65f81e232` changes-requested；round 2 `019fb63a-9fae-7de2-8b15-29467ae705b4` passed。
- Raw output: round 2 未发现 `blocking` 或 `important`；确认 FDR-001/FDR-002/FDR-003 已关闭。
- Merge policy: 已逐条核验 reviewer finding 与本地 design/checklist/roadmap/code 事实；nit/suggestion 已做 focused closure。
- Gate effect: independent review completed，允许本地合并后定稿 `passed`。

## 2. Design Summary

- Goal: 用真实 Native Windows x64 + Herdr CLI/socket spike 证明 session、pane、send、capture、kill、restore 和 provider dry-run 是否足够支撑后续正式 Herdr adapter。
- Key contracts: 只产出 spike/evidence，不修改生产 resolver、mux contract、ccbd、provider runtime、doctor 或 package metadata；核心 Native Windows Herdr run 必须执行或产出 blocked evidence。
- Steps: 6 个 step，覆盖 host admission、schema/status、session/pane I/O、provider dry-run、kill/restore semantics、evidence verdict。
- Checks: 9 个 check 覆盖 fail-closed host admission、schema traceability、named session、sentinel I/O、provider dry-run、kill、restore 隔离、evidence validator 和 production no-change guard。
- Baseline / validation: CMD-001/CMD-002 YAML gate；CMD-003 evidence validator；CMD-004 production no-change guard；CMD-005 是 core/manual-core native Herdr spike；CMD-006 最小机器检查。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- FDR-006 `capability_projection` 到 `MuxCapabilitiesV2` 的 `unknown` 映射后续仍需正式 V2 design 归类。
  - Evidence: design 已明确 `unknown` 只表示 spike 未证实状态，不能直接视作 `supported` 或 `workaround`。
  - Impact: 不阻塞 spike；后续 `mux-backend-contract-herdr-v2` 必须把 unknown 转成明确 capability policy。

### learning

- `manual_core` 不能替代 `core: true`；本 design 同时保留二者，表达“真实 host run 是核心，但缺 host 时必须落 blocked evidence”。

### praise

- scope 边界清楚：spike 不改生产 runtime，不提前引入 Herdr adapter。
- restore 语义分离 live detach/reattach 与 server restart restore，并要求 dedicated/disposable server 或 isolated socket/config。
- Herdr agent state 只作为 diagnostics/observation，不作为 CCB provider completion authority。
- evidence 增加 `capability_projection`，下游能更直接评估 continue / stop / needs-upstream-issue。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只是事实型 spike gate；如果 Native Windows x64 + Herdr host 不可用，正确结果是 blocked evidence，不是继续 adapter。
- implement 需要重点遵守：CMD-005 为 core；server restart 不能碰全局 Herdr server；无法隔离时必须 blocked。
- code review / QA / acceptance 需要重点复核：生产代码 no-change guard、evidence artifact refs、restart_scope、residual_risks、capability_projection 与 adapter_recommendation 的一致性。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 至 AC-009，并映射 S1 至 S6、证据类型和命令 / 动作。 | none |
| DoD Contract | pass | E | design §3.4 覆盖 design、implementation、review、QA、acceptance DoD 与 required artifacts。 | implementation 补齐 new tests / run_spike。 |
| Steps and checks traceability | pass | E | checklist steps/checks 均可追溯到 AC / DOD / 明确不做；CMD-005 已为 core。 | none |
| Roadmap contract compliance | pass | E | roadmap item `minimal_loop: true` 要求 kill/provider dry-run；design/checklist 覆盖 session/pane/send/capture/kill/restore/provider dry-run。 | none |
| Module interface design | pass | C | 本地核验现有 mux contract/resolver 测试面；本 feature 不改生产 contract，只输出 spike evidence。 | 后续 V2 design 另起正式 contract。 |
| Validation and artifacts | pass | E | CMD-003/CMD-006 验证 evidence schema 与语义；CMD-004 守生产 no-change；Required Artifacts 可反查。 | Native Windows host evidence 是实现硬依赖。 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- `test/test_herdr_contract_spike_evidence.py`、`run_spike.py`、`herdr-contract-spike-evidence.json` 当前尚未存在，属于 implementation 阶段必须补齐的产物。
- Native Windows x64 + Herdr 真机 evidence 不可由 WSL/Linux 替代；缺 host、缺 Herdr 或 restart 无法隔离时只能产出 blocked evidence。
- Herdr socket/schema 是外部变化面；实现阶段必须以 runtime schema snapshot 为准。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop，继续处理下一个未完成 child；本 child 的 design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-005。
- Attributed delta: CMD-005 改为 `core: true` 且保留 `manual_core`；新增 `--isolated-server` 与 blocked evidence 规则；展开 `HerdrProbeSummary`、`ProviderDryRunEvidence`、`HerdrRestoreEvidence`、`HerdrCapabilityProjection`；CMD-006 加入 `residual_risks` 与 `restart_scope` 检查。
- Verification: checklist YAML 与 roadmap items YAML 校验通过；round 2 independent reviewer 返回 `passed`；本地 grep 复核 `residual_risks`、`restart_scope`、`capability_projection`、CMD-005/CMD-006 均已落入 design/checklist。
- Classification: focused closure 只补强 evidence 字段和 validator 约束，不改变 feature 范围、公开契约或 roadmap 依赖。
