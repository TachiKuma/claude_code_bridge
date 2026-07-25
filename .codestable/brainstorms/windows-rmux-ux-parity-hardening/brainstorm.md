---
doc_type: brainstorm
slug: windows-rmux-ux-parity-hardening
created: 2026-07-25
status: active
summary: 记录 Windows/rmux/WezTerm 从“基本跑通”走向 Linux/macOS 同等体验的 UX parity 维度
tags: [windows, rmux, wezterm, ux-parity, hardening, epic-candidate]
---

# Windows Rmux UX Parity Hardening

> 创意空间 | 2026-07-25 | 下一步：cs-epic

## 出发点

当前 native Windows + WezTerm + rmux 路线已经进入“基本跑通”阶段，但这不等于 Linux/macOS tmux 路线的日用体验已经完全同等。近期 Windows/rmux 现场已暴露过多个体验类缺口：Git Bash 弹窗、鼠标滚轮无法回看、右键粘贴被 rmux buffer 劫持、pane 点击需要双击、文本选区错位、pane id target alias 导致 layout 绑定错误等。

因此后续需要把“同等体验”拆成可证伪的 parity 维度，而不是只用 full-chain smoke 证明链路可运行。

## 聊过的方向

### 1. 前台交互 parity

已收敛为独立 feature：`.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-brainstorm.md`。

关键决策：普通 pane 采用 WezTerm GUI-native parity；sidebar 全接管；不追求 tmux-like 鼠标逐条一致。

### 2. 历史与输出 parity

需要覆盖 scrollback、copy-mode、capture-pane、provider completion capture、ANSI、宽字符、换行、尾部空白和 wrapping 等行为。

初步边界：

- 用户前台滚轮不作为后端 capture 的验证路径。
- provider completion 和 `ccb ask` 依赖后端 capture 契约，不能依赖用户是否能滚动。
- 如果后续需要 history viewer 或显式 copy-mode 入口，应作为独立 feature 设计，不混入第一版前台交互。

### 3. Pane identity / layout parity

需要系统性收口 pane id、pane index、split 后 target canonicalization、布局重建、agent 与 pane 绑定、重启后身份恢复。

已知背景：

- Windows/rmux 曾暴露 `%N` exact pane id 与 pane index alias 混淆问题。
- 这类问题会影响 layout、鼠标目标、provider runtime 绑定和 recovery，不能只按单个 bug 修。

### 4. 视觉与无干扰 parity

需要覆盖状态栏、标题、边框、动态状态、Git 分支、ccbd health、无 Git Bash 弹窗、无额外 console window。

已知背景：

- 当前 Windows/rmux 为避免 Git Bash 弹窗，已临时禁用外部 shell 状态脚本、border hook 和 resize shell hook。
- 这属于止血，不是最终 parity；后续若恢复动态状态，应采用 rmux 原生隐藏执行或 Windows-safe 非弹窗路径。

### 5. 生命周期 parity

需要覆盖 attach/reconnect、关闭 WezTerm 后 namespace/provider 继续存活、重新 `ccb` attach、`ccb kill` 清理、pane/provider/rmux daemon crash 后恢复或 degraded diagnostics。

初步边界：

- 这不是前台交互问题，而是 authority、cleanup、supervision 和 diagnostics 问题。
- full-chain smoke 只能证明最小 start/ask/kill，不能替代长期日用 recovery parity。

### 6. 可支持性 parity

需要覆盖 doctor/diagnostics、install.ps1、npm win32、support tier、runbook、错误分类和用户可见承诺。

初步边界：

- support tier 必须由 route approval、validation matrix、local install smoke、npm gate 等机器证据驱动。
- 不能在未完成 validation/full support gate 前把 Windows/rmux 描述为 supported。
- README、installer、doctor、package metadata 不能各自发明状态。

## 当前倾向

倾向于把 Windows/rmux UX parity hardening 拆成一个后续 epic，而不是继续塞进当前 `windows-rmux-native-backend` 的“基本跑通”终点。

建议拆解方向：

- foreground interaction parity：已进入 feature brainstorm。
- output/capture parity：机器 capture 与用户可见历史解耦验证。
- pane identity/layout parity：身份 canonicalization 与 layout 恢复。
- visual/no-popup parity：状态栏和 hook 的 Windows-safe 实现。
- lifecycle/recovery parity：attach/reconnect/kill/crash recovery。
- supportability parity：doctor/install/support tier/docs contract。

## 已敲定的点

- 已确认：下一步优先处理前台交互 parity。
- 已确认：普通 pane 选择 GUI-native 体验，而不是 tmux-like 鼠标 parity。
- 已确认：另外 5 个维度先作为后续 parity hardening 输入记录，不进入第一版交互 feature 范围。

## 遗留问题 & 下一步

- 是否将 `windows-rmux-ux-parity-hardening` 拆成正式 `cs-epic` roadmap。
- 是否为 “Windows/rmux 选择 GUI-native parity，而不是 tmux-like mouse parity” 写 ADR。
- 现有 `windows-rmux-native-backend` 中 pending 的 `ccbd-windows-full-chain-smoke` 与 `rmux-packaging-docs-contracts` 如何和 parity hardening 二期衔接。
