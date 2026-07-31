---
doc_type: feature-design-review
feature: 2026-07-31-herdr-bounded-recovery-boundary
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fb932-07fc-7220-837d-c21a80979dbb"
reviewed: 2026-08-01
round: 4
---

# herdr-bounded-recovery-boundary feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-checklist.yaml`
- Intent / brainstorm: none
- Requirement: `.codestable/requirements/native-windows-ccb-via-herdr.md`
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Roadmap items: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Related docs: `.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`、`.codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md`
- Code facts checked: `lib/ccbd/services/runtime_recovery_policy.py`、`lib/ccbd/supervision/recovery.py`、`lib/ccbd/supervision/recovery_transitions.py`、`lib/ccbd/supervision/backoff.py`、`lib/ccbd/supervision/evidence.py`、`lib/ccbd/supervision/recovery_events.py`、`lib/ccbd/supervision/recovery_context.py`、`lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py`、`lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/support.py`、`lib/provider_backends/pane_log_support/lifecycle_recovery.py`、`lib/provider_backends/pane_log_support/lifecycle_common.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fb6fd-4a66-7bb0-b09b-0c6b1d9cb39a` changes-requested；round 2 `019fb706-2bc8-76e3-a192-533bdaa67a30` changes-requested；round 3 `019fb713-f810-76b2-927b-a71ea4e7d7a1` passed；requirement update 后 round 4 `019fb932-07fc-7220-837d-c21a80979dbb` changes-requested。
- Raw output: round 4 确认主契约覆盖 recovery owner、auto restore fail-closed、90 秒 probation、raw token redaction、lifecycle start gate、Native Windows x64 hard gate 和 upstream admission；唯一 blocking 是 `CMD-008` 会把合法 `restore_token_present` 误判为 raw `restore_token` 泄漏。
- Merge policy: 已逐条核验 reviewer finding 与 design/checklist/roadmap/code 事实；只合并有仓库事实支撑的结论。
- Gate effect: round 4 blocking 已通过 focused closure 关闭；design-review gate passed。

## 2. Design Summary

- Goal: 定义 Herdr backend 下 CCB bounded recovery 的唯一 owner，Herdr restore 只作为 private backend operation/evidence。
- Key contracts: `HerdrRecoveryPolicy.owner="ccb"`；Herdr auto restore 只有 `disabled` 可进入 recovery-capable/supported；public recovery evidence 只输出 sanitized refs 与 `restore_token_present`；Herdr agent state diagnostics-only；probation/circuit/backoff 均由 CCB gate 决定。
- Steps: 7 个步骤，覆盖 admission、policy/evidence、probation/circuit、action routing、provider pane primitive、regression/scope、Native Windows recovery evidence。
- Checks: 9 个 checks 覆盖 upstream admission、owner boundary、redaction、probation/circuit、lifecycle start gate、tmux/rmux regression、scope guard 和 manual transcript。
- Baseline / validation: CMD-003 作为 upstream acceptance fail-closed gate；CMD-007 覆盖 provider completion/user-surface/package/release/update/installer/Herdr socket schema-client 越界；CMD-008 覆盖 probation/circuit presence 与 public raw restore token leakage guard。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- 可在实现阶段把 CMD-007/CMD-008 的长内联 Python 沉淀为只读工具脚本，降低 quoting 和 regex 漂移风险。当前 design 阶段不新增工具脚本。

### learning

- 本 feature 的关键是 CCB recovery state machine 的 hard gate，而不是把 Herdr restore 能力接上去。
- `restored` 在现有 CCB 中是通用成功 health；Herdr probation 应限定在 Herdr recovery projection，不应全局改写 `restored` 语义。
- raw restore token 风险来自 public evidence ledger/event/project/log/support 投影；presence projection 必须保留为合法 public evidence。

### praise

