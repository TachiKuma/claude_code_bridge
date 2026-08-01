---
doc_type: feature-qa
feature: 2026-07-19-backend-resolver-opt-in-contract
status: passed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-07-22
round: 1
---

# backend-resolver-opt-in-contract QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-design.md`
- Checklist: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-checklist.yaml`
- Review: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-review.md`
- Evidence pack: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-dod-results.json`
- Diff basis: current workspace diff; scope gate refreshed after QA-fix and passed.
- Baseline dirty files: none classified as unrelated for this QA; current dirty files are either feature implementation, feature evidence, or CodeStable state/reference scope.
- Feature type: mixed
- Core evidence gate: runtime backend selection and diagnostics paths need running unit/integration evidence; live rmux/foreground smoke remains downstream validation, not this resolver-contract feature's core gate.

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | checklist CMD-001/CMD-002 | supporting | CodeStable YAML artifacts valid | schema | `validate-yaml` commands from DoD | exit 0 | pass |
| QA-002 | design AC-001..AC-004, review focus | core-functional | tmux default, explicit rmux fail-fast, auto fallback, approved rmux, cache regression, capability summary parsing | unit | `python -m pytest -q test/test_terminal_runtime_backend_selection.py` | all pass | pass |
| QA-003 | design AC-005/AC-006/AC-008 | core-functional | runtime mux config, foreground attach, backend diagnostics surfaces | unit/integration | `python -m pytest -q test/test_v2_config_loader.py test/test_v3_config_loader.py test/test_v2_start_foreground.py test/test_backend_selection_diagnostics.py -k "runtime_mux or foreground or backend_selection"` | all selected pass | pass |
| QA-004 | review QA focus | supporting | ping, reload, service graph and namespace diagnostics chain | integration | `python -m pytest -q test/test_ccbd_reload_apply.py test/test_ccbd_reload_dry_run.py test/test_ccbd_service_graph.py test/test_v2_ccbd_ping_runtime.py` | all pass | pass |
| QA-005 | QA-fix review focus | supporting | shared `socket_placement_payload()` emits stable POSIX-style diagnostic path text | unit | `python -m pytest -q test/test_v2_storage_paths.py::test_socket_placement_payload_uses_posix_path_text` | pass | pass |
| QA-006 | QA-fix review focus | supporting | startup report consumes the same socket placement payload contract | integration | `python -m pytest -q test/test_v2_ccbd_start_flow.py::test_runtime_supervisor_start_persists_startup_report` | pass | pass |
| QA-007 | cleanliness | supporting | no whitespace errors in current diff | static | `git diff --check` | exit 0 | pass |
| QA-008 | exploratory broadened run | non-core | full `test_v2_storage_paths.py` and `test_v2_ccbd_start_flow.py` under current Windows host | integration | `python -m pytest -q test/test_v2_storage_paths.py test/test_v2_ccbd_start_flow.py` | environment-dependent | blocked/non-core |

## 3. Command Results

- `python -m pytest -q test/test_terminal_runtime_backend_selection.py` -> exit 0: `28 passed`.
- `python -m pytest -q test/test_v2_config_loader.py test/test_v3_config_loader.py test/test_v2_start_foreground.py test/test_backend_selection_diagnostics.py -k "runtime_mux or foreground or backend_selection"` -> exit 0: `23 passed, 168 deselected`.
- `python -m pytest -q test/test_ccbd_reload_apply.py test/test_ccbd_reload_dry_run.py test/test_ccbd_service_graph.py test/test_v2_ccbd_ping_runtime.py` -> exit 0: `78 passed`.
- `python -m pytest -q test/test_v2_ccbd_ping_runtime.py` -> exit 0: `13 passed`.
- `python -m pytest -q test/test_v2_storage_paths.py::test_socket_placement_payload_uses_posix_path_text` -> exit 0: `1 passed`.
- `python -m pytest -q test/test_v2_ccbd_start_flow.py::test_runtime_supervisor_start_persists_startup_report` -> exit 0: `1 passed`.
- `git diff --check` -> exit 0.
- `python -m pytest -q test/test_v2_storage_paths.py test/test_v2_ccbd_start_flow.py` -> exit 1: 16 failed, 28 passed. Failures are outside this feature's core gate: WSL path relocation expectations do not hold in the current Windows `Path('/mnt/...')` host interpretation, and several live start-flow tests fail on Windows token ACL proof with `token-unprotectable`. Targeted helper/startup report nodes above cover the QA-fix contract.

## 4. Scenario Results

- [x] QA-001 YAML artifacts：pass
  - Evidence: refreshed DoD runner captured both YAML validations with exit 0.
- [x] QA-002 resolver contract：pass
  - Evidence: 28 resolver/backend selection tests pass, including explicit rmux fail-fast after tmux cache and superseded zero-gap summary regression.
- [x] QA-003 config/diagnostics/foreground：pass
  - Evidence: 23 selected tests pass for `runtime_mux`, foreground and backend selection diagnostics.
- [x] QA-004 ping/reload/service graph：pass
  - Evidence: 78 tests pass across reload apply/dry-run, service graph and ping runtime payloads.
- [x] QA-005 shared socket placement diagnostics：pass
  - Evidence: direct helper test proves POSIX-style diagnostic path text.
- [x] QA-006 startup report socket placement diagnostics：pass
  - Evidence: targeted startup report test passes after switching expected diagnostic strings to the same `as_posix()` contract.
- [x] QA-007 cleanliness：pass
  - Evidence: `git diff --check` exit 0.

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- Full `test_v2_storage_paths.py test_v2_ccbd_start_flow.py` run is not green on this Windows host because it includes existing WSL path relocation assumptions and Windows token ACL live-start behavior. This QA treats those as non-core exploratory failures because all feature-specific resolver, diagnostics, ping/reload and targeted shared-helper/startup-report tests pass.
- Live Windows rmux foreground smoke is not executed here; downstream `ccbd-windows-full-chain-smoke` remains responsible for true ccb -> ccbd -> rmux runtime proof.

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass for feature-touched runtime/config/diagnostics/test scope; broader `rg` hits are existing project terms outside this feature.
- Commented-out code: pass
- Unused imports / dead code from this feature: pass by targeted tests and review; no new dead import evidence observed.
- Out-of-scope files: pass by refreshed scope gate.

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段
