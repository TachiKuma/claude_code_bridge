# 13B：删除 CCB 主动补 Herdr Agent 身份路径

**What to build：** 在 13A 证明 Herdr `agent_id` 权威稳定后，删除 CCB 侧主动补 Herdr Agent 身份的旧
路径。目标是让 CCB 消费 Herdr agent identity，而不是反向写入通用运行时身份。

**Blocked by：** 13A（Herdr agent_id 权威确认）

**Status:** wontfix（源码验证：report_pane_agent 是对等权威来源、非历史补丁，删除有害，见 ADR 0001 修订）

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

**Live probe（2026-08-24）：** 实机查 Herdr 0.8.2 原生 API 证实 `pane.report_agent` 是 Herdr 认可的
**唯一 agent 归属 API**（CCB→Herdr push 身份），Herdr 无 `agent_id` 回写。故删除 CCB 主动补身份
路径不仅不达标，删除还会**直接破坏 agent 状态归属**。保持 blocked-by-13A；见
`topics/herdr-0.8.2-native-capability-probe.md`。