- upstream admission 正确禁止用 `provider-runtime-on-herdr` design-review passed 代替 implementation/acceptance。
- design 明确要求 lifecycle start queued-slot refresh 复用同一 Herdr owner/backoff/probation/circuit gate，避免形成第二个 recovery owner。
- `CMD-008` focused closure 后精确允许 `restore_token_present` / `namespace_restore_token_present`，同时继续禁止 raw `restore_token` public 泄漏。

## 4. User Review Focus

- 用户需要重点拍板：父 roadmap §4.6 已收紧为 redacted recovery evidence；implementation 前仍依赖 `provider-runtime-on-herdr` acceptance。
- implement 需要重点遵守：CCB 唯一 recovery owner、Herdr auto restore disabled hard gate、lifecycle start refresh 同 gate、90 秒 probation/circuit、raw token private-only、Herdr pane recovery 不进 tmux ownership/identity。
- code review / QA / acceptance 需要重点复核：probation 不被 `restored` 短路；public payload 只包含 presence projection；scope guard 不误报也不漏过 package/release/update/installer 和 Herdr socket schema/client owner 越界。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-001 至 AC-011 覆盖 admission、ledger、auto restore、backoff、recovery、redaction、regression、manual evidence、scope boundary。 | implementation 重点验证 redaction tests。 |
| DoD Contract | pass | E | DOD 覆盖 design、implementation、review、QA、acceptance；DOD-IMPL-002/003/006 显式约束 redaction、probation/circuit、scope boundary。 | none |
| Steps and checks traceability | pass | E | checklist S1-S7 与 checks/CMD 对齐；S2/S3/S4/S6 覆盖 reviewer 风险点。 | none |
| Roadmap contract compliance | pass | E/C | roadmap 要求 CCB recovery owner、auto restore disabled、90 秒 probation、redacted evidence、Native Windows evidence；design/checklist 已对齐。 | none |
| Module interface design | pass | C | runtime_recovery_policy、supervision recovery/backoff/evidence、lifecycle start slots、pane lifecycle recovery 代码事实支撑 seam。 | implementation/code review 复核。 |
| Validation and artifacts | pass | E/C | design/checklist/items YAML passed；CMD-007 passed；CMD-008 regex fixture 证明允许 presence projection、禁止 raw key。 | CMD-008 完整运行需 implementation diff 提供 probation/circuit evidence。 |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- `provider-runtime-on-herdr` 仍是 design-review passed 而非 accepted；implementation admission 必须继续 dependency-blocked，直到 CMD-003 通过。
- 现有代码仍是 tmux/rmux recovery 基线，无 Herdr policy/probation/circuit 实现；这是本 feature 实现范围，不是 design 缺口。
- CMD-008 是静态 regex guard，不是唯一 redaction 证明；实现阶段必须有 `runtime.namespace_ref` raw token fixture、ledger sanitizer unit test、event/log/project-visible payload redaction test。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop；本 child design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: round 1 `FDR-001`、`FDR-002`、`FDR-003`；round 2 `FDR-R2-001`、`FDR-R2-002`；round 4 `HBR-FDR-001`（`CMD-008` raw token guard 误杀 presence projection）。
- Attributed delta: design/checklist 收紧 package/release/update/installer 与 Herdr socket schema/client owner scope guard；`CMD-007` 增加 forbidden files、Herdr owner path guard 和 untracked implementation content scan；`CMD-008` 增加 untracked `lib/test` scan，并把 raw token regex 改为 `(?<![A-Za-z0-9_])restore_token(?![A-Za-z0-9_])`。
- Verification: `validate-yaml.py` 校验 design、checklist、roadmap items 均通过；`git diff --check` 通过；CMD-007 执行通过；CMD-008 合成 fixture 证明 `restore_token_present` / `namespace_restore_token_present` 不触发，raw `restore_token` public key 触发。
- Classification: 本轮 closure 只修复 validation guard 对既有 redaction 契约的误判，并补齐 requirement update 下的 scope guard 显式边界；没有改变 recovery owner、public contract、架构 seam 或实现范围。
