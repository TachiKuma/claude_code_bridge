---
doc_type: feature-acceptance
feature: 2026-07-20-ccbd-windows-process-liveness
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: "approval-report.md#goal-acceptance"
accepted: 2026-07-22
round: 1
---

# ccbd-windows-process-liveness 验收报告

> 阶段：阶段 3（验收闭环）  
> 验收日期：2026-07-22  
> 关联方案 doc：`.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-design.md`

## 1. 接口契约核对

**接口示例逐项核对**：
- [x] `lib/process_liveness.py::process_exists(pid: int | None) -> bool`：输入 pid，输出只读 alive/dead bool；实际实现按平台 dispatch，invalid pid fast false。
- [x] Windows backend：`OpenProcess` / `WaitForSingleObject(handle, 0)` / `CloseHandle` 与 design 错误码表一致；`ctypes` 函数签名已声明，避免 64-bit HANDLE 截断。
- [x] POSIX backend：保留 `os.kill(pid, 0)` signal probe，并通过 `/proc/<pid>/stat` 把 zombie `Z` 判 dead。

**名词层"现状 → 变化"逐项核对**：
- [x] `ccbd.system.process_exists` 从直接 `os.kill(pid, 0)` 改为共享 owner wrapper。
- [x] `cli.kill_runtime.processes.is_pid_alive` 复用共享 owner，并保留 zombie dead guard。
- [x] `provider_core.runtime_lock._is_pid_alive` 复用共享 owner，关闭独立 Windows OpenProcess helper。

**流程图核对**：
- [x] ccbd ownership/keeper/health 与 kill_runtime consumer 都落到共享 liveness helper；`rg` 消费者清单已在 QA 中记录。

## 2. 行为与决策核对

**需求摘要逐项验证**：
- [x] Windows 分支不调用 `os.kill(pid, 0)`：QA guard 只在 `lib/process_liveness.py` POSIX 分支命中。
- [x] alive / exited / invalid pid 行为可观察：native Windows smoke 记录 `current_alive=True`, `child_alive=True`, `child_exited=False`, `invalid_zero=False`。
- [x] access denied / invalid / not-found / unknown / wait-failed 映射由 `test/test_process_liveness.py` 锁定。
- [x] ccbd ownership/keeper/health 默认路径由 focused integration tests 覆盖。

**明确不做逐项核对**：
- [x] 未引入 psutil 必需依赖。
- [x] 未实现 Job Object 进程树 evidence。
- [x] 未改变 `terminate_pid_tree()` / `kill_pid()` 终止语义。
- [x] 未实现 Windows TCP control-plane transport、Rmux backend、provider parser 或 packaging/docs。

**关键决策落地**：
- [x] 单一 liveness owner 固定为 `lib/process_liveness.py`。
- [x] Windows 使用标准库 `ctypes` WinAPI wrapper，不依赖外部命令 `tasklist`。
- [x] `ERROR_ACCESS_DENIED` 按 alive 处理，避免误 takeover；未知 wait/open error fail-safe false。

**挂载点反向核对（可卸载性）**：
- [x] 挂载点清单与代码落点一致：`lib/process_liveness.py`、`lib/ccbd/system.py`、`lib/cli/kill_runtime/processes.py`、`lib/provider_core/runtime_lock.py`、相关 focused tests。
- [x] 反向核查：`rg "process_liveness|is_pid_alive|process_exists"` 与 QA 消费者清单匹配；handoff 补丁触碰的 path/TMUX/mobile files 已由 review 和 QA 归因。
- [x] 拔除沙盘推演：移除共享 owner 时会影响 ccbd wrapper、kill_runtime、runtime_lock 和 tests；无隐藏 runtime owner 残留。

## 3. 验收场景核对

- [x] AC-001 invalid pid：`process_exists(None|0|negative)` false，单测覆盖。
- [x] AC-002/003 Windows alive/exited：fake WinAPI 单测 + native Windows smoke 覆盖。
- [x] AC-004 Windows 错误码映射：单测覆盖 access denied、invalid、not-found、unknown、wait-failed。
- [x] AC-005 POSIX errors：单测覆盖 ProcessLookupError / PermissionError / generic OSError。
- [x] AC-006 POSIX zombie：`test_cli_kill_runtime_zombies.py` 通过。
- [x] AC-007 ccbd.system default：wrapper diff + tests 覆盖。
- [x] AC-008/009/010 OwnershipGuard / keeper / HealthMonitor：46 passed, 2 skipped。
- [x] AC-011/012 kill_runtime sharing 和传递消费者：73 passed，`rg` 清单已审查。
- [x] AC-013 scope guard：scope-gate passed，`git status --porcelain -uall` 全量 dirty/untracked 已纳入 evidence。

**review 报告重点复核**：
- [x] WinAPI HANDLE 签名已修复并由 `test_windows_api_declares_pointer_sized_handle_signatures` 覆盖。
- [x] Windows path/TMUX/mobile handoff 回归由 38 passed 覆盖。
- [x] runtime_lock 独立 helper 已收敛到共享 owner。

