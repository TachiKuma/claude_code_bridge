---
doc_type: feature-design-review
feature: 2026-07-19-tmux-backend-contract-adapter
status: passed
review_state: passed
review_reason: ""
reviewer_id: ""
reviewed: 2026-07-19
round: 2
---

# tmux-backend-contract-adapter feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-19-tmux-backend-contract-adapter/tmux-backend-contract-adapter-design.md`
- Checklist: `.codestable/features/2026-07-19-tmux-backend-contract-adapter/tmux-backend-contract-adapter-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: `.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-design.md`、`.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-checklist.yaml`、`.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-design-review.md`
- Code facts checked: `lib/terminal_runtime/tmux_backend.py`、`lib/terminal_runtime/tmux_readiness.py`、`lib/terminal_runtime/backend_types.py`、`lib/terminal_runtime/layouts_models.py`、`lib/terminal_runtime/layouts_root.py`、`lib/terminal_runtime/tmux_backend_panes.py`、`lib/terminal_runtime/tmux_backend_control.py`、`lib/terminal_runtime/tmux_backend_logs.py`、`lib/ccbd/services/project_namespace_runtime/backend.py`、`lib/cli/services/runtime_launch_runtime/tmux_panes.py`、`lib/ccbd/services/project_namespace_runtime/agent_window_reflow.py`、`lib/cli/services/start_foreground.py`、`lib/ccbd/handlers/project_clear.py`、`lib/provider_backends/codex/launcher_runtime/bridge.py`、`lib/provider_backends/codex/session_runtime/live_identity.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: subagent `019f7b25-91df-7cf1-b18c-3fcec2167a1c`、subagent `019f7b2b-f908-76e3-a3ee-d0a18e0439f5`
- Raw output: round 1 建议 `changes-requested`，无 blocking，提出 4 important 和 1 suggestion；主 agent 修订范围边界、namespace ref 映射、错误映射覆盖和 implementation admission gate 后，round 2 确认 4 important 全部关闭，无 blocking / important / nit。
- Merge policy: 主 agent 已逐条本地核验 reviewer findings；可证实问题已修入 design/checklist。round 2 的 CMD-004 文案 suggestion 已作为非契约 focused closure 处理。
- Gate effect: independent review completed and merge verified；允许交回 `cs-epic` child design batch。

## 2. Design Summary

- Goal: 将现有 `TmuxBackend` 适配到 `MuxBackend` 契约，保持 Linux、macOS、WSL tmux 行为不漂移，并为后续 RmuxBackend 提供对照 adapter。
- Key contracts: `TmuxMuxBackendAdapter` 包装旧 `TmuxBackend`；`_tmux_run` 只留在 adapter 内部；refs 含稳定 `namespace_id` 和 socket ipc evidence；tmux failures 归一为 `MuxCommandError`。
- Steps: 8 步，覆盖 implementation admission、adapter shell、error mapping、namespace lifecycle、window layout、pane/io/presentation/logging、代表性调用方迁移、回归与泄漏 guard。
- Checks: 15 项，覆盖 parent contract admission、ref 映射、错误分类、旧 public method 兼容、代表路径迁移、inventory-only 未迁移路径和不越界项。
- Baseline / validation: checklist YAML、items YAML、adapter unit tests、layout/reflow/runtime launch/project clear 抽样回归、parent contract import smoke。

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

- adapter feature 需要把 `_tmux_run` 泄漏面拆成“本轮代表性迁移”和“inventory-only 后续迁移”；否则既容易扩大范围，也会让 roadmap 收口不可核对。
- `MuxNamespaceRef` 在 tmux 下不能只 shape 对齐；`namespace_id`、`ipc_kind`、`ipc_ref` 的稳定来源会影响后续 Rmux 替换、多 namespace 隔离和 diagnostics。
- epic child batch 的 design-review passed 不等于 implementation-ready；当前 feature 明确要求 parent `mux-backend-contract` item `done` 和 contract/fake/error 类型可导入后才能实现。

### praise

- 设计选择包装式 `TmuxMuxBackendAdapter`，没有把新协议硬塞进现有 `TmuxBackend` 类，边界符合单一职责。
- 旧 `TmuxBackend` public methods 兼容和 `_tmux_run` 不进入 public protocol 都写成了验收项。
- 错误映射同时要求 normalized category 与原始 evidence，兼顾调用层语义和 diagnostics。

## 4. User Review Focus

- 用户需要重点拍板：接受“代表性迁移 + inventory-only 未迁移路径”的范围边界；不要求本 feature 一次性清空所有 `_tmux_run`。
- implement 需要重点遵守：先执行 S0/CMD-006 admission；`namespace_id` / `ipc_ref` 规则不得随机；permission、unsupported、subprocess exception 不得裸抛。
- code review / QA / acceptance 需要重点复核：未迁移路径 inventory 是否完整，尤其 foreground attach、provider-specific runtime、project clear、materialize topology、move/remove patch agents、pane log helpers。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 到 AC-008，并映射 S0 到 S7 | none |
| DoD Contract | pass | E | design §3.4 覆盖 design / implementation / review / QA / acceptance DoD，并新增 DOD-IMPL-006 admission | none |
| Steps and checks traceability | pass | E | checklist steps/checks 可追溯到 design §2.4、§3.1、§3.3、§3.4 | none |
| Roadmap contract compliance | pass | E/C | design 消费 roadmap §4.1 的 refs、capabilities、`MuxCommandError`、`reflow_window` 和 no `_tmux_run` public seam | none |
| Module interface design | pass | E/C | wrapper adapter、stable refs、error mapping、scope boundary 均有明确 interface 设计检查 | none |
| Validation and artifacts | pass | E | CMD-001 到 CMD-006 覆盖 YAML、adapter tests、tmux regression 和 parent contract import smoke | none |

Summary: E=6, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- 当前仓库事实下 implementation admission 仍不会通过：parent `mux-backend-contract` item 仍为 `in-progress`，production `mux_backend_contract.py` / `fake_mux_backend.py` 尚不存在。这是预期 hard gate，不是 design 缺陷；实现入口必须先执行 S0/CMD-006。
- 剩余 `_tmux_run` inventory 范围较大；acceptance 必须核对 inventory 是否点名所有未迁移路径，避免后续 Rmux 路线继续被 tmux argv 泄漏牵制。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child design batch；本 feature design 保持 `draft`，等待所有子 feature design-review passed 后统一 owner 确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004、SG-001
- Attributed delta: `.codestable/features/2026-07-19-tmux-backend-contract-adapter/tmux-backend-contract-adapter-design.md` 与 `.codestable/features/2026-07-19-tmux-backend-contract-adapter/tmux-backend-contract-adapter-checklist.yaml`
- Verification: round 2 independent reviewer `019f7b2b-f908-76e3-a3ee-d0a18e0439f5` 确认 4 个 important 全部关闭；主 agent 将 CMD-004 说明收紧为 project clear 是 inventory-only 未迁移路径的不漂移守卫；YAML 校验通过。
- Classification: SG-001 只改命令说明文字，不改变行为、公开契约、架构边界、验收语义或范围；无需第三轮完整复审。
