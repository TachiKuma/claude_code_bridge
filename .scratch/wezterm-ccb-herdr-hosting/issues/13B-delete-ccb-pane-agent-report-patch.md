# 13B：删除 CCB 主动补 Herdr Agent 身份路径

**What to build：** 在 13A 证明 Herdr `agent_id` 权威稳定后，删除 CCB 侧主动补 Herdr Agent 身份的旧
路径。目标是让 CCB 消费 Herdr agent identity，而不是反向写入通用运行时身份。

**Blocked by：** 13A（Herdr agent_id 权威确认）

**Status:** blocked-by-13A

**Evidence to inspect：** `lib/platforms/windows/herdr/lifecycle_bridge.py`、
`lib/platforms/windows/herdr/backend.py`、`lib/platforms/windows/herdr/runtime/client.py`、
`lib/platforms/windows/herdr/runtime/cli.py`

- [ ] 删除或停用 CCB 主动 `report_pane_agent` 写入身份的正常路径
- [ ] `release_pane_agent` 仅保留 Herdr 要求的 teardown/兼容路径
- [ ] 删除前有 characterization test 证明旧行为
- [ ] 删除后 runtime binding 仍包含 pane/agent/provider/generation 归属
- [ ] 无稳定 `agent_id` 时不允许删除

**Validation：**

- `pytest test/test_herdr_runtime_contracts.py test/test_v2_project_namespace_state.py`

**Audit（2026-08-24）：** 13A 仍阻塞（Herdr `agent_id` 权威未在实机验证），本节点不执行
删除；保持 blocked-by-13A。

