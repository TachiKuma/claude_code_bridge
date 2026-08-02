---
doc_type: feature-review
feature: 2026-07-31-herdr-bounded-recovery-boundary
status: changes-requested
reviewer: subagent
reviewed: 2026-08-03
round: 4
lane_a_state: completed
lane_a_ref: "019fc4a4-3585-7990-b7fb-97cb8df5d04d"
lane_a_reason: "Bohr completed independent rereview; result: changes-requested"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "ocr CLI is available, but current workspace has large baseline dirty outside this feature scope; protocol forbids naked workspace OCR and ocr review has no include-file flag"
---

# herdr-bounded-recovery-boundary 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/evidence/native-windows-x64-herdr-recovery-blocked-evidence.md`
- Gate results: none
- DoD results: implementation report section "最后一轮本地审计"
- Implementation evidence: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-implementation.md`
- Diff basis: current workspace diff, scoped to this feature files only
- Review mode: full-rereview
- Baseline dirty files: many existing roadmap/provider-runtime/Herdr namespace lifecycle dirty files are present; this review scope excludes them.

### Independent Review

- Detection: Task agent capability available; OCR CLI available.
- 环节 A 独立隔离 Task agent: independent-agent completed, ref `019fc4a4-3585-7990-b7fb-97cb8df5d04d` (`Bohr`); result `changes-requested`. Round 3 reviewer `019fc477-3352-7142-8064-7bfa961b6e99` (`Sartre`) completed with `changes-requested`; REV-006/REV-007 have since received review-fix changes.
- 环节 B OCR CLI: skipped
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion, Low->discarded
- Merge policy: Bohr findings have been locally fact-checked against current repository code and merged below; OCR is skipped for scope ambiguity.
- Gate effect: unresolved blocking finding prevents QA transition; next step is feature implementation review-fix.

## 2. Diff Summary

- 新增：
  - `test/test_ccbd_herdr_recovery_boundary.py`
  - `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-implementation.md`
  - `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/evidence/native-windows-x64-herdr-recovery-blocked-evidence.md`
- 修改：
  - `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-checklist.yaml`
  - `lib/agents/models_runtime/runtime_runtime/agent.py`
  - `lib/agents/store.py`
  - `lib/ccbd/services/runtime_recovery_policy.py`
  - `lib/ccbd/services/provider_runtime_facts.py`
  - `lib/ccbd/services/runtime.py`
  - `lib/ccbd/services/runtime_runtime/attach.py`
  - `lib/ccbd/services/runtime_runtime/attach_models.py`
  - `lib/ccbd/services/runtime_runtime/attach_records.py`
  - `lib/ccbd/services/runtime_runtime/attach_values.py`
  - `lib/ccbd/services/runtime_runtime/refresh.py`
  - `lib/ccbd/supervision/recovery.py`
  - `lib/ccbd/supervision/recovery_transitions.py`
  - `lib/ccbd/supervision/recovery_events.py`
  - `lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/support.py`
  - `lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py`
  - `lib/provider_backends/pane_log_support/lifecycle_recovery.py`
- 删除：none
- 未跟踪 / staged：本 feature 新文件未跟踪；无 staged diff
- 风险热点：recovery state machine、event evidence redaction、lifecycle start routing、pane lifecycle primitive

## 3. Adversarial Pass

- 假设的生产 bug：真实 Herdr runtime 若不能持久化 `herdr_auto_restore_mode=disabled`，recovery 会按 design fail-closed 并保持 blocked，而不是自动恢复。
- 主动攻击过的反例：非 disabled auto restore、raw namespace token fixture、Herdr 3 次不稳定、非 Herdr 6 次 circuit、lifecycle start process-dead、namespace action mapping、Herdr pane_ref 不带 `%`。
- 结果：Bohr 确认 `REV-006` redaction 边界已闭合，但发现 `REV-007` 的修复只覆盖 direct `refresh_slot_runtime_for_start()` 路径，真实 lifecycle-start tick iterator 路径仍会静默跳过 blocked runtime，升级为 `R4-001`。

## 4. Findings

### blocking

- [ ] R4-001 `lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/tick.py:13-14` / `lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py:184-187` lifecycle-start 常规 tick 路径仍会绕过 durable blocked evidence。
  - Evidence: `tick_jobs()` 只对 `iter_runnable_slots()` yield 出来的 slot 调用 `start_next_queued_job()`；`start_next_queued_job()` 才会调用 `refresh_slot_runtime_for_start()`。但 `iter_runnable_agent_slots()` 在 degraded runtime 上先执行 `_degraded_runtime_action()`，当 action 为 `blocked` 或 `drop` 时直接 `continue`，不会触发 `refresh_slot_runtime_for_start()` 中新增的 `_record_lifecycle_recovery_blocked()`。现有测试 `test_lifecycle_start_blocked_herdr_auto_restore_writes_evidence` 直接调用 `refresh_slot_runtime_for_start()`，覆盖的是旁路而不是生产 tick 路径。
  - Impact: Herdr `observe-only|unsupported|unknown` capability-blocked runtime 在真实 lifecycle-start queue scan 中仍可能被静默跳过；虽然不会调用 `refresh_provider_binding(recover=True)`，但仍违反 AC-003 / REV-007 的 durable `recover_blocked` supervision evidence 要求。
  - Expected fix scope: 在 `iter_runnable_agent_slots()` 对 `action == "blocked"` 的 `continue` 前复用同一 `_record_lifecycle_recovery_blocked()`，或重构为所有 lifecycle-start degraded admission 都走一个统一决策函数；保持幂等，避免重复 tick 反复写事件，并继续禁止 `refresh_provider_binding(recover=True)`。

### important

- [ ] REV-005 `lib/ccbd/services/provider_runtime_facts.py` lacks a real production capability producer for `herdr_auto_restore_mode`.
  - Evidence: current implementation reads and persists the field, and tests can supply fixture values, but no concrete Herdr backend capability source is proven in this feature.
  - Impact: safety behavior remains fail-closed as `unknown`; QA/acceptance must record this as blocked evidence and must not claim real recovery is supported until a producer exists.
  - Round 4 disposition: Bohr confirmed this remains important / residual risk rather than blocking, because current policy fail-closes for non-`disabled` modes and the producer is outside this recovery-boundary feature.

### nit

none.

### suggestion

- Bohr 建议后续 cleanup 考虑复用递归 redaction 语义，避免未来新增 nested ref 时浅层 sanitizer 漂移成新漏洞；当前 `AgentRuntime.to_record()` 与 `RuntimeService.attach()` 对本 design 指定的 raw namespace token 边界已基本闭合。
- 可在后续 cleanup 中把 checklist CMD-004 的旧测试文件名迁移到当前真实文件 `test/test_v2_ccbd_supervision_loop.py`，并把 CMD-007/CMD-008 从全 workspace dirty 扫描改为接受 scoped changed-files 输入，降低长程 goal 下的历史 dirty 误杀。

### learning

- Herdr recovery gate 当前按 design fail-closed：没有可证明的 `herdr_auto_restore_mode=disabled` 时不会自动 recovery。
- 当前 Herdr server `not_running`，只能作为 blocked evidence，不能作为 recovery pass。
- 当前实现没有观察到 `agents runtime model -> provider_runtime helper` 的循环 import；`AgentRuntime` 使用本文件私有 sanitizer，未导入 `provider_runtime`。
- `_supervision_event_store()` 会避开类名以 `Job` 开头的 `_event_store`，未发现 job event store 污染；本轮问题是生产 tick 路径没有走到 writer。

### praise

- S1-S5 都有 RED/GREEN 证据，且本轮 scoped tests 覆盖 policy、redaction、probation/circuit、lifecycle start gate 与 pane_ref primitive。
- REV-006 的最终持久化边界比上一轮明确：`AgentRuntime.to_record()` 成为最后防线，`RuntimeService.attach()` explicit raw refs 也经过 normalization。

## 5. Test And QA Focus

- QA 必须重点复核：
  - 复核 `herdr_auto_restore_mode=disabled`、Herdr refs 和 token-presence evidence 是否能从真实 session payload/attach/refresh 路径进入 supervision。
  - `recovery_evidence_ledger` public payload 不含 raw namespace token；只暴露 `restore_token_present`。
  - Herdr `namespace-crashed` / `process-dead` / `daemon-unavailable` 的 recovery action 是否仍由 CCB supervision owner 决定。
  - backend-neutral pane rebound 是否不调用 tmux ownership/identity，同时保持 provider recovery block。
- Evidence pack residual risks / gate warnings：
  - S7 是 blocked evidence：Herdr binary exists, server `not_running`, capabilities null。
  - Global CMD-007/CMD-008 受既有 dirty 影响；implementation 使用 scoped guard。
- 建议新增或加强的测试：
  - 通过 `tick_jobs()` 构造 queued Herdr degraded `observe-only` runtime，断言写入 `recover_blocked` supervision event / `recovery_evidence_ledger`，并断言 `refresh_provider_binding(recover=True)` 未调用。
  - direct `AgentRuntime(...)` and `RuntimeService.attach(...)` raw refs never reach `to_record()`.
  - lifecycle-start blocked admission writes durable recovery evidence and does not refresh.
  - REV-003 nested details redaction remains covered.
- 不能靠 review 完全确认的点：真实 Herdr host recovery transcript、90 秒真实 wall-clock probation。

## 6. Residual Risk

- Bohr round 4 completed with one blocking finding (`R4-001`), so the current report cannot pass the review gate.
- REV-006 is independently confirmed closed for the specified namespace restore-token persistence boundary.
- REV-007 is not fully closed because direct helper coverage missed the production tick iterator path; superseded by `R4-001`.
- REV-003 is closed and REV-002/REV-004 were superseded by the more precise REV-006/REV-007/R4-001 findings.
- 当前 evidence 不能证明真实 Herdr recovery pass，只能证明 blocked/fail-closed。

## 7. Verdict

- Status: changes-requested
- Next: 回到 `cs-feat` implementation review-fix，仅修复 `R4-001`；修复后必须重新进入 `cs-code-review`。Goal lane 不得进入 QA。

## 8. Focused Closure

none
