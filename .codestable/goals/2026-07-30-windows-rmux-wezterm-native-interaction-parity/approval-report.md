---
doc_type: approval-report
unit: .codestable/goals/2026-07-30-windows-rmux-wezterm-native-interaction-parity
status: approved
reason: route-choice
approvals:
  goal-direction-real-parity: approved
  goal-strategy-gui-native-per-role: approved
  goal-acceptance-hybrid: approved
  goal-mouse-policy-contract-change: approved
approval_groups: {}
created_at: 2026-07-30
---

# Approval Report

## Decision Needed

在为本 goal 动生产代码前，owner 需要拍板四件事，因为它们改变 UX 契约、验收边界并授权
修改公共鼠标策略：(1) 终态方向；(2) ordinary 三项交互的 parity 模型；(3) 验收闭环；
(4) 是否授权直接改 CCB 生产鼠标配置与 rmux/tmux 策略公共契约。

## Why Now

5 项失败 child 已完成诊断闭环但**未选策略、未落生产修复**，且根因指向全局 `mouse on`
这一公共契约。任何一项落地都要先定 UX 策略并触碰生产配置，属于 `RouteChoice` +
`RiskAcceptance` 触发，必须先取得授权再实现。

## Context

见 `goal.md` 起点报告与
`.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/root-cause-review-and-feature-split.md`。
核心矛盾：sidebar 点击需要 mouse-on 才能把事件路由到 crossterm；ordinary pane 的真
GUI-native 拖拽/粘贴/滚轮又要求关掉 mouse reporting。两者互斥，只能按 role 分策略。

## Options

- **方向**：A 落地真·parity（选中）/ B 统一 tmux-like 可用方案 / C documented subset /
  D 只做最高优先项。
- **ordinary 策略**：A 真 GUI-native 按 role 分策略（选中）/ B SHIFT-bypass / C tmux-rmux-like。
- **验收**：A owner 全程手测 / B 尽量机器可验证 / C 混合（选中，sidebar 自动化 e2e +
  ordinary owner 前台确认）。
- **节奏/预算**：A 按 root-cause 顺序做到底、无硬预算（选中）/ B 分阶段停对齐 / C 自定义。

## Recommendation

采用 owner 已选组合：方向 A + 策略 A + 验收 C + 节奏 A。该组合最贴近 owner 原始「像普通
WezTerm 一样」的期待，同时用混合验收把无法自动化的 GUI-native 项交给 owner 前台确认，避免
再次把 list-keys 误当前台通过。

## Risks And Tradeoffs

- 关闭 ordinary pane mouse reporting 会使 pane 内应用（vim/less 等）默认收不到鼠标，需要
  「应用要鼠标时再开」的切换机制，否则是能力回退。
- 按 role 分策略增加鼠标策略状态面，需保证不破坏单击聚焦 baseline 与 sidebar 点击路由。
- ordinary 三项最终 pass 依赖 owner 前台真机复测，goal 完成节奏受 owner 可用性影响。

## Non-Automatic Actions

- 不会自动执行 git commit / push / merge / release / deploy —— 均需 owner 另行批准。
- 不会自动改 direction/strategy 之外的公共契约；本授权仅限鼠标策略（mouse policy /
  role-based routing / 相关 fallback binding）范围。

## Decision History

- 2026-07-30 owner 通过 grill 依次确认：方向 A、ordinary 策略 A、验收 C、节奏 A，并明确
  授权在本 goal 内直接改 CCB 生产鼠标配置与 rmux/tmux 策略公共契约（git 写操作除外）。
  四项 named approval 记为 `approved`。

## After You Answer

授权已获得。进入 Iteration 001：先做 sidebar `send-keys -M → crossterm` e2e 关键链路
诊断与修复，再按顺序处理 ordinary 三项。若后续出现本授权范围外的破坏性/契约变更/git 写
操作，将重新写 pending 决策并 owner-stop。
