# 02：`source=ccb` 成为 CCB 管理 pane 的身份权威

**What to build:** 对 CCB 创建并管理的 pane，CCB 上报的 provider kind、agent 身份、状态和 session 信息成为权威事实；Herdr 屏幕检测只作为非 CCB pane 或缺少 CCB 上报时的兜底，`report_pane_agent` 与 `release_pane_agent` 正常路径继续保留并受回归保护。

**Blocked by:** None (can start immediately).

**Status:** done

- [x] CCB 管理 pane 的 agent/provider 身份由 `source=ccb` 上报结果决定，不被屏幕启发式检测覆盖。
- [x] 非 CCB 管理 pane 仍可使用 Herdr 观测结果作为兜底，不破坏外部 pane 的可见性。
- [x] 启动或接管 pane 时能清理 stale pane agent authority，再以 CCB 来源重新声明当前身份。
- [x] 释放 pane 时能通过 CCB 来源释放对应 provider 的身份归属，不残留旧身份。
- [x] 上报与释放的对外合约包含 pane、session、provider kind、state、seq 和可选 session 信息。
- [x] 非法 state、缺少 pane 或缺少 provider kind 的上报必须 fail closed，不能静默成功。
- [x] 局部门禁覆盖 `source=ccb` 权威、屏幕检测兜底边界、旧身份清理和 `report_pane_agent` 正常路径不可删除。

**Validation:**

- `pytest -q test/test_herdr_lifecycle_bridge.py test/test_herdr_backend_client.py test/test_runtime_launch_timings.py`
- `pytest -q test/test_herdr_lifecycle_bridge.py::test_bridge_skips_missing_provider_or_unknown_state_without_consuming_seq`

**Evidence:** Herdr CLI adapter 以 `--source ccb` 执行 `pane report-agent`/`pane release-agent`；启动路径先 best-effort release 旧 authority，再以 idle+seq 报告 CCB 管理 pane；生命周期桥接对 CCB 状态切换单调递增 seq，并在缺 pane、缺 provider、非 Herdr namespace 或未知状态时不上报。
