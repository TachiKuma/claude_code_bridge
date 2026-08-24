# 10C：断线重连后的 snapshot 重种子

**What to build：** 在 Herdr socket 断线、handshake invalidate、runtime generation 改变或事件订阅重连
后，先重新读取 runtime snapshot 重种子 projector，再继续消费增量事件。目标是避免旧 pane 状态在
重连后残留。

**Blocked by：** 10A（polling/refresh 入口）、10B（订阅重连路径；没有事件能力时只覆盖 polling reconnect）

**Status:** done

**Evidence to inspect：** `lib/platforms/windows/herdr/backend.py`、
`lib/platforms/windows/herdr/runtime/client.py`、
`lib/platforms/windows/herdr/runtime/events.py`、
`lib/ccbd/services/runtime_runtime/refresh.py`、
`test/test_herdr_backend_client.py`、
`test/test_herdr_runtime_contracts.py`

- [x] `invalidate_handshake()` 或 transient-unavailable 后下一轮必须重读 snapshot
- [x] generation 改变时丢弃旧 seq 游标和旧 pane 状态
- [x] snapshot 缺目标 pane 时，目标状态投影为 unknown 或 pane-missing，不回退旧 root summary
- [x] 重连后的第一批增量事件必须满足当前 binding/generation/seq
- [x] 测试覆盖：断线重连、generation 切换、pane_id 变更、旧事件延迟到达

**Validation：**

- `pytest test/test_herdr_runtime_contracts.py test/test_ccbd_runtime_refresh.py`
