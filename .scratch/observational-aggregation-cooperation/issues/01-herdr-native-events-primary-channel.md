# 01：Herdr 原生 events 成为主状态通道

**What to build:** CCB 优先通过 Herdr 原生 events 获取 pane 运行时状态变化；当 events 能力缺失、订阅不可用、订阅失败或事件批次非法时，显式回退到 snapshot polling，并让调用方与读模型能看见状态来源和回退原因。

**Blocked by:** None (can start immediately).

**Status:** done

- [x] 当 Herdr runtime events 可用时，状态更新来源记录为 event，且 snapshot 只作为初始种子。
- [x] 当 events 能力缺失时，系统回退到 snapshot polling，并记录 `runtime_events_unsupported` 或等价的明确原因。
- [x] 当订阅不可用、订阅失败或事件批次非法时，系统回退到 snapshot polling，并记录可诊断的 `fallback_reason`。
- [x] 事件归属校验覆盖 server、session、workspace、pane、agent、provider、runtime generation 和 seq；不匹配或旧 seq 不得覆盖当前状态。
- [x] Herdr `done` 与 `unknown` 的运行时语义被保留；`done` 不直接关闭业务 job，`unknown` 不降级为 idle。
- [x] 既有 snapshot polling 兜底行为保持可回归，失败时仍记录 unknown 与 failure reason。
- [x] 局部门禁覆盖 events 优先、polling 兜底、generation/seq 去重和运行时事实不替代业务判定。

**Validation:**

- `pytest -q test/test_herdr_runtime_contracts.py test/test_herdr_snapshot_polling.py`
- `pytest -q test/test_herdr_snapshot_polling.py::test_herdr_runtime_events_polling_falls_back_when_event_batch_is_invalid`

**Evidence:** 事件订阅入口已按 `snapshot seed -> event drain` 工作；events unsupported、断开和非法批次均显式回退 snapshot polling 并持久化 `source`/`fallback_reason`；projector 保留 `done`/`unknown` 运行时语义并按 generation/seq/归属字段丢弃旧事件或外部事件。
