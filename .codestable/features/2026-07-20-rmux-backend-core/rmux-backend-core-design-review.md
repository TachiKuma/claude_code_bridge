---
doc_type: feature-design-review
feature: 2026-07-20-rmux-backend-core
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7c95-d939-7081-81ce-6347c4ef9681"
reviewed: 2026-07-20
round: 1
---

# rmux-backend-core feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-design.md`
- Checklist: `.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: 前序 epic child design-review 结论：`provider-runtime-backend-session-contract`、`rmux-daemon-ownership-boundary`
- Code facts checked:
  - `lib/terminal_runtime/tmux_backend.py::TmuxBackend`
  - `lib/terminal_runtime/tmux_backend_panes.py`
  - `lib/ccbd/services/project_namespace_runtime/backend.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7c95-d939-7081-81ce-6347c4ef9681`
- Raw output: reviewer verdict `passed`，未发现 blocking 或 important findings
- Merge policy: 已逐条核验 reviewer 覆盖点，并用 design / checklist / roadmap / 代码事实合并
- Gate effect: 首轮独立 reviewer 已完成，允许定稿 `passed`

## 2. Design Summary

- Goal: 实现 Rmux namespace、session、window、pane、list、split、respawn、kill、title、user-option、style 的 backend core。
- Key contracts: `RmuxBackend` 是 production adapter，消费 backend-neutral `MuxNamespaceRef` / `MuxPaneRef`；capability gate 在 construction 与 operation 两层 fail-fast；Rmux daemon 只作为 backend evidence。
- Steps: 6 个步骤，覆盖 capability gate、command client seam、namespace/window、pane、presentation、compatibility guard。
- Checks: 8 项检查，均能回到 design 的 scope、acceptance、DoD 或 checklist source。
- Baseline / validation: YAML 校验、fake client unit tests、tmux compatibility 抽样回归、import guard。

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

- epic child 的 backend core 范围应保持在 mux lifecycle 基础操作，provider IO、completion parser 和 ccbd production lifecycle 分离到后续 item，降低契约耦合。

### praise

- design 明确把 Rmux pane id 保持为 backend-local `MuxPaneRef`，不伪装成 tmux `%N`，该边界能减少后续兼容层污染。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只交付 Rmux backend core，不交付 send/capture/logging，也不接入 ccbd production lifecycle。
- implement 需要重点遵守：required unsupported capability 必须 fail-fast；Rmux command strings 只停留在 command client / diagnostics；上层不能解析 Rmux stderr。
- code review / QA / acceptance 需要重点复核：每个 operation 都经过 capability guard；`MuxPaneRef` 没有 tmux `%N` 伪装；import guard 确认 tmux path 与 rmux path 不互相污染。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.1 / §3.3 覆盖 AC-001 至 AC-007 | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4 | none |
| Roadmap contract compliance | pass | E | roadmap item `rmux-backend-core` 与 design frontmatter / summary 对齐 | none |
| Module interface design | pass | C | design §2.1 定义 `RmuxBackend` entry 和 runtime 分层；CodeGraph 核验现有 `TmuxBackend` 事实存在 | none |
| Validation and artifacts | pass | E | checklist `dod.commands` 覆盖 YAML、unit、regression、import guard；本轮 YAML 校验通过 | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- Rmux CLI/SDK 的真实输出格式仍需 implementation 阶段用 fake fixtures 和真实平台证据复核；本 design 已把 parser、error mapping 和 malformed output 纳入 AC-005 / DOD-IMPL-005。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop，继续下一个 epic child；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

none
