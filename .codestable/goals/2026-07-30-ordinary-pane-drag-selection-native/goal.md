---
doc_type: goal
goal: ordinary-pane-drag-selection-native
status: complete
---

# ordinary-pane-drag-selection-native Goal

## Objective

完成 `ordinary-pane-drag-selection-native` 的诊断闭环与终端验收，确认当前 Windows + WezTerm + rmux 下普通 pane 拖拽选区不能作为 GUI-native mouse parity pass，并给出可被 epic 聚合的 UX parity evidence。

## Starting Point

- Root-cause split: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/root-cause-review-and-feature-split.md`
- 父 QA: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-qa.md`
- Split child: `ordinary-pane-drag-selection-native`
- 当前事实：
  - owner 在 2026-07-27 的 native Windows + WezTerm + rmux 前台复测中确认普通 pane 拖拽无法选中任何字符串。
  - CCB 默认 tmux/rmux policy 多处启用 `mouse on`。
  - rmux fallback 未重绑 `MouseDrag1Pane` 是正确的负向保护，但不能证明 WezTerm GUI-native selection 已恢复。

## Acceptance Criteria

- 功能验收确认当前默认 CCB/rmux/tmux policy 多处启用 `mouse on`，普通 pane drag selection 在应用 mouse reporting 路径下不能被负向绑定断言证明为 WezTerm GUI-native 行为。
- 功能验收确认 rmux fallback 未重绑 `MouseDrag1Pane` / `copy-mode -M` 是必要回归保护，但不足以宣称真实前台可选中字符串。
- 功能验收确认本 goal 未修改运行时代码，未关闭全局 mouse policy，未把 `Shift` bypass 或 tmux/rmux copy-mode selection 宣称为默认 native drag pass。
- 功能验收确认 evidence JSON 投影为 `evidence_status=blocked`、`failure_class=unsupported_capability`、`parity_dimension=foreground_interaction`。
- 功能验收确认本 goal complete 只代表 `ordinary-pane-drag-selection-native` 诊断闭环完成，不代表 epic 其他 child 完成。

## Non-Goals

- 不实现新的普通 pane mouse on/off 策略。
- 不把 `Shift` bypass 文档化为已支持默认路径。
- 不把 tmux/rmux copy-mode selection 替代为 GUI-native drag selection。
- 不修改运行时代码或测试代码。
- 不执行 git commit、push、merge、release 或 deploy。

## Decisions And Assumptions

- 用户通过 `$codestable:cs-goal ordinary-pane-drag-selection-native` 要求推进该 split child。
- 本 goal 采用 evidence-first 深度：当前目标是把失败路径归因和能力投影收口，而不是在 goal driver 内改变长期 mouse contract。
- 后续若要把该 child 从 `blocked` 改为 pass，需要另开 feature 选择并实现明确策略：普通 pane mouse reporting off、受支持的 modifier bypass，或显式改成 tmux/rmux-like copy-mode selection。

## Current State

`state.yaml` 当前为 `complete`，`current_iteration=1`。Task agent 功能验收已通过，最终 iteration 已引用 `functional-acceptance.md`。

## Next Action

Goal 已完成。后续 epic 应把该 child 视为诊断闭环完成、前台 ordinary pane drag selection parity 仍为 `blocked/unsupported_capability`；不得解读为真实无修饰键拖拽选区已通过。