**QA 报告重点复核**：
- [x] QA 报告：`.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-qa.md`
- [x] QA `status=passed`，failed / blocked 均为 none。
- [x] QA residual-risk 只包含后续 feature 边界：Windows TCP transport、full-chain smoke、feature-local `scope-min.json` 处理；未承载本 feature 核心缺口。
- [x] Evidence pack、DoD Results、Gate Results 均为 passed。

## 4. 术语一致性

- `process liveness`：代码落点统一为 `process_liveness` / `process_exists`，无第二个 Windows liveness owner。
- `signal probe`：只保留在 POSIX backend；Windows liveness 不使用。
- `job-object evidence`：本 feature 未引入该术语对应实现，仍保留给 `windows-job-object-runtime-evidence`。
- 防冲突：旧 `psmux` / Rmux backend 概念未混入本 feature 实现。

## 5. 领域影响盘点（提示而非代写）

- [x] 新名词候选：`process liveness owner`。结论：这是内部基础 helper，当前 design/roadmap 已记录；暂不需要 `cs-domain` 写 CONTEXT。
- [x] 结构性选择候选：Windows liveness 采用 WinAPI handle probe。结论：有可复用经验价值，但不是独立 ADR 级路线选择；建议后续用 `cs-keep` 沉淀 ctypes WinAPI 签名经验。
- [x] 流程级约束候选：Windows 不得用 `os.kill(pid, 0)` 做 alive probe。结论：roadmap §8 已记录 blocker，acceptance 不直接写 ADR。

## 6. requirement delta / clarification 回写

无 requirement 影响。该 feature 是 roadmap 内部控制面 blocker 修复，frontmatter `requirement` 为空；未新增用户层能力或公开配置表面，不需要 req delta。

## 7. roadmap 回写

- [x] `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 中 `ccbd-windows-process-liveness` 已从 `in-progress` 改为 `done`。
- [x] `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md` item 20 已同步为 `accepted`，并记录对应 feature 与验收摘要。
- [x] `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml` 当前 feature 已标记 `accepted`，`current_feature_index` 推进到 4。
- [x] Goal driver 未执行 scoped commit：`goal-state.yaml.status` 按协议设置为 `handoff`，原因是当前 AGENTS 指令要求未主动请求时不执行 `git commit`。

## 8. attention.md 候选盘点

- [x] attention.md 候选：无。本 feature 未暴露每个后续 feature 都会反复踩的本地命令、代理、路径或环境规则。
- [x] cs-keep 候选：`ctypes` 调 WinAPI 时必须声明 `argtypes/restype`，尤其 HANDLE 在 64-bit Windows 上不能依赖默认 `c_int`。
- [x] docs 候选：无。未改变用户文档或公开 API。

## 9. 遗留

- 后续优化点：可把 `process_liveness._proc_pid_state` 提升为公开窄 helper，避免 `kill_runtime.processes` 直接导入私有符号。
- 已知限制：本 feature 不证明 Windows TCP loopback control-plane transport；不证明 `ccb -> ccbd -> rmux` full-chain smoke。
- 实现阶段顺手发现：Windows external runtime path 文本、TMUX socket ref 与 legacy mobile command parsing 已作为 handoff 修复纳入本 feature scope 和 tests。

## 10. 最终审计

- 验证证据来源：`ccbd-windows-process-liveness-qa.md`
- Evidence sources：`ccbd-windows-process-liveness-evidence-pack.md` / `dod-results.json` / `scope-gate-results.json`
- 聚合命令：
  - `python -m pytest -q test/test_process_liveness.py test/test_cli_kill_runtime_zombies.py` -> 22 passed。
  - `python -m pytest -q test/test_v2_ccbd_mount_ownership.py test/test_cli_daemon_keeper_runtime.py test/test_ccbd_service_graph.py` -> 46 passed, 2 skipped。
  - `python -m pytest -q test/test_v2_kill_service.py test/test_cli_kill_runtime_zombies.py test/test_runtime_accelerator_ownership.py test/test_mobile_host_service.py` -> 73 passed。
  - `python -m pytest -q test/test_provider_core_session_binding_fields.py test/test_terminal_runtime_tmux.py test/test_mobile_host_service.py` -> 38 passed。
  - Native Windows smoke -> current/child alive true，exited/invalid false。
  - `git diff --check` / `py_compile` / static `rg` guards -> passed。
- 场景复核：re-verified 13 / trust-prior-verify 0。
- 交付物复核：代码、测试、review、QA、evidence pack、checklist、roadmap writeback 均已落盘。
- 完整工作区复核：dirty/untracked 文件均为本 feature 交付物、CodeStable evidence 或 roadmap driver metadata；无 staged diff。
- diff 清洁度：通过。新增 diff 无 TODO/FIXME/XXX/debugger/print；`os` import 均有实际使用。
- 知识沉淀出口：建议后续 `cs-keep` 记录 WinAPI ctypes 签名经验；无 attention/docs/API 更新候选。
- Workflow-next：`codestable-workflow-next.py epic --roadmap ... --json` 返回 `ok: true`、`status: handoff`、`next_action: CS_ROADMAP_GOAL_HANDOFF`，handoff 原因与 `goal-state.yaml` 一致：feature acceptance passed，但 scoped commit 未执行。
- 结论：通过。`ccbd-windows-process-liveness` feature 已验收完成；roadmap driver 因未执行 scoped commit 按协议 handoff。
