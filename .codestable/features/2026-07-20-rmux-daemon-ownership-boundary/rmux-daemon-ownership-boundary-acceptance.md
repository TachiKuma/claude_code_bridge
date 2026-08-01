---
doc_type: feature-acceptance
feature: rmux-daemon-ownership-boundary
status: accepted
updated_at: "2026-07-23"
---

# rmux-daemon-ownership-boundary Acceptance

## Acceptance Summary

本 feature 已 accepted。

完成内容：

- 新增 Rmux daemon evidence contract：`RmuxDaemonRef`、`RmuxDaemonEvidence`、`RmuxCleanupPlan`。
- 定义 start_result success / failure evidence，并覆盖 `healthy`、`crashed`、`unreachable` 映射。
- 定义 cleanup plan 默认安全策略：namespace/project cleanup 默认 `leave_running`，daemon-wide cleanup 仅 explicit force。
- 定义 `backend_daemon_*` diagnostics projection，并接入 namespace summary；默认 tmux namespace 不输出 Rmux daemon diagnostics。
- Provider health diagnostics 可携带 backend daemon evidence，且不改变 runtime health authority。
- 保持 ccbd lease / keeper / lifecycle authority 不变，不实现 Rmux backend core / IPC。

## Gate Evidence

- Checklist：`.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-checklist.yaml` 全部 `done`。
- Review：独立 Task agent Maxwell 初审要求修改，closure review `pass`，未发现阻塞问题。
- QA：`.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-qa.md` 为 `pass`。
- Goal 功能验收：Task agent Lagrange verdict `pass`。

## Commands

- CMD-001：checklist YAML validate 通过。
- CMD-002：roadmap items YAML validate 通过。
- CMD-003：`test/test_rmux_daemon_ownership_boundary.py`，`9 passed`。
- CMD-004：`test/test_v2_tmux_project_cleanup.py test/test_ccbd_startup_fence_app.py test/test_ccbd_service_graph.py -k "cleanup or keeper or daemon or ownership"`，`7 passed, 13 deselected`。
- CMD-005：`test/test_ccbd_health_monitor_rebind.py test/test_v2_ccbd_socket.py -k "health or doctor or namespace or daemon"`，`5 passed, 46 deselected`。
- `python -m compileall -q "lib"`：通过。
- `git diff --check`：通过。

## Residual Risks

- 未运行全量测试套件；本轮证据来自 focused DOD 与兼容性抽样。
- `backend_daemon_action` 当前是 diagnostics 动态投影字段；若后续需要静态类型强约束，应提升到 `RmuxDaemonEvidence` 字段。
- Rmux backend core、IPC、send/capture/logging 和真实 daemon lifecycle 仍在后续 roadmap item 中。

## Delivery Record

- Roadmap item 将回写为 `done`。
- Roadmap goal feature 状态将回写为 `accepted`。
