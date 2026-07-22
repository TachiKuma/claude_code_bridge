---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: rmux-send-capture-logging
feature: 2026-07-20-rmux-send-capture-logging
status: accepted
---

# rmux-send-capture-logging Goal Feature Spec

## 1. Identity

- Roadmap item: rmux-send-capture-logging
- Feature dir: `.codestable/features/2026-07-20-rmux-send-capture-logging`
- Design: `.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-design.md`
- Checklist: `.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-checklist.yaml`
- Design review: `.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-design-review.md`
- Review output: `.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-review.md`
- QA output: `.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-qa.md`
- Acceptance output: `.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-acceptance.md`
- Depends on: rmux-backend-core
- Feature kind: implementation

## 2. Deliverable

Rmux send/capture/logging semantics 已完成：

- `RmuxBackend` exposes `send_text`、`send_key`、`capture_pane`、`ensure_pane_log`、`pane_log_path`。
- Rmux IO module handles key allowlist、chunked text send、structured capture result、binary stdout bytes 和 Windows logging builder bridge。
- Completion capture fixtures prove Codex / Claude / AGY / DeepSeek/session snapshot input compatibility.

## 3. Core Runtime Path

见 design 的 Acceptance Coverage Matrix、feature checklist、review、QA 和 acceptance 报告。

## 4. Mandatory Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-checklist.yaml" --yaml-only`
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`
- `python -m pytest -q "test/test_rmux_send_capture_logging.py"`
- `python -m pytest -q "test/test_rmux_completion_capture_fixtures.py"`
- `python -m pytest -q "test/test_terminal_runtime_tmux_send.py" "test/test_terminal_runtime_tmux_logs.py" "test/test_ccbd_project_view.py" -k "send or log or capture or pane"`
- `python -m pytest -q "test/test_rmux_send_capture_logging_import_guard.py"`

## 5. Gates And Recovery

- Implementation gate: checklist steps done, scope-gate, dod-runner and evidence-pack passed.
- Review gate: independent cs-code-review passed with no unresolved blocking findings.
- QA gate: cs-feat QA passed and covers design scenarios, DoD commands and review QA focus.
- Acceptance gate: goal functional acceptance passed by Task agent Confucius; checklist checks passed and roadmap item writeback complete.
- Recovery: implementation defects return to implementation then review/QA/acceptance; stage evidence defects repair the owning stage only.

## 6. Evidence And Cleanliness

- Evidence required: design/checklist/review/QA/acceptance, gate JSON, evidence pack, command outputs, roadmap/items writeback.
- Cleanliness: no debug output, temporary TODO/FIXME/XXX, commented-out code, dead imports, same-name validation shims or unexplained scope drift.
