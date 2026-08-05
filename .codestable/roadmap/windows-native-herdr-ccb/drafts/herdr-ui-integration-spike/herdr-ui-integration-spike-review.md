---
doc_type: code-review
scope: herdr-ui-integration-spike
status: changes-requested
reviewer: subagent+ocr
reviewed: 2026-08-05
round: 1
lane_a_state: completed
lane_a_ref: "019fd1d2-079a-7cd2-942a-145072bd3de0"
lane_a_reason: ""
lane_b_state: completed
lane_b_ref: "ocr review"
lane_b_reason: ""
---

# herdr-ui-integration-spike 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/README.md`
- Checklist: `.codestable/roadmap/windows-native-herdr-ccb/follow-ups/herdr-ui-integration-spike.md`
- Evidence pack: `.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260805-194307/`
- Gate results: `git diff --check` 通过，无空白错误。
- DoD results: none
- Implementation evidence: 当前工作区 unstaged diff；staged diff 为空。
- Diff basis: `git diff --stat` 为 5 files, 76 insertions, 21 deletions。
- Review mode: initial
- Baseline dirty files: 当前 5 个 modified 文件和 1 个 untracked evidence 目录均纳入本轮 review。

### Independent Review

- Detection: 独立 Task agent 可用；OCR CLI 可用。
- 环节 A 独立隔离 Task agent: independent-agent + completed
- 环节 B OCR CLI: completed
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded
- Merge policy: 各环节结果已逐条本地核验后合并；OCR 关于 Windows 空文件 `msvcrt.locking(..., 1)` 必然失败的结论已用本地临时空文件复现排除。
- Gate effect: completed lanes merged；当前 findings 阻断 passed verdict。

## 2. Diff Summary

- 新增：none
- 修改：
  - `.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1`
  - `ccb8.ps1`
  - `lib/ccbd/app_runtime/lifecycle.py`
  - `lib/storage/locks.py`
  - `lib/terminal_runtime/herdr_backend_runtime/cli.py`
- 删除：none
- 未跟踪 / staged：未跟踪 evidence `run-20260805-194307/`；staged diff 为空。
- 风险热点：Windows wrapper 参数绑定、ccbd lifecycle 恢复、跨进程锁、Herdr foreground attach 语义、spike evidence 路径采集。

## 3. Adversarial Pass

- 假设的生产 bug：多次 `ccb8.cmd` / `ccb8.cmd --kill f` 后，旧 ccbd 状态、Windows 参数绑定和 Herdr attach 降级会把真实失败伪装成启动或采集成功。
- 主动攻击过的反例：frozen lifecycle 状态转换、缺失导入路径、PowerShell 5.1 `[char[]]` 参数拆分、installed PID 保护绕过、runtime state root 已包含 project id 的 relocated 场景、foreground attach timeout/non-zero。
- 结果：升级为 findings 的项见下；Windows 空文件锁静态疑点未升级，保留为测试建议。

## 4. Findings

### blocking

- [ ] REV-001 `lib/ccbd/app_runtime/lifecycle.py:50` stale mounted owner 恢复路径会在运行时失败。
  - Evidence: 新增代码在 `lifecycle.py:55` 调用 `process_exists(owner_pid)`，但文件 import 列表没有从 `ccbd.system` 导入该符号；同一分支在 `lifecycle.py:60` 执行 `lifecycle.phase = 'starting'`，而 `CcbdLifecycle` 在 `lib/ccbd/services/lifecycle.py:36` 是 `@dataclass(frozen=True)`。
  - Impact: 命中“旧 ccbd 崩溃后 lifecycle 仍为 mounted 且 owner_pid 已死”的 expected-fence 恢复路径时，会先遇到 `NameError`，补 import 后仍会遇到 `FrozenInstanceError`。该路径正对应本轮多次 kill/start 后需要恢复的场景，阻断验收。
  - Expected fix scope: 用现有 immutable helper 构造新的 lifecycle 值，并显式处理旧 `owner_pid` / `owner_daemon_instance_id`；补 stale mounted + dead owner_pid + expected fence 的单测。

- [ ] REV-002 `ccb8.ps1:544` prestart cleanup final sweep 绕过 installed CCB PID 保护。
  - Evidence: `Stop-SourceDevRuntimePids` 在 `ccb8.ps1:353` 读取 `Read-ProtectedInstalledPids`，并在 `ccb8.ps1:358` 跳过 installed PID；新 final sweep 从 `ccb8.ps1:544` 重新读取 targets 后直接 `Stop-Process`，没有复用 protected 集合。
  - Impact: 如果 source-dev state 文件仍指向 installed CCB 的 PID，final sweep 会越过前置保护杀掉 installed daemon。`--kill f` / prestart cleanup 的边界从“只清 source-dev runtime”扩大到可能影响已安装实例。
  - Expected fix scope: final sweep 必须沿用同一 protected PID 策略；补一个 source-dev stale state 指向 installed PID 的 wrapper 测试。

### important

