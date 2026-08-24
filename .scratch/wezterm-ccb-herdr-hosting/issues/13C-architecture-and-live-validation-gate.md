# 13C：旧路径删除门禁与架构证据

**What to build：** 把 Phase 5 的删除治理变成可重跑门禁：每个删除项必须有 characterization test、
Windows live validation、以及最新架构图或 `archi .` 结果。该节点不直接删除业务代码，只建立验收
证据清单和检查脚本/文档。

**Blocked by：** 13A、13B；可与 12C 的 live validation 准备并行

**Status:** ready-for-agent-after-13A

**Evidence to inspect：** `archify-ccbd-runtime.v4.json`、
`archify-ccbd-runtime.v4.html`、`plans/architecture-optimization/*`、
`.scratch/wezterm-ccb-herdr-hosting/spec.md`

- [x] 记录优化前 `E:\claude_code_bridge` 与优化后当前目录的关键差异（见门禁文档）
- [x] 为每个删除项列出 characterization test、live validation 和 rollback condition
- [ ] Windows live validation 覆盖：无 WezTerm GUI、有 mux、多项目 attach、mobile gateway 脱敏（门禁已声明所需 artifact，实机执行待环境）
- [ ] `archi .` 或 archify 产物可重跑，Herdr/CLI runtime hotspot 不恶化（门禁已声明 `archi-hotspot-baseline.json`，实机记录待环境）
- [x] 删除门禁失败时父工单保持 blocked，不允许 contract step

**Validation：**

- `pytest test/test_herdr_runtime_contracts.py test/test_ccbd_project_view.py test/test_mobile_gateway_service.py`

**Audit（2026-08-24）：** 删除门禁依赖 13A（Herdr `agent_id` 权威）与 Windows live validation
环境；按 issue 自身门禁规则，门禁未通过时父工单保持 blocked，本节点暂不落地删除验收清单
的执行，仅记录状态。

**Implementation（2026-08-24）：** 门禁脚手架已落地——`scripts/phase5_deletion_gate.py`（可重跑，
读 `DELETION_ITEMS` 逐项校验 characterization test 存在性与 live validation 证据，fail-closed 时
退出码 2）、`test/test_phase5_deletion_gate.py`（6 项外部行为测试，含证据齐备放行、缺证据/裸
`passed` 无 evidence/未通过均 blocked、CLI 非零退出）、
`plans/architecture-optimization/topics/phase5-deletion-gate.md`（删除验收清单 + 优化前后差异 +
rollback 条件 + fail-closed 规则）。当前对真实仓库运行门禁**如实报 blocked**（缺 live validation
证据），符合预期。脚手架不删除任何业务代码；13A/13B 删除动作与 12C 仍保持上游阻塞，需实机
证据以 `passed=true` + 非空 `evidence` 落盘于 `live-validation/` 后方可放行。已跑：门禁 6 项测试
通过；13C 声明的 characterization 测试集
（`test_herdr_runtime_contracts`/`test_ccbd_project_view`/`test_mobile_gateway_service`/
`test_v2_project_namespace_state`/`test_herdr_backend_client`）`504 passed`；`compileall`、
`git diff --check` 通过。

