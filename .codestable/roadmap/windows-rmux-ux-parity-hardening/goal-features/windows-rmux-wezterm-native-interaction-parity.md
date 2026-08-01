---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: windows-rmux-wezterm-native-interaction-parity
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: pending
---

# windows-rmux-wezterm-native-interaction-parity Goal Feature Spec

## 1. Identity

- Roadmap item: `windows-rmux-wezterm-native-interaction-parity`
- Feature dir: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity`
- Design: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml`
- Design review: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design-review.md`
- Review output: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-review.md`
- QA output: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-qa.md`
- Acceptance output: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-acceptance.md`
- Depends on: none
- Feature kind: mixed

## 2. Deliverable

Windows/rmux 普通 pane 采用 GUI-native 交互：wheel / right-click / left-click passthrough 不被 copy-mode、paste-buffer 或裸 `send-keys -M` 劫持；sidebar mouse controls 继续全接管。

## 3. Core Runtime Path

Native Windows + WezTerm + rmux 前台交互 runbook；缺 GUI 或 rmux 时只能 partial/blocked，不能 full pass。

## 4. Mandatory Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml" --yaml-only`
- `python -m pytest -q test/test_v2_tmux_ui.py`
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" shifted_q_is_project_kill_across_terminal_key_encodings --quiet`
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --quiet`
- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"`
- `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings`

## 5. Gates And Recovery

- Implementation gate: checklist steps done, scope-gate, dod-runner and evidence-pack passed.
- Review gate: independent cs-code-review passed with no unresolved blocking findings.
- QA gate: cs-feat QA passed and covers unit, cargo, live binding snapshot and manual WezTerm runbook evidence.
- Acceptance gate: cs-feat acceptance passed via `approval-report.md#goal-acceptance`, checklist checks passed and roadmap item writeback complete.
- Recovery: interaction behavior regressions return to implementation then review/QA/acceptance; missing live evidence is QA evidence repair unless it changes the claimed support level.

## 6. Evidence And Cleanliness

- Evidence required: command output, `evidence/live-binding-snapshot.txt` or QA equivalent, `evidence/manual-wezterm-runbook.md` or QA equivalent, review, QA, acceptance, gate JSON, evidence pack.
- Cleanliness: no new interaction mode config, no production shell status hook, no same-name validation shim, no unexplained scope drift outside UI binding / sidebar regression surface.
