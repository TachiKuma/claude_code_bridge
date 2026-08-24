# 13A：Herdr agent_id 权威确认

**What to build：** 在删除 CCB 主动补 Herdr Agent 身份前，先证明 Herdr 能在 runtime ensure/agent start
后稳定返回 `agent_id`，并写入 binding/runtime.json 或等价 runtime fact。本节点只做确认和契约测试，
不删除旧路径。

**Blocked by：** 12A（agent_id_authority capability）、Windows live validation 环境

**Status:** blocked-upstream

**Evidence to inspect：** `lib/platforms/windows/herdr/runtime/contracts.py`、
`lib/platforms/windows/herdr/runtime/client.py`、`.ccb/agents/*/runtime.json`、
`test/test_herdr_runtime_contracts.py`

- [ ] Herdr snapshot/binding 中每个 pane-agent 都有稳定 `agent_id`
- [ ] reconnect/restore 后同一 pane-agent 的 `agent_id` 不漂移
- [ ] `startup-report.json` 不再是唯一 pane_agent_report 证据
- [ ] 缺 `agent_id` 时 deletion gate fail-closed
- [ ] 实机记录附到 issue 或 validation artifact

**Validation：**

- `pytest test/test_herdr_runtime_contracts.py`

