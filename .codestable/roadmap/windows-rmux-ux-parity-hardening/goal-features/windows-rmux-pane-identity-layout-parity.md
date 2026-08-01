---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: windows-rmux-pane-identity-layout-parity
feature: 2026-07-25-windows-rmux-pane-identity-layout-parity
status: pending
---

# windows-rmux-pane-identity-layout-parity Goal Feature Spec

## 1. Identity

- Roadmap item: `windows-rmux-pane-identity-layout-parity`
- Feature dir: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity`
- Design: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-checklist.yaml`
- Design review: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-design-review.md`
- Review output: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-review.md`
- QA output: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-qa.md`
- Acceptance output: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-acceptance.md`
- Depends on: `windows-rmux-wezterm-native-interaction-parity`
- Feature kind: mixed

## 2. Deliverable

收口 pane id/index canonicalization、layout 重建和 agent-pane binding 恢复 evidence；仅在证据证明 drift 时做最小实现修复。

## 3. Core Runtime Path

Pane identity snapshot、agent-pane binding recovery、identity conflict diagnostics；输出 `evidence/windows-rmux-ux-parity-evidence.json`，`parity_dimension=pane_identity_layout`。

## 4. Mandatory Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-checklist.yaml" --yaml-only`
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"`
- `python -m pytest -q test/test_windows_rmux_pane_identity_layout_parity.py`
- `python -m pytest -q test/test_v2_project_namespace_backend.py -k "canonicalizes_rmux_index_alias or prefers_exact_pane_id or respawn_adapter_canonicalizes"`
- `python -m pytest -q test/test_rmux_backend_core.py`
- `python -m py_compile "lib/terminal_runtime/rmux_backend_runtime/targets.py" "lib/terminal_runtime/rmux_backend_runtime/panes.py" "lib/ccbd/services/project_namespace_runtime/backend.py"`

## 5. Gates And Recovery

- Implementation gate: upstream interaction item must be `done`; checklist steps done; gates passed.
- Review gate: independent cs-code-review passed.
- QA gate: identity snapshot, binding recovery and conflict diagnostics evidence covered.
- Acceptance gate: checklist checks passed, UX evidence JSON exists, roadmap item done.
- Recovery: if drift is only evidenced in QA artifact, repair evidence first; if canonicalization behavior is broken, return to implementation and rerun review/QA.

## 6. Evidence And Cleanliness

- Evidence required: UX parity evidence JSON, pane identity report, command output, gate JSON, evidence pack.
- Cleanliness: do not preemptively refactor production canonicalization; no layout rewrite unless evidence proves current behavior broken.
