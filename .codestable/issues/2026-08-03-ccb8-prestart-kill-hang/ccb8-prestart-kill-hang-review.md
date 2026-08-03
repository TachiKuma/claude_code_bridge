---
doc_type: issue-review
issue: 2026-08-03-ccb8-prestart-kill-hang
status: passed
reviewer: subagent
reviewed: 2026-08-03
round: 2
lane_a_state: completed
lane_a_ref: "019fc843-9fe9-7910-930e-06eedd203355"
lane_a_reason: ""
lane_b_state: unavailable
lane_b_ref: ""
lane_b_reason: "最终 PID liveness 复审时 ocr llm test 30 秒超时；按协议降级为本地行级核验。"
---

# ccb8-prestart-kill-hang 代码审查报告

## 1. Scope And Inputs

- Issue report: `.codestable/issues/2026-08-03-ccb8-prestart-kill-hang/ccb8-prestart-kill-hang-report.md`
- Issue analysis: `.codestable/issues/2026-08-03-ccb8-prestart-kill-hang/ccb8-prestart-kill-hang-analysis.md`
- Fix note: `.codestable/issues/2026-08-03-ccb8-prestart-kill-hang/ccb8-prestart-kill-hang-fix-note.md`
- Implementation evidence: `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd`
- Diff basis: 外部 wrapper 文件内容审查 + 本仓库 issue 产物新增；`ccb8.cmd` 不在当前 git 仓库内，无法用本仓库 `git diff` 归因。
- Review mode: initial + focused-closure + PID liveness rereview
- Baseline dirty files: 当前仓库存在多处既有 dirty 文件，非本轮 wrapper 修复范围。

### Independent Review

- Detection: multi-agent 独立 reviewer 可用；`ocr llm test` 通过。
- 环节 A 独立隔离 Task agent: independent-agent completed。
- 环节 B OCR CLI: skipped。
- OCR severity mapping: High→blocking/important, Medium→nit/suggestion, Low→discarded。
- Merge policy: 独立 reviewer finding 已逐条本地核验；针对 changes-requested 做 focused closure 后通过。
- Gate effect: `reviewer: subagent`，放行。

## 2. Diff Summary

- 新增：`.codestable/issues/2026-08-03-ccb8-prestart-kill-hang/*`
- 修改：`D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd`
- 新增：`lib/process_liveness.py`
- 修改：`lib/project/identity_store.py`、`lib/ccbd/system.py`、`test/test_project_identity_store.py`
- 删除：none
- 未跟踪 / staged：issue 目录为未跟踪；wrapper 位于仓库外。
- 风险热点：Windows batch/PowerShell 引号与 errorlevel 传播；避免误杀已安装 CCB/v5。

## 3. Adversarial Pass

- 假设的生产 bug：定向清理失败被吞掉，源码开发态残留继续干扰启动。
- 主动攻击过的反例：errorlevel 传播、PID 复用、项目 `.ccb` 与 `.ccb-source-dev` 双 daemon、bounded `kill -f` 超时。
- 结果：独立 reviewer 首轮发现 errorlevel 被吞，已修复并完成 focused closure；PID 复用保守跳过列为残余风险。

## 4. Findings

### blocking

none

### important

none

### nit

- [ ] REV-001 `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd:133` PID 读取仍基于 `findstr` 和冒号分隔，适配当前 pretty JSON；若将来状态文件变成单行 JSON，可能漏清理。当前不阻塞。

### suggestion

none

### learning

- Windows wrapper 中调用 batch 子例程时，内部失败必须逐层检查 `errorlevel`，否则顶层清理 gate 会失效。

### praise

- 新增负向保护优先保守跳过项目 `.ccb` 中已记录的 PID，符合“不影响已安装 CCB/v5”的约束。

## 5. Test And QA Focus

- QA 必须重点复核：在外部项目执行 `.\\ccb8.cmd`，确认 `.ccb-source-dev` 旧 daemon/keeper 被清掉，项目 `.ccb` 的 v5 daemon/keeper 未被停止。
- Evidence pack residual risks / gate warnings：正常启动未在 Codex 内执行，需外部验证。
- 建议新增或加强的测试：若后续把该 wrapper 逻辑产品化，应改为 PowerShell 脚本或 CCB 内部命令测试。
- 不能靠 review 完全确认的点：Windows 实机上 `Stop-Process` 与 bounded `kill -f` 的真实启动前行为。

