---
doc_type: feature-brainstorm
feature: 2026-07-27-sidebar-settings-click-e2e
status: confirmed
summary: "sidebar settings 点击端到端诊断先行"
tags: [windows, rmux, wezterm, sidebar, mouse, diagnostics]
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: sidebar-settings-click-e2e
split_parent: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
split_child: sidebar-settings-click-e2e
confirmed_by: owner
confirmed_at: 2026-07-27
---

# sidebar-settings-click-e2e Brainstorm

## 1. 真问题

Owner 在 2026-07-27 前台复测确认：sidebar settings 点击没有反应。根因审查已经指出，当前自动化只能证明 rmux 接受 binding 字符串，不能证明真实鼠标事件经过 `rmux root binding -> send-keys -M -> crossterm Event::Mouse -> header_action_at -> open_config_ui`。

因此这个 split child 的真问题不是“settings 图标坐标是否写对”，而是要把前台无反应拆成可归因的几段：

- 真实 pane 是否是 sidebar。
- 运行的 helper 是否是当前 binary。
- rmux binding 是否命中 sidebar 分支。
- `send-keys -M` 是否到达 crossterm mouse event。
- settings action 是否触发 config UI ready/failed 可见反馈。

## 2. 候选方向

### 方向 A：恢复 mux 层 `send-keys c`

优点是改动小，可能让 settings 快速触发键盘路径。缺点是绕过 Rust TUI 的 mouse hit-test，不能证明 `send-keys -M` 链路，并且会把 settings 和 kill 再次绑到 mux 坐标条件上。

结论：不采用。

### 方向 B：只补 Rust hit-test 单测

优点是自动化容易跑。缺点是现有 Rust 单测已经覆盖 `header_action_at()` 和 `handle_mouse_down()`，前台失败不应继续归因到单元 hit-test。

结论：不采用。

### 方向 C：诊断优先，先建立 e2e probe 再最小修复

优点是能区分 pane identity、helper stale、binding、mouse event、config UI launch 多个断点；缺点是需要定义 opt-in probe 和手工前台 transcript。

结论：采用。

## 3. 已敲定

- 本 feature 只做 `sidebar-settings-click-e2e`，不合并 `sidebar-kill-project-click-e2e`。
- 不修改 ordinary pane drag/right/wheel 策略。
- 不恢复 mux 层 `send-keys c` 作为默认 settings 修复。
- 诊断证据必须遵守 roadmap 的 `WindowsRmuxUxParityEvidence` 顶层 schema；settings 专用字段只能放在 details 或 artifact 中。
- 如实现需要新增 probe，必须 opt-in，默认 UI 无调试噪音。
- Owner 已在 2026-07-27 明确要求“按拆分 feature”继续，本 brainstorm 作为该 split child 进入 design 的确认记录。

## 4. 最大未知

- rmux 在 native Windows + WezTerm 前台是否稳定把 `send-keys -t = -M` 转成 crossterm `Event::Mouse`。
- 当前失败是否由 stale sidebar helper、pane option 缺失、root binding 未刷新，还是 rmux mouse passthrough 本身失败导致。
- config UI 失败是否已有可见状态但 owner 未观察到，还是事件根本没有触发到 settings action。
