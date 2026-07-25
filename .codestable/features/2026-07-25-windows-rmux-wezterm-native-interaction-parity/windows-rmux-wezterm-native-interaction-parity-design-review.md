---
doc_type: feature-design-review
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f96f8-30c4-7f23-999a-f412735f503d"
reviewed: 2026-07-25
round: 2
---

# windows-rmux-wezterm-native-interaction-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-brainstorm.md`
- Roadmap: none
- Related docs: `.codestable/brainstorms/windows-rmux-ux-parity-hardening/brainstorm.md`
- Code facts checked: `lib/cli/services/tmux_ui_runtime/service.py`, `test/test_v2_tmux_ui.py`, `tools/ccb-agent-sidebar/src/tui.rs`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f96f8-30c4-7f23-999a-f412735f503d`
- Raw output: 第二轮复审结论为无 blocking / important；上一轮 FDR-001~004 均已关闭；剩余 nit 已由主 agent focused closure 修正 checklist S3 文案。
- Merge policy: 已逐条核验并合并；未直接照抄未经核验结论。
- Gate effect: none

## 2. Design Summary

- Goal: Windows/rmux/WezTerm 前台交互选择 GUI-native parity，普通 pane 透明化，sidebar 专属接管。
- Key contracts: 普通 pane 不被 copy-mode、paste-buffer 或普通左键 mouse passthrough 劫持；sidebar 保留 mouse/header/KillProject 行为；不新增交互模式配置。
- Steps: 5 步，风险热点是 live rmux snapshot 与真实 WezTerm GUI 手工验收。
- Checks: 10 条，已追踪到 design §1、AC IDs 和 checklist steps。
- Baseline / validation: checklist YAML 已通过；后续实现需跑 `test/test_v2_tmux_ui.py`、sidebar cargo tests、py_compile、rmux live binding snapshot 和手工 WezTerm runbook。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] FDR-005 `design §3.4 / manual runbook artifacts` QA 阶段可把 manual runbook 固定为最小字段：OS、WezTerm 版本、rmux 可用性、实际操作结果、残留限制分类。
  - Evidence: design 已要求 `manual-wezterm-runbook.md` 或 QA 同名小节，但未规定字段 schema。
  - Impact: 不影响 design 可执行性；结构化字段能提高 acceptance 复核效率。

### learning

- unit、live binding snapshot、manual WezTerm runbook 分层是合理的：unit 证明 binding 生成，live 证明 rmux 接受，manual 才能证明 GUI-native 体验。
- output/capture parity 被留到后续 brainstorm，避免把 provider completion capture 与前台滚轮混成一个 feature。

### praise

- design 明确记录当前代码和测试仍按旧语义断言普通 pane wheel copy-mode，避免把待实现状态误写成已完成事实。
- seam 保持在既有 `_apply_sidebar_mouse_controls()` / fallback 分支内，没有为一次 binding 收紧引入新 adapter，符合 KISS / YAGNI。

## 4. User Review Focus

- 用户需要重点拍板：是否确认 Windows/rmux 前台交互采用 GUI-native parity，而不是 tmux-like mouse parity。
- implement 需要重点遵守：普通 pane 不进入 copy-mode、不走 paste-buffer、不裸透传普通左键；sidebar 全接管且 `x` 保持 KillProject。
- code review / QA / acceptance 需要重点复核：live binding snapshot 不能替代真实 WezTerm 手工记录；skipped live test 不能计 full pass。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001~AC-007，每个核心场景有 step 与证据类型 | none |
| DoD Contract | pass | E | design §3.4 与 checklist `dod.commands` 均列出核心命令和 artifact | none |
| Steps and checks traceability | pass | E | checklist checks source 已追踪到 `design §1`、AC、S step | none |
| Roadmap contract compliance | n/a | E | 本 feature 非 roadmap 起头；相关二期维度记录在 brainstorm | none |
| Module interface design | pass | C | design §2.1 说明 seam 在 existing UI binding owner；代码事实位于 `service.py` | none |
| Validation and artifacts | pass | E | design §2.4 / §3.4 指定 live snapshot、manual runbook、skip/blocked/partial 归因 | QA 阶段重点执行 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- GUI-native 行为最终仍依赖真实 Windows + WezTerm + rmux 前台手工证据；live snapshot 只能证明 root binding 字符串，不足以证明拖选、右键粘贴和滚轮体验完全符合预期。QA / acceptance 必须按 DOD-QA-001 / DOD-ACCEPT-001 卡住 full pass。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review；用户确认 design 后才能把 `status` 改为 `approved` 并进入实现阶段。

## 8. Focused Closure

- Closed findings: first-round FDR-001, FDR-002, FDR-003, FDR-004, markdown table nit, second-round S3 wording nit
- Attributed delta: design/checklist 仅补强左键 focus 追踪、测试断言反转边界、live/manual artifact 路径、skip/blocked/partial 归因、check source 和表格列数；second-round 后只收紧 checklist S3 文案。
- Verification: `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml" --yaml-only` 通过。
- Classification: 修订没有改变用户目标、公开 UX 决策、架构边界或 feature 范围；只是把验证语义和证据路径写得可执行。
