---
doc_type: feature-design-review
feature: 2026-07-31-herdr-backend-contract-spike
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb8f4-1da6-72a2-8a84-1643c4389291
reviewed: 2026-08-01
round: 4
---

# herdr-backend-contract-spike feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/requirements/native-windows-ccb-via-herdr.md`、`.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap-review.md`、`.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`、`.codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md`
- Code facts checked: `lib/terminal_runtime/mux_backend_contract.py`、`lib/terminal_runtime/backend_resolver.py`、`test/test_mux_backend_contract.py`、`test/test_terminal_runtime_backend_selection.py`、`test/test_v2_project_namespace_backend.py`、`test/test_v2_runtime_launch.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019fb8f4-1da6-72a2-8a84-1643c4389291`
- Raw output: 第 4 轮只读复审未发现 `blocking` 或 `important`；确认 Kepler 上轮关注点已闭合。
- Merge policy: 已逐条核验 reviewer finding 与本地 design/checklist/roadmap/code 事实；唯一 nit 已做 focused closure。
- Gate effect: independent review completed and merged; final verdict may pass.

## 2. Design Summary

- Goal: 用真实 Native Windows x64 + Herdr CLI/socket spike 证明 session、pane、send、capture、kill、restore 和 provider CLI dry-run 是否足够支撑后续正式 Herdr adapter。
- Key contracts: 只产出 spike/evidence，不修改生产 resolver、mux contract、ccbd、provider runtime、doctor 或 package metadata；Native Windows x64、platform gate、Herdr 缺失或 capability 不完整必须 fail closed。
- Steps: 8 个 step，覆盖 host admission、schema/status、session/pane I/O、provider CLI dry-run、kill pane、detach/reattach、isolated server restart、evidence verdict。
- Checks: 10 个 check 覆盖 fail-closed host admission、schema traceability、named session、sentinel I/O、provider/fallback 分离、kill、detach、restart isolation、evidence truth table 和 production no-change guard。
- Baseline / validation: CMD-001/CMD-002 YAML gate；CMD-003 evidence validator；CMD-004 production no-change guard；CMD-005 是 core/manual-core native Herdr spike；CMD-006 是 truth table focused validator。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- 实现阶段建议给 `adapter_recommendation` truth table 做最小 fixture 表，而不是只靠测试名表达覆盖意图。

### learning

- production no-change guard 有代码事实支撑：当前 resolver 只接受 `tmux|rmux|auto`，非法值走 `invalid-request`；当前 mux contract 不含 `herdr-native`。
- `manual_core` 不替代 `core: true`；本 design 表达“真实 host run 是核心，但缺 host 时必须落 blocked evidence”。

### praise

- `HostEvidence` 已把 Native Windows x64 / 非 WSL / platform gate ref 固化为非 blocked verdict 的机器前置条件。
- `RestartIsolationEvidence` 已把 restart 隔离证明展开为可审计 object，避免触碰用户全局 Herdr session。
- `provider_cli_dry_run` 与 `fallback_terminal_smoke` 已分离，且明确 `public_provider_parity_claimed=false`。
- kill / detach / isolated restart 已原子化为独立 steps。
- `adapter_recommendation="continue"` truth table 覆盖 host、top-level failure_class、核心 operations、restart isolation、provider CLI dry-run 和 capability gaps。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只是事实型 spike gate；如果 Native Windows x64 + Herdr host、platform gate 或 restart isolation 不满足，正确结果是 blocked evidence，不是继续 adapter。
- implement 需要重点遵守：CMD-005 必须显式传 `--platform-gate-ref`；server restart 不能碰全局 Herdr server；fallback terminal smoke 不代表 provider dry-run pass。
- code review / QA / acceptance 需要重点复核：production no-change guard、HostEvidence、RestartIsolationEvidence、provider/fallback split、truth table、capability_projection 与 adapter_recommendation 的一致性。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 至 AC-010，并映射 S1 至 S8、证据类型和命令 / 动作。 | none |
| DoD Contract | pass | E | design §3.4 覆盖 design、implementation、review、QA、acceptance DoD，DOD-IMPL-006 覆盖 production no-change guard。 | implementation 补齐 new tests / run_spike。 |
| Steps and checks traceability | pass | E | checklist steps/checks 均可追溯到 AC / DOD / 明确不做；kill、detach、restart 已分离。 | none |
| Roadmap contract compliance | pass | E | roadmap item `minimal_loop: true` 要求 kill/provider dry-run；design/checklist 覆盖 session/pane/send/capture/kill/restore/provider dry-run，并明确不代表 all-provider parity。 | none |
| Module interface design | pass | C | 本地核验现有 mux contract/resolver 测试面；本 feature 不改生产 contract，只输出 spike evidence。 | 后续 V2 design 另起正式 contract。 |
| Validation and artifacts | pass | E | CMD-003/CMD-006 验证 evidence schema、host gate、restart isolation、provider/fallback split 与 truth table；CMD-004 守 production no-change。 | Native Windows host evidence 是实现硬依赖。 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- `test/test_herdr_contract_spike_evidence.py`、`test/test_herdr_spike_no_production_route.py`、`run_spike.py`、`herdr-contract-spike-evidence.json` 当前尚未存在，属于 implementation 阶段必须补齐的产物。
- Native Windows x64 + Herdr 真机 evidence 不可由 WSL/Linux 替代；缺 host、缺 platform gate、缺 Herdr 或 restart 无法隔离时只能产出 blocked evidence。
- Herdr schema/API 是外部变化面；实现阶段必须以本机安装的 `herdr api schema --json` 为准。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop，继续处理下一个未完成 child；本 child 的 design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: Kepler FDR-001 HostEvidence / platform gate evidence；FDR-002 restart isolation proof；FDR-003 provider/fallback split；FDR-004 step 原子性；FDR-005 production no-change guard；FDR-006 recommendation truth table；Gibbs nit `--platform-gate-ref` 与 `host.platform_gate_ref` 映射。
- Attributed delta: design/checklist 新增 `HostEvidence`、`RestartIsolationEvidence`、`ProviderCliDryRunEvidence`、`FallbackTerminalSmokeEvidence`、`OperationFailureClass`、truth table、no-change guard、`--platform-gate-ref` 命令参数，并拆分 kill/detach/restart steps。
- Verification: reviewer `019fb8f4-1da6-72a2-8a84-1643c4389291` 返回无 blocking/important；本地复核 requirement hard gates、roadmap item notes、current mux resolver/contract code facts、checklist YAML 和 roadmap items YAML。
- Classification: Kepler findings 之后已做完整独立复审；Gibbs 的术语 nit 只补 CLI 参数名到 evidence 字段名映射，不改变行为、公开契约、架构边界、验收语义或范围，按 focused closure 处理。
