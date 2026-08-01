---
doc_type: feature-design-review
feature: 2026-07-25-windows-rmux-pane-identity-layout-parity
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f9869-2064-7273-82b8-108434a0d258"
reviewed: 2026-07-25
round: 2
---

# windows-rmux-pane-identity-layout-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-brainstorm.md`
- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Related docs: `.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-acceptance.md`, `.codestable/features/2026-07-20-ccbd-rmux-namespace-lifecycle/ccbd-rmux-namespace-lifecycle-acceptance.md`
- Code facts checked: `lib/terminal_runtime/rmux_backend_runtime/targets.py`, `lib/terminal_runtime/rmux_backend_runtime/panes.py`, `lib/ccbd/services/project_namespace_runtime/backend.py`, `test/test_v2_project_namespace_backend.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f9869-2064-7273-82b8-108434a0d258`
- Raw output: round 1 reported one blocking, two important, one nit, one suggestion, plus residual risks；round 2 reported no blocking/important and `verdict: passed`。
- Merge policy: 已逐条核验，并把成立 finding 合并；round 2 确认 FDR-001 到 FDR-005 已关闭。
- Gate effect: independent review completed，允许本地合并为 passed。

## 2. Design Summary

- Goal: 以 identity evidence + contract first 方式验证 Windows/rmux pane identity/layout parity，不默认重写 layout authority 或 canonicalization。
- Key contracts: `pane-identity-layout-report.json` 细粒度 snapshots、`BindingRecoveryCase`、conflict diagnostics；`windows-rmux-ux-parity-evidence.json` roadmap §4.1 汇总 evidence。
- Steps: 7 步，风险热点是 exact/id alias source 归因、binding recovery 字段完整性、identity conflict fail closed、live GUI lane 与 headless fixture 的边界。
- Checks: 9 条，覆盖 brainstorm admission、baseline reuse、snapshot fields、exact-first、ambiguous alias/conflict fail closed、reattach_reprojection 边界和 scope guard。
- Baseline / validation: 复用 `rmux-backend-core`、`ccbd-rmux-namespace-lifecycle` accepted baseline，以及 existing project namespace adapter canonicalization tests。

## 3. Findings

### blocking

- [x] FDR-001 `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-design.md#2.1` `binding_recovery` schema 过浅，无法承载 expected/observed/source/diagnostics 契约。
  - Evidence: round 1 design 中 `PaneIdentityLayoutReport.binding_recovery` 只是场景到 verdict 的浅映射，但 design/checklist 同时要求 split、respawn、reattach 场景说明 expected agent、expected pane、observed pane、source 和 diagnostics。
  - Impact: implementation 即使生成合法 JSON，也无法证明 agent-pane binding 是否真的恢复，acceptance 不可证伪。
  - Expected fix scope: 新增 `BindingRecoveryCase` 并把 `binding_recovery` 改成 case list 或 keyed case object；同步 checklist S4 与 AC matrix。
  - Closure: design §2.1 已新增 `BindingRecoveryCase`，包含 `scenario`、`expected_agent`、`expected_pane`、`observed_pane`、`canonicalization_source`、`verdict`、`diagnostics_ref`、`residual_risk_ref`；`PaneIdentityLayoutReport.binding_recovery` 已改为 `list[BindingRecoveryCase]`；checklist S4 已同步。

### important

- [x] FDR-002 `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md#4.4` / `#4.6` `reattach` 边界没有定义清楚。
  - Evidence: roadmap §4.4 要求 split/respawn/reattach 后 snapshot 重新关联 agent 与 pane，roadmap §4.6 又把 terminal closed、crash recovery 放到 lifecycle/recovery UX；round 1 design 未把两者边界完全收紧。
  - Impact: implementation 容易把 lifecycle attach/reconnect 做深，或反过来只用 fixture 伪造 reattach，导致与后续 lifecycle feature 责任重叠或验收失真。
  - Closure: design §0 新增 `reattach binding reprojection`，§1、§2.2、AC-006、coverage matrix 和 checklist S4 均限定为非 crash、已有 namespace/layout/runtime state 的重新读取与绑定重投影；terminal closed、provider/rmux daemon crash 和 reconnect UX 明确留给 lifecycle feature。

- [x] FDR-003 `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md#4.1` UX parity evidence 的完整 schema 校验没有落到明确字段级契约。
  - Evidence: roadmap §4.1 要求 `WindowsRmuxUxParityEvidence` 必含 `schema_version`、`host_kind`、`terminal_host`、`backend_impl`、`control_plane`、`parity_dimension`、`evidence_status`、`failure_class`、`artifacts`、`residual_risks`；round 1 design 主要强调 `parity_dimension=pane_identity_layout`。
  - Impact: implementation 可能只校验 dimension，遗漏 native Windows / WezTerm / ccbd 固定值或 partial/blocked/failed 的 residual/failure 规则。
  - Closure: design §2.1 已增加 UX evidence projection 表，逐字段声明固定值、允许值和 status/failure_class 组合规则；checklist S6 exit_signal 已同步完整字段。

### nit

