---
doc_type: feature-design-review
feature: 2026-07-25-windows-rmux-output-capture-parity
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f9858-46af-72f2-bba2-499d803ee7be"
reviewed: 2026-07-25
round: 2
---

# windows-rmux-output-capture-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-brainstorm.md`
- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Related docs: `.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-design.md`, `.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-acceptance.md`
- Code facts checked: `lib/terminal_runtime/rmux_backend_runtime/io.py`, `lib/terminal_runtime/rmux_backend.py`, `test/test_rmux_send_capture_logging.py`, `test/test_rmux_completion_capture_fixtures.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f9858-46af-72f2-bba2-499d803ee7be`
- Raw output: round 1 reported one blocking, two important, one nit, one suggestion, plus residual risks；round 2 reported no blocking/important and `verdict: passed`。
- Merge policy: 已逐条核验，并把成立 finding 合并；round 2 确认 FDR-001 到 FDR-005 已关闭。
- Gate effect: independent review completed，允许本地合并为 passed。

## 2. Design Summary

- Goal: 以 evidence-first 方式验证 Windows/rmux output capture parity，区分 machine capture、provider completion、user-visible history。
- Key contracts: `output-capture-parity-report.json` 细粒度 case report；`windows-rmux-ux-parity-evidence.json` roadmap §4.1 汇总 evidence。
- Steps: 7 步，风险热点是 normalized artifact 可追溯、JSON validator 可执行、parent dependency 未 accepted 时 GUI lane 归因。
- Checks: 9 条，覆盖 brainstorm admission、baseline reuse、三条 evidence lane、documented delta、provider parser guard、parent dependency gate。
- Baseline / validation: 复用 `rmux-send-capture-logging` accepted baseline，同时新增 `test/test_windows_rmux_output_capture_parity_evidence.py` 作为 JSON evidence validator 命令入口。

## 3. Findings

### blocking

- [x] FDR-001 `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md#4.3` normalized 输出 artifact ref 没有进入 feature schema。
  - Evidence: roadmap §4.3 要求原始输出和 normalized 输出都保留 artifact ref；round 1 design 只有 `raw_artifact` 与 `normalized_output_sha256`。
  - Impact: implementation 和 acceptance 只能看到 normalized hash，无法重放 normalized 文本，delta 归因不可审计。
  - Expected fix scope: 给 case 增加 `normalized_artifact`，并要求 schema test 校验 raw 与 normalized artifact refs。
  - Closure: design §2.1 已新增 `normalized_artifact`；design §2.2、§2.4、§3.1、§3.4 和 checklist S2/S3/CMD-003 已要求 raw/normalized artifacts 都可解析。

### important

- [x] FDR-002 `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-design.md#3.4` JSON evidence validator 的命令入口不够可执行。
  - Evidence: round 1 commands 只有 YAML 校验、历史 pytest、py_compile、import guard；没有明确命令覆盖两个 JSON evidence。
  - Impact: 机器可读契约可能退化为人工检查。
  - Closure: design §3.4 与 checklist dod 已新增 CMD-003 `python -m pytest -q test/test_windows_rmux_output_capture_parity_evidence.py`，覆盖 schema、enum、artifact refs、raw/normalized artifacts、residual risk 和 parent dependency gate。

- [x] FDR-003 `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml` parent dependency 状态未进入 checklist gate。
  - Evidence: item depends_on `windows-rmux-wezterm-native-interaction-parity`，该依赖当前仍是 `in-progress`；round 1 checklist 未要求 implementation 前检查依赖。
  - Impact: GUI/user-visible history 证据可能在前置交互未 accepted 时误记为 pass。
  - Closure: design §1、AC-008、Coverage Matrix、DOD-IMPL-007 和 checklist check 已规定 parent 未 accepted 时只能推进 headless machine/provider lanes，GUI lane 必须 blocked/partial。

### nit

- [x] FDR-004 `RmuxCaptureParityCase` 的“向后兼容扩展”表述过开放。
  - Closure: design §1 已改为“本 design 固定的 `RmuxCaptureParityCase`”，不再使用开放式扩展表述。

### suggestion

- [x] FDR-005 provider projection 可以包含 `artifact_ref` / `detector_ref` / `failure_class`。
  - Closure: design §2.1 已新增 `ProviderProjectionEvidence`，包含 `status`、`detector_ref`、`artifact_ref`、`failure_class`、`explanation`。

### learning

- `RmuxCaptureResult` 已在 `lib/terminal_runtime/rmux_backend_runtime/io.py` 存在，`capture_pane()` 经 `RmuxBackend` 暴露；当前 design 的 baseline reuse 判断有代码事实支撑。

### praise

- 需求边界清晰：machine capture、provider completion、user-visible history 三条 lane 不互相替代。
- 挂载点集中在 feature `evidence/`，production IO 层保持 evidence-first，不默认重写。

## 4. User Review Focus

- 用户需要重点拍板：接受 documented delta 作为 parity evidence 的通过方式，但差异必须有 artifact、hash、classification 和 residual risk。
- implement 需要重点遵守：不重写 capture IO；先交付 JSON report、UX evidence JSON、provider projection 和 GUI supporting runbook。
- code review / QA / acceptance 需要重点复核：headless transcript 不得冒充 native Windows + WezTerm GUI pass；旧 accepted tests 不能替代新 JSON validator。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-008 已补入 design/checklist，round 2 reviewer confirmed | none |
| DoD Contract | pass | E | CMD-003 已补 JSON validator 命令入口，round 2 reviewer confirmed | none |
| Steps and checks traceability | pass | E | normalized artifact、provider projection、dependency gate 已补 checklist，round 2 reviewer confirmed | none |
| Roadmap contract compliance | pass | E/C | roadmap §4.1/§4.3 已显式映射，round 2 reviewer confirmed | none |
| Module interface design | pass | C | design 明确 evidence-only，无 production adapter | none |
| Validation and artifacts | pass | E | raw/normalized artifact refs 已补，CMD-003 gate 已明确 | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- native Windows + WezTerm GUI evidence 仍依赖真实前台环境；acceptance 必须重点核验 `host_kind=native_windows` 与 `terminal_host=wezterm` 未被 headless transcript 伪装。
- CMD-003 在 design/checklist 中已明确覆盖两个 JSON、enum、artifact refs、raw/normalized artifacts、residual risk 和 parent dependency gate；实现阶段必须创建真实测试并覆盖这些断言，不能只做浅层 JSON parse。
- parent `windows-rmux-wezterm-native-interaction-parity` 当前仍为 `in-progress`；QA/acceptance 必须核验 user-visible history lane 未被写成 pass，除非 parent 已 accepted 且 native GUI evidence 真实存在。

## 7. Verdict

- Status: passed
- Next: epic child batch 可返回 `cs-epic`，继续下一个 child feature gate。

## 8. Focused Closure

- Closed findings: FDR-001, FDR-002, FDR-003, FDR-004, FDR-005
- Attributed delta: 仅修改 design/checklist 的 evidence schema、validator command、dependency gate 与 provider projection 字段。
- Verification: checklist YAML validate passed；items YAML validate passed；round 2 independent reviewer reported no blocking/important and `verdict: passed`。
- Classification: 上述修订改变 evidence contract，已通过第二轮完整独立复审；最终 verdict 为 passed。
