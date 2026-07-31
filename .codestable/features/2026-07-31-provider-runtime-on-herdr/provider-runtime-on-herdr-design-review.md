---
doc_type: feature-design-review
feature: 2026-07-31-provider-runtime-on-herdr
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb92a-dd3f-79b3-baeb-c738cf51ca1e
reviewed: 2026-08-01
round: 3
---

# provider-runtime-on-herdr feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-design.md`
- Checklist: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-checklist.yaml`
- Intent / brainstorm: none
- Requirement: `.codestable/requirements/native-windows-ccb-via-herdr.md`
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Roadmap items: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Related docs: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design.md`、`.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design-review.md`
- Code facts checked: `lib/provider_core/registry_runtime/builtin_backends.py`、`lib/cli/services/runtime_launch_runtime/ensure.py`、`lib/cli/services/runtime_launch_runtime/tmux_runtime.py`、`lib/cli/services/runtime_launch_runtime/tmux_panes.py`、`lib/cli/services/runtime_launch_runtime/session_files.py`、`lib/provider_runtime/session_payload.py`、`lib/terminal_runtime/backend_selection.py`、`lib/provider_backends/pane_log_support/lifecycle.py`、`lib/provider_backends/pane_log_support/lifecycle_common.py`、`lib/provider_core/contracts.py`、`lib/provider_core/manifests.py`、`lib/ccbd/services/dispatcher_runtime/polling_service.py`、`lib/ccbd/services/dispatcher_runtime/cancellation.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fb6ea-1eeb-79e3-8af9-dfa8efa15add` changes-requested；round 2 `019fb6f3-1e1d-7e42-a2af-ddf585f7e0ce` changes-requested；round 3 `019fb922-2d6c-7cd0-860a-de54f6fdcd3b` changes-requested；round 4 `019fb92a-dd3f-79b3-baeb-c738cf51ca1e` passed。
- Raw output: round 3 提出 3 个 important：all-public-provider gate 缺可审计 provider 清单冻结、Herdr agent state completion guard 不覆盖 untracked 新文件、Herdr socket schema/client scope guard 偏文本脆弱。round 4 复审确认无 blocking / important，verdict `passed`。
- Merge policy: 已逐条核验 reviewer finding 与 design/checklist/roadmap/code 事实；只合并有仓库事实支撑的结论。
- Gate effect: independent review completed；本地合并后 design-review gate passed。

## 2. Design Summary

- Goal: 让 CCB 托管的所有公开 provider 在 Herdr pane 中启动、ask、pend、completion、cancel，并保持 provider state、auth、completion、queue/cancellation 的 authority 归 CCB。
- Key contracts: Native Windows x64 Herdr route 缺 capability/evidence 时 fail closed；Herdr 只提供 PaneIO/PanePresentation/PaneLogging terminal primitive；`ProviderRuntimeBackendRef` 记录 backend-neutral refs、managed_home、`completion_source` 与精确 `completion_source_kind`；Herdr agent state 只能 diagnostics-only。
- Steps: 7 个 step，覆盖 upstream admission、backend-neutral launch、session payload/resolver、provider session lifecycle、ask/pend/completion authority、cancel/restart evidence、scope/regression/manual evidence。
- Checks: 12 个 check 均追溯到 AC / DOD / S1-S7；S7 明确冻结 provider catalog `public_providers` snapshot。
- Baseline / validation: CMD-003 fail-closed admission、CMD-009 scope/content guard、CMD-010 completion authority guard、CMD-011 all-public-provider Native Windows x64 manual transcript matrix 共同覆盖硬门槛。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- 可在实现阶段把 CMD-003/CMD-009/CMD-010 的长内联检查沉淀为 `.codestable` 只读脚本，以降低 YAML quoting 和正则维护成本。当前 design 阶段不创建新工具脚本。

### learning

- provider runtime on Herdr 的关键不是 pane 能启动，而是 CCB provider authority、completion gate、cancel/job state 与 backend terminal primitive 的边界清晰。
- 对 roadmap 粗粒度 `completion_source` 与代码精确 `CompletionSourceKind` 分层保存，可以同时服务 support/evidence 报告和 provider-native completion 语义。
- all-provider supported 证据必须从当前 provider catalog 冻结 snapshot；只验证 Codex/Claude/Gemini/Opencode 不能代表所有公开 provider。

