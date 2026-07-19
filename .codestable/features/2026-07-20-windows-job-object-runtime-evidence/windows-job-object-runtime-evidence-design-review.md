---
doc_type: feature-design-review
feature: 2026-07-20-windows-job-object-runtime-evidence
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7c0d-26cd-7d81-831f-86cd1e5a9f6d"
reviewed: 2026-07-20
round: 2
---

# windows-job-object-runtime-evidence feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-windows-job-object-runtime-evidence/windows-job-object-runtime-evidence-design.md`
- Checklist: `.codestable/features/2026-07-20-windows-job-object-runtime-evidence/windows-job-object-runtime-evidence-checklist.yaml`
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: `.codestable/features/2026-07-19-windows-namespace-ipc-schema/windows-namespace-ipc-schema-design.md`、`.codestable/features/2026-07-20-windows-shell-log-builder/windows-shell-log-builder-design.md`、`docs/ccbd-windows-psmux-plan.md`
- Code facts checked: `lib/agents/models_runtime/runtime_runtime/agent.py`、`lib/ccbd/services/provider_runtime_facts.py`、`lib/provider_runtime/helper_manifest.py`、`lib/provider_runtime/helper_cleanup.py`、`lib/provider_runtime/health.py`、`lib/runtime_pid_cleanup/collection.py`、`lib/runtime_pid_cleanup/matching.py`、`lib/runtime_pid_cleanup/termination.py`、`lib/cli/kill_runtime/processes.py`、`lib/ccbd/services/health.py`、`lib/ccbd/system.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: subagent `019f7c0d-26cd-7d81-831f-86cd1e5a9f6d`
- Raw output: previous findings 已 closed；new blocking/important 为 none；verdict passed；delta 属于 focused closure，不需要升级完整复审。
- Merge policy: 主 agent 已按 reviewer findings 修订 CMD-006、owner_pid canonical、process_ref seam 和 runtime_health 挂载点，并通过 YAML / guard 命令复核。
- Gate effect: independent review completed and merge verified；允许交回 `cs-epic` child design batch。

## 2. Design Summary

- Goal: 为 Windows provider runtime 增加 Job Object / process tree evidence 链，并把它接入 runtime authority、health、kill / recovery 和 diagnostics。
- Key contracts: `process_ref` 进入 runtime authority；canonical authority 字段固定为 `process_ref.owner_pid`；`ccbd` 仍是 authority，Job Object 只作为 evidence；`lib/provider_runtime/process_ref.py` 作为唯一 builder + eligibility seam；`runtime_health()` 必须在 pane success 短路前读取 `process_ref`。
- Steps: 6 步，覆盖 contract、probe seam、runtime wiring、kill / recovery gating、diagnostics exposure、regression / guard。
- Checks: 12 项，覆盖 canonical field、seam、health 顺序、ownership gating、legacy compatibility、non-Windows 保持不变。
- Baseline / validation: YAML 校验通过；CMD-006 已修成可执行 fixed-string guard，并在本地命中当前基线红灯。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- Job Object evidence 最好集中成一个本地 seam，否则 health、kill 和 helper cleanup 很容易各自解释同一组字段。

### praise

- `ccbd` authority 与 Job Object evidence 的边界保持得很清楚。
- `pane alive != provider healthy` 已经被放进设计核心，而不是只写在备注里。

## 4. User Review Focus

- 用户需要重点拍板：`process_ref.owner_pid` 作为 canonical authority 字段，`job_owner_pid` 只保留 legacy / diagnostics 语义。
- implement 需要重点遵守：`lib/provider_runtime/process_ref.py` 必须成为唯一 seam；`runtime_health()` 不得被 pane success 提前短路。
- code review / QA / acceptance 需要重点复核：Windows ownership gating、`taskkill /T` 只作为降级 primitive、旧 runtime 记录兼容。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-001 到 AC-008 覆盖 runtime facts、health、kill、cleanup、diagnostics | none |
| DoD Contract | pass | E | DOD-DESIGN / IMPL / REVIEW / QA / ACCEPT 均覆盖 | none |
| Steps and checks traceability | pass | E | checklist sources 已改为 design / AC / DOD 可定位来源 | none |
| Roadmap contract compliance | pass | E/C | canonical `process_ref.owner_pid` 对齐 roadmap §4.3，Job Object 仍是 evidence | none |
| Module interface design | pass | E/C | `provider_runtime/process_ref.py` 作为唯一 seam，depth / locality 收束清楚 | none |
| Validation and artifacts | pass | E | YAML 校验通过，CMD-006 已改为可执行 guard 并命中当前基线红灯 | none |

Summary: E=6, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- 真正的 Windows Job Object attach / kill / stale 行为仍需要后续 Windows 真机 smoke 承接；本次 design 只能证明契约和 gating。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review；本 feature design 保持 `draft`，等待所有子 feature design-review passed 后统一 owner 确认。

## 8. Focused Closure

- Closed findings: CMD-006 命令 quoting、`process_ref.owner_pid` / `job_owner_pid` 命名冲突、health 判定挂载点、process_ref seam 缺失
- Attributed delta: `.codestable/features/2026-07-20-windows-job-object-runtime-evidence/windows-job-object-runtime-evidence-design.md`、`.codestable/features/2026-07-20-windows-job-object-runtime-evidence/windows-job-object-runtime-evidence-checklist.yaml`
- Verification: YAML 校验通过；CMD-006 可执行；subagent `019f7c0d-26cd-7d81-831f-86cd1e5a9f6d` 确认 previous findings 已 closed、new blocking/important none
- Classification: 本次修订只收束契约、seam 与验证守护，不改变 runtime authority 归属或 acceptance 语义
