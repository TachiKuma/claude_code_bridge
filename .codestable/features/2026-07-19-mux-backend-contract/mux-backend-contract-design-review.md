---
doc_type: feature-design-review
feature: 2026-07-19-mux-backend-contract
status: passed
review_state: passed
review_reason: ""
reviewer_id: ""
reviewed: 2026-07-19
round: 2
---

# mux-backend-contract feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-design.md`
- Checklist: `.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-design.md`、`.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-design-review.md`
- Code facts checked: `lib/terminal_runtime/backend_types.py`、`lib/terminal_runtime/layouts_models.py`、`lib/terminal_runtime/tmux_backend.py`、`lib/terminal_runtime/tmux_backend_panes.py`、`lib/terminal_runtime/tmux_backend_control.py`、`lib/ccbd/services/project_namespace_runtime/backend.py`、`lib/cli/services/runtime_launch_runtime/tmux_panes.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: subagent `019f7b10-63a4-7b40-b945-81b22b561987`、subagent `019f7b16-56c8-7021-85dd-4fdd06e11fdf`
- Raw output: round 1 判定 `changes-requested`，包含 2 blocking、1 important、1 nit；主 agent 补齐能力协议、error evidence、`MuxCapabilities`、direction literal 后，round 2 确认前 3 项关闭，仅剩 reflow seam important；主 agent focused closure 增加 `reflow_window()` canonical seam。
- Merge policy: 主 agent 已逐条本地核验 reviewer findings，修订 design/checklist 并保留 closure evidence。
- Gate effect: independent review completed and merge verified；最终 focused closure 只显式化 reflow seam，不扩大范围。

## 2. Design Summary

- Goal: 定义 backend-neutral mux 能力协议、引用类型、错误契约和 fake backend 测试替身。
- Key contracts: 小协议覆盖 namespace lifecycle、window layout/reflow、pane io、presentation/logging、diagnostics；`_tmux_run` 不进入 public protocol。
- Steps: 6 步，覆盖 datatypes、capability protocols、fake backend、compat facade、leakage inventory、tests。
- Checks: 10 项，覆盖 contract 独立性、backend-neutral refs、fake state/event、structured error、capabilities、tmux 兼容和不越界。
- Baseline / validation: checklist YAML、items YAML、contract/fake backend tests、tmux/layout/runtime 抽样回归。

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

- `WindowLayout` 需要把 `reflow_window()` 作为 first-class seam；`select_layout()` 只能是 adapter 可用的低阶 primitive。
- `MuxCommandError` 必须同时保留 normalized category 和原始 command/evidence，才能服务 startup、doctor 和 diagnostics。
- `MuxCapabilities` 需要对齐 roadmap 的 `command_status`、`semantic_status`、`blocking_gaps`，否则 route approval / capability gap 会各自发明 shape。

### praise

- design 明确避免胖 `Protocol`，按能力拆分。
- `_tmux_run` 被列为泄漏 inventory 输入，而不是 public protocol。
- scope 没有越界到 RmuxBackend、provider session payload 或 ccbd transport。

## 4. User Review Focus

- 用户需要重点拍板：接受小协议 + facade 的 contract 方向，以及 fake backend 作为后续实现测试入口。
- implement 需要重点遵守：`reflow_window()` 是 canonical seam；`select_layout()` 只是 adapter primitive；command/evidence 只用于 diagnostics，不是公开 runner。
- code review / QA / acceptance 需要重点复核：fake backend 能覆盖 namespace/window/pane/io/presentation/logging；leakage inventory 足够具体；旧 tmux 行为不漂移。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 到 AC-006，并映射 S1 到 S6 | none |
| DoD Contract | pass | E | design §3.4 定义 contract independence、protocol split、fake backend、capabilities、tmux regression DoD | none |
| Steps and checks traceability | pass | E | checklist steps/checks 可追溯到 design §2.4、§3.1、§3.3、§3.4 | none |
| Roadmap contract compliance | pass | E/C | design 覆盖 roadmap §4.1 的 namespace/window/pane/diagnostics 能力边界，且不做胖接口 | none |
| Module interface design | pass | E/C | 小协议拆分，fake backend 不被迫实现无关能力，`_tmux_run` 不进入 public protocol | none |
| Validation and artifacts | pass | E | CMD-003 覆盖 contract/fake backend；CMD-004 覆盖 tmux/layout/runtime 抽样回归 | none |

Summary: E=6, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- `MuxBackend` facade 后续实现仍需防止退化成胖接口；code review 必须检查调用方只依赖需要的小协议。
- leakage inventory 当前是 design 约束，implementation 必须把它做成可核对清单，避免 adapter 迁移漏掉 reflow、move/swap、foreground attach、pane log。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child design batch；本 feature design 保持 `draft`，等待所有子 feature design-review passed 后统一 owner 确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004、FDR-005
- Attributed delta: `.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-design.md` 与 `.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-checklist.yaml`
- Verification: round 2 independent reviewer `019f7b16-56c8-7021-85dd-4fdd06e11fdf` 确认 command/evidence、capabilities、direction literal、`_tmux_run` boundary 已关闭；主 agent focused closure 增加 `reflow_window()` 并本地核验 design/checklist 均可搜索到 canonical seam；YAML 校验通过。
- Classification: 最后一轮 closure 只显式化已有 roadmap reflow 能力，不改变行为、公开契约、架构边界、验收语义或范围；无需启动第三轮完整复审。
