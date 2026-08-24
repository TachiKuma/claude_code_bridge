# 12B：readiness/liveness 下放到 Herdr runtime fact

**What to build：** 把通用 pane readiness/liveness 的判断从 CCB shell、PowerShell 和 lifecycle 文件推断，
迁到 Herdr runtime snapshot/event fact。CCB 仍保留 Provider session restore/auth/continuation 等业务
边界。

**Blocked by：** 10A（snapshot polling）、12A（能力契约）

**Status:** done

**Evidence to inspect：** `lib/ccbd/services/runtime_runtime/refresh.py`、
`lib/ccbd/services/runtime_runtime/restore_runtime/readiness.py`、
`lib/ccbd/services/project_namespace_runtime/backend.py`、`test/test_ccbd_runtime_refresh.py`

- [x] readiness 使用 Herdr pane/agent fact，不主动 shell 探测通用 pane 存活
- [x] liveness 能区分 alive/missing/unknown，unknown 不当作 healthy
- [x] Provider-specific session restore 仍由 CCB contract 保护
- [x] 通用 pane 崩溃不伪造 Provider session 已恢复
- [x] 无 Herdr fact 时保持兼容层并暴露 fallback reason

**Validation：**

- `pytest test/test_ccbd_runtime_refresh.py test/test_ccbd_restore_helpers.py`

**Evidence:** `lib/ccbd/services/runtime_runtime/refresh.py`
（`_herdr_snapshot_pane_state`、`_herdr_health_from_pane_state`、无 fact 时写入
`fallback_reason=herdr_snapshot_unavailable` 的自描述快照）、
`test/test_ccbd_runtime_refresh.py`

**Notes：** Herdr provider 的 readiness/liveness 以 `runtime_snapshot` 为事实源：pane 在快照中
即 alive，缺失即 pane-missing，快照不可用即 unknown（不伪装 healthy）并暴露 fallback reason。
通用 pane 崩溃不会被投影为 Provider session 已恢复；snapshot 缺目标 pane 时不回退 root
summary。
