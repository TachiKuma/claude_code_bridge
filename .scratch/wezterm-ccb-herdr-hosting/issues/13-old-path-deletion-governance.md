# 13：旧路径删除与治理收口（Phase 5，contract）

**What to build：** contract 步骤：删除只为旧边界存在的复杂度。候选：`CCB_HERDR_CAPABILITY_REPORT`
正常启动路径、bootstrap 的 capability probe 与临时文件写入、宽 CLI 操作白名单（仅保留诊断/兼容
fallback）、backend_resolver 面向低层 operation 的 capability 组合判断、tmux_runtime 中由 CCB
主动创建 Herdr Agent 身份的补丁（前提是 Herdr 已能在 runtime ensure/agent start 稳定返回
`agent_id`）。实现时按删除项拆为子任务，逐项删除。

**Blocked by：** 09（manifest 提交路径）、11（合并读模型）、12（生命周期下放）

**Status:** ready-for-agent

- [ ] 删除 `CCB_HERDR_CAPABILITY_REPORT` 正常启动路径
- [ ] 删除 bootstrap capability probe 与临时文件写入
- [ ] 收窄宽 CLI 操作白名单，仅保留诊断/兼容 fallback
- [ ] 移除 backend_resolver 低层 capability 组合判断
- [ ] 移除 tmux_runtime 中 CCB 主动建 Herdr Agent 身份的补丁（Herdr 稳定返回 agent_id 后）
- [ ] 每处删除前均有等价 characterization test 与 Windows live validation
- [ ] `archi .` 可重跑时，治理分数与 Herdr/CLI runtime hotspot 继续改善
