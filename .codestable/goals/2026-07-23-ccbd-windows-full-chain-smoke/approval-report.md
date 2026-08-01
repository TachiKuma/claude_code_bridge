---
doc_type: approval-report
unit: .codestable/goals/2026-07-23-ccbd-windows-full-chain-smoke
status: approved
reason: blocker
approvals:
  native-windows-full-chain-runner: approved
  expand-scope-windows-runtime-fix: approved
  restore-rmux-090-dependency: approved
approval_groups: {}
created_at: 2026-07-23
---

# Approval Report

## Decision History

- 2026-07-23：owner 在对话中回复“确认”，批准 `approval-report.md#native-windows-full-chain-runner`。
- 2026-07-23：已消费该批准并执行多次 CMD-004。runner/parser 资产验证通过，但真实 native Windows transcript 未通过；失败证据已记录在 `iterations/002.md` 和 `artifacts/ccbd-windows-full-chain-smoke/transcript.json`。
- 2026-07-23：owner 回复“我确认 expand-scope-windows-runtime-fix 和 restore-rmux-090-dependency”，批准生产 runtime Windows fix 与 `rmux 0.9.0` 依赖恢复。

## Decision Needed

是否批准扩大当前 goal 范围，处理真实 CMD-004 暴露的 goal 外部 blocker：

- 命名授权一：`approval-report.md#expand-scope-windows-runtime-fix`。
- 命名授权二：`approval-report.md#restore-rmux-090-dependency`。

## Why Now

当前 full-chain smoke 已证明 `ccb -> ccbd` 和 TCP loopback 证据可采集，route approval bootstrap 后 backend selection 也能进入 `rmux`。但真实链路仍不能 pass：

- PATH 上的 `rmux` 是 `rmux 0.8.0`，与 route approval 选择的 `rmux 0.9.0` 证据不匹配。
- 先前记录的 WinGet `rmux 0.9.0` 路径当前不存在。
- 生产 runtime 在 Windows 上触发 `module 'signal' has no attribute 'SIGKILL'`，导致 start/ask/kill cleanup 失败。

这些都不是 runner/parser 本身能安全修正的问题。

## Context

已完成：

- Parser / runner / tests / scope guard 资产实现。
- focused pytest：25 passed。
- PowerShell parse：`parse-ok`。
- scope guard：`ok: true`。
- CMD-004 真实执行，生成 redacted transcript 与 command artifacts。

关键失败证据：

- `artifacts/ccbd-windows-full-chain-smoke/commands/preflight-rmux-version.stdout.txt` -> `rmux 0.8.0`。
- `artifacts/ccbd-windows-full-chain-smoke/commands/ccb-start.stderr.txt` -> `module 'signal' has no attribute 'SIGKILL'`。
- `artifacts/ccbd-windows-full-chain-smoke/commands/ccb-ask.stderr.txt` -> `module 'signal' has no attribute 'SIGKILL'`。
- `artifacts/ccbd-windows-full-chain-smoke/commands/ccb-kill-force.stderr.txt` -> same Windows SIGKILL traceback。
- `artifacts/ccbd-windows-full-chain-smoke/transcript.json` -> parser verdict `test_design_failure`，ask artifact 为空，cleanup failed。

## Options

1. 批准两项授权（推荐，仅当 owner 接受扩大范围）。
   允许创建/引用 issue 产物并修改生产 runtime 的 Windows cleanup/startup bug，同时恢复或安装 `rmux 0.9.0` 并用 `CCB_RMUX_BIN` 指向匹配 binary，然后重跑 CMD-004/CMD-005。

2. 只批准 runtime fix。
   允许修复 Windows `SIGKILL` bug，但不改变本机 rmux dependency。修完后仍可能被 `rmux 0.8.0` 能力不匹配阻塞。

3. 只批准 rmux dependency 恢复。
   允许恢复或安装 `rmux 0.9.0`，但不修改生产 runtime。即使 binary 匹配，`SIGKILL` cleanup/startup bug 仍可能阻塞 start/ask/kill。

4. 暂不扩大范围。
   保持 goal blocked。当前产物保留为失败证据，不把 full-chain smoke 标记为 done。

## Recommendation

推荐选项 1。原因是两个 blocker 都在真实 CMD-004 路径上出现，单独处理任一项都不能可靠闭合 full-chain pass。

## Risks And Tradeoffs

- 修复 Windows runtime cleanup/startup 属于生产代码范围，会越过当前 smoke goal 的 scope guard，需要相应 issue/fix governance。
- 恢复或安装 `rmux 0.9.0` 属于本机依赖状态变更；可能影响后续本地验证命令。
- 继续重跑 CMD-004 仍会启动 temp project runtime、提交 `ccb ask`，并尝试 `ccb kill -f` cleanup。
- 不批准扩大范围则当前 roadmap item 不能验收为 done。

## Non-Automatic Actions

不会自动执行 `git commit`、`git push`、发布、merge、tag、release、全局依赖安装或生产切换。任何 package install / dependency restore 都需要本 approval 的明确授权后才执行。

## After You Answer

如果批准两项授权，我会先创建或引用对应 issue/fix 产物，修复 Windows runtime `SIGKILL` 路径，再恢复 `rmux 0.9.0` binary，最后重跑 CMD-004/CMD-005 并继续功能验收。

如果只批准其中一项，我会只做该项并保留剩余 blocker。

如果不批准，goal 保持 blocked，并以 Iteration 002 作为当前终态证据。
