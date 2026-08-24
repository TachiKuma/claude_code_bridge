# 10B：Herdr runtime event 订阅适配器

**What to build：** 在 Herdr 暴露事件能力时接入真正的 runtime event 订阅；能力缺失或订阅失败时，
显式回退 10A 的 snapshot polling。订阅入口必须保持事件语义：启动顺序为 `snapshot seed -> subscribe
incremental events`。

**Blocked by：** 10A（polling 兜底可运行）、12A（Herdr 原生能力探测；若上游尚未提供可先保留 disabled 分支）

**Status:** done

**Evidence to inspect：** `lib/platforms/windows/herdr/runtime/client.py`、
`lib/platforms/windows/herdr/runtime/cli.py`、`lib/platforms/windows/herdr/runtime/events.py`、
`lib/platforms/windows/herdr/runtime/capabilities.py`

- [x] 定义最小订阅接口，输出 `HerdrRuntimeEvent`，不泄漏原始 stdout/transcript
- [x] 首次订阅前强制读取 snapshot 种子
- [x] 订阅断开时切换到 polling，并暴露 fallback reason
- [x] 重复、乱序、过期 generation 事件继续由 projector 丢弃
- [x] capability 不支持 events 时不 fail-open，状态来源标记为 `snapshot_polling`

**Validation：**

- `pytest test/test_herdr_runtime_contracts.py`

**Evidence:** `lib/platforms/windows/herdr/runtime/events.py`
（`HerdrRuntimeEventSubscription`/`create_runtime_event_subscription`/`parse_runtime_event`）、
`lib/platforms/windows/herdr/runtime/client.py`、`lib/platforms/windows/herdr/backend.py`
（`runtime_events()`）、`lib/ccbd/services/herdr_snapshot_polling.py`
（`poll_herdr_runtime_events`）、`lib/ccbd/app_runtime/lifecycle.py`（心跳切换订阅入口）、
`test/test_herdr_runtime_contracts.py`、`test/test_herdr_backend_client.py`、
`test/test_herdr_snapshot_polling.py`

**Notes：** 心跳调度已从 polling-only 入口切换为 `poll_herdr_runtime_events`；上游尚无真实事件
能力时，capability 或订阅失败会显式回退 snapshot polling，并把 `source`/`fallback_reason`
写入持久化快照，不静默降级。
