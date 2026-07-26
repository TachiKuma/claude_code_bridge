---
doc_type: feature-design-review
feature: 2026-07-26-windows-rmux-lifecycle-recovery-ux-parity
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f9e47-6efd-7b20-8f0b-6b8882c082e8"
reviewed: 2026-07-26
round: 2
---

# windows-rmux-lifecycle-recovery-ux-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-design.md`
- Checklist: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-brainstorm.md`
- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Related docs: `.codestable/features/2026-07-20-rmux-supervision-recovery/rmux-supervision-recovery-acceptance.md`, `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-acceptance.md`, `.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-acceptance.md`, parent design-review for output capture and pane identity/layout.
- Code facts checked: `scripts/rmux_windows_validation_matrix.py`, `lib/ccbd/supervision/store.py`, `lib/ccbd/supervision/recovery_events.py`, existing supervision / diagnostics tests referenced by CMD-005.

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f9e47-6efd-7b20-8f0b-6b8882c082e8`
- Raw output: follow-up reviewer reported `blocking / important: none` and confirmed the four requested closure points.
- Merge policy: 已逐条核验 reviewer 结论，并用 design / checklist / roadmap / parent review 事实确认。
- Gate effect: independent review completed，允许本地合并为 passed。

## 2. Design Summary

- Goal: 以 UX lifecycle evidence first 方式验证 Windows/rmux/WezTerm lifecycle recovery parity，不默认重写 supervision/recovery。
- Key contracts: `lifecycle-recovery-ux-report.json` 细粒度 case report；`windows-rmux-ux-parity-evidence.json` roadmap §4.1 汇总 evidence；每个 case 必含 next action、evidence source、failure class 和 residual risks。
- Steps: 7 步，风险热点是 parent readiness、terminal close 与 kill 边界、crash/degraded diagnostics、feature-local builder/validator 边界。
- Checks: 12 条，覆盖 case 字段、failure class 组合、GUI full pass evidence source、parent readiness、scope guard 和 validation matrix 边界。
- Baseline / validation: 复用 supervision recovery、full-chain smoke、validation matrix baseline；新增 `test/test_windows_rmux_lifecycle_recovery_ux_parity.py` 作为 lifecycle report 和 UX evidence validator 入口。

## 3. Findings

### blocking

- none

### important

- [x] FDR-001 `.codestable/features/2026-07-26-windows-rmux-lifecycle-recovery-ux-parity/windows-rmux-lifecycle-recovery-ux-parity-design.md#1` parent identity/capture readiness 没有进入 checklist / DoD 机器检查。
  - Evidence: parent roadmap item 依赖 `windows-rmux-pane-identity-layout-parity` 与 `windows-rmux-output-capture-parity`；两者 design-review passed，但尚无 acceptance evidence。
  - Impact: implementation 可能把依赖 identity/capture 的 live lifecycle lane 误写成 full pass。
  - Closure: design §1、§2.2、AC-001、AC-009、DOD-IMPL-008 和 checklist S1/check 已要求机器读取 parent readiness；未 accepted 时相关 live lane 只能 partial/blocked。

- [x] FDR-002 `WindowsRmuxLifecycleUxReportCase` 字段契约不一致，缺少 `next_action` / `evidence_source` / `failure_class` / `residual_risks` 的统一口径。
  - Evidence: roadmap §4.1 要求 partial/blocked/failed 有 residual/failure detail；lifecycle UX 还要求 degraded diagnostics 和下一步建议。
  - Impact: non-pass case 可能只留下底层 event，用户不可理解，supportability 也无法消费。
  - Closure: design typed dict、字段语义表、自我批判和 checklist checks 已统一必填字段；CMD-003 明确覆盖这些校验。

- [x] FDR-003 示例里 `verdict=partial` 但 `failure_class=none`，语义冲突。
  - Evidence: roadmap §4.1 规定 `partial` 必须写 residual risk，且 `blocked` 必须有具体 failure_class；本 design 进一步规定 `partial|failed|blocked` 不允许 `failure_class=none`。
  - Impact: 会让 validator 和 reviewer 无法区分真实通过与 degraded pass。
  - Closure: terminal_closed 示例已改为 `failure_class=wezterm_gui_unavailable`，并保留 residual risk。

