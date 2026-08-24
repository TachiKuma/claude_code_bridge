# 13A：Herdr agent_id 权威确认

**What to build：** 在删除 CCB 主动补 Herdr Agent 身份前，先证明 Herdr 能在 runtime ensure/agent start
后稳定返回 `agent_id`，并写入 binding/runtime.json 或等价 runtime fact。本节点只做确认和契约测试，
不删除旧路径。

**Blocked by：** 12A（agent_id_authority capability）、Windows live validation 环境

**Status:** wontfix（源码验证：Herdr 无 agent_id 权威，见 ADR 0001 修订）

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

**Audit（2026-08-24）：** 12A 已收口（capability 可表达 `agent_id_authority`），但本节点
的验收依赖 Herdr 在真实环境中稳定返回 `agent_id` 并写入 binding/runtime.json，以及 Windows
live validation；当前会话无该实机环境，保持 blocked-upstream。

**Live probe（2026-08-24）：** 已在实机连上运行中的 Herdr 0.8.2（protocol 20），直接查其原生 API
（`herdr api schema --json` / `api snapshot` / `agent list`）。结论：全 schema 中 `agent_id` 出现
**0 次**；`AgentInfo` 身份=`pane_id`+`agent`+`name`，Herdr 不铸造也不回传稳定 `agent_id`；agent 归属
权威方向是 **CCB→Herdr**（`pane.report_agent` push，`pane.clear_agent_authority` 清除）。因此 13A
最低要求在 Herdr 0.8.2 下**无法达成**，属上游 API 缺能力（非缺环境）。证据：
`plans/architecture-optimization/live-validation/agent-id-authority.json`（`passed:false`）与
`plans/architecture-optimization/topics/herdr-0.8.2-native-capability-probe.md`。deletion gate 据此
持续 fail-closed，保持 blocked-upstream。

