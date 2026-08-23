# 06：持久 Runtime Client 握手收敛（Phase 1）

**What to build：** 把 Herdr 连接、server info、capability 和 generation 收敛成一个进程内一次性
握手对象。缓存 server_info/capabilities/socket ref/server 与 session identity；仅在首次握手、连接
恢复或 generation 改变时刷新，停止每个操作都无条件重复调用 server_info。用户体感上启动/恢复/
attach/teardown 不再因重复握手而变慢。

**Blocked by：** 无（立即可开）

**Status:** partial

**Implementation:** `3b4f75b4`

**Evidence:** `lib/platforms/windows/herdr/runtime/client.py`、`test/test_herdr_backend_client.py`

**Notes:** 已有进程内握手对象、`force_refresh` 与 `invalidate_handshake()`；runtime generation 改变自动
识别并触发刷新仍未形成完整闭环。

- [x] 提供握手对象，缓存 server_info/capabilities/socket/identity
- [x] 操作前不再无条件重复 server_info，仅在首次/重连/generation 改变时刷新
- [x] 断线重连后握手可正确重建并刷新缓存
- [x] 操作前的重复 server_info 调用次数显著下降（有测试佐证）
- [ ] generation 改变被识别并触发缓存刷新
