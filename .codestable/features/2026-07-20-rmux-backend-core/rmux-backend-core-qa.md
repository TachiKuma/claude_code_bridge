---
doc_type: feature-qa
feature: 2026-07-20-rmux-backend-core
roadmap_item: rmux-backend-core
status: pass
updated_at: "2026-07-23"
---

# rmux-backend-core QA

## Scope

本 QA 覆盖 `rmux-backend-core` design / checklist 的 DoD：capability guard、command client seam、namespace/window core、pane core、presentation core、error mapping、tmux compatibility 和 import/scope guard。

## Fresh Evidence

- CMD-001：`python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-checklist.yaml" --yaml-only`：`1 passed, 0 failed`。
- CMD-002：`python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`：`1 passed, 0 failed`。
- CMD-003：`python -m pytest -q "test/test_rmux_backend_core.py"`：`9 passed`。
- CMD-004：`python -m pytest -q "test/test_terminal_runtime_backend_selection.py" "test/test_v2_project_namespace_backend.py" "test/test_cli_runtime_launch_tmux_panes.py" -k "tmux or backend or pane or namespace"`：`52 passed`。
- CMD-005：`python -m pytest -q "test/test_rmux_backend_core_import_guard.py"`：`3 passed`。
- Extra：`python -m compileall -q "lib"`：通过。
- Extra：`python -m pytest -q "test/test_terminal_runtime_rmux.py" "test/test_terminal_runtime_backend_selection.py"`：`36 passed`。
- Extra：`python -m pytest -q "test/test_tmux_mux_backend_adapter.py" "test/test_mux_backend_contract.py"`：`27 passed`。
- Extra：`python -m pytest -q "test/test_v2_start_foreground.py" -k "rmux or backend"`：`3 passed, 10 deselected`。
- Extra：`git diff --check`：通过，仅有 CRLF 提示。

## Coverage Notes

- Capability guard 覆盖 construction、operation、`new-window` conditional guard、`select-pane` hidden command guard。
- Namespace/window 覆盖 `create_session`、`session_alive` missing/unreachable 区分、`list_windows`、`ensure_window`。
- Pane core 覆盖 `list_panes`、`split_pane`、`respawn_pane`、`kill_pane`，并断言 Rmux pane id 不需要 tmux `%N`。
- Presentation 覆盖 title、user option、style orchestration 和 partial failure diagnostics。
- Error mapping 覆盖 malformed output、permission、transient-unavailable、unsupported。
- Scope guard 覆盖不实现 send/capture/logging/foreground attach，且 Rmux core 不导入 tmux/psmux implementation。

## Verdict

`pass`。

## Residual Risks

- 未运行全量测试套件。
- Rmux production command semantics 仍依赖既有 capability report；本 feature 使用 fake command client 做 deterministic contract tests，不启动真实 Rmux daemon。
