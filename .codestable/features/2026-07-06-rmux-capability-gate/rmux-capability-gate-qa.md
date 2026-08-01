---
doc_type: feature-qa
feature: 2026-07-06-rmux-capability-gate
status: passed
qa_state: passed
review_ref: .codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-review.md
latest_capability_report: .codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T094438Z-4728/capability-report.json
updated: 2026-07-20
---

# rmux-capability-gate QA 报告

## 1. Scope

- Design: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-design.md`
- Checklist: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml`
- Review: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-review.md`
- Evidence pack: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-evidence-pack.md`
- DoD results: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-dod-results.json`
- Latest capability report: `.codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T094438Z-4728/capability-report.json`

## 2. Verification Evidence

| ID | Result | Evidence |
|---|---|---|
| CMD-001 | passed | `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml" --yaml-only` |
| CMD-002 | passed | `python -m pytest -q test/test_rmux_capability_probe.py` -> 13 passed |
| CMD-003 | passed | `python "scripts/probe_rmux_capability.py" --work-root ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate"` -> `probe_status=completed`, `blocking_gaps=7` |
| CMD-004 | passed | `python -m pytest -q test/test_codex_pane_status_probe.py` -> 37 passed |

DoD runner was refreshed with `stage=acceptance`; machine result is `status=passed` with no blocking or warnings.

## 3. Capability Report QA

Latest report facts:

- `backend_impl=rmux`
- `version=rmux 0.8.0`
- `platform=windows`
- `probe_status=completed`
- command catalog count: 31
- semantic catalog count: 15
- artifact index count: 53
- daemon pre-state evidence exists at `artifacts/preflight/daemon-pre-state.json`; `detected=false`

The report preserves seven conservative blocking gaps. QA treats them as expected factual output for downstream `rmux-route-approval`, not as failure of this feature:

- command `attach-session`: required partial without accepted workaround; impact `core-lifecycle`
- command `refresh-client`: required partial without accepted workaround; impact `degradable-ui`
- command `kill-server`: required partial without accepted workaround; impact `diagnostic`
- semantic `attach_reattach`: required partial without accepted workaround; impact `core-lifecycle`
- semantic `capture_last_n_lines`: required partial without accepted workaround; impact `parser-fidelity`
- semantic `capture_format_fidelity_for_provider_completion`: required partial without accepted workaround; impact `parser-fidelity`
- semantic `ctrl_c_ctrl_d`: required partial without accepted workaround; impact `core-io`

## 4. Design Scenario Coverage

- AC-001 is covered by `test/test_rmux_capability_probe.py`.
- AC-002 through AC-004 are covered by the Windows probe report and artifacts.
- AC-005 is covered by fixture tests plus real Rmux capture fidelity artifacts; fixture and real artifacts remain distinct.
- AC-006 is covered by mechanical `blocking_gaps` generation in tests and latest report.
- AC-007 is covered by artifact index and redaction tests.
- AC-008 is covered by daemon pre-state and cleanup artifacts.

## 5. Review QA Focus

The passed review requires downstream route approval to consume the seven gaps conservatively. QA confirms the latest report still exposes those gaps with evidence, degrade impact and consequence, so no hidden pass-through to backend implementation exists.

## 6. Residual Risks

- `probe_status=completed` only means fact collection completed; it does not approve the Rmux route.
- `attach-session`, `refresh-client`, `kill-server`, `attach_reattach`, `capture_last_n_lines`, `capture_format_fidelity_for_provider_completion` and `ctrl_c_ctrl_d` remain route-approval inputs.
- No git commit was performed in this QA pass per current turn constraint.

## 7. Verdict

QA passed. Proceed to feature acceptance using `approval-report.md#goal-acceptance`, with the explicit constraint that the next feature must consume the seven blocking gaps instead of bypassing them.
