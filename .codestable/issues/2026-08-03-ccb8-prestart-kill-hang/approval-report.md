---
doc_type: issue-approval
issue: 2026-08-03-ccb8-prestart-kill-hang
status: pending
checkpoint: ConfirmFixCompletion
---

# 修复完成确认

## 待确认事项

修复已实现并通过独立 focused closure review。正常启动验证需要在外部项目执行 `.\\ccb8.cmd`，确认源码版 CCB 能启动，且已安装 CCB/v5 未被停止。

外部复现失败后的新增根因已定位并修正：旧 wrapper 清理块没有对 Windows 路径分隔符做归一化，且正则没有稳定命中 `ccbd\main.py` / `ccbd\keeper_main.py`，导致 `.ccb-source-dev` PID `14312/14572` 被识别后又被筛掉。最终只读 dry-run 已确认当前匹配条件会命中这两个 source-dev PID。

再次外部复现后，又定位到 wrapper 的源码根 fallback `E:\GITHUB~1\TACHIK~1\CLAUDE~1` 在本机实际指向 `claude_code_bridgebak`，导致外部项目没有显式 `CCB_SOURCE_ROOT` 时仍运行备份源码。已改为 `E:\GITHUB~1\TACHIK~1\claude_code_bridge` 并同步到外部项目 wrapper；wrapper 自检、full-env 自检、AST、BOM、旧路径残留扫描和 SHA 一致性均通过。正常启动仍未在 Codex 内执行。

最新外部复现已确认源码 runtime 实际位于 `D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03\ccbd`。当前卡点不是旧备份源码，而是 Windows 控制台中断传播到后台 keeper/ccbd 子进程，以及 `ensure_daemon_started()` 对 failed 终态的等待语义。相关修复已落地并通过 focused tests；仍需外部重新运行 `.\\ccb8.cmd` 做实机验证。

用户最新提供的 `bug.txt` 表明 `.\\ccb8.cmd --diagnose` 已通过，正常 `.\\ccb8.cmd` 失败进入 `invalid Herdr namespace ref`。只读 runtime 证据显示 ccbd 已启动、healthy 且 socket 可连接，问题已经推进到 Herdr project namespace 层。已修复旧 tmux namespace state 被注入 Herdr backend 的问题，并让 Herdr CLI adapter 复用 Windows 无窗口 `_run` 包装以减少窗口闪烁；相关 pytest、py_compile 和 diff check 均已通过。正常启动仍未在 Codex 内执行。

随后外部启动已越过 namespace ref 错误，但失败为 `authoritative topology cmd pane is missing`。只读 runtime 证据显示 daemon 在 `pane_recovery:cmd` 循环中持续重建 Herdr namespace。已修复 materialize 后 cmd pane 只靠 metadata 回读导致丢失的问题，并移除 start flow 对 Herdr pane 的 tmux `%` id/空 socket 假设；相关 namespace state、Herdr/backend 和 start-flow 定点测试均已通过。正常启动仍需在外部项目复验。

## Owner 决策

- status: pending
- checkpoint: ConfirmFixCompletion
- decision: 待外部验证后确认
