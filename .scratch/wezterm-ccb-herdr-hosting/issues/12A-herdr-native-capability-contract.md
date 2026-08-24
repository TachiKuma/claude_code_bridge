# 12A：Herdr 原生生命周期能力契约

**What to build：** 固化 Herdr 上游原生能力探测：`runtime.ensure`、runtime event、稳定 `agent_id`。
本节点不切换生命周期实现，只把能力可用/不可用/版本不匹配的判断变成结构化 contract，让后续下放
不会靠猜测。

**Blocked by：** 09（manifest 提交路径）

**Status:** ready-for-agent

**Evidence to inspect：** `lib/platforms/windows/herdr/runtime/capabilities.py`、
`lib/platforms/windows/herdr/runtime/client.py`、`lib/platforms/windows/herdr/backend.py`、
`test/test_herdr_backend_client.py`

- [ ] capability 里能表达 `runtime.ensure`、`runtime.events`、`agent_id_authority`
- [ ] 上游缺能力时保持当前兼容层，且 reason 可观测
- [ ] 明确选择 Herdr 但 schema/能力不匹配时 fail-closed
- [ ] capability 证据来自握手/server info，不回退临时 capability 文件
- [ ] 测试覆盖 supported/unsupported/schema mismatch 三类路径

**Validation：**

- `pytest test/test_herdr_backend_client.py test/test_herdr_runtime_contracts.py`

