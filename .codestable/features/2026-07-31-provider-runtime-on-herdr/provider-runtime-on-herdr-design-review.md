---
doc_type: feature-design-review
feature: 2026-07-31-provider-runtime-on-herdr
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb6f3-1e1d-7e42-a2af-ddf585f7e0ce
reviewed: 2026-07-31
round: 2
---

# provider-runtime-on-herdr feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-design.md`
- Checklist: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design.md`、`.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design-review.md`
- Code facts checked: `lib/cli/services/runtime_launch_runtime/ensure.py`、`tmux_runtime.py`、`tmux_panes.py`、`session_files.py`、`lib/provider_runtime/session_payload.py`、`lib/terminal_runtime/backend_selection.py`、`lib/provider_backends/pane_log_support/lifecycle.py`、`lifecycle_common.py`、`lib/provider_core/contracts.py`、`lib/provider_core/manifests.py`、`lib/ccbd/services/dispatcher_runtime/polling_service.py`、`cancellation.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fb6ea-1eeb-79e3-8af9-dfa8efa15add` changes-requested；round 2 `019fb6f3-1e1d-7e42-a2af-ddf585f7e0ce` changes-requested，剩余 finding 通过 focused closure 关闭。
- Raw output: round 1 提出 3 个 important：upstream implementation/acceptance admission 缺稳定核验、`completion_source` 与现有 `CompletionSourceKind` 不完全对齐、checklist steps 缺稳定 id。round 2 确认后两项关闭，只剩 CMD-003 未机械核验 required artifacts / evidence refs。
- Merge policy: 已逐条核验 reviewer finding 与 design/checklist/roadmap/code 事实；只合并有仓库事实支撑的结论。
- Gate effect: independent review completed；最后一项是命令映射窄修，focused closure 后允许定稿 `passed`。

## 2. Design Summary

- Goal: 让 CCB 托管 provider 在 Herdr pane 中启动、ask、pend、completion、cancellation 和 provider pane restart surface 工作，同时保持 CCB 对 provider state、auth、completion 和 job terminal verdict 的权威。
- Key contracts: Herdr 只提供 PaneIO/PanePresentation/PaneLogging terminal primitive；`ProviderRuntimeBackendRef` 记录 backend-neutral refs、managed_home、roadmap 粗粒度 `completion_source` 与精确 `completion_source_kind`；Herdr agent state 只能 diagnostics-only。
- Steps: 7 个 step，覆盖 upstream admission、backend-neutral launch、session payload/resolver、provider session lifecycle、ask/pend/completion authority、cancel/restart evidence、scope/regression/manual evidence。
- Checks: 12 个 check 均追溯到 AC / DOD / S1-S7。
- Baseline / validation: CMD-001/CMD-002 YAML gate；CMD-003 upstream acceptance + precondition focused tests；CMD-004 至 CMD-008 runtime/provider/dispatcher focused tests；CMD-009/CMD-010 scope 和 completion authority guard；CMD-011 Native Windows x64 real provider dry run。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- 可在实现阶段把 CMD-003 的长内联 admission 检查沉淀为 `.codestable` 只读脚本，以降低 YAML quoting 和正则维护成本。当前 design 阶段不创建新工具脚本。

### learning

- 对 roadmap 粗粒度 `completion_source` 与代码精确 `CompletionSourceKind` 分层保存，可以同时服务 support/evidence 报告和 provider-native completion 语义，避免把 session snapshot / structured result 混成普通 log。
- Provider runtime on Herdr 的关键不是“pane 能启动”，而是 CCB provider authority、completion gate、cancel/job state 与 backend terminal primitive 的边界清晰。

### praise

- 设计明确禁止 Herdr agent state 单独产生 `completed` verdict，并把该约束落到 design、checklist 和 CMD-010。
- 挂载点集中在 runtime launch、session payload、backend resolver、pane lifecycle 和 dispatcher/cancel seam，没有把 provider-specific launcher 内部实现列成平铺改动清单。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只把 provider runtime 接入 Herdr pane；bounded recovery owner、Mobile/Config UI、doctor/support、release/public matrix 仍留给后续 child。
- implement 需要重点遵守：S1 admission 必须检查 upstream roadmap done + acceptance passed + required artifacts/evidence refs；缺失时写 dependency-blocked，不得用 design-review passed 替代。
- code review / QA / acceptance 需要重点复核：Herdr session 不得回退 tmux factory；Herdr agent state 不得产出 completed；`completion_source_kind` 必须保留现有 provider manifest 精确语义。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 至 AC-013，并映射 S1-S7、证据类型和命令 / 动作。 | none |
| DoD Contract | pass | E | design §3.4 覆盖 design、implementation、review、QA、acceptance DoD、validation commands 和 Required Artifacts。 | implementation 落地 upstream admission report。 |
| Steps and checks traceability | pass | E | checklist steps 已有 `id: S1..S7`；checks source 引用 AC / DOD / Sx；YAML 校验通过。 | none |
| Roadmap contract compliance | pass | E | roadmap §4.5 要求 provider HOME/auth/session binding/completion 归 CCB，Herdr agent state 不得单独完成；design 正面落实。 | none |
| Module interface design | pass | C | 现有 runtime launch、session payload、backend resolver、pane log lifecycle 和 dispatcher completion/cancel 代码事实支撑 backend-neutral seam。 | code review 复核 tmux-oriented fallback 是否全部受 capability gate 限制。 |
| Validation and artifacts | pass | E | CMD-003 已机械检查 upstream roadmap done、acceptance passed 和 artifact/evidence refs；CMD-009/CMD-010 覆盖 scope 与 completion authority guard。 | CMD-003 可后续沉淀为脚本。 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 当前前置 child 在 roadmap items 中仍是 `in-progress`，且尚无 acceptance 文件；这是 implementation admission 的预期 block，不阻塞 design review。
- 代码事实仍显示 runtime launch 和 pane lifecycle 明显 tmux-oriented；implementation/code review 必须重点复核 `ensure_agent_runtime()`、`get_backend_for_session()`、pane log lifecycle 的 Herdr path 不回退 tmux。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop；本 child design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: round 1 FDR-001、FDR-002、FDR-003；round 2 PRH-FDR-001。
- Attributed delta: 增加 S1 upstream acceptance artifact/evidence refs gate；增加 `completion_source_kind` / `provider_native_ref_kind` 并明确 CompletionSourceKind 映射；checklist steps 增加 `id: S1..S7`；CMD-003 增加 `artifact_marker` / `ref_marker` 机械核验；CMD-005 标注 includes-new-test-files。
- Verification: checklist YAML 与 roadmap items YAML 均通过；本地扫描确认 S1、`completion_source_kind`、artifact/evidence refs guard 均已出现在 checklist。
- Classification: 本轮 closure 只收紧 admission 命令与追踪映射，未改变 feature 行为、公开契约、架构边界、验收范围或不做范围；因此不启动第三轮完整独立复审。
