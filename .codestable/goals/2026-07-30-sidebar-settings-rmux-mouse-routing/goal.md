---
doc_type: goal
goal: sidebar-settings-rmux-mouse-routing
status: complete
---

# sidebar-settings-rmux-mouse-routing Goal

## Objective

完成 `sidebar-settings-rmux-mouse-routing` 的 QA 后终端功能验收与 goal 终态记录，确保该 child 以 evidence-complete 的 `unsupported_capability` 结论交回 epic，而不是误宣称 settings mouse parity passed。

## Starting Point

- Feature 目录：`.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/`
- Roadmap owner：`.codestable/roadmap/windows-rmux-ux-parity-hardening/`
- 已有状态：
  - design: approved
  - design-review: passed
  - code review: passed
  - QA: passed
- 当前产品结论：真实 Windows + WezTerm + rmux settings mouse click 仍是 `blocked/unsupported_capability`。

## Acceptance Criteria

- 功能验收确认 feature 产物链完整：design approved、design-review passed、code review passed、QA passed。
- 功能验收确认 UX JSON 精确投影为 `evidence_status=blocked`、`failure_class=unsupported_capability`、`selected_route=unsupported_capability`、`runtime_behavior_changed=false`、`broad_fallback_added=false`。
- 功能验收确认没有新增 broad sidebar-left-click settings fallback，direct `c` 只作为诊断证据，不计为 mouse click parity pass。
- 功能验收确认本 goal 的 final iteration 与 `functional-acceptance.md` 双向引用，`state.yaml` 可恢复为 complete。

## Non-Goals

- 不实现新的 rmux 或 WezTerm settings-only mouse route。
- 不继续原 `windows-rmux-wezterm-native-interaction-parity` acceptance。
- 不修改用户无关 dirty 文件，例如 `笔记.md`。
- 不执行 git commit、push、merge、release 或 deploy。

## Decisions And Assumptions

- 用户通过 `$codestable:cs-goal sidebar-settings-rmux-mouse-routing` 明确要求进入 goal driver；本 goal 仅包装已存在 feature 的终端验收和状态闭环，不替代 `cs-feat` 实现规则。
- QA passed 的含义是 evidence gate 完整，不是 settings mouse parity passed。
- 若功能验收发现产物自相矛盾、JSON 投影不精确或 broad fallback 风险，goal 不完成，回到 feature 修复。

## Current State

`state.yaml` 当前为 `complete`，`current_iteration=1`。Task agent 功能验收已通过，最终 iteration 已引用 `functional-acceptance.md`。

## Next Action

Goal 已完成。后续 epic 恢复时应把 `sidebar-settings-rmux-mouse-routing` 视为 evidence-complete 的 `unsupported_capability` child，而不是 settings mouse parity passed。