### praise

- 设计明确禁止 Herdr agent state 单独产生 `completed` verdict，并把该约束落到 design、checklist 和 CMD-010。
- S1 admission 明确要求 upstream roadmap `done` + acceptance `passed` + artifact/evidence refs，正确阻止用 design-review passed 代替实现验收。
- CMD-009/CMD-010 已在 Windows PowerShell 下实测可执行，并覆盖 untracked implementation files 的关键越界风险。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只把 provider runtime 接入 Herdr pane；bounded recovery owner、Mobile/Config UI、doctor/support、package/release/update/installer/public matrix 仍留给后续 child。
- implement 需要重点遵守：实现前必须满足 upstream implementation/acceptance admission；缺 Herdr capability/evidence 时直接 dependency-blocked，不得 fallback 到 tmux/rmux success。
- code review / QA / acceptance 需要重点复核：Herdr session 不得回退 tmux factory；Herdr agent state 不得产出 completed；`completion_source_kind` 必须保留现有 provider manifest 精确语义；acceptance 必须冻结 `public_providers` snapshot 并逐 provider 给出 pass/blocked row。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E/C | design §3.3 覆盖 AC-001 至 AC-013；AC-012 要求 catalog snapshot + all-provider transcript/blocked evidence。 | implementation / acceptance 执行 snapshot 和 transcript matrix。 |
| DoD Contract | pass | E | design §3.4 覆盖 design、implementation、review、QA、acceptance DoD、validation commands 和 Required Artifacts。 | CMD-003 admission 预期在前置 child 未完成时 fail-closed。 |
| Steps and checks traceability | pass | E | checklist steps `S1..S7` 与 checks source 可追溯；S7 覆盖 scope/regression/manual evidence。 | none |
| Roadmap contract compliance | pass | E/C | roadmap 要求 Native Windows Herdr fail-closed、all-public-provider workflow、`public_providers` snapshot；design/checklist 已对齐。 | acceptance 时不能沿用旧 supported evidence。 |
| Module interface design | pass | C | runtime launch、session payload、backend resolver、pane lifecycle、dispatcher/cancel 代码事实支撑 backend-neutral seam。 | code review 复核 tmux-oriented fallback 是否全部受 capability gate 限制。 |
| Validation and artifacts | pass | E/C | CMD-001/CMD-002/YAML 校验通过；CMD-009/CMD-010 在 PowerShell 下实测通过；CMD-011 明确 all-provider manual gate。 | 长内联命令后续可沉淀脚本。 |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- `PRH-DEP-ADMISSION`：当前前置 child 在 roadmap items 中仍是 `in-progress`，且尚无 acceptance passed/artifact evidence；这是 implementation admission 的预期 block，不阻塞 design review。
- 代码事实仍显示 runtime launch 和 pane lifecycle 明显 tmux-oriented；implementation/code review 必须重点复核 `ensure_agent_runtime()`、`get_backend_for_session()`、pane log lifecycle 的 Herdr path 不回退 tmux。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop；本 child design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: round 1 `FDR-001`、`FDR-002`、`FDR-003`；round 2 `PRH-FDR-001`；round 3 `PRH-FDR-001`、`PRH-FDR-002`、`PRH-FDR-003`。
- Attributed delta: design/checklist 增加 requirement frontmatter；把单 provider dry run 收紧为 all-public-provider Herdr pane workflow；要求 acceptance 冻结 `public_providers` snapshot；把 package/release/update/installer 和 Herdr socket schema/client owner 纳入 scope guard；CMD-010 扩展到 untracked `lib/test` 新文件并修复 Windows quoting。
- Verification: `validate-yaml.py` 校验 design、checklist、roadmap items 均通过；CMD-009/CMD-010 从 checklist 读取后在 PowerShell 下执行通过；round 4 independent reviewer confirmed `passed`。
- Classification: 本轮 closure 收紧 acceptance/guard 语义以对齐已确认 requirement/roadmap 硬门槛，没有扩大本 feature 实现范围；因此以完整独立复审结果作为最终 gate。
