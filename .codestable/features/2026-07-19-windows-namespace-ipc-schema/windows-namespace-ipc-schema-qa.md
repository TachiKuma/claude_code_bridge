---
doc_type: feature-qa
feature: 2026-07-19-windows-namespace-ipc-schema
roadmap: windows-rmux-native-backend
roadmap_item: windows-namespace-ipc-schema
status: passed
updated_at: "2026-07-22"
---

# windows-namespace-ipc-schema QA

## Scope

QA 覆盖 state/event canonical roundtrip、MuxNamespaceRef 投影、ping/doctor payload 双 schema、no-clobber、foreground attach canonical-first 与 legacy fallback，以及 checklist / roadmap YAML 合法性。

## Evidence

- `python -m py_compile "lib/ccbd/services/project_namespace_state_runtime/models.py" "lib/ccbd/handlers/ping_runtime/payloads.py" "lib/cli/services/start_foreground.py" "lib/cli/render_runtime/ops_views_doctor.py" "lib/ccbd/services/project_namespace_runtime/models.py" "lib/ccbd/services/project_namespace_runtime/controller.py" "lib/terminal_runtime/tmux_readiness.py"`：passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-19-windows-namespace-ipc-schema/windows-namespace-ipc-schema-checklist.yaml" --yaml-only`：passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`：passed。
- `python -m pytest -q "test/test_v2_project_namespace_state.py"`：31 passed。
- `python -m pytest -q "test/test_v2_ccbd_ping_runtime.py"`：14 passed。
- `python -m pytest -q "test/test_v2_project_namespace_state.py" "test/test_v2_ccbd_ping_runtime.py" "test/test_v2_start_foreground.py" "test/test_v2_cli_render.py" "test/test_v2_tmux_cleanup_history.py::test_doctor_summary_includes_namespace_state_and_latest_event"`：94 passed。
- `python -m pytest -q "test/test_terminal_runtime_backend_selection.py::test_default_project_namespace_backend_env_rmux_uses_resolver_fail_fast" "test/test_terminal_runtime_backend_selection.py::test_default_project_namespace_backend_project_config_rmux_uses_resolver_fail_fast"`：2 passed。
- `python -m pytest -q "test/test_v2_cli_render.py" "test/test_ccbd_project_view.py" -k "namespace_tmux or namespace_ or tmux_socket_path"`：2 passed, 114 deselected。
- `git diff --check`：passed。

## Documented Baseline

`CMD-004` 在 native Windows 组合运行时为 `2 failed, 29 passed, 42 deselected`：

- `test_ccbd_socket_bad_client_does_not_block_later_ping`：当前 Python/Windows 环境缺 `socket.AF_UNIX`。
- `test_ccbd_socket_rejects_mutating_requests_while_lifecycle_stopping`：Windows TCP control-plane shutdown 期间连接被远端重置。

这两个失败属于既有 ccbd control-plane transport / Windows shutdown 基线，不是 namespace schema 字段断言失败。相同组合中的 namespace/ping/doctor/attach 断言通过；`test_ping_namespace_summary` 单独运行通过。

## Verdict

通过。核心 schema 与兼容性证据完整，`CMD-004` 的剩余失败已作为 Windows control-plane baseline 记录。
