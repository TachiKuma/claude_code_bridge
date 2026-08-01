---
doc_type: feature-brainstorm
feature: 2026-07-25-windows-rmux-visual-no-popup-parity
status: confirmed
summary: Windows/rmux 视觉动态信息采用 evidence-gated dynamic restore，所有恢复路径必须先证明 no-popup
tags: [windows, rmux, wezterm, visual, no-popup, status, border, title, evidence, parity]
---

# Windows Rmux Visual No-Popup Parity Brainstorm

> Stage 0 | 2026-07-25 | 下一步：cs-feat（由主入口选择 lane）

## 想做什么、为什么

当前 roadmap 要求 `windows-rmux-visual-no-popup-parity` 在 design 前单独完成 `$cs-brainstorm`。这个 item 的真实问题不是“再修一次 Git Bash 弹窗”：`.codestable/issues/2026-07-24-windows-rmux-git-bash-popup/windows-rmux-git-bash-popup-fix-note.md` 已经记录过止血修复，Windows + rmux 下禁用了 `ccb-git.sh`、`ccb-status.sh`、`ccb-border.sh`、`#()` 和 `run-shell` 外部 shell hook，避免可见 Git Bash / console 弹窗。

真正要解决的是 Windows/rmux/WezTerm 下视觉动态信息如何恢复或替代，并且恢复前必须能证明不会再次产生可见 popup。状态栏、标题、边框、Git branch、ccbd health、resize/border hook 都是用户可见 polish，但不应为了恢复动态效果把 shell popup 风险重新分散到每个 hook。

本轮讨论收敛为 **evidence-gated dynamic restore**：保留 static fallback 作为安全 baseline，先建立 no-popup probe、visual command policy 和 UX parity evidence；只有某条动态路径有 no-popup evidence，才允许恢复对应动态状态。

## 考虑过的方向

### 方向 A：evidence-gated dynamic restore

- 描述：以当前 static fallback 为安全 baseline，新增或复用 no-popup probe evidence；动态 Git branch、ccbd health、border/title/status 只有通过 probe 后才能恢复。最终产出 `visual_no_popup` 的 UX parity evidence JSON。
- 价值：既不放弃视觉 parity，也不把 popup 风险重新引入默认路径；实现阶段可以按 probe 结果逐项恢复或保留 static fallback。
- 代价：第一版需要先设计机器可读 policy/report 和 live/manual popup evidence；动态恢复不再是无条件打开。
- 结论：选定。

### 方向 B：static-only accepted

- 描述：把当前 static fallback 正式化为完成状态，只要求状态栏、边框和 hooks 不产生可见 popup，不恢复动态 Git branch / ccbd health。
- 价值：风险最低，复用现有止血修复与测试。
- 代价：UX parity 较弱，用户仍看不到动态状态；supportability 只能记录 visual parity partial 或 static fallback。
- 结论：否决为默认方向；保留为 probe 不通过时的 fail-closed fallback。

### 方向 C：直接实现 Windows hidden process renderer

- 描述：绕过 shell hook，新增 Windows hidden execution 或 renderer，主动恢复动态状态。
- 价值：长期可能恢复完整状态栏/边框动态体验。
- 代价：会把范围扩大到 process runner、hidden execution policy、diagnostics 和可能的 installer/support 表达；没有 no-popup evidence 前直接实现风险过高。
- 结论：不作为第一版默认方向；可以成为 evidence-gated dynamic restore 的候选执行路径。

### 方向 D：把动态状态移出状态栏

- 描述：状态栏永久保持轻量静态，把 Git branch、ccbd health、diagnostics 信息迁移到 sidebar 或 doctor。
- 价值：彻底避开 tmux/rmux status hook 执行风险。
- 代价：从“恢复视觉状态”变成“替代视觉状态”，可能弱化 roadmap 对状态栏/标题/边框 parity 的目标。
- 结论：否决为默认方向；可以作为某些高风险动态字段的替代策略。

## 已敲定的设计点

- 已确认：本 item 采用 **evidence-gated dynamic restore**。
- 已确认：当前 Windows/rmux static fallback 是安全 baseline，不是失败状态；没有 no-popup evidence 时必须保持或回退到 static fallback。
- 已确认：动态 Git branch、ccbd health、border/title/status 恢复必须先有 no-popup probe evidence。
- 已确认：不复活可见 shell hook：不得默认恢复 `#(ccb-git.sh)`、`#(ccb-status.sh)`、`run-shell ccb-border.sh`、resize shell hook 或任何会产生 Git Bash / console popup 的路径。
- 已确认：本 item 必须产出 `evidence/windows-rmux-ux-parity-evidence.json`，且 `parity_dimension=visual_no_popup`。
- 已确认：本 item 不重复定义 `rmux-packaging-docs-contracts` 的 base support projection、npm gate、`install.ps1` gate 或 release guard；只提供 UX parity overlay evidence。
- 已确认：owner 已批准本 brainstorm 结论，并允许进入 feature design。

## 选定方向与遗留问题

选定方向是 `windows-rmux-visual-no-popup-parity`：建立 Windows/rmux 视觉 no-popup parity evidence，证明状态栏、标题、边框和动态状态路径不会产生可见 Git Bash / console popup；在证据通过的路径上恢复或替代动态信息，在证据缺失或失败时 fail-closed 保持 static fallback。

核心行为：

- 生成可机器读取的 visual command policy / no-popup evidence，覆盖 `dynamic_status_enabled`、`execution_kind`、`popup_probe_status`、`disabled_reason` 等字段。
- 验证当前 static fallback 不包含 shell scripts、`#()`、`run-shell` 或可见 popup 风险。
- 为动态 Git branch、ccbd health、border/title/status 恢复定义 no-popup gate；未通过 gate 不得写成 full pass。
- 产出 roadmap §4.1 `WindowsRmuxUxParityEvidence`，固定 `parity_dimension=visual_no_popup`。

明显不做：

- 不默认恢复 `ccb-git.sh` / `ccb-status.sh` / `ccb-border.sh` shell hook。
- 不把 Windows hidden process renderer 作为无证据默认实现。
- 不修改 foreground mouse/focus/scroll policy；该边界由 interaction feature 管理。
- 不修改 output/capture、pane identity/layout 或 lifecycle/recovery 契约。
- 不提升 support tier，不修改 npm/install gate，不发布任何包。

遗留给 design 的问题：

- no-popup probe 的证据形式：process sampling、live rmux `show-options/show-hooks/list-keys` transcript、WezTerm 前台手工记录，还是组合 report。
- 动态恢复路径的第一版范围：Git branch、ccbd health、title、border 是否都作为 candidates，还是先只恢复低风险字段。
- `WindowsRmuxVisualCommandPolicy` 是否只作为 feature evidence JSON 内部结构，还是也要投影到 doctor/diagnostics 供 supportability feature 消费。
