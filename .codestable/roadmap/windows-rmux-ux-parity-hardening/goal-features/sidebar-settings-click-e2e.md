---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: sidebar-settings-click-e2e
feature: 2026-07-27-sidebar-settings-click-e2e
status: blocked
---

# sidebar-settings-click-e2e Goal Feature Spec

## 1. Identity

- Roadmap item: `sidebar-settings-click-e2e`
- Split parent: `windows-rmux-wezterm-native-interaction-parity`
- Feature dir: `.codestable/features/2026-07-27-sidebar-settings-click-e2e`
- Design: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-design.md`
- Checklist: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-checklist.yaml`
- Design review: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-design-review.md`
- Review output: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-review.md`
- QA output: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-qa.md`
- Acceptance output: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-acceptance.md`
- Depends on: none
- Feature kind: diagnostic-fix

## 2. Deliverable

Native Windows + WezTerm + rmux 前台点击 sidebar header settings 后，真实 sidebar pane 能观察到 mouse event，并触发 config UI ready 或显示明确失败状态。

## 3. Core Runtime Path

`WezTerm mouse -> rmux root binding -> @ccb_role=sidebar branch -> send-keys -M -> crossterm Event::Mouse -> header_action_at -> open_config_ui`

## 4. Mandatory Commands

本节继承 `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-checklist.yaml` 的 `dod.commands`；下列命令是 goal driver 必须执行的摘要，不能弱化 checklist。

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-checklist.yaml" --yaml-only`
- `python -m pytest -q -rs test/test_v2_tmux_ui.py`
- `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings`
- `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml --quiet`
- `python -m py_compile lib/cli/services/tmux_ui_runtime/service.py test/test_v2_tmux_ui.py`
- checklist CMD-005：校验 `.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/windows-rmux-ux-parity-evidence.json` 的 required fields、artifact refs、non-pass failure detail/residual，以及 `blocked|failed` 时 `failure_class != none`。
- checklist CMD-006：运行 `codestable-workflow-next.py feature --feature ".codestable/features/2026-07-27-sidebar-settings-click-e2e" --epic-child-batch --json`，确认 split child 可恢复且无 owner mismatch。

## 5. Gates And Recovery

- Design gate: design review passed 后回到 epic batch loop，不单独要求用户确认。
- Implementation gate: checklist steps done，且 opt-in probe 默认关闭、有界输出。
- Review gate: independent cs-code-review passed with no unresolved blocking findings.
- QA gate: native Windows + WezTerm + rmux foreground transcript 与 UX parity JSON 均存在；headless 自动化不能替代 core foreground evidence。
- Acceptance gate: settings click 证据写入 `evidence/windows-rmux-ux-parity-evidence.json`，并能投影到 supportability。
- Recovery: event 未到达 Rust 时回 rmux binding / pane identity；event 到达但无 action 时回 Rust hit-test；action 到达但 config UI 失败时回 launch diagnostics。

## 6. Evidence And Cleanliness

- Evidence required: pane identity/helper fingerprint、root mouse binding、opt-in mouse event/action probe、manual foreground transcript、UX parity JSON、review、QA、acceptance。
- Cleanliness: no default debug noise, no temporary TODO/FIXME/XXX, no scope drift into KillProject or ordinary pane drag/right/wheel.

## 7. Blocked Outcome

2026-07-27 真实 Windows + WezTerm + rmux 前台复测确认：

- sidebar helper identity 和 launch args 已可核验；
- rmux root mouse binding 能收到真实前台点击；
- rmux 未提供 `mouse_x` / `mouse_y`；
- `send-keys -M` 未进入 Rust/crossterm `Event::Mouse`；
- direct `send-keys -t %0 c` 可打开 config UI，但 owner 拒绝 broad sidebar-left-click fallback。

因此本 goal feature blocked。后续能力拆分到 `sidebar-settings-rmux-mouse-routing`。
