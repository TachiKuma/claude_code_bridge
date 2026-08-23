# 10：HerdrRuntimeEvent 模型 + 事件投影/snapshot polling（Phase 3）

**What to build：** 引入 `HerdrRuntimeEvent` 模型与运行时事件订阅：启动时先读 `runtime_snapshot`
再订阅增量事件；无上游事件时先用 snapshot polling 兼容实现，但对外模型保持事件语义。事件按
server_id/session/workspace/pane/agent/runtime_generation/seq 校验，丢弃乱序、重复与过期
generation 的事件；`pane_id` 变化视为新运行时所有权，旧状态不沿用。

**Blocked by：** 02（binding 锚点）、06（握手对象）

**Status:** partial

**Implementation:** `3b4f75b4`

**Evidence:** `lib/platforms/windows/herdr/runtime/contracts.py`、
`lib/platforms/windows/herdr/runtime/events.py`、`test/test_herdr_runtime_contracts.py`

**Notes:** CCB 侧事件模型、snapshot 初始投影与去重/过期丢弃规则已落地；真正上游事件订阅、后台
snapshot polling 循环、断线重连后的自动重读 snapshot 尚未接入。
补充：`HerdrRuntimeEventProjector` 现已支持 `refresh(binding, snapshot=...)` 用快照重新种子，用于
重连后重读 snapshot，避免旧 pane 状态继续残留；事件订阅与 polling 闭环仍待后续接入。

补充：`poll_runtime_snapshot(projector, binding, backend)` 已提供 snapshot polling 的正式入口，
可由后续循环调度器直接调用；本轮仍未接入持续轮询线程或订阅循环。

- [x] 新增 `HerdrRuntimeEvent` 模型与事件 projector 基础
- [ ] 接入真正运行时事件订阅；无上游事件时 snapshot polling 兜底
- [x] projector 以 binding snapshot 初始化当前状态，再消费增量事件
- [ ] 断线重连后重读 snapshot，并按 generation+seq 丢弃旧事件
- [x] 乱序、重复事件不污染当前状态
- [x] `pane_id` 变化被视为新运行时所有权，旧状态不沿用
