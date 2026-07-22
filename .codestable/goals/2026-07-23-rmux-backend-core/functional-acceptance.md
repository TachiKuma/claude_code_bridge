---
doc_type: goal-functional-acceptance
goal: "rmux-backend-core"
status: pass
reviewer_id: "019f8ba0-0945-78e1-bee2-efb75f5ef6ae"
final_iteration: "iterations/001.md"
---

# rmux-backend-core 功能验收

## Reviewer

- Task agent：Noether
- Agent id：`019f8ba0-0945-78e1-bee2-efb75f5ef6ae`
- Role：终端功能验收 Task agent
- 模式：只读功能验收；未修改文件，未执行 commit/push/reset。
- 生命周期：验收结论已消费，agent 已关闭。

## Acceptance Checks

- `pass`：`RmuxBackend` 不再继承或导入 `TmuxBackend` / `PsmuxBackend`；import guard 覆盖 `rmux_backend.py` 和 `rmux_backend_runtime/*.py`。
- `pass`：required unsupported command fail-fast，覆盖 construction、`split-window`、`new-window`、`select-pane` 等路径。
- `pass`：namespace/window/pane/presentation 返回 backend-neutral refs / records；Rmux pane id 使用 backend-local id，不伪造 tmux `%N`。
- `pass`：command error mapping 保留 `command`、`ipc_ref`、daemon evidence；unreachable 映射为 `transient-unavailable`。
- `pass`：未越界实现 send/capture/logging/provider parser/foreground attach/ccbd lifecycle；`attach_namespace` 明确 unsupported。
- `pass`：独立 review closure 为 `pass`，QA 为 `pass`。

## Functional Evidence

- CMD-001：checklist YAML valid。
- CMD-002：roadmap items YAML valid。
- CMD-003：`test/test_rmux_backend_core.py`，`9 passed`。
- CMD-004：tmux/backend/pane/namespace compatibility 抽样，`52 passed`。
- CMD-005：`test/test_rmux_backend_core_import_guard.py`，`3 passed`。
- `python -m compileall -q "lib"`：通过。
- `git diff --check`：通过，仅有 CRLF 提示。

## Verdict

`pass`。Goal acceptance criteria 已满足。

## Residual Risks

- 未运行全量测试套件。
- `RmuxSubprocessCommandClient` 复用 `terminal_runtime.tmux.tmux_family_base` 拼接 tmux-family base argv；未导入 tmux backend implementation，若后续要求更严格 helper 分离，可单独收口。

## Delivery Record

- Final iteration：`iterations/001.md`。
- Feature acceptance：`.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-acceptance.md`。
