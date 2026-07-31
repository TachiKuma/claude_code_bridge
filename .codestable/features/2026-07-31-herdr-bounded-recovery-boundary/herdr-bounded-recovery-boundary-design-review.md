---
doc_type: feature-design-review
feature: 2026-07-31-herdr-bounded-recovery-boundary
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fb713-f810-76b2-927b-a71ea4e7d7a1"
reviewed: 2026-07-31
round: 3
---

# herdr-bounded-recovery-boundary feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`、`.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Related docs: `.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`、`.codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md`
- Code facts checked: `lib/ccbd/services/runtime_recovery_policy.py`、`lib/ccbd/supervision/recovery.py`、`lib/ccbd/supervision/recovery_transitions.py`、`lib/ccbd/supervision/backoff.py`、`lib/ccbd/supervision/evidence.py`、`lib/ccbd/supervision/recovery_events.py`、`lib/ccbd/supervision/recovery_context.py`、`lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py`、`lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/support.py`、`lib/provider_backends/pane_log_support/lifecycle_recovery.py`、`lib/provider_backends/pane_log_support/lifecycle_common.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fb6fd-4a66-7bb0-b09b-0c6b1d9cb39a`；round 2 `019fb706-2bc8-76e3-a192-533bdaa67a30`；round 3 `019fb713-f810-76b2-927b-a71ea4e7d7a1`
- Raw output: round 1 returned `changes requested`；round 2 returned `changes requested`；round 3 returned `passed`
- Merge policy: 已逐条本地核验 round 1/2 findings 并修订；round 3 确认两个 round 2 blocking 已关闭，未发现 round 1 closure 回退。
- Gate effect: completed; final verdict may pass

## 2. Design Summary

- Goal: 定义 Herdr backend 下 CCB bounded recovery 的唯一 owner，Herdr restore 只作为 backend operation/evidence。
- Key contracts: `HerdrRecoveryPolicy.owner="ccb"`；public recovery evidence 只输出 `restore_token_present`；Herdr agent state diagnostics-only；probation/circuit/backoff 均由 CCB gate 决定。
- Steps: 7 个步骤，风险热点是 admission、redaction、probation/circuit、lifecycle start refresh、backend-neutral pane recovery。
- Checks: 9 个 checks，已覆盖 dependency admission、owner boundary、redaction、probation/circuit、routing、tmux/rmux regression、scope guard 与 manual transcript。
- Baseline / validation: YAML 校验通过；scope guard 修正后不扫描 `.codestable` design 文档自身。

## 3. Findings

### blocking

- [x] FDR-001 `roadmap §4.6 / design Roadmap contract delta` 父 roadmap 的 `HerdrRecoveryEvidence.restore_token` 与 child redaction 契约冲突。
  - Evidence: roadmap §4.6 原先公开 `restore_token: str | None`；design 要求 public/event 只输出 `restore_token_present`。
  - Impact: 实现者可能按父契约输出 raw token，破坏 secret boundary。
  - Expected fix scope: 已把 roadmap §4.6 改为 `restore_token_present` + `herdr_agent_state_ref`，并在 design 加 `Roadmap contract delta`。

- [x] FDR-002 `lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py` dispatcher lifecycle start 可能绕过 bounded recovery owner gate。
  - Evidence: `refresh_slot_runtime_for_start()` 可直接调用 `refresh_provider_binding(recover=True)`，只依赖 recoverable health/provider resume。
  - Impact: queued-slot refresh 可能绕过 backoff、recover_started ledger、probation 和 circuit。
  - Expected fix scope: design 已要求 lifecycle start recovery 复用 Herdr owner/backoff/probation/circuit admission，或在 Herdr degraded/probation/circuit 状态下 keep/drop。

