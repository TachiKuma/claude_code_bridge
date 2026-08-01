---
doc_type: feature-review
feature: 2026-07-20-rmux-backend-core
roadmap_item: rmux-backend-core
status: pass
reviewer_id: "019f8b97-402d-75a2-91ca-c465fb93aa63"
updated_at: "2026-07-23"
---

# rmux-backend-core Review

## Reviewer

- Task agent：Gauss
- Agent id：`019f8b97-402d-75a2-91ca-c465fb93aa63`
- Role：独立 code review Task agent
- 模式：只读 review；未修改文件，未执行 commit/push/reset。
- 生命周期：初审和 closure 结果已消费，agent 已关闭。

## Initial Verdict

`changes_requested`。

Blocking findings：

- `create_session(window_name=...)` 只 guard `new-session`，未 guard `new-window`。
- `session_alive()` 把 daemon unreachable / no-server-running 误判为 missing session，未抛 `transient-unavailable`。

Important findings：

- `set_pane_title()` 实际执行 `select-pane`，但未 guard hidden command。
- import guard 只扫描 `rmux_backend.py`，未扫描 `rmux_backend_runtime/*.py`。
- checklist steps/checks 仍为 `pending`。

## Fixes

- `create_session()` 按是否传入 `window_name` 动态 guard `("new-session", "new-window")`。
- `session_alive()` 只对 missing-session detail 返回 `False`；unreachable/no-server-running 映射为 `MuxCommandError(category="transient-unavailable")` 并保留 daemon evidence。
- `set_pane_title()` guard `select-pane`；default capability projection 从 `user_options_title` semantic evidence 投影 `select-pane=workaround`，从 `pane_death` semantic evidence 投影 `kill-pane=workaround`。
- import guard 扫描 `rmux_backend.py` 和 `rmux_backend_runtime/*.py`。
- checklist steps/checks 更新为 `done`。

## Closure Verdict

`pass`。

Gauss focused closure 确认上一轮 blocking / important findings 全部关闭。

## Closure Evidence

- `python -m pytest -q "test/test_rmux_backend_core.py" "test/test_rmux_backend_core_import_guard.py"`：`12 passed`。
- `python -m compileall -q "lib/terminal_runtime/rmux_backend.py" "lib/terminal_runtime/rmux_backend_runtime"`：通过。
- checklist YAML 校验：通过。
- `python -m pytest -q "test/test_terminal_runtime_rmux.py"`：`8 passed`。
- tmux compatibility 抽样：`52 passed`。
- `git diff --check`：通过，仅有 CRLF 提示。

## Residual Risks

- 未运行全量测试套件。
- closure review 聚焦上一轮 findings，不替代终端功能验收。
