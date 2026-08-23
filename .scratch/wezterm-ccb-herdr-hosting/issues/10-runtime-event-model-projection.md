# 10：HerdrRuntimeEvent 模型 + 事件投影/snapshot polling（Phase 3）

**What to build：** 引入 `HerdrRuntimeEvent` 模型与运行时事件订阅：启动时先读 `runtime_snapshot`
再订阅增量事件；无上游事件时先用 snapshot polling 兼容实现，但对外模型保持事件语义。事件按
server_id/session/workspace/pane/agent/runtime_generation/seq 校验，丢弃乱序、重复与过期
generation 的事件；`pane_id` 变化视为新运行时所有权，旧状态不沿用。

**Blocked by：** 02（binding 锚点）、06（握手对象）

**Status:** ready-for-agent

- [ ] 新增 `HerdrRuntimeEvent` 模型与订阅；无上游事件时 snapshot polling 兜底
- [ ] 启动先读 snapshot 再消费增量事件
- [ ] 断线重连后重读 snapshot，并按 generation+seq 丢弃旧事件
- [ ] 乱序、重复事件不污染当前状态
- [ ] `pane_id` 变化被视为新运行时所有权，旧状态不沿用
