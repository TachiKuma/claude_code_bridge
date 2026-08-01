---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: windows-rmux-visual-no-popup-parity
feature: 2026-07-25-windows-rmux-visual-no-popup-parity
status: pending
---

# windows-rmux-visual-no-popup-parity Goal Feature Spec

## 1. Identity

- Roadmap item: `windows-rmux-visual-no-popup-parity`
- Feature dir: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity`
- Design: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-checklist.yaml`
- Design review: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-design-review.md`
- Review output: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-review.md`
- QA output: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-qa.md`
- Acceptance output: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-acceptance.md`
- Depends on: `windows-rmux-wezterm-native-interaction-parity`
- Feature kind: mixed

## 2. Deliverable

恢复或替代动态状态栏、边框、标题，同时保证 Windows/rmux 不产生 Git Bash 或 console popup；输出 `parity_dimension=visual_no_popup` 的 UX evidence。

## 3. Core Runtime Path

Static command audit + no-popup probe + native Windows/WezTerm live/manual evidence。动态项没有 no-popup pass artifact 时必须保持 disabled 并记录 reason。

## 4. Mandatory Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-checklist.yaml" --yaml-only`
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"`
- `python -m pytest -q test/test_windows_rmux_visual_no_popup_parity.py`
- `python -m pytest -q test/test_v2_tmux_ui.py -k "windows_rmux_project_ui_avoids_shell_status_commands or set_tmux_ui_active or ccb_tmux_on or rmux_accepts_mouse_context_project_ui_bindings"`
- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "lib/cli/services/tmux_ui_runtime/activation.py" "test/test_v2_tmux_ui.py"`
- `python -m pytest -q test/test_rmux_packaging_docs_contracts.py test/test_cli_doctor_rmux_packaging.py`

## 5. Gates And Recovery

- Implementation gate: upstream interaction item must be `done`; checklist steps done; gates passed.
- Review gate: independent cs-code-review passed.
- QA gate: static command audit, no-popup probe and dynamic disabled/enabled decisions covered.
- Acceptance gate: UX evidence JSON and roadmap item writeback complete.
- Recovery: popup evidence failures return to implementation; missing GUI evidence cannot be converted to full pass.

## 6. Evidence And Cleanliness

- Evidence required: `ux_parity_evidence_json`, no-popup probe report, static command audit, command output, review, QA, acceptance.
- Cleanliness: no support tier/npm/install gate changes; no hidden shell hook restore without probe evidence.
