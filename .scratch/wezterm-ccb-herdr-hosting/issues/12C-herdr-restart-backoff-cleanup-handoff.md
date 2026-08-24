# 12C：restart/backoff/workspace cleanup 下放收口

**What to build：** 在 12B 的 readiness/liveness fact 稳定后，把通用 pane restart/backoff 和 workspace
cleanup 的执行权交给 Herdr。CCB 只声明 manifest、接收结果、决定 Provider 是否允许恢复、是否 job
失败/重试。

**Blocked by：** 12B（Herdr readiness/liveness adapter）、上游 Herdr 原生 restart/backoff/cleanup 能力

**Status:** blocked-upstream

**Evidence to inspect：** `lib/platforms/windows/herdr/runtime/ensure.py`、
`lib/ccbd/services/project_namespace_runtime/destroy.py`、
`lib/ccbd/stop_flow_runtime/service.py`、`test/test_ccbd_stop_flow_runtime.py`

- [ ] restart/backoff 策略来自 manifest 或 Herdr runtime.ensure 结果
- [ ] CCB 不再直接 respawn 通用 pane，只处理 Provider 恢复许可
- [ ] workspace cleanup 由 Herdr 返回结构化 evidence
- [ ] kill/stop/reload 保持幂等，旧 workspace 不累积
- [ ] Windows live validation 覆盖 kill/restart/reload 后 workspace 数量稳定

**Validation：**

- `pytest test/test_ccbd_stop_flow_runtime.py test/test_v2_project_namespace_state.py`

**Audit（2026-08-24）：** 12B 已收口（readiness/liveness 已下放 Herdr runtime fact），本节点
剩余阻塞仅为「上游 Herdr 原生 restart/backoff/cleanup 能力」与 Windows live validation 环境，
不在本会话可执行范围；保持 blocked-upstream，不伪实现。

