---
doc_type: root-cause-review
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: failed
reviewed: 2026-07-27
reviewer: main-agent-and-independent-subagent
independent_reviewer_id: 019fa3a0-891c-7d33-9b12-04303133dd2f
---

# Windows/rmux/WezTerm 前台交互根因审查与拆分方案

## 1. 结论

当前 `windows-rmux-wezterm-native-interaction-parity` 不应继续按单个 feature 修复和验收。Owner 在 2026-07-27 的 native Windows + WezTerm + rmux 前台复测已经证明 1 项 PASS、5 项 FAIL：

- 普通 pane 单击聚焦：PASS。
- 普通 pane 拖拽选区：FAIL。
- 普通 pane 右键粘贴：FAIL。
- 普通 pane 滚轮：FAIL。
- sidebar settings 点击：FAIL。
- sidebar `x` KillProject 点击：FAIL。

根因不是单个坐标表达式或 Rust hit-test 小 bug，而是当前实现把“未绑定 copy-mode / paste-buffer / scroll command”误当成“普通 pane 已回到 WezTerm GUI-native 行为”。在 `mouse on` 下，鼠标事件已经被 terminal application mouse reporting 路径捕获；CCB 删除部分绑定只是不执行对应 tmux/rmux 命令，并不会让事件自动回到 WezTerm 默认选择、粘贴或滚动路径。

因此本 feature 的正确状态是 `failed`。下一步必须拆成更小 feature，并为每条交互路径建立能观察真实前台事件的验收。

## 2. 证据

### 2.1 WezTerm mouse reporting

`%TEMP%/codestable-src/wezterm/docs/config/mouse.md`：

- 第 12-15 行：默认应用不响应鼠标；应用可请求 mouse event tracking；启用后 mouse event 不匹配 WezTerm mouse assignment，而是传给应用。
- 第 17-23 行：可通过 `SHIFT` 或 `bypass_mouse_reporting_modifiers` 绕过应用 mouse reporting。
- 第 42-60 行：WezTerm 默认 mouse assignment 包含选择、完成选择与 middle paste 等 GUI 行为。
- 第 119-126 行：`mouse_reporting=true` 的 binding 会阻止 pane 中应用收到该 mouse event；反向也说明 mouse reporting 是终端侧和应用侧之间的互斥边界。

推论：只要 rmux/tmux session 处于应用 mouse reporting 路径，普通 pane 的左键拖拽、右键/中键粘贴、滚轮是否表现为 WezTerm native 行为，不能用 rmux `list-keys` 或 CCB 负向绑定断言证明。

### 2.2 rmux mouse on/off 语义

`%TEMP%/codestable-src/rmux/docs/human-friendly-config.md`：

- 第 17-19 行：rmux 官方 human-friendly 配置选择 `set -g mouse off`，说明 native selection 只在没有 opt into pane mouse mode 时像普通终端。

`%TEMP%/codestable-src/rmux/crates/rmux-server/src/outer_terminal/features.rs`：

- 第 45-52 行：`mouse=on` 会把 outer terminal mouse tracking mode 设为 `Button` 或 `All`，否则为 `Off`。

`%TEMP%/codestable-src/rmux/crates/rmux-client/src/attach_windows/terminal.rs`：

- 第 109-110 行：Windows attach 端存在动态开关 mouse input 的 API。
- 第 724-735 行：启用 mouse input 时设置 `ENABLE_MOUSE_INPUT` 并清除 `ENABLE_QUICK_EDIT_MODE`；注释明确 Windows console 自身会消费 drag selection 和 wheel scroll，应用收不到事件。

推论：Windows/rmux 的 `mouse on` 是一个端到端 capture 开关。它既影响 WezTerm 是否走默认 GUI mouse binding，也影响 Windows console input mode。普通 pane native drag / wheel 失败不是测试偶发，而是当前全局策略下的预期风险。

### 2.3 CCB 当前 mouse 策略

本仓库证据：

- `config/tmux-ccb.conf:11-12` 默认 `set -g mouse on`。
- `config/tmux-ccb.conf:178-179` 仅提供手动 mouse on/off toggle。
- `lib/terminal_runtime/rmux_backend_runtime/namespace.py:55-62` rmux namespace policy 设置 `mouse=on`。
- `lib/terminal_runtime/tmux_mux_backend.py:140-146` tmux mux backend policy 设置 `mouse=on`。
- `lib/cli/services/runtime_launch_runtime/tmux_panes.py:119-124` detached tmux server prepare 也设置 `mouse on`。
- `lib/cli/services/tmux_ui_runtime/service.py:266-290` Windows/rmux fallback 对 `MouseDown1Pane`、`MouseDown1Border`、`WheelUpPane`、`WheelDownPane` 设置 root binding，普通分支只执行 `select-pane -t =`，sidebar 分支执行 `select-pane -t = ; send-keys -t = -M`。

推论：普通 pane 单击聚焦 PASS 是因为 `select-pane -t =` 可工作；但普通 pane drag/right/wheel 失败不能由“没有 copy-mode/paste-buffer/scroll command”反证为 CCB 未劫持，因为 `mouse on` 本身已经把事件引入 rmux mouse path。

## 3. 当前测试设计的问题

### 3.1 自动化只证明绑定字符串，不证明前台派发

`test/test_v2_tmux_ui.py` 的 live rmux 测试创建临时 session，调用 `_apply_sidebar_mouse_controls()` 后读取 `list-keys`。它没有启动真实 CCB sidebar pane，没有确认 `@ccb_role=sidebar`，没有确认当前运行的 `ccb-agent-sidebar` binary，也没有观察 crossterm `Event::Mouse`。

