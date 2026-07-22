---
doc_type: feature-acceptance
feature: rmux-send-capture-logging
status: accepted
updated_at: "2026-07-23"
---

# rmux-send-capture-logging Acceptance

## Acceptance Summary

本 feature 已 accepted。

完成内容：

- `RmuxBackend` 暴露 `send_text`、`send_key`、`capture_pane`、`ensure_pane_log`、`pane_log_path` 和 `get_text` 兼容入口。
- 新增 `rmux_backend_runtime/io.py`，承载 Rmux pane IO、capture policy、key allowlist 和 logging builder bridge。
- `send_text` 支持空文本 no-op、长文本 chunk、多行、shell metachar 和 submit Enter 控制，不使用 tmux `load-buffer` / `paste-buffer`。
- `send_key` 使用 allowlist，覆盖 Ctrl-C、Ctrl-D、Enter、Tab、Escape、Backspace、方向键等常用键。
- `capture_pane` 返回结构化 `RmuxCaptureResult`，包含 `text`、真实 `raw_bytes`、range、ANSI mode、trim policy 和 diagnostics。
- `ensure_pane_log` 消费 `WindowsCommandBuilder.build_pipe_log_command()`，Rmux IO 层不拼平台 shell literal。
- completion fixtures 覆盖 Codex、Claude、AGY、DeepSeek/session snapshot 等 capture/log 文本形态。

## Gate Evidence

- Checklist：`.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-checklist.yaml` 全部 `done`。
- Review：独立 Task agent Halley 初审要求修改，focused closure verdict `pass`。
- QA：`.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-qa.md` 为 `pass`。
- Goal 功能验收：Task agent Confucius verdict `pass`。

## Commands

- CMD-001：checklist YAML validate 通过。
- CMD-002：roadmap items YAML validate 通过。
- CMD-003：`test/test_rmux_send_capture_logging.py`，`11 passed`。
- CMD-004：`test/test_rmux_completion_capture_fixtures.py`，`6 passed`。
- CMD-005：`test/test_terminal_runtime_tmux_send.py test/test_terminal_runtime_tmux_logs.py test/test_ccbd_project_view.py -k "send or log or capture or pane"`，`16 passed, 72 deselected`。
- CMD-006：`test/test_rmux_send_capture_logging_import_guard.py`，`5 passed`。
- Combined feature suite：`22 passed`。
- `python -m compileall -q "lib/terminal_runtime/rmux_backend.py" "lib/terminal_runtime/rmux_backend_runtime" "lib/terminal_runtime/rmux_runner.py"`：通过。

## Residual Risks

- 未运行全量测试套件。
- 本轮未启动真实 Rmux daemon；Windows ConPTY / daemon full-chain 留给后续 `ccbd-rmux-namespace-lifecycle` 和 `rmux-windows-validation-matrix`。
- completion fixtures 证明 parser 对 Rmux capture/log 文本形态兼容，但真实 provider 交互仍由后续 lifecycle 和 validation matrix 证明。

## Delivery Record

- Roadmap item 将回写为 `done`。
- Roadmap goal feature 状态将回写为 `accepted`。
