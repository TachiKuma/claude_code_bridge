---
doc_type: feature-qa
feature: 2026-07-20-rmux-send-capture-logging
roadmap_item: rmux-send-capture-logging
status: pass
updated_at: "2026-07-23"
---

# rmux-send-capture-logging QA

## Scope

本 QA 覆盖 `rmux-send-capture-logging` design / checklist 的 DoD：capability guard、send text、send key、capture format、logging bridge、provider completion fixtures、scope guard 和 tmux compatibility 抽样。

## Fresh Evidence

- CMD-001：`python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-checklist.yaml" --yaml-only`：`1 passed, 0 failed`。
- CMD-002：`python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`：`1 passed, 0 failed`。
- CMD-003：`python -m pytest -q "test/test_rmux_send_capture_logging.py"`：`11 passed`。
- CMD-004：`python -m pytest -q "test/test_rmux_completion_capture_fixtures.py"`：`6 passed`。
- CMD-005：`python -m pytest -q "test/test_terminal_runtime_tmux_send.py" "test/test_terminal_runtime_tmux_logs.py" "test/test_ccbd_project_view.py" -k "send or log or capture or pane"`：`16 passed, 72 deselected`。
- CMD-006：`python -m pytest -q "test/test_rmux_send_capture_logging_import_guard.py"`：`5 passed`。
- Combined feature suite：`python -m pytest -q "test/test_rmux_send_capture_logging.py" "test/test_rmux_completion_capture_fixtures.py" "test/test_rmux_send_capture_logging_import_guard.py"`：`22 passed`。

## Coverage Notes

- Capability guard 覆盖 `send-keys`、`capture-pane`、`pipe-pane` unsupported fail-fast，不 fallback tmux。
- `send_text` 覆盖空文本 no-op、多行/长文本 chunk、shell metachar、submit Enter 可控，且无 `load-buffer` / `paste-buffer`。
- `send_key` 覆盖 Ctrl-C、Ctrl-D、方向键和未知 key fail-fast；Ctrl-D 使用 Rmux logical sequence。
- `capture_pane` 覆盖 ANSI/range/tail lines、tail whitespace preserve、diagnostics、not-found error、真实 stdout bytes。
- `ensure_pane_log` 覆盖 path prepare、builder bridge 和无 shell literal 泄漏。
- completion fixtures 覆盖 Codex pane status、Claude pane status、protocol turn、terminal quiet、AGY pane snapshot、DeepSeek/session snapshot family。
- scope guard 覆盖无 tmux/psmux backend import、无 tmux buffer fallback、无 Rmux IO shell literal、无 provider parser / ccbd / mobile gateway 变更。

## Verdict

`pass`。

## Residual Risks

- 未运行全量测试套件。
- 本轮不启动真实 Rmux daemon；真实 Windows ConPTY / provider full-chain 行为由后续 `ccbd-rmux-namespace-lifecycle` 和 `rmux-windows-validation-matrix` 覆盖。
