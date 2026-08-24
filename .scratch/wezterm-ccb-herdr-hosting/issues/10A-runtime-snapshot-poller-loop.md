# 10A：snapshot polling 调度循环接线

**What to build：** 把已经存在的 `poll_runtime_snapshot(projector, binding, backend)` 接到 ccbd 可运行
的后台调度循环中。循环只负责读取 Herdr runtime snapshot、刷新 projector、拿到变化的 `pane_id`，
再触发 registry/project_view 修订递增或缓存失效；不在本节点引入上游事件订阅。

**Blocked by：** 10（事件模型/projector 基础）、06（持久 Runtime Client 握手）

**Status:** done

**Evidence to inspect：** `lib/platforms/windows/herdr/runtime/events.py`、
`lib/platforms/windows/herdr/runtime/client.py`、`lib/ccbd/project_view/service.py`、
`lib/ccbd/services/registry.py`、`test/test_herdr_runtime_contracts.py`

- [x] ccbd 启动后能为 Herdr runtime binding 建立 polling worker 或维护循环
- [x] 每次 polling 先使用当前 binding/generation，不消费无归属 snapshot
- [x] `poll_runtime_snapshot()` 返回变化 pane 后，`project_view` 缓存能失效
- [x] polling 异常被记录为运行时不可确定，不把 `unknown` 降级成 `idle`
- [x] 单元测试覆盖：snapshot 变化触发失效、无变化不重复刷、backend 不支持 snapshot 时 no-op

**Validation：**

- `pytest test/test_herdr_runtime_contracts.py test/test_ccbd_project_view.py`

**Evidence:** `lib/ccbd/services/herdr_snapshot_polling.py`, `lib/ccbd/app_runtime/lifecycle.py`,
`lib/agents/models_runtime/runtime_runtime/agent.py`, `lib/agents/store.py`,
`test/test_herdr_snapshot_polling.py`
