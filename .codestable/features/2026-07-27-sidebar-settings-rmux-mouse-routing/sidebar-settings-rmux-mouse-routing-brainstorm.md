---
doc_type: feature-brainstorm
feature: 2026-07-27-sidebar-settings-rmux-mouse-routing
status: confirmed
summary: "settings-only 鼠标通道研究，不接受 sidebar 左键 broad fallback"
tags: [windows, rmux, wezterm, sidebar, mouse, capability]
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: sidebar-settings-rmux-mouse-routing
split_parent: sidebar-settings-click-e2e
confirmed_by: owner
confirmed_at: 2026-07-27
---

# sidebar-settings-rmux-mouse-routing Brainstorm

> Stage 0 | 2026-07-27 | 下一步：cs-feat design/design-review

## 想做什么、为什么

`sidebar-settings-click-e2e` 已证明 settings 快捷键和 config UI 本身健康，但真实 Windows + WezTerm + rmux 前台点击没有进入 Rust/crossterm mouse event。rmux root mouse binding 能命中 sidebar pane，却没有提供 `mouse_x/mouse_y`，`send-keys -t = -M` 也没有透传到 pane。

Owner 已明确拒绝“sidebar 任意左键都打开 settings”的 broad fallback，因为它会覆盖普通 sidebar click 和 `x` KillProject。这个 feature 的真问题因此不是“让 settings 能打开”，而是确认是否存在精确到 settings 控件的通道；没有就把能力边界写成可复现 evidence。

## 考虑过的方向

### 方向 A：恢复 broad sidebar-left-click fallback

- 描述：rmux sidebar 分支中把任意左键映射为 `send-keys -t = c`。
- 价值：已验证可以打开 settings。
- 代价：无法区分 settings、`x` 和普通 sidebar 区域，直接破坏用户已指出的 KillProject/普通 click 语义。
- 结论：否决。Owner 已选择不接受该退化。

### 方向 B：rmux capability/source audit 后接入精确 mux 条件

- 描述：审查 rmux 是否支持 tmux 等价 mouse format、`=` mouse target、`send-keys -M` 透传，或存在其它可取坐标字段。
- 价值：如果能力存在但 CCB 用法错误，可以最小修正 current binding。
- 代价：如果 rmux 当前实现缺能力，本方向只能产出 unsupported evidence，不能强行实现。
- 结论：选定为第一优先级。

### 方向 C：WezTerm 层 settings-only 绑定

- 描述：研究 WezTerm 是否能在应用 mouse tracking 开启时，对特定 terminal cell / pane / top header 区域注入精确按键或事件。
- 价值：可能绕过 rmux 坐标缺失，同时保持 settings-only。
- 代价：WezTerm mouse assignment 在应用启用 mouse reporting 时可能不会匹配普通 click；若只能全局/全 pane 绑定，同样不可接受。
- 结论：作为第二候选，只接受精确到 settings 区域且不会影响普通 pane/`x` 的证据。

### 方向 D：明确 unsupported capability

- 描述：如果 rmux 无坐标且不透传，WezTerm 也不能提供精确 settings-only 通道，则不做假修复，产出 capability evidence。
- 价值：supportability 能清楚声明 Windows/rmux 当前限制，避免把 blocked 写成 pass。
- 代价：settings 前台点击继续 blocked，用户只能用键盘 `c` 或后续替代 UI。
- 结论：作为失败收敛路径，必须有可复现命令、版本/源码引用和前台 transcript。

## 已敲定的设计点

- 已确认：不得把 sidebar 任意左键映射到 settings。
- 已确认：不得改变 `x` KillProject、普通 sidebar click、普通 pane drag/right/wheel。
- 已确认：direct `send-keys -t %0 c` 只能作为 settings action 健康证据，不能当作 mouse click pass。
- 已确认：design 必须先做 rmux/WezTerm capability audit，再决定实现或 unsupported projection。
- 待验证：rmux 是否有等价 `mouse_x` / `mouse_y` / `mouse_pane` / `send-keys -M` 支持；若没有，需要记录到 evidence。
- 待验证：WezTerm 是否能在 crossterm mouse capture 打开时提供精确 settings-only 绑定；若只能全局点击注入，必须否决。

## Baseline reuse / delta

- 复用父 feature 的前台复测和 UX JSON：helper/settings action/config UI 健康，rmux root binding 可命中 sidebar，但坐标为空且 `send-keys -M` 未进入 Rust。
- 复用现有 Rust sidebar probe 和 token 脱敏能力，不重新定义 settings action 健康口径。
- 复用当前测试中禁止 `send-keys -t = c` broad fallback 的回归保护。
- 本 feature 的增量只覆盖 rmux/WezTerm capability matrix、settings-only `selected_route`、当前 child 的 UX parity JSON projection，以及必要的精确通道接入。

## 选定方向与遗留问题

选定方向是 capability-first：先证明 rmux/WezTerm 是否能表达 settings-only 点击，再最小接入；不能证明精确通道时，不写行为退化，而是把 `windows-rmux-ux-parity-evidence.json` 投影为 `blocked/unsupported_capability`。

遗留给 design 的问题：

- 需要哪些命令/源码位置能证明 rmux mouse format 和 `send-keys -M` 能力边界？
- WezTerm 精确绑定如果存在，怎样避免影响普通 pane 和 sidebar `x`？
- unsupported evidence 的 schema 必须包含哪些字段，才能被 supportability feature 消费？
