# 13：旧路径删除与治理收口（Phase 5，contract）

**What to build：** contract 步骤：删除只为旧边界存在的复杂度。候选：`CCB_HERDR_CAPABILITY_REPORT`
正常启动路径、bootstrap 的 capability probe 与临时文件写入、宽 CLI 操作白名单（仅保留诊断/兼容
fallback）、backend_resolver 面向低层 operation 的 capability 组合判断、tmux_runtime 中由 CCB
主动创建 Herdr Agent 身份的补丁（前提是 Herdr 已能在 runtime ensure/agent start 稳定返回
`agent_id`）。实现时按删除项拆为子任务，逐项删除。

**Blocked by：** 09（manifest 提交路径）、11（合并读模型）、12（生命周期下放）

**Status:** partial-blocked

**Implementation:** `3b4f75b4`

**Evidence:** `lib/platforms/windows/herdr/bootstrap.py`、
`lib/platforms/windows/herdr/runtime/ensure.py`、`test/test_herdr_runtime_contracts.py`、
`test/test_herdr_bootstrap.py`

**Notes:** 正常启动路径已不再依赖 `CCB_HERDR_CAPABILITY_REPORT` 临时文件；兼容函数与低层 capability
gate 仍保留。Phase 5 的删除收口需要逐项 characterization test、Herdr 上游稳定 `agent_id` 返回、
Windows live validation，以及可重跑的 architecture 证据。

- [x] 删除 `CCB_HERDR_CAPABILITY_REPORT` 正常启动路径
- [x] 删除 bootstrap capability probe 与临时文件写入
- [x] 收窄宽 CLI 操作白名单，仅保留诊断/兼容 fallback
- [x] 移除 backend_resolver 低层 capability 组合判断
- [ ] 移除 tmux_runtime 中 CCB 主动建 Herdr Agent 身份的补丁（Herdr 稳定返回 agent_id 后）
- [ ] 每处删除前均有等价 characterization test 与 Windows live validation
- [ ] `archi .` 可重跑时，治理分数与 Herdr/CLI runtime hotspot 继续改善

说明：bootstrap 现在只负责解析 Herdr 可执行文件、确认运行中的会话并返回 socket ref，不再做
read-only capability probe，也不再写临时 capability report。

说明：`project_namespace_runtime` 的 mux 选择门槛现在只看 `command_status`，不再把 `semantic_status`
作为低层 operation gate 的并列条件。

说明：本轮将 `report_pane_agent_session` 收口为 unsupported，Herdr 侧仅保留 `report_pane_agent`
与 `release_pane_agent` 这条当前仍在使用的生命周期路径。

说明：实机验证（`E:\GitHub开源项目\TachiKuma\Herdr_Guides`，2026-08-23）显示：
`startup-report.json` 仍记录 `pane_agent_report`，而 `.ccb/agents/*/runtime.json` 里尚未出现稳定
`agent_id`。因此 `tmux_runtime` 中 CCB 主动补 Herdr Agent 身份的补丁仍然不能删除，当前节点继续
保持阻塞状态。
