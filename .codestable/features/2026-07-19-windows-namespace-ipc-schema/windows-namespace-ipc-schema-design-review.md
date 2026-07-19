---
doc_type: feature-design-review
feature: 2026-07-19-windows-namespace-ipc-schema
status: passed
review_state: passed
review_reason: ""
reviewer_id: ""
reviewed: 2026-07-19
round: 4
---

# windows-namespace-ipc-schema feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-19-windows-namespace-ipc-schema/windows-namespace-ipc-schema-design.md`
- Checklist: `.codestable/features/2026-07-19-windows-namespace-ipc-schema/windows-namespace-ipc-schema-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: `.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-design.md`、`.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-design-review.md`、`.codestable/features/2026-07-19-tmux-backend-contract-adapter/tmux-backend-contract-adapter-design.md`、`.codestable/features/2026-07-19-tmux-backend-contract-adapter/tmux-backend-contract-adapter-design-review.md`
- Code facts checked: `lib/project/ids.py`、`lib/storage/paths_ccbd.py`、`lib/ccbd/services/project_namespace_state_runtime/models.py`、`lib/ccbd/services/project_namespace_runtime/records.py`、`lib/ccbd/handlers/ping_runtime/payloads.py`、`lib/ccbd/handlers/ping_runtime/summaries.py`、`lib/cli/services/doctor_runtime/ccbd.py`、`lib/cli/render_runtime/ops_views_doctor.py`、`lib/cli/services/start_foreground.py`、`lib/ccbd/services/project_namespace_pane.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: subagent `019f7b56-7569-7cd0-b28f-b3ea5f8006d0`
- Raw output: round 4 focused closure 判定 `passed`，findings 为空；仅保留实现层 reserved-key 过滤与不同 sentinel 测试的 residual risk。
- Merge policy: 主 agent 已逐条本地核验 reviewer findings，并把 `namespace_id == project_id`、reserved-key 过滤和 no-clobber sentinel 要求写入 design/checklist。
- Gate effect: independent review completed and merge verified；允许交回 `cs-epic` child design batch。

## 2. Design Summary

- Goal: 为 ccbd namespace state、ping/doctor payload 和 foreground attach 输入引入 mux-neutral canonical schema，并保留 tmux 迁移期兼容层。
- Key contracts: canonical schema 包含 `namespace_id`、`namespace_backend_family`、`namespace_backend_impl`、`namespace_session_name`、`namespace_ipc_kind`、`namespace_ipc_ref`；`namespace_id == project_id`；plain `tmux_socket_path` / `tmux_session_name` 只留 state/event record，不进入 ping/doctor 顶层。
- Steps: 5 步，覆盖 schema contract、state/event roundtrip、ping/doctor payload、foreground attach input compatibility、compatibility regression。
- Checks: 14 项，覆盖 canonical/alias、`MuxNamespaceRef` projection、reserved-key 过滤、顶层 no-clobber、foreground attach 保持行为不变、旧 fixture 兼容。
- Baseline / validation: checklist YAML、items YAML、state/schema tests、namespace ref projection tests、ping/doctor no-clobber tests、foreground compatibility tests。

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

- `namespace_id` 必须收敛成单一身份规则，否则 `MuxNamespaceRef` projection 无法稳定验收。
- plain `tmux_socket_path` 与 ccbd 顶层 `tmux_socket_path` 语义不同，必须通过 reserved-key 过滤和不同 sentinel 测试守住边界。
- `namespace_tmux_*` 兼容层只适合 ping/doctor 顶层 namespace 语义，不能再让 plain `tmux_*` 参与 payload 合并。

### praise

- 设计把 canonical schema、legacy alias 和 no-clobber 边界拆得足够清楚。
- `MuxNamespaceRef` 投影关系明确，后续 Rmux / diagnostics 不需要再猜字段来源。
- foreground attach 保持 tmux 行为不变，没有越界到后续 `MuxBackend.attach_namespace()`。

## 4. User Review Focus

- 用户需要重点拍板：`namespace_id == project_id` 作为唯一规则，以及 plain `tmux_*` 不进入 ping/doctor 顶层的边界。
- implement 需要重点遵守：reserved-key 过滤必须显式落地；no-clobber 测试不能复用同值 sentinel。
- code review / QA / acceptance 需要重点复核：`MuxNamespaceRef` projection、顶层 `tmux_socket_path` 不被覆盖、foreground attach canonical-first/alias-fallback。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 到 AC-007 | none |
| DoD Contract | pass | E | design §3.4 覆盖 design / implementation / review / QA / acceptance DoD | none |
| Steps and checks traceability | pass | E | checklist steps/checks 可追溯到 design §2.4、§3.1、§3.3、§3.4 | none |
| Roadmap contract compliance | pass | E/C | design 对齐 roadmap §4.3，且收敛 `namespace_id == project_id` 与 reserved-key 过滤 | none |
| Module interface design | pass | E/C | canonical schema、alias、projection、no-clobber 边界清楚 | none |
| Validation and artifacts | pass | E | CMD-001/CMD-002 YAML 校验通过，且有明确后续 pytest 验证命令 | none |

Summary: E=6, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- 实现层仍需把 reserved-key 过滤和不同 sentinel no-clobber 测试真正落到代码里。
- roadmap §4.3 仍是示意性 JSON；后续评审要继续防止误读 `namespace_id` 为 session-derived 变体。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child design batch；本 feature design 保持 `draft`，等待所有子 feature design-review passed 后统一 owner 确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002
- Attributed delta: `.codestable/features/2026-07-19-windows-namespace-ipc-schema/windows-namespace-ipc-schema-design.md`、`.codestable/features/2026-07-19-windows-namespace-ipc-schema/windows-namespace-ipc-schema-checklist.yaml`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`
- Verification: final independent reviewer `019f7b56-7569-7cd0-b28f-b3ea5f8006d0` 确认 findings 为空；YAML 校验通过；主 agent 已将 `namespace_id == project_id`、reserved-key 过滤和 no-clobber sentinel 要求固化进 design/checklist。
- Classification: 本次 closure 仅收紧 schema / payload 约束，不改变行为、公开契约、架构边界或验收语义。