- [x] FDR-004 builder / validator 挂载点不够明确，可能继续把 lifecycle 逻辑塞进 `scripts/rmux_windows_validation_matrix.py`。
  - Evidence: validation matrix 已承担 matrix manifest、parser、summary、scope guard；本 feature 需要新的 lifecycle UX schema 和 pass/fail 语义。
  - Impact: 会污染既有 matrix pass semantics，也降低 feature 可卸载性。
  - Closure: design §2.3 明确 `scripts/windows_rmux_lifecycle_recovery_ux_report.py` 为 feature-local builder / validator；`scripts/rmux_windows_validation_matrix.py` 只作为输入 source 或既有 smoke，不承载 lifecycle UX schema / pass 判定。checklist 也加入对应硬检查。

### nit

- none

### suggestion

- none

### learning

- Parent feature 的 design-review 均已 passed，但当前没有 acceptance artifact；本 feature 的 readiness gate 不能只看 design-review passed，implementation / QA 仍要按 accepted 状态 fail closed。
- lifecycle UX evidence 应作为 supportability 的机器输入，不应由自由 Markdown、headless fixture 或 validation matrix row 单独推导 supported 状态。

### praise

- 范围控制清晰：不默认重写 supervision/recovery，不重做 full-chain smoke，不改 provider parser / support tier / installer / npm。
- 证据分层健康：细粒度 lifecycle report 与 roadmap §4.1 UX evidence JSON 分离，supportability 可消费后者，review/QA 可追溯前者。

## 4. User Review Focus

- 用户需要重点拍板：接受 parent identity/capture 未 accepted 时 lifecycle full pass 必须 partial/blocked，即使 schema/headless lanes 可以先推进。
- implement 需要重点遵守：先交付 feature-local builder/validator、JSON report、UX evidence JSON 和 parent readiness evidence；没有 broken path evidence 不做 production supervision/recovery 重构。
- code review / QA / acceptance 需要重点复核：headless evidence 不得冒充 native Windows + WezTerm GUI full pass；`terminal_closed` 不得等同 `ccb kill`；provider failure 不得污染 rmux/system failure。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-001 到 AC-010 覆盖 baseline、六个 lifecycle scenario、valid_non_success、UX evidence 和 scope guard | none |
| DoD Contract | pass | E | DOD-IMPL-001 到 DOD-IMPL-009 覆盖 JSON、case coverage、residue、diagnostics、parent readiness 和 builder scope | none |
| Steps and checks traceability | pass | E | checklist steps/checks 已映射 design §2.4、§3.1、§3.4；YAML validate passed | none |
| Roadmap contract compliance | pass | E/C | design 明确遵守 roadmap §4.1 和 §4.6；parent items.yaml 指向当前 feature 且 brainstorm admitted | none |
| Module interface design | pass | E/C | feature-local builder/validator 挂载点明确；production runtime 仅 broken path evidence 触发最小修改 | none |
| Validation and artifacts | pass | E | CMD-001/CMD-002 已通过；CMD-003 到 CMD-006 作为 implementation/QA 必跑命令列入 DoD | implementation 创建真实测试和 evidence artifacts |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- 实现阶段必须把 parent readiness 的解析路径固定为 roadmap item + feature artifacts，不能让 test helper 自己猜 acceptance 来源。
- native Windows + WezTerm foreground evidence 仍依赖真实 GUI 环境；缺失时必须 partial/blocked，不得用 fixture/headless transcript 写 full pass。
- `scripts/windows_rmux_lifecycle_recovery_ux_report.py` 当前是计划新增入口；implementation 必须创建真实 builder/validator 和对应测试，不能只做浅层 JSON parse。

## 7. Verdict

- Status: passed
- Next: epic child batch 可返回 `cs-epic`，继续下一个 child feature gate。

## 8. Focused Closure

- Closed findings: FDR-001, FDR-002, FDR-003, FDR-004
- Attributed delta: design/checklist 的 parent readiness gate、case required fields、failure_class 组合规则、feature-local builder/validator 挂载边界。
- Verification: checklist YAML validate passed；roadmap items YAML validate passed；design frontmatter validate passed；round 2 independent reviewer reported no blocking/important。
- Classification: 上述修订改变验收语义和挂载边界，已通过第二轮完整独立复审；最终 verdict 为 passed。
