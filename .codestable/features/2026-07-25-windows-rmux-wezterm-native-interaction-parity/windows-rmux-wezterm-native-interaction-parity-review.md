---
doc_type: feature-review
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: passed
reviewer: subagent
reviewed: 2026-07-27
round: 3
lane_a_state: completed
lane_a_ref: "agent:019fa387-061d-7830-b6aa-be51d79ea44d"
lane_a_reason: "independent QA-fix review completed; important sidebar wheel scope finding and nit test-process finding handled"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "workspace contains unrelated dirty files and OCR scope is ambiguous; local line review covered current feature files"
---

# windows-rmux-wezterm-native-interaction-parity 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-gate-results.json`
- DoD results: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-dod-results.json`
- Implementation evidence: `review-packet-round3.md`、本轮验证命令输出、`evidence/live-binding-snapshot.txt`、`evidence/manual-wezterm-runbook.md`
- Diff basis: 当前工作区 diff；本轮代码审查范围为 `lib/cli/services/tmux_ui_runtime/service.py`、`test/test_v2_tmux_ui.py`、`tools/ccb-agent-sidebar/src/tui.rs`
- Review mode: full-rereview after QA-fix
- Baseline dirty files: `.codestable/reference/agent-conventions.md` 来自 runtime sync；`bin/ccb-agent-sidebar.exe` 为进入本轮前已有 binary dirty；二者不纳入本 review verdict。

### Independent Review

- Detection: independent Task agent 可用并完成，agent id `019fa387-061d-7830-b6aa-be51d79ea44d`。
- 环节 A 独立隔离 Task agent: independent-agent completed。
- 环节 B OCR CLI: skipped。
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded。
- Merge policy: 独立 reviewer 结论已逐条用仓库事实核验；important 已修复后重跑验证。
- Gate effect: `reviewer: subagent`，满足 feature review gate。

## 2. Diff Summary

- 新增：`review-packet-round3.md`
- 修改：`lib/cli/services/tmux_ui_runtime/service.py`、`test/test_v2_tmux_ui.py`、`tools/ccb-agent-sidebar/src/tui.rs`、`evidence/live-binding-snapshot.txt`、`evidence/manual-wezterm-runbook.md`
- 删除：Windows/rmux fallback 中的 settings/kill mux 坐标分支 helper。
- 未跟踪 / staged：`review-packet-round3.md` 未跟踪；无 staged diff。
- 风险热点：Windows/rmux root mouse binding、sidebar crossterm 鼠标事件透传、真实 WezTerm GUI 前台复测。

## 3. Adversarial Pass

- 假设的生产 bug：sidebar settings / x 仍可能因为 rmux/WezTerm/crossterm 端到端事件派发差异而前台失败。
- 主动攻击过的反例：fallback 仍发送 `c/Q`、仍使用 `#{mouse_x}` / `#{mouse_y}` mux 条件、sidebar wheel 被遗漏、ordinary pane wheel 进入 copy-mode/scroll command、Rust header 测试只在 Unix 运行。
- 结果：自动化和 live `list-keys` 已关闭代码路径风险；真实前台结果仍必须由 QA/owner 复测确认。

## 4. Findings

### blocking

none

### important

none

Round 3 独立 reviewer 的 important 已处理：

- REV-001：Windows/rmux fallback 漏掉 sidebar wheel 分流。已补 `WheelUpPane` / `WheelDownPane` 与 left-click 一致的 sidebar passthrough 绑定；ordinary 分支仍只 `select-pane -t =`，不进入 copy-mode / scroll command / paste-buffer。证据：`service.py`、`test_v2_tmux_ui.py`、`evidence/live-binding-snapshot.txt`。

### nit

none

Round 3 独立 reviewer 的 nit 已处理：

- REV-002：Rust header hit-test 测试解除 Unix-only 后不应 spawn 当前测试二进制。已改为纯 `header_action_at` 命中断言；settings launch 失败路径保留在单独测试。

### suggestion

- 已采纳：对 `MouseDown1Border`、`WheelUpPane`、`WheelDownPane` 增加与 `MouseDown1Pane` 相同的 fake binding 精确断言。

### learning

- Windows/rmux fallback 里能依赖 `-t =` 定位鼠标 pane，但不应在 mux 层用 header 坐标表达式模拟 sidebar 内部按钮；sidebar 内部按钮交给 Rust TUI 的 `header_action_at` 更直接。

### praise

- 生产代码净减少，fallback 行为收敛为 sidebar passthrough 与 ordinary focus 两个分支，没有新增配置或公共接口。

## 5. Test And QA Focus

- QA 必须重点复核真实 Windows + WezTerm + rmux 前台：sidebar `⚙` 点击、sidebar `x` KillProject、拖选行偏移重新归因。
- 自动化已覆盖：不再出现 `send-keys -t = c` / `send-keys -t = Q`、不再出现 `#{mouse_x}` / `#{mouse_y}` header 分支、fallback 全部 `if-shell -F -t =`、ordinary 不进入 copy-mode/scroll/paste-buffer。
- 不能靠 review 完全确认的点：WezTerm/rmux/crossterm 端到端鼠标事件是否确实抵达 Rust TUI，以及 pane-asymmetric 拖选偏移的真实归因。

## 6. Residual Risk

- 右键粘贴与 ordinary pane 原生滚轮仍按 design 作为 GUI-native residual，不是本轮代码 blocker。
- 拖选行偏移不能直接写死为 rmux 外部 residual；manual evidence 显示 pane-asymmetric，需要 owner 前台复测/重判。
- sidebar `⚙` / `x` 的真实前台结果仍需 owner 复测；当前 review 只能确认代码路径和绑定内容。

## 7. Verdict

- Status: passed
- Next: Goal feature 进入 `cs-feat` QA；QA 在 owner 前台复测前应保持 blocked，不得进入 acceptance。

## 8. Focused Closure

none
