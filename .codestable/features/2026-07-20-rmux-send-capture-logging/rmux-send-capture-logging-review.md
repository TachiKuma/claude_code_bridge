---
doc_type: feature-review
feature: 2026-07-20-rmux-send-capture-logging
roadmap_item: rmux-send-capture-logging
status: pass
reviewer_id: "019f8bb0-e62f-7210-82a0-b9077e635e12"
updated_at: "2026-07-23"
---

# rmux-send-capture-logging Review

## Reviewer

- Task agent：Halley
- Agent id：`019f8bb0-e62f-7210-82a0-b9077e635e12`
- Role：独立 code review Task agent
- 模式：只读 review；未修改文件，未执行 commit/push/reset。
- 生命周期：初审和 focused closure 结果已消费，agent 已关闭；close result returned completed status。

## Initial Verdict

`changes_requested`。

Blocking findings：

- `test/test_rmux_send_capture_logging_import_guard.py` 的 `_status_path()` 先 `strip()` 再固定截取 `text[3:]`，会漏掉 unstaged modified 路径，削弱 AC-008 scope guard。

Important findings：

- `capture_pane()` 的 `raw_bytes` 由已解码 stdout 重新 encode，不能代表真实 stdout bytes。
- checklist / roadmap / goal state 尚未回写完成，后续 acceptance 前必须补齐。

Nit：

- completion fixtures 通过手写 capture shape 模拟 parser 输入，未直接消费 `RmuxBackend.capture_pane()` 返回；本轮接受为 parser 兼容 fixture，capture result 字段由 IO 单测覆盖。

## Fixes

- `_status_path()` 改为保留 git porcelain 前两列状态位后取路径，并新增测试覆盖 ` M`、`M `、`??`、rename。
- `RmuxCommandResult` 增加可选 `stdout_bytes` / `stderr_bytes`。
- `RmuxSubprocessCommandClient.run()` 对 `capture-pane` 使用 binary capture，解码 text 同时保留真实 bytes。
- `capture_pane()` 优先返回 `result.stdout_bytes`，并在 diagnostics 记录 `raw_bytes_source`。
- 新增不可解码 byte 与 subprocess binary capture 测试。

## Closure Verdict

`pass`。

Halley focused closure 确认原 blocking 已关闭，raw bytes important finding 已关闭，无新增 blocking / important / nit。

## Fresh Evidence

- CMD-001：`python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-checklist.yaml" --yaml-only`：通过。
- CMD-002：`python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`：通过。
- CMD-003 / CMD-004 / CMD-006：`python -m pytest -q "test/test_rmux_send_capture_logging.py" "test/test_rmux_completion_capture_fixtures.py" "test/test_rmux_send_capture_logging_import_guard.py"`：`22 passed`。
- CMD-005：`python -m pytest -q "test/test_terminal_runtime_tmux_send.py" "test/test_terminal_runtime_tmux_logs.py" "test/test_ccbd_project_view.py" -k "send or log or capture or pane"`：`16 passed, 72 deselected`。

## Residual Risks

- 未运行全量测试套件。
- completion fixtures 证明 parser 对 Rmux capture/log 文本形态兼容；真实 provider / Rmux daemon 全链路仍由后续 lifecycle 与 validation matrix item 覆盖。
