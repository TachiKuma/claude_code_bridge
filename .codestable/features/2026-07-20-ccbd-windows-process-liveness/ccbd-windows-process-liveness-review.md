---
doc_type: feature-review
feature: 2026-07-20-ccbd-windows-process-liveness
status: passed
reviewer: subagent+ocr
reviewed: 2026-07-21
round: 2
lane_a_state: completed
lane_a_ref: "019f8560-2ccc-7622-8d94-b4a7ca3c3406"
lane_a_reason: ""
lane_b_state: completed
lane_b_ref: ""
lane_b_reason: "ocr CLI completed synchronously; second pass generated 0 comments, with a non-blocking attempted read of non-existent lib/ccbd/socket_server_runtime.py"
---

# ccbd-windows-process-liveness 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/dod-results.json`
- Implementation evidence: 当前工作区 diff、DoD/scope/evidence-pack fresh results、独立 reviewer 两轮输出、OCR 两轮输出。
- Diff basis: `git status --porcelain -uall` 全量 dirty/untracked 清单；`git diff --check` 通过；无 staged diff。
- Review mode: full-rereview + focused-closure。
- Baseline dirty files: `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml` 是本 epic goal handoff/resolution 流程元数据，已显式纳入 scope-gate allowlist。

### Independent Review

- Detection: Task agent 可用；OCR CLI 可用，`ocr llm test` 成功。
- 环节 A 独立隔离 Task agent: independent-agent completed，第二轮 agent `019f8560-2ccc-7622-8d94-b4a7ca3c3406`。
- 环节 B OCR CLI: completed。第一轮发现 WinAPI 签名问题；修复后第二轮 0 comment。
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion, Low->discarded。
- Merge policy: 所有外部 finding 均已本地核验；未复现或已被后续 diff 关闭的 finding 不进入 blocking。
- Gate effect: `reviewer: subagent+ocr`，满足下游 gate。

## 2. Diff Summary

- 新增：`lib/process_liveness.py`、`test/test_process_liveness.py`、CodeStable gate/evidence 产物。
- 修改：`lib/ccbd/system.py`、`lib/cli/kill_runtime/processes.py`、`lib/provider_core/runtime_lock.py`、`lib/cli/services/mobile_host.py`、`lib/provider_core/session_binding_evidence_runtime/fields.py`、`lib/terminal_runtime/tmux.py`、相关 focused tests、feature checklist、epic goal-state。
- 删除：none。
- 未跟踪 / staged：未跟踪文件已由 `git status --porcelain -uall` 和 scope-gate 覆盖；无 staged diff。
- 风险热点：Windows WinAPI 句柄、PID liveness 共享语义、Windows 命令引号/空格路径、AF_UNIX 不可用平台测试替代层。

## 3. Adversarial Pass

- 假设的生产 bug：Windows native 上旧 `os.kill(pid, 0)` 或 64-bit HANDLE 截断导致 ccbd/lock/kill 判断进程存活状态错误。
- 主动攻击过的反例：invalid pid、access denied、exited handle、wait failed、POSIX zombie、Windows 带空格脚本路径、外部 legacy mobile gateway、`/tmp` 外部 session ref、`C:\...` TMUX socket ref、无 AF_UNIX 的 lifecycle test。
- 结果：WinAPI 签名、runtime_lock 单一 owner、path/command 直接测试、全量 scope evidence 均已关闭；真实 Windows full-chain smoke 留给 QA。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- REV-S01 `lib/cli/kill_runtime/processes.py:9` 当前直接导入 `process_liveness._proc_pid_state` 以保留 zombie 判定语义。后续可公开窄 helper，减少跨模块私有符号依赖；不阻塞本轮。

### learning

- `ctypes` 调 WinAPI 时必须声明 `argtypes/restype`；`ctypes` 默认 `c_int` 在 64-bit Windows 上会让 HANDLE 截断风险被 fake tests 掩盖。

### praise

- `lib/process_liveness.py:21` 把 WinAPI wrapper 和 POSIX fallback 收敛到单一 owner，`ccbd.system`、`kill_runtime`、`runtime_lock` 均复用该 owner。
- `test/test_v2_ccbd_mount_ownership.py:191` 的 AF_UNIX-unavailable fake transport 注入保持在测试侧，没有把测试兼容分支推入生产 lifecycle。

## 5. Test And QA Focus

- QA 必须重点复核：真实 Windows native `OpenProcess + WaitForSingleObject` alive/exited/access-denied；64-bit Python 下 HANDLE 不截断。
- QA 必须重点复核：provider lock stale cleanup、ccbd heartbeat/shutdown、legacy mobile takeover、TMUX socket ref/session path handoff。
- Evidence pack residual risks / gate warnings：OCR 第二轮尝试读不存在的 `lib/ccbd/socket_server_runtime.py` 失败，但未生成 comment；本地 scope 文件已覆盖实际 diff。
- 建议新增或加强的测试：QA 阶段补真实 Windows smoke；本轮 unit/focused coverage 已覆盖 fake WinAPI、path text、TMUX ref、mobile quoted command、runtime_lock delegate。
- 不能靠 review 完全确认的点：真实 Windows full-chain smoke、后续 TCP loopback transport 和 rmux backend 行为。

## 6. Residual Risk

- 本 feature 解决 process liveness 与 handoff 阻塞，不实现完整 Windows TCP control-plane transport；AF_UNIX 不可用平台的 production daemon transport 仍由后续 `ccbd-windows-tcp-loopback-transport` feature 收口。
- 未在本 review 中执行真实 Windows full-chain smoke；QA 需要在 native Windows 上复核。

## 7. Verdict

- Status: passed
- Next: Goal feature 通过 code review gate，进入 `cs-feat` QA 阶段。

## 8. Focused Closure

- Closed findings: 第一轮 B1/I1/I2/I3/N1；第二轮 important-1/important-2。
- Attributed delta: `lib/process_liveness.py` WinAPI 签名；`lib/provider_core/runtime_lock.py` 共享 liveness owner；`test/test_mobile_host_service.py` 真实 quoted Windows legacy command positive/negative；checklist CMD-008 改为全量 `git status --porcelain -uall`；scope-gate 使用全工作区 check-path 并允许 epic `goal-state.yaml`。
- Targeted verification:
  - `python -m pytest -q test/test_process_liveness.py test/test_mobile_host_service.py` -> 40 passed
  - `python -m pytest -q test/test_process_liveness.py test/test_cli_kill_runtime_zombies.py` -> 22 passed
  - `python -m pytest -q test/test_v2_ccbd_mount_ownership.py test/test_cli_daemon_keeper_runtime.py test/test_ccbd_service_graph.py` -> 46 passed, 2 skipped
  - `python -m pytest -q test/test_v2_kill_service.py test/test_cli_kill_runtime_zombies.py test/test_runtime_accelerator_ownership.py test/test_mobile_host_service.py` -> 73 passed
  - `codestable-dod-runner.py --stage implementation.before_review` -> passed
  - `codestable-scope-gate.py --check-path "." ...` -> passed
  - `codestable-evidence-pack.py --stage implementation.before_review` -> passed
  - `git diff --check` -> passed
  - `ocr review ...` second pass -> 0 comments
- Classification: 第二轮 closure 只改测试和 CodeStable gate metadata；生产行为未再变化，公开契约、安全、数据、并发和架构边界不变。
