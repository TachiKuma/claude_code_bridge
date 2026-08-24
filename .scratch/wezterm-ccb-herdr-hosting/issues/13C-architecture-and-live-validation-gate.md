# 13C：旧路径删除门禁与架构证据

**What to build：** 把 Phase 5 的删除治理变成可重跑门禁：每个删除项必须有 characterization test、
Windows live validation、以及最新架构图或 `archi .` 结果。该节点不直接删除业务代码，只建立验收
证据清单和检查脚本/文档。

**Blocked by：** 13A、13B；可与 12C 的 live validation 准备并行

**Status:** ready-for-agent-after-13A

**Evidence to inspect：** `archify-ccbd-runtime.v4.json`、
`archify-ccbd-runtime.v4.html`、`plans/architecture-optimization/*`、
`.scratch/wezterm-ccb-herdr-hosting/spec.md`

- [ ] 记录优化前 `E:\claude_code_bridge` 与优化后当前目录的关键差异
- [ ] 为每个删除项列出 characterization test、live validation 和 rollback condition
- [ ] Windows live validation 覆盖：无 WezTerm GUI、有 mux、多项目 attach、mobile gateway 脱敏
- [ ] `archi .` 或 archify 产物可重跑，Herdr/CLI runtime hotspot 不恶化
- [ ] 删除门禁失败时父工单保持 blocked，不允许 contract step

**Validation：**

- `pytest test/test_herdr_runtime_contracts.py test/test_ccbd_project_view.py test/test_mobile_gateway_service.py`

**Audit（2026-08-24）：** 删除门禁依赖 13A（Herdr `agent_id` 权威）与 Windows live validation
环境；按 issue 自身门禁规则，门禁未通过时父工单保持 blocked，本节点暂不落地删除验收清单
的执行，仅记录状态。