- [x] FDR-003 `design Probation / circuit transition contract` 90 秒 probation / durable circuit 状态机不够可实现。
  - Evidence: 现有 `SUCCESS_RUNTIME_HEALTHS` 包含 `restored`，`mark_recovery_succeeded()` 会立即写 steady。
  - Impact: AC-007 / DOD-IMPL-003 可能被字段名实现短路，无法证明 90 秒 probation。
  - Expected fix scope: design 已补最小 transition contract：probation 起止字段、90 秒 gate、`recover_succeeded` 条件、`circuit_threshold=3`、reset 规则。

- [x] FDR-R2-001 `lib/ccbd/supervision/evidence.py / namespace_ref` raw restore token 仍可能经 `namespace_ref` 间接进入 public evidence。
  - Evidence: roadmap §4.3 的 `MuxNamespaceRefV2` 含 `restore_token`；现有 `runtime_namespace_ref()` 原样复制 dict，`build_runtime_evidence_ledger()` 会把它写入 public `evidence_ledger.namespace_ref`。
  - Impact: 即使 `HerdrRecoveryEvidence` 改为 `restore_token_present`，raw token 仍可能通过 namespace_ref 泄露到 event/log/support/project evidence。
  - Expected fix scope: design/checklist 已要求 public ledger sanitize `namespace_ref.restore_token`，删除该键并投影 `restore_token_present=True`；新增含 raw token fixture 的 namespace_ref sanitizer / redaction tests。

- [x] FDR-R2-002 `checklist CMD-008` 原始命令在 PowerShell 下 quoting 不稳，且误禁 private `restore_token`。
  - Evidence: round 2 reviewer 在 PowerShell 下复现 `SyntaxError: unterminated string literal`；命令还会误伤合法 private backend call/test fixture。
  - Impact: core validation command 不稳定，且会阻塞必要 redaction fixture。
  - Expected fix scope: CMD-008 已改为无嵌套 quote regex 的 Python inline；guard 从禁止任意 `restore_token` key 改为禁止 public evidence/log/event raw token 泄露，允许 private call/test fixture。

### important

- [x] FDR-004 `recovery_context.py / recovery_transitions.py` namespace restore seam 没定义到接口深度。
  - Evidence: `attempt_recovery_action()` 对 namespace health 未 reflow 时直接失败；`RecoveryContext` 无 restore seam。
  - Impact: implementation 可能在 transition 内直接调用 Herdr client。
  - Expected fix scope: design 已要求通过 CCB-owned runtime/namespace service private call 承载 namespace restore，transition 不解析 Herdr JSON。

- [x] FDR-005 `lifecycle_recovery.py / lifecycle_common.py` pane lifecycle 的 tmux 依赖不止 `%pane`。
  - Evidence: respawn 后续还有 tmux ownership 与 `apply_session_tmux_identity()`。
  - Impact: 只移除 `%` 会让 Herdr pane_ref 进入 tmux-specific 逻辑。
  - Expected fix scope: design/checklist 已要求 backend-neutral Herdr pane recovery helper；tmux ownership/identity 仅保留在 tmux-family 分支。

- [x] FDR-006 `checklist CMD-007` scope guard 会因 design 文档自身误报。
  - Evidence: 原命令读取 untracked `.md/.yaml/.json`，当前 feature design 含禁止项文字。
  - Impact: 核心验证命令不可用。
  - Expected fix scope: CMD-007 已收紧为只扫描 `lib/`、`test/`、`bin/`、`scripts/` diff/cached diff。

Round 3 independent review: none。

### nit

- [x] FDR-007 `design action enum` action 名称风格不统一。
  - Evidence: design、roadmap 和现有 recovery event details 混用 `namespace_restore`、`circuit-open`、`namespace_recover`。
  - Expected fix scope: design/roadmap 已统一到 snake_case canonical enum，legacy detail 映射到同一 enum。

Round 3 independent review: none。

### suggestion

- [x] FDR-008 `checklist S3/S6` S3 粒度偏宽。
  - Evidence: 原 S3 同时覆盖 backoff、probation、circuit、crash logs。
  - Expected fix scope: S3 收敛为 probation/circuit state machine，S6 承接 bounded crash log retention and regression guard。

