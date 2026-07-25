---
doc_type: feature-brainstorm
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: confirmed
summary: Windows/rmux/WezTerm 前台交互采用 GUI-native parity，普通 pane 透明化，sidebar 专属接管
tags: [windows, rmux, wezterm, interaction, mouse, keyboard, clipboard, sidebar, parity]
---

# Windows Rmux WezTerm Native Interaction Parity Brainstorm

> Stage 0 | 2026-07-25 | 下一步：cs-feat（由主入口选择 lane）

## 想做什么、为什么

当前项目已在 native Windows + WezTerm GUI 中基本跑通 `ccb -> ccbd -> rmux` 全链路，但真实使用体验仍暴露出和 Linux/macOS tmux 路线不同的交互缺口：鼠标滚轮、文本选区、右键粘贴、pane 聚焦、sidebar header 点击等行为容易被 rmux/tmux-style binding 破坏。

本轮不追求 rmux 鼠标绑定逐条模拟 tmux，而是选择 Windows GUI-native parity：普通 agent pane 让 WezTerm 和系统剪贴板承担原生终端体验；CCB 只接管 sidebar 这种 CCB 自有 TUI。

## 考虑过的方向

### 方向 A：WezTerm GUI 原生优先

- 普通 agent pane 尽量透明，选择、复制、右键粘贴、滚轮优先交给 WezTerm / 系统 / pane 内应用。
- CCB 只保证普通 pane 单击聚焦，以及 sidebar 专属交互。
- 价值：减少 Windows + ConPTY + rmux + TUI 多层 mouse event 转换导致的错位、双击聚焦、右键粘贴劫持和空 scrollback `[0/0]`。
- 代价：不追求普通 pane 的 tmux-like 鼠标 copy-mode 心智。
- 结论：选定。

### 方向 B：tmux copy-mode 优先

- 所有 pane 尽量模拟 Linux/macOS tmux 鼠标行为，滚轮和选择更多走 rmux/copy-mode。
- 价值：表面上更接近 tmux 使用习惯。
- 代价：已在 Windows/rmux/WezTerm 现场暴露过错位、右键劫持、空 history 等问题；实现会继续叠加 fragile binding。
- 结论：否决第一版默认方向。

### 方向 C：模式开关

- 提供 `transparent | tmux_like | hybrid` 一类交互模式。
- 价值：可覆盖不同用户偏好。
- 代价：第一版会把尚未稳定的行为变成配置负担，增加测试矩阵和诊断复杂度。
- 结论：暂不进入第一版；若后续真实用户需要，再单独设计。

## 已敲定的设计点

- 已确认：普通 agent pane 采用 GUI-native parity，不追求 Windows/rmux 鼠标绑定与 Linux/macOS tmux 逐条一致。
- 已确认：普通 pane 的拖选复制、右键粘贴以 WezTerm / 系统剪贴板为准；CCB 不默认把右键改写为 `paste-buffer -p`。
- 已确认：普通 pane 滚轮默认不进入 rmux copy-mode，不制造空 scrollback `[0/0]` 体验。
- 已确认：普通 pane 左键单击只负责 focus，不透传不必要 mouse event；目标是单击即可输入，且不破坏拖选。
- 已确认：第一版不新增显式 history viewer、sidebar 查看历史入口或 copy-mode 快捷入口。
- 已确认：sidebar 是 CCB-owned TUI，第一版全接管鼠标交互，包括滚轮、agent 选择、配置入口和退出入口。
- 已确认：sidebar `x` 入口保持 Kill project 语义，不改成仅隐藏 sidebar。
- 已确认：Windows/WezTerm/crossterm 下 `Q` 与 `Shift+Q` 编码差异应兼容到同一 KillProject 语义。
- 倾向：`focus_follows_mouse` / hover focus 作为备选探索项记录，不作为第一版默认行为。

## 选定方向与遗留问题

选定方向是 `windows-rmux-wezterm-native-interaction-parity`：普通 pane 透明化，sidebar 专属接管，滚轮和剪贴板交还 GUI，后端 capture/provider completion 与用户前台滚轮解耦。

核心行为：

- 普通 agent pane 不被 CCB/rmux 鼠标绑定劫持选择、复制、右键粘贴和滚轮。
- 普通 agent pane 单击可聚焦，拖选仍按 WezTerm 原生行为工作。
- sidebar pane 保持 CCB 专属 mouse/key 语义，且绑定必须按 pane identity 分流，不能泄漏到普通 pane。
- live binding snapshot、单元断言和手工 WezTerm runbook 共同验证。

明显不做：

- 不实现完整 tmux-like mouse parity。
- 不新增交互模式配置开关。
- 不新增显式历史查看入口。
- 不改变 sidebar `x` 的 Kill project 语义。

遗留给 design 的问题：

- 当前代码中 Windows/rmux fallback binding 的最终 owner 和测试入口在哪里最合适。
- 如何在测试里稳定区分普通 pane 与 sidebar pane，避免字符串断言过脆。
- 是否需要将 GUI-native parity 作为 ADR 记录，因为该方向是对 tmux-like parity 的结构性取舍。

## 后续 UX Parity 维度记录

本 feature 只处理前台交互。其他 5 个 parity 维度已记录到 `.codestable/brainstorms/windows-rmux-ux-parity-hardening/brainstorm.md`，供后续 `cs-epic` 或独立 feature 拆解：

- 历史与输出 parity。
- pane identity / layout parity。
- 视觉与无干扰 parity。
- 生命周期 parity。
- 可支持性 parity。
