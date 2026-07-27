---
doc_type: feature-design-review
feature: 2026-07-25-windows-rmux-lifecycle-recovery-ux-parity
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fa114-4b0d-7d62-88f7-87fc273d2a92"
reviewed: 2026-07-27
round: 2
---

# windows-rmux-lifecycle-recovery-ux-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-25-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-brainstorm.md`
- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Related docs:
  - `.codestable/features/2026-07-20-rmux-supervision-recovery/rmux-supervision-recovery-acceptance.md`
  - `.codestable/features/2026-07-20-ccbd-rmux-namespace-lifecycle/ccbd-rmux-namespace-lifecycle-acceptance.md`
  - `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-acceptance.md`
  - `.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-acceptance.md`
- Code facts checked: `scripts/rmux_windows_validation_matrix.py` cleanup parsing/report logic；existing attach/supervision/diagnostics/validation test entry names from design and repository facts.

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019fa10b-cd57-7ba1-9a39-4b770c89fb07` round 1；`019fa114-4b0d-7d62-88f7-87fc273d2a92` round 2。
- Raw output: round 1 returned `changes-requested` with one blocking and four important findings. Round 2 reported no blocking, confirmed FDR-001 to FDR-005 basically closed, and raised one important ambiguity plus one nit.
- Merge policy: 主 agent 已逐条核验 reviewer 结论；round 2 important/nit 通过 focused closure 修正，不改变范围、架构边界或 roadmap 公共契约。
- Gate effect: none

## 2. Design Summary

- Goal: 以 UX continuity first 验证 Windows/rmux/WezTerm lifecycle recovery parity；crash 场景以可证伪 diagnostics 和 degraded evidence 为通过基础。
- Key contracts: `LifecycleRecoveryReport.cases[]` 是 roadmap §4.6 单 case record 的 superset；supportability 唯一消费 `evidence/windows-rmux-ux-parity-evidence.json`，细粒度 lifecycle report 只作为 artifact ref。
- Steps: 8 个 scenario 级步骤，覆盖 baseline/schema、reattach、terminal_closed、kill_cleanup、pane_crash、provider_crash、rmux_daemon_crash、UX evidence/scope guard。
- Checks: 12 条，覆盖 brainstorm admission、roadmap §4.1/§4.6、residue schema、terminal_host 常量、scenario diagnostics、scope guard。
- Baseline / validation: 复用 accepted supervision recovery、namespace lifecycle、full-chain smoke、validation matrix；新增 focused lifecycle parity validator 和 UX evidence JSON。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- FDR2-003 implementation / QA 阶段必须把 `CMD-008` 展开为真实 touched Python module 列表；design 阶段保留动态占位可接受。

### learning

- supportability 的唯一公开输入必须保持 roadmap §4.1 `WindowsRmuxUxParityEvidence`；feature 私有 detail report 只能通过 `artifacts` 引用。
- cleanup residue 字段应复用 validation matrix 语义，避免各 report builder 自行发明 endpoint/token/session/process residue 名称。

### praise

- 设计已经把 terminal closed 与 kill cleanup 分开，避免把关闭 GUI 宿主误算为 project cleanup。
- shared daemon degraded-only 与 owned/project daemon recovery 边界清晰，延续了 `rmux-supervision-recovery` accepted safety model。

## 4. User Review Focus

- 用户需要重点拍板：接受 crash 场景第一版可以用可证伪 degraded/partial 通过，而不是要求所有 crash 自动恢复。
- implement 需要重点遵守：supportability 只消费 UX evidence JSON；`LifecycleRecoveryReport` 不作为下游公开接口；terminal_host 固定 `"wezterm"`。
- code review / QA / acceptance 需要重点复核：GUI lane 不可用时不能 full pass；`CMD-008` 必须展开为真实 touched modules；residue report 必须覆盖 endpoint/token/rmux namespace/session/provider process/provider job/owned process。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 将 AC-001..AC-009 映射到 S1..S8，scenario 粒度已拆开 | none |
| DoD Contract | pass | E | design §3.4 与 checklist `dod.commands` 覆盖 schema、UX evidence、continuity、crash/degraded、residue、scope guard | implementation 展开 CMD-008 |
| Steps and checks traceability | pass | E | checklist checks 使用 `design §... / AC... / DOD...` 精确 source | none |
| Roadmap contract compliance | pass | E/C | roadmap §4.1 只由 UX evidence JSON 暴露给 supportability；§4.6 case record 由 superset cases[] 校验 | none |
| Module interface design | pass | C | seam 位于 transcript importer / report builder / diagnostics projection；production recovery 仅证据触发最小修复 | none |
| Validation and artifacts | pass | E/C | required artifacts、scenario validator、diagnostics/residue tests、baseline tests 和 manual runbook/blocked 规则已列出 | QA 防止 skipped/headless 被写成 pass |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- `test/test_windows_rmux_lifecycle_recovery_parity.py` 和 feature `evidence/` 目录当前仍是 implementation 产物；QA 必须验证真实 artifact refs，不得只靠 Markdown runbook。
- native Windows + WezTerm GUI lane 依赖 live/manual transcript；缺证据时只能 `partial|blocked`。
- `CMD-008` 是 design-time 动态命令占位；implementation/QA 必须替换成真实 touched Python module 列表。

## 7. Verdict

- Status: passed
- Next: epic child batch 可返回 `cs-epic`，继续下一个 child feature gate。

## 8. Focused Closure

- Closed findings: FDR-001, FDR-002, FDR-003, FDR-004, FDR-005, FDR2-001, FDR2-002
- Attributed delta:
  - FDR-001：design §1/§2.1/§4 收紧 supportability 唯一公开输入为 `evidence/windows-rmux-ux-parity-evidence.json`。
  - FDR-002：design §2.1 新增 `LifecycleCleanupResidue`，字段覆盖 endpoint/token/rmux namespace/session/provider process/provider job/owned process/retained reason。
  - FDR-003：design §2.1/§4 明确 `cases[]` 是 roadmap §4.6 record superset。
  - FDR-004：design §2.4 和 checklist steps 拆为 scenario 级恢复。
  - FDR-005：CMD-008 改为 touched Python modules，并要求 implementation 展开实际模块。
  - FDR2-001：design §2.1 和 checklist 明确 `terminal_host` 始终为 `"wezterm"`，GUI 不可用只通过 `failure_class=wezterm_gui_unavailable`、`evidence_status=partial|blocked` 和 residual risks 表达。
  - FDR2-002：`supportability_notes` 改名为 `lifecycle_notes`，避免私有 report 字段被误读为 supportability 输入。
- Verification:
  - `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-checklist.yaml" --yaml-only` passed。
  - `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml" --yaml-only` passed。
- Classification: FDR2 focused closure 只消除字段歧义并将私有字段改名以匹配已审定的 roadmap 公共契约；没有新增行为、范围、架构边界、验收场景或下游公开接口。