## 6. Residual Risk

- 极端 PID 复用场景下，如果项目 `.ccb` 状态文件过期且恰好记录源码态 PID，负向保护会保守跳过源码态清理。这符合“不能影响已安装 CCB/v5”的优先级，但可能需要手动清理源码态残留。

## 7. Verdict

- Status: passed
- Next: 用户在外部项目执行正常启动验证；通过后确认修复完成。

## 8. Focused Closure

- Closed findings: 首轮 independent reviewer 的 important finding：定向清理失败 errorlevel 被上层子例程吞掉。
- Attributed delta: `ccb8.cmd` 的 `:StopSourceDevRuntimePids`、`:StopPidsFromJson`、`:StopPidKey` 增加 errorlevel 传播；`:StopSourceDevPid` 增加项目 `.ccb` PID 负向保护。
- Targeted verification: `cmd /d /c ""D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd" --diagnose"`，结果通过并输出 `v8.5.2`。
- Classification: wrapper 逻辑修复；未改 CCB 主程序、公开 API、数据结构或已安装态配置。

## 9. Focused Closure After External Repro Failure

- Trigger: 用户外部执行 `.\\ccb8.cmd` 后故障依旧；只读 dry-run 发现旧清理条件对当前 Windows 命令行返回 `Regex=False`、`ProjectLike=False`，导致 `.ccb-source-dev` PID `14312/14572` 被跳过。
- Delta: `ccb8.cmd:116` 对 `$project` 和 `$cmd` 统一做 `/` 到 `\` 的路径归一化；用大小写不敏感 `IndexOf` 判断项目根；修正 `ccbd\main.py` / `ccbd\keeper_main.py` 的正则匹配。
- Local read-only verification: 最终表达式对 source-dev PID `14312/14572` 返回 `Regex=True`、`ProjectIndex>=0`、`WouldStop=True`；未停止进程，未执行正常启动。
- Independent focused closure: reviewer `019fc804-0dcc-77e2-9085-c48d6ff1ad5e` 复审通过，blocking/important 均为 none。
- Reviewer conclusion: 停止候选仍只来自 `.ccb-source-dev/state/runtime-state/.../ccbd/{lease,keeper,lifecycle}.json`；`.ccb/ccbd` 只用于保护 PID，当前保护 `12652/12720`，不会误杀已安装 `.ccb` v5。
- Residual risk: 若 `.ccb` 保护文件严重陈旧且 PID 被源码态复用，最坏是过度保护导致漏杀 source-dev，不是误杀 v5。

## 10. Final PID Liveness Rereview

- Trigger: 短 runtime 下最新 `ccbd.stderr.log` 暴露源码层根因：Windows / Python 3.14 上 `os.kill(pid, 0)` 对活的已安装 CCB PID 返回 `OSError`，导致 `identity_store._process_exists()` 和 `ccbd.system.process_exists()` 误判 daemon/keeper 不活。
- Delta: 新增 `lib/process_liveness.py`，Windows 分支改用 `OpenProcess(SYNCHRONIZE, False, pid)`；`identity_store.py` 与 `ccbd/system.py` 委托共享 helper；测试覆盖 helper、`ensure_project_identity()` 默认回归路径和 `ccbd.system` 委托。
- Independent rereview: reviewer `019fc843-9fe9-7910-930e-06eedd203355` 复审后 blocking 为 none；原 important finding 均已关闭。其指出的新文件未跟踪交付风险已通过将 `lib/process_liveness.py` 纳入 index 关闭。
- Targeted verification:
  - `python -m pytest test/test_project_identity_store.py test/test_ccbd_startup_identity.py` -> `14 passed`。
  - `python -m py_compile lib/process_liveness.py lib/project/identity_store.py lib/ccbd/system.py` -> passed。
  - `cmd /d /c ""D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd" --diagnose"` -> 输出 `v8.5.2`。
  - 只读函数级验证：`_process_exists(12652)=True`、`_process_exists(12720)=True`、`_legacy_evidence(...).active_runtime=True`。
- Verdict: passed。
