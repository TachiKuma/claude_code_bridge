---
doc_type: goal
goal: root-cause-review-and-feature-split
status: complete
---

# root-cause-review-and-feature-split Goal

## Objective

完成 `root-cause-review-and-feature-split.md` 的终端验收与 goal 终态记录，确认 `windows-rmux-wezterm-native-interaction-parity` 已从单一失败 feature 正确转为可恢复的拆分 handoff。

## Starting Point

- Root-cause report: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/root-cause-review-and-feature-split.md`
- Parent feature QA: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-qa.md`
- Epic roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/`
- 当前事实：
  - root-cause report frontmatter `status: failed`
  - 父 feature QA `status: failed`
  - epic workflow 返回 `handoff`
  - roadmap items 已包含 `split_required: true` 与六项 `split_children`

## Acceptance Criteria

- 功能验收确认 root-cause 报告记录 1 PASS / 5 FAIL、根因和六项拆分，且明确不得继续父 feature acceptance。
- 功能验收确认 roadmap `items.yaml` 引用 root-cause 文件，标记 `split_required=true`，并保留六项 `split_children` 与后续动作。
- 功能验收确认 epic `goal-state.yaml` 的 `handoff_next` 指向 root-cause 文件，并要求从 sidebar e2e diagnostics 开始，而不是继续原 acceptance。
- 功能验收确认父 feature workflow 恢复为 QA failed / acceptance missing，并由 epic owner 接管。
- 功能验收确认已启动至少一个拆分后的 sidebar e2e 诊断分支，且不会把 root-cause split goal 误写成所有 child feature 已完成。

## Non-Goals

- 不实现 ordinary drag/right/wheel 或 sidebar kill-project 的修复。
- 不把 `windows-rmux-wezterm-native-interaction-parity` 标为 accepted 或 passed。
- 不修改运行时代码或测试代码。
- 不执行 git commit、push、merge、release 或 deploy。

## Decisions And Assumptions

- 用户通过 `$codestable:cs-goal root-cause-review-and-feature-split.md` 指定以该 root-cause 文件为 goal 起点。
- 本 goal 的职责是终端验收和状态闭环，不替代后续各拆分 child 的 feature workflow。
- `sidebar-settings-rmux-mouse-routing` 已作为拆分后 sidebar e2e 诊断链的一部分完成独立 goal；其他 split child 仍可按 epic handoff 继续。

## Current State

`state.yaml` 当前为 `complete`，`current_iteration=1`。Task agent 功能验收已通过，最终 iteration 已引用 `functional-acceptance.md`。

## Next Action

Goal 已完成。后续 epic 继续处理各拆分 child；不得把父 feature 恢复为单一 acceptance，也不得把此 goal 解读成所有拆分 child 均已完成。
