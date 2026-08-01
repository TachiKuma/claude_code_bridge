---
doc_type: feature-acceptance
feature: 2026-07-19-windows-namespace-ipc-schema
roadmap: windows-rmux-native-backend
roadmap_item: windows-namespace-ipc-schema
status: passed
updated_at: "2026-07-25"
---

# windows-namespace-ipc-schema 验收

## Acceptance Checks

- `ProjectNamespaceState` / `ProjectNamespaceEvent` 已提供 mux-agnostic canonical fields，并保留旧 `namespace_tmux_*` 兼容别名。
- `build_ccbd_payload()` 和 doctor summary 采用 state canonical 字段优先，不让 event summary 覆盖 namespace state。
- ping / doctor 同时输出 canonical namespace 字段和 legacy alias，顶层 `tmux_socket_path` 不被 namespace alias 覆盖。
- foreground attach 使用 canonical-first、legacy fallback，保持旧 tmux 行为兼容。
- `default_project_namespace_backend()` 不通过 `CCB_TERMINAL_BACKEND` 绕开 resolver 构造 rmux backend。
- feature review、QA、goal functional acceptance 和 roadmap writeback 均已完成。

## Functional Evidence

- feature review：Task agent `019f8a14-1e14-7931-8490-c7fbaebad8d5` 复审通过，无 unresolved blocking / high / medium findings。
- feature QA：`python -m pytest -q "test/test_v2_project_namespace_state.py" "test/test_v2_ccbd_ping_runtime.py" "test/test_v2_start_foreground.py" "test/test_v2_cli_render.py" "test/test_v2_tmux_cleanup_history.py::test_doctor_summary_includes_namespace_state_and_latest_event"` -> `94 passed`。
- goal functional acceptance：Task agent `019f8a19-78e1-77b3-9025-9772dd8bf21d` 验收 `pass`。
- checklist YAML 与 roadmap items YAML 均已通过 `.codestable/tools/validate-yaml.py`。

## Roadmap Writeback

- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 中本 item 为 `done`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml` 中本 feature 为 `accepted`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-features/windows-namespace-ipc-schema.md` 为 `accepted`。

## Delivery Record

已交付 mux-agnostic namespace schema、payload 投影、doctor / ping 双 schema、foreground attach 兼容输入、回归测试、review 与 QA 记录。本文件补齐 feature acceptance 缺口。

## Residual Risks

- QA 记录的 `CMD-004` native Windows control-plane 基线失败属于后续 transport / shutdown 边界，已由后续 `ccbd-windows-tcp-loopback-transport` 与 full-chain/matrix evidence 覆盖。

## Verdict

`passed`。本 feature 可视为 accepted。
