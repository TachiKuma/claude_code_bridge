---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: windows-rmux-supportability-parity-contract
feature: 2026-07-26-windows-rmux-supportability-parity-contract
status: pending
---

# windows-rmux-supportability-parity-contract Goal Feature Spec

## 1. Identity

- Roadmap item: `windows-rmux-supportability-parity-contract`
- Feature dir: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract`
- Design: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-design.md`
- Checklist: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-checklist.yaml`
- Design review: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-design-review.md`
- Review output: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-review.md`
- QA output: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-qa.md`
- Acceptance output: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-acceptance.md`
- Depends on: `windows-rmux-wezterm-native-interaction-parity`, `windows-rmux-output-capture-parity`, `windows-rmux-pane-identity-layout-parity`, `windows-rmux-visual-no-popup-parity`, `windows-rmux-lifecycle-recovery-ux-parity`
- Feature kind: non-functional

## 2. Deliverable

聚合前 5 个 upstream UX dimensions 和 base packaging projection，输出 `rmux_supportability` doctor/docs/bundle seam 与 `parity_dimension=supportability` evidence。`support_tier` 是唯一对外 tier 字段。

## 3. Core Runtime Path

none；以 schema/projection/doctor/docs consistency evidence 替代用户运行路径。不得把 supportability 自身 evidence 当输入。

## 4. Mandatory Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-checklist.yaml" --yaml-only`
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"`
- `python -m pytest -q test/test_windows_rmux_supportability_parity_contract.py`
- `python -m pytest -q test/test_rmux_packaging_docs_contracts.py test/test_cli_doctor_rmux_packaging.py test/test_ccbd_diagnostics_bundle_rmux.py test/test_rmux_docs_consistency_gate.py`
- `python -m py_compile "scripts/windows_rmux_supportability_projection.py" "lib/terminal_runtime/rmux_packaging_support.py" "lib/cli/services/doctor.py" "lib/cli/render_runtime/ops_views_doctor.py"`
- `npm run pack:check`

## 5. Gates And Recovery

- Implementation gate: all five upstream UX dimension items must be `done`; checklist steps done; gates passed.
- Review gate: independent cs-code-review passed.
- QA gate: projection, doctor/docs consistency, missing/partial/blocked/failed rules and scope guard covered.
- Acceptance gate: supportability evidence JSON, support projection and roadmap writeback complete.
- Recovery: missing upstream evidence projects to missing and cannot be replaced by design-review Markdown; base packaging owner contract remains authoritative.

## 6. Evidence And Cleanliness

- Evidence required: support projection, supportability evidence, validator output, docs/doctor consistency evidence, scope diff review, validation commands.
- Cleanliness: do not modify release guard, npm publish, package win32, provider parser or upstream child evidence unless separately authorized.
