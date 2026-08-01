---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: sidebar-settings-rmux-mouse-routing
feature: 2026-07-27-sidebar-settings-rmux-mouse-routing
status: in-progress
---

# sidebar-settings-rmux-mouse-routing Goal Feature Spec

## 1. Identity

- Roadmap item: `sidebar-settings-rmux-mouse-routing`
- Split parent: `sidebar-settings-click-e2e`
- Feature dir: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing`
- Brainstorm: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-brainstorm.md`
- Design: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-design.md`
- Checklist: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml`
- Design review: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-design-review.md`
- Review output: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-review.md`
- QA output: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-qa.md`
- Acceptance output: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-acceptance.md`
- Depends on: `sidebar-settings-click-e2e`
- Feature kind: capability-research-fix

## 2. Deliverable

在不改变 sidebar `x` KillProject、普通 sidebar click、普通 pane drag/right/wheel 行为的前提下，给 sidebar settings 前台点击找到 settings-only 通道；如果 rmux/WezTerm 当前能力不支持，则产出可复现 capability evidence，并把 supportability 投影为 `unsupported_capability`。

## 3. Core Runtime Path

Baseline blocked path:

`WezTerm mouse -> rmux root binding -> @ccb_role=sidebar branch -> send-keys -t = -M -> no crossterm Event::Mouse`

Known facts from parent:

- rmux root binding receives real foreground click.
- rmux resolves target pane and role.
- rmux did not populate `mouse_x` / `mouse_y` in the probe.
- `send-keys -M` did not reach Rust/crossterm.
- Direct `send-keys -t %0 c` opens config UI, but broad sidebar-left-click fallback is rejected.

## 4. Mandatory Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"`
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml" --yaml-only`
- `python -m pytest -q -rs test/test_v2_tmux_ui.py`
- `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml --quiet`
- Any new rmux/WezTerm capability probe tests introduced by the design.
- UX evidence JSON validator for `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/windows-rmux-ux-parity-evidence.json`.

## 5. Gates And Recovery

- Brainstorm gate: required; parent blocked evidence is input but does not replace this feature's brainstorm.
- Design gate: design must explicitly choose one of:
  - settings-only implementation path that does not affect KillProject or ordinary sidebar clicks;
  - capability-research-only path that proves unsupported capability and updates supportability evidence.
- Implementation gate: no broad fallback; ordinary pane and KillProject behavior must remain unchanged.
- Review gate: independent cs-code-review passed.
- QA gate: native Windows + WezTerm + rmux foreground transcript is required for any pass; blocked evidence must include exact rmux/WezTerm capability details.
- Acceptance gate: UX parity JSON can be `pass` only if settings-only click is restored without scope drift.

## 6. Evidence And Cleanliness

- Evidence required: parent blocked transcript, rmux list-keys/display-message coordinate probe, `send-keys -M` passthrough probe, candidate channel proof, final foreground transcript, UX parity JSON.
- Cleanliness: no fallback that maps all sidebar left-clicks to settings; no changes to ordinary pane drag/right/wheel; no token leakage in probe evidence.
