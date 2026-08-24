# 10B：Herdr runtime event 订阅适配器

**What to build：** 在 Herdr 暴露事件能力时接入真正的 runtime event 订阅；能力缺失或订阅失败时，
显式回退 10A 的 snapshot polling。订阅入口必须保持事件语义：启动顺序为 `snapshot seed -> subscribe
incremental events`。

**Blocked by：** 10A（polling 兜底可运行）、12A（Herdr 原生能力探测；若上游尚未提供可先保留 disabled 分支）

**Status:** ready-for-agent-after-10A

**Evidence to inspect：** `lib/platforms/windows/herdr/runtime/client.py`、
`lib/platforms/windows/herdr/runtime/cli.py`、`lib/platforms/windows/herdr/runtime/events.py`、
`lib/platforms/windows/herdr/runtime/capabilities.py`

- [ ] 定义最小订阅接口，输出 `HerdrRuntimeEvent`，不泄漏原始 stdout/transcript
- [ ] 首次订阅前强制读取 snapshot 种子
- [ ] 订阅断开时切换到 polling，并暴露 fallback reason
- [ ] 重复、乱序、过期 generation 事件继续由 projector 丢弃
- [ ] capability 不支持 events 时不 fail-open，状态来源标记为 `snapshot_polling`

**Validation：**

- `pytest test/test_herdr_runtime_contracts.py`