- FDR-R3-S001 `checklist CMD-008` regex guard 只适合作为实现阶段快速防线，不能作为唯一 redaction 证明。
  - Evidence: CMD-008 只扫描 `git diff -- lib test` 并匹配 public-context 关键词。
  - Expected follow-up: 实现阶段必须同时落地 `runtime.namespace_ref` raw token fixture、ledger sanitizer unit test、event/log/project-visible payload redaction test。

### learning

- `restored` 在现有 CCB 中已经是通用成功 health；Herdr probation 应限定在 Herdr recovery projection，不应全局改写 `restored` 语义。
- 现有代码事实支持 raw token 风险判断：`runtime_namespace_ref()` 当前原样复制 `namespace_ref`，`build_runtime_evidence_ledger()` 投影到 public ledger，`append_recovery_event()` 写入 event details，后续 `SupervisionEvent.to_record()` 也按 details 原样投影。

### praise

- dependency admission 与 redaction 边界明确；CMD-003 在 provider runtime 未 accepted 时会 fail closed，符合设计意图。
- Round 3 reviewer 确认 redaction 契约已足够明确：public ledger 前必须删除 `namespace_ref.restore_token`，并投影 top-level `restore_token_present=True`；checklist S2 和 evidence_required 也要求 raw token fixture / sanitizer / ledger redaction tests。

## 4. User Review Focus

- 用户需要重点拍板：父 roadmap §4.6 已收紧为 redacted recovery evidence；implementation 前仍依赖 `provider-runtime-on-herdr` acceptance。
- implement 需要重点遵守：CCB 唯一 recovery owner、lifecycle start refresh 同 gate、90 秒 probation/circuit、raw token private-only、Herdr pane recovery 不进 tmux ownership/identity。
- code review / QA / acceptance 需要重点复核：probation 不被 `restored` 短路、scope guard 不误报、不修改 provider completion/user surfaces/release surface。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC matrix 覆盖核心场景，round 3 确认 namespace_ref sanitizer / CMD-008 修订可放行 | implementation 重点验证 redaction tests |
| DoD Contract | pass | E | DOD 已补 probation/lifecycle start/crash log split 与 namespace_ref sanitizer | none |
| Steps and checks traceability | pass | E | S1-S7 与 checks/CMD 对齐，S2 已补 namespace_ref raw token fixture | none |
| Roadmap contract compliance | pass | E | roadmap §4.6 已同步 redacted evidence；§4.3 private restore_token 进入 public ledger前需 sanitize | none |
| Module interface design | pass | C | 代码事实支撑 seam；namespace restore 和 ledger sanitizer 已补，round 3 未发现 blocking/important | implementation/code review 复核 |
| Validation and artifacts | pass | E | YAML passed，CMD-007 passed，CMD-008 在 PowerShell 下可解析并按实现阶段 guard 预期断言 | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- `provider-runtime-on-herdr` 仍是 design-review passed 而非 accepted；implementation admission 必须继续 dependency-blocked，直到 CMD-003 通过。
- `provider-runtime-on-herdr` 仍是 design-review passed 而非 accepted；implementation admission 必须继续 dependency-blocked，直到 CMD-003 通过。
- CMD-008 是静态 regex guard，不是唯一 redaction 证明；实现阶段必须有 runtime.namespace_ref raw token fixture、ledger sanitizer unit test、event/log/project-visible payload redaction test。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child batch loop。

## 8. Focused Closure

- Closed findings: none
- Attributed delta: 本轮继续实质修订 namespace_ref sanitizer/redaction contract 和 CMD-008 public leak guard，不适用 focused closure。
- Verification: checklist YAML passed；roadmap items YAML passed；CMD-007 passed；CMD-008 在 PowerShell 下无 quoting/SyntaxError，当前因尚无 implementation diff 在 probation/circuit 断言处失败，符合 implementation-stage guard 预期；round 3 independent review passed。
- Classification: 改变 public evidence sanitizer 与 core validation semantics，必须完整独立复审。
