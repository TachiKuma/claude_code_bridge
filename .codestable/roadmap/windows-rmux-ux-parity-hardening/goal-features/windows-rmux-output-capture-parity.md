---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: windows-rmux-output-capture-parity
feature: 2026-07-25-windows-rmux-output-capture-parity
status: pending
---

# windows-rmux-output-capture-parity Goal Feature Spec

## 1. Identity

- Roadmap item: `windows-rmux-output-capture-parity`
- Feature dir: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity`
- Design: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-checklist.yaml`
- Design review: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-design-review.md`
- Review output: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-review.md`
- QA output: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-qa.md`
- Acceptance output: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-acceptance.md`
- Depends on: `windows-rmux-wezterm-native-interaction-parity`
- Feature kind: mixed

## 2. Deliverable

建立 output/capture parity evidence：machine capture、provider completion、user-visible history 三条 lane 各自可验证，并输出 `evidence/windows-rmux-ux-parity-evidence.json`，`parity_dimension=output_capture`。

## 3. Core Runtime Path

Rmux capture fixtures、provider completion golden fixtures、native Windows + WezTerm user-visible history runbook；用户滚轮不是 capture 证据。

## 4. Mandatory Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-checklist.yaml" --yaml-only`
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"`
- `python -m pytest -q test/test_windows_rmux_output_capture_parity_evidence.py`
- `python -m pytest -q test/test_rmux_send_capture_logging.py`
- `python -m pytest -q test/test_rmux_completion_capture_fixtures.py`
- `python -m py_compile "lib/terminal_runtime/rmux_backend.py" "lib/terminal_runtime/rmux_backend_runtime/io.py"`
- `python -m pytest -q test/test_rmux_send_capture_logging_import_guard.py`

## 5. Gates And Recovery

- Implementation gate: upstream interaction item must be `done`; checklist steps done; scope/dod/evidence gates passed.
- Review gate: independent cs-code-review passed.
- QA gate: capture/provider/history lanes all covered; GUI unavailable can only produce partial/blocked status.
- Acceptance gate: UX evidence JSON and roadmap item writeback complete.
- Recovery: provider auth/quota failure is classified separately and does not contaminate rmux lane; capture defects return to implementation.

## 6. Evidence And Cleanliness

- Evidence required: `evidence/windows-rmux-ux-parity-evidence.json`, capture parity report, provider completion artifacts, manual/history evidence or explicit blocked reason, command output.
- Cleanliness: no default rewrite of Rmux IO; no replacing machine evidence with Markdown-only summary.