因此 `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/live-binding-snapshot.txt` 只能作为“rmux 接受绑定字符串”的证据，不能作为“前台点击到达 Rust TUI”的证据。

### 3.2 负向断言不能替代 native 行为

当前测试断言没有 `copy-mode`、`paste-buffer`、`scroll-up/down`，这是必要的回归保护，但不是充分的 GUI-native 验收。GUI-native 必须由 WezTerm 前台选择、粘贴、滚动真实观测证明，或由明确的 host-terminal probe 证明。

### 3.3 sidebar 单元测试不能覆盖 rmux -> crossterm

`tools/ccb-agent-sidebar/src/tui.rs` 中 Rust 测试覆盖 `header_action_at()`、`handle_mouse_down()`、键盘 `Q` / `Shift+Q` 等本进程逻辑。它没有覆盖 rmux `send-keys -M` 是否能把真实 mouse event 送到 crossterm `event::read()`。

## 4. 六项拆分

### 4.1 ordinary-pane-single-click-focus-baseline

- 当前状态：已通过。
- 目标：保留 `select-pane -t =` 的最小聚焦行为。
- 验收：native Windows + WezTerm + rmux 前台单击普通 pane 后 active pane 切换；自动化保留 fallback binding 断言。
- 不做：不把拖拽、右键、滚轮归入该 feature。

### 4.2 ordinary-pane-drag-selection-native

- 当前状态：失败，需要重新设计。
- 核心问题：`mouse on` 下 WezTerm native drag selection 不会自然接管。
- 候选方向：
  - 关闭普通 pane mouse reporting 或改为可切换策略。
  - 文档化并验证 `SHIFT` bypass 作为受支持路径。
  - 放弃 native drag，改为 tmux/rmux copy-mode selection，但这会改变原先 GUI-native 目标。
- 必须验收：真实前台可选中字符串；若选择 bypass，验收动作必须写明修饰键。

### 4.3 ordinary-pane-right-click-paste

- 当前状态：失败，需要重新设计。
- 核心问题：在 `mouse on` 下 WezTerm 默认 mouse binding 不会执行；fallback 不重绑右键后也不会自动粘贴。
- 候选方向：
  - 显式实现 host clipboard paste 桥。
  - 恢复 rmux/tmux `paste-buffer` 但先解决 buffer 来源和多行粘贴语义。
  - 改用 WezTerm 配置层 mouse binding，并明确不是 CCB 生产代码默认能力。
- 必须验收：先从其他软件复制文本，右键普通 pane 后文本进入 shell input；多行内容要明确是粘贴还是禁用。

### 4.4 ordinary-pane-wheel-scroll

- 当前状态：失败，需要重新设计。
- 核心问题：当前 ordinary 分支把 wheel 消费成 `select-pane -t =`，并不能触发 WezTerm native scroll；不绑定 copy-mode 也不能证明滚动可用。
- 候选方向：
  - tmux/rmux-like copy-mode scroll。
  - host terminal native scroll，但需要 `mouse off` 或 bypass。
  - 应用内滚动透传，前提是 pane app 自己支持 mouse wheel。
- 必须验收：在 WezTerm 前台滚轮有可见滚动，并记录滚动的是 terminal scrollback、rmux copy-mode，还是 pane app。

### 4.5 sidebar-settings-click-e2e

- 当前状态：失败，需要端到端诊断。
- 核心问题：Rust hit-test 通过不等于 rmux `send-keys -M` 到达 crossterm。
- 诊断入口：
  - 真实 sidebar pane 的 `@ccb_role` 是否为 `sidebar`。
  - 真实 pane 是否运行当前 `ccb-agent-sidebar` binary，`@ccb_sidebar_helper_id` 是否匹配源码构建产物。
  - sidebar 进程是否实际收到 `Event::Mouse`。
  - 点击后 `config ui` 失败时是否有可见错误状态。
- 必须验收：点击 settings 后 config UI 打开，或 sidebar 显示具体 launch error；不能只凭 cargo test pass。

### 4.6 sidebar-kill-project-click-e2e

- 当前状态：失败，需要端到端诊断。
- 核心问题：与 settings 相同，先证明 mouse event 到达 Rust；再验证 `ExitAction::KillProject` 和 `ccb kill` 子进程路径。
- 诊断入口：
  - sidebar click 是否返回 `ExitAction::KillProject`。
  - `ccb_program_for_sidebar()` 在 Windows 是否解析到当前源码入口或正确安装的 `ccb`。
  - `ccb kill` 是否在 `project_root` 下成功执行，并清理 rmux/ccbd/project residue。
- 必须验收：点击 `x` 后项目被 kill，或明确显示 kill failure；不能只验收键盘 `Q`。

## 5. 下一轮处理顺序

1. 先封存 `ordinary-pane-single-click-focus-baseline`，只保留防回归。
2. 先做 `sidebar-settings-click-e2e` 与 `sidebar-kill-project-click-e2e` 的诊断 feature。原因是它们验证 rmux `send-keys -M` 到 crossterm 的关键链路；该链路不清楚时，继续改 header 坐标或 Rust hit-test 风险很高。
3. 再分别处理 ordinary drag、right-click、wheel。每一项都必须先选择交互策略：GUI-native、tmux/rmux-like、或 documented bypass；不能在一个 feature 中混合。

## 6. 本轮不得继续的做法

- 不得把 `list-keys` 通过写成前台交互通过。
- 不得把“未出现 `paste-buffer` / `copy-mode` / `scroll-up/down`”写成 native pass。
- 不得把 sidebar settings/x 失败先归因到 Rust hit-test；必须先证明真实 mouse event 是否到达 Rust。
- 不得在 QA failed 后进入 acceptance。

