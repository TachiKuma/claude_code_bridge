---
doc_type: feature-qa
feature: 2026-07-31-herdr-bounded-recovery-boundary
status: passed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-08-03
round: 1
---

# herdr-bounded-recovery-boundary QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-checklist.yaml`
- Review: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-review.md`
- Evidence pack: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/evidence/native-windows-x64-herdr-recovery-blocked-evidence.md`
- Gate results: none
- DoD results: implementation report verification sections
- Diff basis: current workspace diff scoped to this feature
- Baseline dirty files: none outside this feature diff
- Feature type: mixed, with core runtime behavior evidence required.
- Core evidence gate: Herdr recovery owner/policy/redaction/probation/circuit/routing and tmux/rmux regression must have running tests; real Native Windows Herdr recovery remains blocked evidence because Herdr server/capability is unavailable.

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | CMD-001 | supporting | checklist YAML 合法 | schema | `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-checklist.yaml" --yaml-only` | exit 0 | pass |
| QA-002 | CMD-002 | supporting | roadmap items YAML 合法 | schema | `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` | exit 0 | pass |
| QA-003 | CMD-003 | core-functional | provider-runtime-on-herdr 已 accepted | artifact | admission Python one-liner | no missing artifacts | pass |
| QA-004 | CMD-005 / review | core-functional | Herdr owner/policy/redaction/probation/circuit/tick blocked evidence | unit | `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" --basetemp "D:/tmp/ccb-herdr-qa-herdr" -p no:cacheprovider` | all pass | pass |
| QA-005 | CMD-004 | core-functional | recovery/restore/crash regression | unit | `python -m pytest -q "test/test_v2_ccbd_supervision_loop.py" "test/test_ccbd_restore_helpers.py" "test/test_pane_crash_reason.py" -k "recovery or recover or crash or backoff or blocked" --basetemp "D:/tmp/ccb-herdr-qa-recovery-regression" -p no:cacheprovider` | all selected pass | pass |
| QA-006 | CMD-006 | core-functional | runtime refresh/rebind recovery path | unit | `python -m pytest -q "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_health_monitor_rebind.py" -k "recovery or recover or herdr or restored or blocked" --basetemp "D:/tmp/ccb-herdr-qa-refresh" -p no:cacheprovider` | all selected pass | pass |
| QA-007 | CMD-007 | core | forbidden scope guard | static | scope/content Python guard | no forbidden files/content | pass |
| QA-008 | CMD-008 | core | probation/circuit presence and raw restore token public leakage guard | static | raw-token/probation Python guard | assertions pass | pass |
| QA-009 | CMD-009 / S7 | core evidence | Native Windows x64 Herdr recovery transcript or blocked evidence | manual/artifact | read `evidence/native-windows-x64-herdr-recovery-blocked-evidence.md` | blocked evidence acceptable; no supported claim | pass |
| QA-010 | review residual risk | core boundary | R4-001 production tick path and idempotence | unit/review | review report + focused test | no blocking; second tick no duplicate event | pass |
| QA-011 | cleanliness | supporting | no debug/TODO/out-of-scope | diff/static | `git diff --check`, scoped `rg` | no errors/matches | pass |

## 3. Command Results

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-checklist.yaml" --yaml-only` -> exit 0: 1 passed.
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` -> exit 0: 1 passed.
- Admission one-liner for `provider-runtime-on-herdr` -> exit 0.
- `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" --basetemp "D:/tmp/ccb-herdr-qa-herdr" -p no:cacheprovider` -> exit 0: 28 passed.
- `python -m pytest -q "test/test_v2_ccbd_supervision_loop.py" "test/test_ccbd_restore_helpers.py" "test/test_pane_crash_reason.py" -k "recovery or recover or crash or backoff or blocked" --basetemp "D:/tmp/ccb-herdr-qa-recovery-regression" -p no:cacheprovider` -> exit 0: 20 passed, 24 deselected.
- `python -m pytest -q "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_health_monitor_rebind.py" -k "recovery or recover or herdr or restored or blocked" --basetemp "D:/tmp/ccb-herdr-qa-refresh" -p no:cacheprovider` -> exit 0: 3 passed, 3 deselected.
- CMD-007 scope/content guard -> exit 0.
- CMD-008 probation/circuit/raw-token guard -> exit 0.
- `git diff --check` scoped files -> exit 0, with LF/CRLF warnings only for CodeStable markdown reports.
- Scoped `rg` for `console.log|console.error|TODO|FIXME|XXX` -> exit 1, no matches.

## 4. Scenario Results

- [x] QA-001 provider runtime admission: pass.
  - Evidence: `provider-runtime-on-herdr` item is `done`, acceptance artifact exists and contains artifact/evidence references.
- [x] QA-002 Herdr recovery policy / owner / auto restore gate: pass.
  - Evidence: Herdr focused tests pass and include non-disabled auto-restore blocked cases.
- [x] QA-003 evidence ledger redaction: pass.
  - Evidence: focused tests and CMD-008 prove raw restore token is not emitted in public payload.
- [x] QA-004 probation/circuit/backoff: pass.
  - Evidence: focused tests cover 90s policy constants, Herdr circuit threshold, and no duplicate blocked evidence on repeated tick.
- [x] QA-005 lifecycle-start production tick path: pass.
  - Evidence: `test_lifecycle_start_tick_records_blocked_herdr_recovery_evidence` covers `tick_jobs()`, no refresh call, `recover_blocked`, and idempotence.
- [x] QA-006 tmux/rmux regression: pass.
  - Evidence: recovery/restore/crash regression command passed.
- [x] QA-007 Native Windows Herdr real recovery: pass as blocked evidence only.
  - Evidence: Herdr binary exists but target server is `not_running`, `capabilities=null`; this does not prove supported recovery and remains a downstream residual risk.

## 5. Findings

### failed

none.

### blocked

none for this QA gate. Real Herdr recovery pass is unavailable, but the design explicitly allows auto-restore-not-proven blocked evidence for S7 and forbids claiming support.

### residual-risk

- `REV-005` remains: no real production producer for `herdr_auto_restore_mode=disabled` is proven in this feature. This is not blocking because current behavior fail-closes and S7 records blocked evidence, but acceptance must not claim real Herdr recovery supported.
- Real 90-second wall-clock probation on a live Herdr recovery was not observed due Herdr server/capability unavailability; unit evidence covers the policy/state-machine side.

## 6. Cleanliness

- Debug output: pass.
- Temporary TODO/FIXME/XXX: pass.
- Commented-out code: pass by diff review.
- Unused imports / dead code from this feature: pass by targeted tests.
- Out-of-scope files: pass.

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段。
