---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: windows-rmux-lifecycle-recovery-ux-parity
feature: 2026-07-26-windows-rmux-lifecycle-recovery-ux-parity
status: pending
---

# windows-rmux-lifecycle-recovery-ux-parity Goal Feature Spec

## 1. Identity

- Roadmap item: `windows-rmux-lifecycle-recovery-ux-parity`
- Feature dir: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity`
- Design: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-design.md`
- Checklist: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-checklist.yaml`
- Design review: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-design-review.md`
- Review output: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-review.md`
- QA output: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-qa.md`
- Acceptance output: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-acceptance.md`
- Depends on: `windows-rmux-pane-identity-layout-parity`, `windows-rmux-output-capture-parity`
- Feature kind: mixed

## 2. Deliverable

建立 lifecycle UX report，覆盖 `reattach`、`terminal_closed`、`kill_cleanup`、`pane_crash`、`provider_crash`、`rmux_daemon_crash`，并输出 `parity_dimension=lifecycle_recovery` 的 UX evidence。

## 3. Core Runtime Path

Native Windows + WezTerm + rmux lifecycle transcript、full-chain cleanup evidence、supervision/diagnostics artifacts。缺 live evidence 时只能 partial/blocked。

## 4. Mandatory Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-checklist.yaml" --yaml-only`
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"`
- `python -m pytest -q test/test_windows_rmux_lifecycle_recovery_ux_parity.py`
- `python -m pytest -q test/test_rmux_windows_validation_matrix.py`
- `python -m pytest -q test/test_ccbd_rmux_supervision_recovery.py test/test_ccbd_rmux_supervision_evidence.py test/test_ccbd_diagnostics_bundle_supervision.py`
- `python -m py_compile "scripts/rmux_windows_validation_matrix.py" "lib/ccbd/supervision/store.py" "lib/ccbd/supervision/recovery_events.py"`

## 5. Gates And Recovery

- Implementation gate: pane identity/layout and output/capture items must be `done`; checklist steps done; gates passed.
- Review gate: independent cs-code-review passed.
- QA gate: lifecycle report scenarios, cleanup residue, diagnostics refs and parent readiness covered.
- Acceptance gate: `lifecycle-recovery-ux-report.json`, UX evidence JSON and roadmap writeback complete.
- Recovery: broken production recovery returns to implementation; missing transcript or diagnostics ref is stage evidence repair unless it changes verdict.

## 6. Evidence And Cleanliness

- Evidence required: `lifecycle-recovery-ux-report.json`, `windows-rmux-ux-parity-evidence.json`, runbook/manual transcript, parent readiness evidence, command output.
- Cleanliness: no default rewrite of supervision/recovery底层；no supportability/install/docs changes.
