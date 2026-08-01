---
doc_type: feature-brainstorm
feature: 2026-07-25-windows-rmux-output-capture-parity
status: confirmed
summary: Windows/rmux output capture parity 先建立可证伪证据矩阵和差异归因，不预设重写 Rmux IO
tags: [windows, rmux, wezterm, output, capture, completion, parity, evidence]
---

# Windows Rmux Output Capture Parity Brainstorm

> Stage 0 | 2026-07-25 | 下一步：cs-feat（由主入口选择 lane）

## 想做什么、为什么

当前 roadmap 已确认 `windows-rmux-output-capture-parity` 必须在 design 前单独经过 `$cs-brainstorm`。这个 item 的真问题不是“再实现一次 capture”，而是 Windows/rmux/WezTerm 下用户可见历史、后端 machine capture、provider completion parser 三条路径是否能被证据区分、对照和归因。

已有 `rmux-send-capture-logging` 已 accepted，覆盖 `RmuxBackend.capture_pane()`、真实 `raw_bytes`、ANSI mode、trim policy、logging bridge 和 provider completion fixtures。直接把本 item 设计成“修 Rmux capture”会重做已验收的 IO 层，并把用户 scrollback 和机器 capture 混成一个问题。

本轮讨论收敛为 evidence-first：先建立 parity fixture/report 与差异分类，只有证据证明生产缺口时，才在 design 中转成实现任务。

## 考虑过的方向

### 方向 A：parity evidence first

- 先建立 capture / scrollback / provider completion 的对照证据、fixture 和分类报告。
- machine capture、provider completion、user-visible history 三条证据路径互不替代。
- Linux/macOS tmux 作为强 baseline，但允许 documented delta；差异必须分类和解释，不要求默认字节级完全一致。
- 价值：复用 `rmux-send-capture-logging` accepted baseline，只补 UX parity delta、跨平台 baseline 刷新和差异归因，避免无证据重写 IO。
- 代价：如果最终发现真实生产缺口，还需要在 design 中把缺口转成实现任务。
- 结论：选定。

### 方向 B：修复优先

- 直接围绕当前怀疑的 capture 缺口设计实现，证据作为附带产物。
- 价值：如果缺口已明确，会更快进入代码修复。
- 代价：当前没有新的失败证据足以推翻 `rmux-send-capture-logging` accepted 结论；容易把已验收的 Rmux IO 层重做一遍。
- 结论：否决第一版默认方向。

### 方向 C：体验优先

- 把 WezTerm 前台 scrollback / 回看体验作为第一目标，machine capture 和 provider completion 只做回归保护。
- 价值：贴近用户日用体验。
- 代价：roadmap 已把前台交互和 output/capture 分开；用户滚轮/scrollback 不能替代 provider completion 所需的后端 capture 证据。
- 结论：否决第一版默认方向；user-visible history 只作为 supporting evidence。

## 已敲定的设计点

- 已确认：本 item 采用 **parity evidence first**，不预设重写 Rmux IO。
- 已确认：证据矩阵分为三条互不替代的路径：
  - machine capture fixtures：`RmuxBackend.capture_pane()` 输出，覆盖 ANSI、宽字符、wrapping、尾部空白、line range、raw bytes。
  - provider completion fixtures：把 capture/log 文本喂给 Codex、Claude、AGY、DeepSeek 等 completion detector，证明 parser 可消费。
  - user-visible history check：WezTerm 前台 scrollback / 回看只作为 UX supporting evidence，不能替代 machine capture。
- 已确认：Linux/macOS tmux 是强 baseline，但允许 documented delta；相同 fixture 在 tmux 与 Windows/rmux 跑，差异必须分类，不要求字节级完全一致才算通过。
- 已确认：差异分类应至少覆盖 `pass`、`known_delta`、`product_bug`、`provider_failure`、`terminal_scrollback_only` 或等价枚举。
- 已确认：design 必须复用 `rmux-send-capture-logging` acceptance 作为 baseline，只补 UX parity delta、跨平台 baseline 刷新和差异归因。
- 已确认：owner 已批准本 brainstorm 结论，并允许进入 feature design。

## 选定方向与遗留问题

选定方向是 `windows-rmux-output-capture-parity`：建立 Windows/rmux/WezTerm output capture parity evidence，证明 machine capture、provider completion 和 user-visible history 的边界与差异归因。

核心行为：生成可重复的 parity fixture/report，覆盖 ANSI、宽字符、wrapping、尾部空白、raw bytes、line range 和 provider completion detector 消费路径。

明显不做：不默认重写 Rmux IO；不把用户滚轮或 WezTerm scrollback 当作 provider completion / machine capture 证据；不修改 provider completion parser 来适配不稳定 capture。

遗留给 design 的问题：

- evidence JSON 是否复用 roadmap 的 `windows-rmux-ux-parity-evidence.json`，还是在该 JSON 下引用更细的 capture parity report。
- documented delta 的枚举和 failure class 如何与 roadmap §4.1 `failure_class` 对齐。
- 没有 native Windows + WezTerm 前台时，user-visible history check 应记为 `blocked` 还是 `partial`。
