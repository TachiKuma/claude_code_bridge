---
doc_type: feature-review
feature: 2026-07-19-backend-resolver-opt-in-contract
status: passed
reviewer: subagent
reviewed: 2026-07-22
round: 2
lane_a_state: completed
lane_a_ref: "multi_agent_v1:019f88b7-7e5e-7b40-86f4-96f41b3bd281"
lane_a_reason: "Round 2 full rereview passed; prior blocking findings from Task agent 019f88ad-0ce2-7451-843d-9057b5175e24 were verified closed."
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "OCR lane was not used for final gate; earlier OCR attempt hung without usable output. Gate release relies on completed independent Task-agent reviewer."
---

# backend-resolver-opt-in-contract 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-design.md`
- Checklist: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-dod-results.json`
- Implementation evidence: implementation gates show `scope-gate`, `dod-runner`, `dod-contract-gate` and `evidence-pack` passed after the review-fix.
- Diff basis: current workspace diff for this goal feature; dirty scope is covered by the refreshed scope gate.
- Review mode: full-rereview
- Baseline dirty files: none classified as unrelated for this feature review; CodeStable state/docs and implementation files are in the current allowed scope.

### Independent Review

- Detection: current host Task-agent API is available through `multi_agent_v1`.
- 环节 A 独立隔离 Task agent: independent-agent + completed
- 环节 A round 1: `019f88ad-0ce2-7451-843d-9057b5175e24` returned `changes-requested` with two blocking findings.
- 环节 A round 2: `019f88b7-7e5e-7b40-86f4-96f41b3bd281` verified both blocking findings closed and returned `passed`.
- QA-fix narrow review: `019f88bf-7a8c-75f3-8310-f4ceb459acb6` accepted the shared helper direction but requested broader tests for `socket_placement_payload()` consumers; focused closure added helper and startup report coverage.
- 环节 B OCR CLI: skipped for the final gate; earlier OCR attempt produced no usable output and was not used as a substitute for Lane A.
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded.
- Merge policy: subagent findings were locally fact-checked against code, tests and refreshed gate artifacts before writing verdict.
- Gate effect: `reviewer: subagent` satisfies the required independent review gate; goal feature may proceed to QA.

## 2. Diff Summary

- 新增：`lib/agents/config_loader_runtime/parsing_runtime/runtime_mux.py`, `lib/cli/services/backend_selection_diagnostics.py`, `lib/terminal_runtime/backend_resolver.py`, `test/test_backend_selection_diagnostics.py`, implementation gate artifacts and review packet.
- 修改：config loader/model/runtime files, terminal runtime selection/API files, ccbd service graph/reload/ping/startup diagnostics, doctor/ping/start foreground surfaces, resolver/config tests, feature checklist/design, CodeStable goal state/reference artifacts.
- 删除：none observed.
- 未跟踪 / staged：untracked files are part of this feature's implementation/gate artifacts; nothing staged.
- 风险热点：config schema, terminal runtime backend selection, CLI diagnostics, reload propagation, legacy tmux compatibility.

## 3. Adversarial Pass

- 假设的生产 bug：backend resolver cache or route summary parsing silently bypasses explicit `rmux` fail-fast.
- 主动攻击过的反例：先缓存 tmux 再 explicit `rmux` 缺 approval；当前 report 有 gap 但 superseded history 有 zero gap；invalid env；project/user/env priority；auto fallback reason；old tmux session payload.
- 结果：round 1 的两个 blocking 已由 targeted fixes and regression tests closed；round 2 independent reviewer found no blocking.

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] REV-003 `lib/terminal_runtime/backend_selection.py` selection cache key does not include route/capability reader result freshness.
  - Evidence: round 2 reviewer noted the key includes request/config/env/platform/project_root, not mutable route/capability contents.
  - Impact: not a current blocker because this feature treats the selection object as request-scoped; future runtime route revocation/refresh would need explicit cache invalidation.
  - Expected fix scope: defer until route approval becomes mutable at runtime.

### learning

- Explicit `rmux` must resolve before backend instance cache reuse; backend cache cannot be the policy source of truth.
- Capability summary parsing must consume structured current facts, not grep across historical blocks.
- Evidence pack freshness is part of the QA/acceptance boundary, not just review bookkeeping.

### praise

- Resolver tests cover tmux default, project/user/env priority, explicit rmux fail-fast, auto fallback, approved rmux factory selection and old tmux session compatibility.
- Diagnostics surfaces keep legacy tmux fields while adding requested/effective/source/fallback/failure summaries.

## 5. Test And QA Focus

- QA 必须重点复核：`runtime.mux.backend` priority, explicit `rmux` fail-fast after tmux cache, `auto` fallback diagnostics, structured route/capability summary parsing, old tmux session compatibility, doctor/ping/start foreground summaries, reload propagation.
- Evidence pack residual risks / gate warnings：refreshed evidence pack has no blocking or warning entries; provider signals are skipped.
- 建议新增或加强的测试：future runtime route revocation/cache invalidation if route approval becomes mutable during a process lifetime.
- 不能靠 review 完全确认的点：live Windows rmux/foreground smoke and running daemon reload timing remain QA responsibilities.

## 6. Residual Risk

- CodeGraph is not initialized in this workspace; review used direct file/diff inspection and independent Task-agent rereview.
- OCR lane was not used for final gate because the earlier OCR path produced no usable output; completed Task-agent review is the gate evidence.
- Full repository test suite and live rmux smoke were not run in review; QA should decide whether to broaden beyond the core DoD commands.

## 7. Verdict

- Status: passed
- Next: Goal feature lane may enter QA.

## 8. Focused Closure

- Closed findings: QA-fix review finding from Task agent `019f88bf-7a8c-75f3-8310-f4ceb459acb6` about insufficient shared helper coverage.
- Attributed delta: `test/test_v2_storage_paths.py` adds direct `socket_placement_payload()` POSIX text coverage; `test/test_v2_ccbd_start_flow.py` updates startup report assertions to the same `as_posix()` diagnostic contract.
- Targeted verification: `python -m pytest -q test/test_v2_storage_paths.py::test_socket_placement_payload_uses_posix_path_text` -> 1 passed; `python -m pytest -q test/test_v2_ccbd_start_flow.py::test_runtime_supervisor_start_persists_startup_report` -> 1 passed.
- Classification: test-only closure after an independent QA-fix review; it does not change production behavior, public runtime policy, security, data, concurrency or architecture.
