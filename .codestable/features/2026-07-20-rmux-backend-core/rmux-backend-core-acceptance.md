---
doc_type: feature-acceptance
feature: rmux-backend-core
status: accepted
updated_at: "2026-07-23"
---

# rmux-backend-core Acceptance

## Acceptance Summary

本 feature 已 accepted。

完成内容：

- `RmuxBackend` 已替换为独立 core adapter，不再继承 `PsmuxBackend` / `TmuxBackend`。
- 新增 Rmux command client seam、capability gate、error mapping、namespace/window、pane、presentation runtime 分层。
- capability report 缺失或 required command unsupported 时 fail-fast，不 fallback 到 tmux。
- namespace/window/pane/presentation 返回 backend-neutral refs / records。
- command failure、malformed output、permission、transient unavailable、unsupported 等错误统一映射为 `MuxCommandError`，保留 command / ipc / daemon evidence。
- 保持 core-only 边界，不实现 send/capture/logging/provider parser/foreground attach/ccbd lifecycle。

## Gate Evidence

- Checklist：`.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-checklist.yaml` 全部 `done`。
- Review：独立 Task agent Gauss 初审要求修改，closure review `pass`。
- QA：`.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-qa.md` 为 `pass`。
- Goal 功能验收：Task agent Noether verdict `pass`。

## Commands

- CMD-001：checklist YAML validate 通过。
- CMD-002：roadmap items YAML validate 通过。
- CMD-003：`test/test_rmux_backend_core.py`，`9 passed`。
- CMD-004：`test/test_terminal_runtime_backend_selection.py test/test_v2_project_namespace_backend.py test/test_cli_runtime_launch_tmux_panes.py -k "tmux or backend or pane or namespace"`，`52 passed`。
- CMD-005：`test/test_rmux_backend_core_import_guard.py`，`3 passed`。
- `python -m compileall -q "lib"`：通过。
- `git diff --check`：通过，仅有 CRLF 提示。

## Residual Risks

- 未运行全量测试套件；本轮证据来自 focused DoD 与兼容性抽样。
- `RmuxSubprocessCommandClient` 复用 tmux-family argv helper，但不导入 tmux backend implementation；如后续需要更严格 helper ownership，可单独拆分。
- send/capture/logging 和真实 ccbd lifecycle 接入仍由后续 roadmap item 覆盖。

## Delivery Record

- Roadmap item 将回写为 `done`。
- Roadmap goal feature 状态将回写为 `accepted`。
