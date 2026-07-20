---
doc_type: feature-qa
feature: 2026-07-20-ccbd-control-plane-transport-seam
status: blocked
runner_state: completed
runner_reason: "QA runner blocked on environment-only evidence gaps: no AF_UNIX on current Windows host and CMD-005 fcntl baseline"
runner_id: "019f7f80-9299-75f2-8f45-f6c98e6aec6e"
tested: 2026-07-20
round: 1
---

# ccbd-control-plane-transport-seam QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml`
- Review: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-review.md`
- Evidence pack: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-scope-gate.json`
- DoD results: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-dod-results.json`
- Diff basis: current working tree diff; no staged diff.
- Baseline dirty files: none outside this feature scope.
- Feature type: mixed. It changes ccbd control-plane runtime seams and endpoint diagnostics, while intentionally avoiding RPC schema / handler dispatch changes.
- Core evidence gate: fake transport, endpoint projection, frame/client/server regression and import guard have runtime evidence. Real Unix AF_UNIX stale cleanup / bootstrap / deferred-connection evidence is blocked by current Windows host lacking AF_UNIX.

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | DoD CMD-001 | supporting | checklist YAML valid | schema | `python ".codestable/tools/validate-yaml.py" --file "...checklist.yaml" --yaml-only` | valid | pass |
| QA-002 | DoD CMD-002 | supporting | roadmap items YAML valid | schema | `python ".codestable/tools/validate-yaml.py" --file "...items.yaml"` | valid | pass |
| QA-003 | AC-001/004/006 | core-functional | endpoint descriptor, fake transport, lease/lifecycle/inspection/ping projection | unit | `python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_control_plane_transport_fake.py` | pass | pass |
| QA-004 | AC-003/005 | core-functional | bootstrap, server, client regression | unit/regression | `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_server.py test/test_ccbd_socket_client.py` | pass or platform skip only | pass with Windows skips |
| QA-005 | AC-002/003 | core-functional | real AF_UNIX lifecycle/bootstrap/stale cleanup | unit/regression | `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_lifecycle.py test/test_ccbd_socket_server_loop.py test/test_ccbd_socket_client.py` | Unix behavior exercised | blocked on Windows skips |
| QA-006 | AC-006 | supporting | start/ping/doctor endpoint projection sample | regression | `python -m pytest -q test/test_v2_start_service.py test/test_v2_phase2_entrypoint.py -k "ccbd or socket or endpoint or ping"` | pass or documented baseline | blocked by existing `fcntl` import baseline |
| QA-007 | AC-007/008 | core-functional | AF_UNIX boundary, no Windows TCP adapter, no RPC handler scope drift | guard | `python -m pytest -q test/test_ccbd_control_plane_transport_import_guard.py` | pass | pass |
| QA-008 | Cleanliness | supporting | compile, whitespace, debug marker hygiene | static | `python -m compileall ...`; `git diff --check`; scope gate | pass | pass |

## 3. Command Results

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml" --yaml-only` -> exit 0: valid.
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` -> exit 0: valid.
- `python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_control_plane_transport_fake.py test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_server.py test/test_ccbd_socket_client.py test/test_ccbd_control_plane_transport_import_guard.py` -> exit 0: `37 passed, 5 skipped`.
- `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_lifecycle.py test/test_ccbd_socket_server_loop.py test/test_ccbd_socket_client.py` -> exit 0: `42 passed, 15 skipped`.
- `python -m compileall -q ...` -> exit 0.
- `git diff --check` -> exit 0.
- `python -m pytest -q test/test_v2_start_service.py test/test_v2_phase2_entrypoint.py -k "ccbd or socket or endpoint or ping"` -> exit 1 / runner raw exit 2: collection blocked by `mobile_gateway.terminal -> import fcntl`, recorded as existing Windows baseline in DoD.
- `wsl --status` / `wsl pwd` -> no usable WSL distribution available on this host; cannot supplement Unix AF_UNIX evidence locally.

## 4. Scenario Results

- [x] QA-001 checklist YAML: pass.
  - Evidence: validation command exit 0.
- [x] QA-002 roadmap items YAML: pass.
  - Evidence: validation command exit 0.
- [x] QA-003 endpoint/fake/projection behavior: pass.
  - Evidence: targeted tests cover canonical endpoint records, legacy `socket_path` fallback, lifecycle/lease/ping projection, fake bootstrap nonce, fake closed/connectability and recv EOF.
- [x] QA-004 bootstrap/server/client regression on available host: pass.
  - Evidence: targeted test command exit 0; Windows platform skips real AF_UNIX-only cases.
- [ ] QA-005 real AF_UNIX behavior: blocked.
  - Evidence: current host lacks AF_UNIX; relevant tests skip. This is an environment evidence gap, not a code failure observed in this feature.
- [ ] QA-006 v2 start/ping/doctor sample: blocked.
  - Evidence: collection fails before feature code path due existing `mobile_gateway.terminal` importing `fcntl` on Windows.
- [x] QA-007 guard/scope: pass.
  - Evidence: import guard passed; scope gate passed; no Windows TCP adapter or RPC schema/handler dispatch changes.
- [x] QA-008 cleanliness: pass.
  - Evidence: compileall, `git diff --check`, and scope gate passed.

## 5. Findings

### failed

- none

### blocked

- [ ] QA-BLOCK-001 Real Unix AF_UNIX control-plane behavior cannot be executed on this Windows host.
  - Evidence: AF_UNIX tests skip; no usable WSL distribution is available.
  - Impact: QA cannot fully prove Unix stale cleanup, real bootstrap readiness, deferred external connection, and overflow close behavior.
- [ ] QA-BLOCK-002 v2 start/ping/doctor sample cannot collect on this Windows host.
  - Evidence: `mobile_gateway.terminal -> import fcntl` collection error.
  - Impact: full start/ping/doctor endpoint projection sample remains environment-blocked; direct projection tests and focused ccbd tests still pass.

### residual-risk

- Unix CI or a Unix-capable host must rerun real AF_UNIX bootstrap/lifecycle/stale-cleanup tests before treating this feature as fully QA passed.
- Existing Windows `fcntl` collection baseline must be resolved or accepted by owner before using CMD-005 as full endpoint diagnostics evidence.

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass by compileall and focused tests
- Out-of-scope files: pass by scope gate

## 7. Verdict

- Status: blocked
- Next: provide Unix/WSL/CI evidence for real AF_UNIX behavior, or owner must explicitly decide whether this environment-only evidence gap is acceptable for the roadmap goal before rerunning `cs-feat` QA.
