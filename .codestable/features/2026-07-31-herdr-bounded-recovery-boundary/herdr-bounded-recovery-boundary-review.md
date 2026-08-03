---
doc_type: feature-review
feature: 2026-07-31-herdr-bounded-recovery-boundary
status: passed
reviewer: subagent+ocr
reviewed: 2026-08-03
round: 5
lane_a_state: completed
lane_a_ref: "019fc4ba-49c8-74f1-9c98-b89035d2be8f"
lane_a_reason: "Kierkegaard completed independent rereview; result: no blocking findings"
lane_b_state: completed
lane_b_ref: "ocr review"
lane_b_reason: "ocr CLI completed; 2 medium findings locally fact-checked and resolved/dispositioned"
---

# herdr-bounded-recovery-boundary 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/evidence/native-windows-x64-herdr-recovery-blocked-evidence.md`
- Gate results: none
- DoD results: implementation report sections "最后一轮本地审计" and "Review-fix 证据（round 4）"
- Implementation evidence: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-implementation.md`
- Diff basis: current workspace diff scoped to R4 review-fix files
- Review mode: full-rereview
- Baseline dirty files: none outside this scoped diff

### Independent Review

- Detection: Task agent capability available; OCR CLI available and `ocr llm test` passed.
- 环节 A 独立隔离 Task agent: independent-agent completed, ref `019fc4ba-49c8-74f1-9c98-b89035d2be8f` (`Kierkegaard`); result: no blocking findings.
- 环节 B OCR CLI: completed; 2 medium findings.
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded.
- Merge policy: subagent and OCR findings were locally fact-checked against current repository code and test evidence.
- Gate effect: no blocking findings remain; review gate may pass.

## 2. Diff Summary

- 新增：none
- 修改：
  - `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-implementation.md`
  - `lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py`
  - `test/test_ccbd_herdr_recovery_boundary.py`
- 删除：none
- 未跟踪 / staged：none
- 风险热点：lifecycle-start tick path, Herdr capability-blocked recovery evidence, idempotent event emission.

## 3. Adversarial Pass

- 假设的生产 bug：`tick_jobs()` production path could still skip a Herdr capability-blocked degraded runtime without writing durable `recover_blocked` evidence.
- 主动攻击过的反例：
  - direct helper coverage passes while `iter_runnable_agent_slots()` still bypasses `refresh_slot_runtime_for_start()`;
  - repeated scheduler ticks append duplicate `recover_blocked` events;
  - blocked branch accidentally calls `refresh_provider_binding(recover=True)`;
  - `drop` / backoff behavior is changed unintentionally.
- 结果：R4 fix now records blocked evidence in `iter_runnable_agent_slots()` before `continue`; the new `tick_jobs()` test covers production entry, no refresh call, durable event write, and second tick idempotence. `drop` remains unchanged.

## 4. Findings

### blocking

none.

### important

none for this scoped diff.

### nit

none.

### suggestion

- OCR suggested making the production tick-path test more explicit. The test was strengthened to assert a second `tick_jobs()` call does not append duplicate `recover_blocked` evidence.

### learning

- `mark_recovery_blocked()` persists health as `provider-recovery-blocked` and appends `recover_blocked`; a later tick is suppressed because `should_record_recovery_capability_block()` no longer treats blocked health as recoverable.
- `R4-001` is closed by testing the real `tick_jobs()` route instead of only `refresh_slot_runtime_for_start()`.

### praise

- The review-fix is narrow: production logic change is confined to the existing blocked branch, with a focused regression test and no scope drift into provider completion, user surfaces, release/update, or Herdr socket/schema/client ownership.

## 5. Test And QA Focus

- QA must verify the same owner boundary through the broader feature evidence: Herdr non-disabled auto restore remains blocked/fail-closed and never claims recovery supported.
- QA should keep `REV-005` as residual risk: no real production producer for `herdr_auto_restore_mode=disabled` is proven in this feature.
- Suggested QA spot check: real `JobDispatcher` + durable `SupervisionEventStore` path, not only `SimpleNamespace` test doubles.
- Review cannot fully confirm real Herdr host recovery pass; current S7 evidence is blocked evidence.

## 6. Residual Risk

- `REV-005` remains non-blocking residual risk: actual Herdr recovery support depends on a production capability producer for `herdr_auto_restore_mode=disabled`. Current feature correctly fail-closes when that producer/evidence is absent and must not be used to claim supported recovery.

## 7. Verdict

- Status: passed
- Next: Goal feature may proceed to `cs-feat` QA stage.

## 8. Focused Closure

none. This was a full rereview because R4 review-fix changed production behavior.
