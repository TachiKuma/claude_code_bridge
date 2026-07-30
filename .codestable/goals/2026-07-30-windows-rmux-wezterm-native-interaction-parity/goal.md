---
doc_type: goal
goal: windows-rmux-wezterm-native-interaction-parity
status: active
---

# Windows/rmux/WezTerm 前台交互 parity 落地 Goal

## Objective

把 2026-07-27 owner 前台复测中失败的 5 项鼠标交互，从当前 `unsupported_capability`
结论落地为真·parity：

- ordinary pane **拖拽选区 / 右键粘贴 / 滚轮** —— 走**真 GUI-native**，通过按 role
  分鼠标策略实现（ordinary pane 关闭 mouse reporting，让 WezTerm 亲自处理；应用需要
  鼠标时提供再开的切换机制）。
- sidebar **settings 点击 / x KillProject 点击** —— 修好 `send-keys -M → crossterm`
  的 e2e 链路，让真实点击到达 Rust TUI 并触发对应动作。

单击聚焦 baseline 已 PASS，仅保留防回归。

## Starting Point

- 父 feature：`.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/`
  QA `status: failed`（1 PASS / 5 FAIL）。
- 根因报告：`.../evidence/root-cause-review-and-feature-split.md` —— 全局 `mouse on`
  把鼠标事件吃进 rmux/tmux application mouse reporting 路径，负向绑定断言不能证明
  GUI-native；六项拆分与各自候选方向已列出。
- 5 项失败 child（`.codestable/goals/2026-07-30-*`）已完成诊断闭环，结论均为
  `unsupported_capability`（**只诊断、未选策略、未落生产修复**）。
- epic `windows-rmux-ux-parity-hardening` 处于 `handoff`，`handoff_next` 要求先做
  sidebar e2e 诊断，再逐项修复 + code review + QA。
- 现有 CCB 鼠标策略：`config/tmux-ccb.conf` 默认 `mouse on`；rmux/tmux backend
  namespace policy 均 `mouse=on`；Windows fallback root binding 对 ordinary 分支只
  执行 `select-pane -t =`，sidebar 分支额外 `send-keys -t = -M`。

## Acceptance Criteria

见 `state.yaml.acceptance`。要点：

1. sidebar 两项做成**自动化 e2e 真证据**（mouse event 到 crossterm + 动作触发），
   不需要 owner 手测。
2. ordinary 三项本质需 owner **前台真机肉眼确认**；impl 完成后附精确手测脚本，owner
   逐项回报 pass 后该项才算通过。
3. 新增按 role 分鼠标策略不得破坏单击聚焦 baseline 与 sidebar 点击路由。
4. 每个 child 经独立 cs-code-review + QA；Task agent 功能验收记录 pass。

## Non-Goals

- 不改 direction/strategy（owner 已定真 GUI-native，不退回 tmux-like / SHIFT-bypass 主方案）。
- 不做 git commit / push / merge / release / deploy（另需 owner 批准）。
- 不新增 6 项之外的交互能力。

## Decisions And Assumptions

- **Direction A**：5 项失败交互全部落地到真·parity（owner 2026-07-30 grill）。
- **Strategy A**：ordinary 三项走真 GUI-native、按 role 分鼠标策略；sidebar 保持 mouse-on。
- **Acceptance C**：混合验收 —— sidebar 两项自动化 e2e；ordinary 三项 owner 前台确认。
- **Order/budget A**：按 root-cause 顺序（sidebar 先，ordinary 后）做到底，无硬预算，
  仅 owner-stop 条件触发才停。
- **Risk 授权**：owner 预先授权在本 goal 内直接改 CCB 生产鼠标配置与 rmux/tmux 策略
  公共契约（遵守 spec-governance）。详见 `approval-report.md`。
- **假设**：ordinary pane「关 mouse reporting」需要一个「应用要鼠标时再开」的切换机制；
  该机制的具体实现（快捷键 / 自动探测 / 手动 toggle）为 AI 可自决的技术细节，除非它改动
  owner 已确认的公共契约边界。

## Current State

Goal 刚创建，`state.yaml.status: active`，`current_iteration: 0`。起点报告与
approval-report 已落盘。尚未开始实现。

## Next Action

Iteration 001：先做 sidebar `send-keys -M → crossterm` e2e 关键链路的诊断与修复
（settings + kill），建立自动化 e2e 真证据后再进入 ordinary 三项。