- [ ] REV-003 `ccb8.ps1:15` `[char[]]` 参数修复条件不覆盖多字符单参数。
  - Evidence: 代码先 `$CcbArgs = @($CcbArgs)`，再只在 `$CcbArgs.Count -eq 1 -and ... -eq 'Char'` 时重组。对抗性模拟 `[char[]]"ps"` 后数组会是两个 Char 元素，条件不会触发。
  - Impact: 如果 PowerShell 5.1 真实绑定把 `ps` / `ping` / `doctor` 这类单参数拆成 char array，wrapper 仍会把单参数逐字符 splat 给 Python，路由异常继续存在。
  - Expected fix scope: 在所有 Count 语义判断前识别“所有元素都是 Char”的数组并 join 回单个字符串；补 `[char[]]"ps"`、单参数 `ps`、`doctor ps`、`ping all` 覆盖。

- [ ] REV-004 `.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1:1007` startup state files 采集路径重复追加 project id。
  - Evidence: 最新 evidence 的 `startup-state-files/runtime-root-ref.json` 中 `runtime_state_root` 已是 `D:\.c8\rs\<project_id>`；`lib/storage/paths_ccbd.py:29` 定义 ccbd state dir 为 `runtime_state_root / 'ccbd'`。但脚本当前拼出 `$runtimeStateRoot\$runtimeProjectId\ccbd`，manifest 已显示搜索了重复 project id 路径并跳过 `lease.json` / `keeper.json` / `lifecycle.json`。
  - Impact: startup-state-files 维度会产生假阴性，后续 QA 无法依赖该 evidence 定位启动状态文件问题。
  - Expected fix scope: relocated runtime root 分支应直接拼 `$runtimeStateRoot\ccbd`；用 `runtime-root-ref.json` fixture 覆盖。

- [ ] REV-005 `lib/terminal_runtime/herdr_backend_runtime/cli.py:767` foreground attach 失败被吞掉但返回 `status: ok`。
  - Evidence: 新代码对 `herdr session attach` 增加 `timeout=5`，但捕获 `OSError` 和所有 `subprocess.SubprocessError` 后直接 `pass`，随后返回 `status: ok`。上层 `lib/cli/services/start_foreground.py:200` 仍以 `attach_namespace` 抛异常作为 foreground attach 失败信号。
  - Impact: 非 Herdr UI 终端、attach timeout 或 attach non-zero 时，用户可能得到“attach 成功”的假阳性，public foreground attach workflow 的验收可信度下降。
  - Expected fix scope: 返回语义需要区分 attached 与 workspace-focused-but-attach-degraded，或只在明确 Herdr UI/daemon 场景降级；补 `TimeoutExpired` / `CalledProcessError` 测试。

### nit

- [ ] REV-006 `lib/storage/locks.py:3` 新增 `import time` 未使用。

### suggestion

- [ ] REV-007 `lib/storage/locks.py:27` Windows byte-range lock 建议补专项测试。
  - Evidence: 本地空文件 `msvcrt.locking(..., 1)` 复现为可成功加锁，因此不采纳 OCR 的 blocking 结论；但当前 diff 没有覆盖双进程 contention。
  - Impact: 跨进程互斥是 ccbd state 写入的关键路径，建议用 Windows 专项测试锁定行为。

### learning

- Herdr agents panel 只能作为 diagnostics evidence，不能作为 CCB provider authority；本轮生产代码没有打破该边界。

### praise

- `ccb8.ps1` prestart `kill -f` 使用 `UseShellExecute=false`、`CreateNoWindow=true` 并捕获 stdout/stderr，方向上符合减少 Herdr UI 闪窗和保留诊断证据的目标。

## 5. Test And QA Focus

- QA 必须重点复核：多次 `.\ccb8.cmd`、`.\ccb8.cmd --kill f` 后的 stale lifecycle 恢复；installed CCB 与 source-dev CCB 并存时的 PID 保护；PowerShell 5.1 单参数 wrapper 行为。
- Evidence pack residual risks / gate warnings：`run-20260805-194307/summary.json` 仍记录 `observed_windows_flash=true`，而 follow-up 中 2026-08-05 04:05 复验记录为 false；需要下一轮真实 Herdr UI QA 消除该不一致。
- 建议新增或加强的测试：ccbd expected-fence stale mounted/dead owner 单测；wrapper `[char[]]` 参数测试；relocated `runtime-root-ref.json` fixture；Herdr attach timeout/non-zero 语义测试；Windows 双进程 file lock contention 测试。
- 不能靠 review 完全确认的点：Herdr UI 闪窗是否仍存在、`session attach` 在不同终端宿主中的真实交互表现。

## 6. Residual Risk

- 本轮只读 review 没有运行 pytest；已运行的 `git diff --check` 只能覆盖空白问题。
- evidence 中 `observed_windows_flash=true` 与已有 follow-up 记录冲突，需要后续重新采集时明确不要传误导性的人工 flag。

## 7. Verdict

- Status: changes-requested
- Next: 进入来源实现技能的 review-fix；修复 REV-001 和 REV-002 后再做 focused closure，若触碰 Herdr attach 契约建议完整复审相关 foreground attach 流程。

## 8. Focused Closure

- none
