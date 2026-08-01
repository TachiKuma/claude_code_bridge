---
doc_type: goal
goal: ordinary-pane-right-click-paste
status: complete
---

# ordinary-pane-right-click-paste Goal

## Objective

完成 `ordinary-pane-right-click-paste` 的诊断闭环与终端验收，确认当前 Windows + WezTerm + rmux 下普通 pane 右键粘贴不能作为 GUI-native mouse parity pass，并给出可被 epic 聚合的 UX parity evidence。

## Starting Point

- Root-cause split: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/root-cause-review-and-feature-split.md`
- 父 QA: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-qa.md`
- Split child: `ordinary-pane-right-click-paste`
- 当前事实：
  - owner 在 2026-07-27 的 native Windows + WezTerm + rmux 前台复测中确认普通 pane 右键没有反应；即使先在其他软件复制，pane 中也无法粘贴。
  - CCB 默认 tmux/rmux policy 多处启用 `mouse on`。
  - Windows/rmux fallback 未重绑 `MouseDown3Pane` / `paste-buffer` 是正确的负向保护，但不能证明 WezTerm GUI-native paste 已恢复。

## Acceptance Criteria

- 功能验收确认当前默认 CCB/rmux/tmux policy 多处启用 `mouse on`，普通 pane right-click paste 在应用 mouse reporting 路径下不能被负向绑定断言证明为 WezTerm GUI-native 粘贴行为。
- 功能验收确认 rmux fallback 未重绑 `MouseDown3Pane` / `paste-buffer` 是必要回归保护，但不足以宣称真实前台右键可把系统剪贴板文本送入 shell input。
- 功能验收确认本 goal 未修改运行时代码，未实现 host clipboard paste bridge，未恢复 `paste-buffer`，未把 WezTerm 配置层 binding 宣称为 CCB 默认生产能力。
- 功能验收确认 evidence JSON 投影为 `evidence_status=blocked`、`failure_class=unsupported_capability`、`parity_dimension=foreground_interaction`。
- 功能验收确认本 goal complete 只代表 `ordinary-pane-right-click-paste` 诊断闭环完成，不代表 epic 其他 child 完成。

## Non-Goals

- 不实现新的 host clipboard paste bridge。
- 不恢复 rmux/tmux `paste-buffer` 右键绑定。
- 不修改 WezTerm 用户配置或把配置层 binding 作为默认生产能力。
- 不修改运行时代码或测试代码。
- 不执行 git commit、push、merge、release 或 deploy。

## Decisions And Assumptions

- 用户通过 `$codestable:cs-goal ordinary-pane-right-click-paste` 要求推进该 split child。
- 本 goal 采用 evidence-first 深度：当前目标是把失败路径归因和能力投影收口，而不是在 goal driver 内改变长期 mouse / clipboard contract。
- 后续若要把该 child 从 `blocked` 改为 pass，需要另开 feature 选择并实现明确策略：host clipboard paste bridge、带清晰 buffer 来源和多行语义的 `paste-buffer` 路径，或明确标注为用户 WezTerm 配置层方案。

## Current State

`state.yaml` 当前为 `complete`，`current_iteration=1`。Task agent 功能验收已通过，最终 iteration 已引用 `functional-acceptance.md`。

## Next Action

Goal 已完成。后续 epic 应把该 child 视为诊断闭环完成、前台 ordinary pane right-click paste parity 仍为 `blocked/unsupported_capability`；不得解读为真实右键粘贴已通过。