- [x] FDR-004 `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-design.md#2.1` `canonicalization_source` 未说明 `display-message` 分类规则。
  - Evidence: `targets.py::canonical_pane_id()` 和 `backend.py::_canonical_mux_pane_id()` 都有 `display-message` fallback，但 enum 只有 `exact_pane_id/index_alias/layout_state/runtime_authority`。
  - Closure: design §2.1 已说明 `display-message` 是解析机制，不单独作为 source；解析结果按 exact pane id、index alias、layout_state 或 runtime_authority 归类。

- [x] FDR-006 `.codestable/features/2026-07-25-windows-rmux-pane-identity-layout-parity/windows-rmux-pane-identity-layout-parity-design.md#2.2` / checklist S4 少量文案仍泛称 `reattach`。
  - Evidence: round 2 reviewer 发现 flowchart 和 checklist action 中仍有少量 `reattach` 泛称。
  - Closure: 已将 flowchart 节点、设计摘要和 checklist S4 action 收敛为 `reattach_reprojection`；这是非契约性措辞修正。

### suggestion

- [x] FDR-005 `PaneIdentityLayoutReport.baseline_refs` 可以约束成 artifact path map。
  - Evidence: design S1 要 baseline refs 指向 acceptance、code、tests；roadmap §4.1 的 `artifacts` 是 `dict[str, str]`。
  - Closure: design §2.1 已将 `baseline_refs` 改为 `dict[str, str]`。

### learning

- 代码事实支持 design 的主要风险判断：`targets.py::canonical_pane_id()` 与 `project_namespace_runtime/backend.py::_canonical_mux_pane_id()` 均存在 rmux canonicalization 路径；`panes.py::split_pane()` 有 split alias resolver；`test/test_v2_project_namespace_backend.py` 已覆盖 index alias、exact-first、无 window/session fallback 和 respawn replacement baseline。

### praise

- 范围控制健康：design 明确 evidence-first，不默认重写 layout authority，也不把 crash recovery、GUI mouse/focus/capture 混入本 item。
- checklist step 拆分清晰：baseline、schema、canonicalization matrix、binding recovery、conflict diagnostics、UX evidence、drift closure 分开，便于 implementation 和验收逐项恢复。

## 4. User Review Focus

- 用户需要重点拍板：接受本 item 只覆盖 pane identity/layout evidence 与非 crash `reattach_reprojection`，不在此处实现 lifecycle crash recovery 或 reconnect UX。
- implement 需要重点遵守：先交付 machine-readable identity report 和 UX evidence JSON；只有 drift 被证实时才做最小 production canonicalization 收敛。
- code review / QA / acceptance 需要重点复核：ambiguous alias 与 identity conflict 必须 fail closed；headless fixture 不得冒充 native Windows + WezTerm GUI pass。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-001 到 AC-009 覆盖 exact-first、alias fallback、binding recovery、conflict diagnostics、UX evidence 与 scope guard；round 2 reviewer confirmed | none |
| DoD Contract | pass | E | DOD-IMPL-001 到 DOD-IMPL-006 与 CMD-003/CMD-004/CMD-005/CMD-006 已覆盖核心 evidence、baseline 与 scope guard | none |
| Steps and checks traceability | pass | E | checklist S1-S7 与 9 条 checks 可追溯到 design §2/§3；S4/S6 已按 findings 修订 | none |
| Roadmap contract compliance | pass | E/C | design §2.1 投影 roadmap §4.1，design §4 投影 roadmap §4.4；items.yaml brainstorm gate 已 admitted | none |
| Module interface design | pass | C | design 明确 evidence-only，production helper 仅 drift 证实时最小收敛；代码事实显示现有 canonicalization seam 存在 | none |
| Validation and artifacts | pass | E/C | Required Artifacts、feature evidence path、JSON validator、existing baseline tests 已列出；新增 test 入口仍待 implementation 创建 | implementation 创建真实测试并覆盖 schema |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- native Windows + WezTerm GUI evidence 仍依赖真实前台环境；acceptance 必须核验 `host_kind=native_windows` 与 `terminal_host=wezterm` 未被 headless transcript 伪装。
- `test/test_windows_rmux_pane_identity_layout_parity.py` 当前是计划新增入口；implementation 必须创建真实测试并校验 `BindingRecoveryCase`、完整 UX evidence projection、conflict diagnostics 和 residual risk 规则。
- 如果 implementation evidence 证明 `targets.py` 与 namespace adapter canonicalization 存在真实 drift，只允许在本 feature 内做最小收敛；更大的 layout authority 统一应另走后续 refactor 或 lifecycle feature。

## 7. Verdict

- Status: passed
- Next: epic child batch 可返回 `cs-epic`，继续下一个 child feature gate。

## 8. Focused Closure

- Closed findings: FDR-001, FDR-002, FDR-003, FDR-004, FDR-005, FDR-006
- Attributed delta: design/checklist 的 evidence schema、reattach_reprojection 边界、UX evidence projection、canonicalization_source 分类、baseline_refs 类型和少量文案收敛。
- Verification: checklist YAML validate passed；items YAML validate passed；round 2 independent reviewer reported no blocking/important and `verdict: passed`。
- Classification: FDR-001 到 FDR-005 的修订改变 evidence contract，已通过第二轮完整独立复审；FDR-006 是非契约文案收敛。最终 verdict 为 passed。
