---
doc_type: feature-qa
feature: 2026-07-20-ccbd-windows-process-liveness
status: passed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-07-22
round: 1
---

# ccbd-windows-process-liveness QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml`
- Review: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-review.md`
- Evidence pack: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/dod-results.json`
- Diff basis: `git status --porcelain -uall` 显示本 feature 代码、测试、CodeStable evidence、roadmap `goal-state.yaml` dirty/untracked；`git diff --check` 通过；无 staged diff。
- Baseline dirty files: 全部 dirty/untracked 已由 implementation scope-gate 覆盖。`.codestable/features/2026-07-20-ccbd-windows-process-liveness/scope-min.json` 是 feature 目录内 scope-gate 诊断输入产物，不是生产代码。
- Feature type: functional
- Core evidence gate: Windows 无副作用 pid liveness、POSIX/zombie regression、ccbd ownership/keeper/health 默认路径、kill_runtime 传递消费者、handoff 中 Windows path/AF_UNIX 兼容回归均需要实际运行证据。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | CMD-001 | supporting | checklist YAML 可解析 | schema | `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml" --yaml-only` | exit 0 | pass |
| QA-002 | CMD-002 | supporting | roadmap items YAML 可解析 | schema | `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` | exit 0 | pass |
| QA-003 | CMD-003 / AC-001..006 | core-functional | WinAPI/POSIX liveness、错误码映射、zombie dead | unit | `python -m pytest -q test/test_process_liveness.py test/test_cli_kill_runtime_zombies.py` | tests pass | pass |
| QA-004 | CMD-004 / AC-008..010 | core-functional | ccbd ownership、keeper、health 默认 pid liveness 路径 | integration | `python -m pytest -q test/test_v2_ccbd_mount_ownership.py test/test_cli_daemon_keeper_runtime.py test/test_ccbd_service_graph.py` | tests pass；AF_UNIX 不可用项只作 compatibility skip | pass |
| QA-005 | CMD-005 / AC-011..012 | core-functional | kill_runtime sharing、accelerator ownership、mobile host consumers | regression | `python -m pytest -q test/test_v2_kill_service.py test/test_cli_kill_runtime_zombies.py test/test_runtime_accelerator_ownership.py test/test_mobile_host_service.py` | tests pass | pass |
| QA-006 | handoff I1 / review QA focus | core-functional | Windows session path、TMUX socket ref、quoted legacy mobile command | regression | `python -m pytest -q test/test_provider_core_session_binding_fields.py test/test_terminal_runtime_tmux.py test/test_mobile_host_service.py` | tests pass | pass |
| QA-007 | review QA focus | core-functional | native Windows real process alive/exited smoke | manual CLI | `python -c "... process_liveness.process_exists(...)"` | current/child alive true，exited/invalid false | pass |
| QA-008 | CMD-006 | supporting | `is_pid_alive` 传递消费者清单 | static | `rg -n "from cli\\.kill_runtime\\.processes import is_pid_alive|is_pid_alive\\(" lib test` | consumers 可归因并已测试/审查 | pass |
| QA-009 | CMD-007 | core-functional | Windows liveness 不保留 signal probe | static | `rg -n "os\\.kill\\(pid, 0\\)|os\\.kill\\([^,]+, 0\\)" lib/ccbd lib/cli/kill_runtime lib/process_liveness.py test/test_process_liveness.py` | 仅 POSIX owner 例外命中 | pass |
| QA-010 | cleanliness | supporting | whitespace、syntax、无新增 debug/TODO/staged diff | static | `git diff --check`; `python -m py_compile ...`; `git diff -U0 ... | rg "TODO|FIXME|XXX|debugger|print\\("`; `git diff --name-only --cached` | 均无阻塞 | pass |

## 3. Command Results

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml" --yaml-only` -> exit 0：1 passed, 0 failed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` -> exit 0：1 passed, 0 failed。
- `python -m pytest -q test/test_process_liveness.py test/test_cli_kill_runtime_zombies.py` -> exit 0：22 passed。
- `python -m pytest -q test/test_v2_ccbd_mount_ownership.py test/test_cli_daemon_keeper_runtime.py test/test_ccbd_service_graph.py` -> exit 0：46 passed, 2 skipped。
- `python -m pytest -q test/test_v2_kill_service.py test/test_cli_kill_runtime_zombies.py test/test_runtime_accelerator_ownership.py test/test_mobile_host_service.py` -> exit 0：73 passed。
- `python -m pytest -q test/test_provider_core_session_binding_fields.py test/test_terminal_runtime_tmux.py test/test_mobile_host_service.py` -> exit 0：38 passed。
- `python -c "... process_liveness.process_exists(...)"` -> exit 0：`platform=win32`, `current_alive=True`, `child_alive=True`, `child_exited=False`, `invalid_zero=False`。
- `rg -n "from cli\\.kill_runtime\\.processes import is_pid_alive|is_pid_alive\\(" lib test` -> exit 0：列出 provider cleanup、runtime accelerator ownership、daemon runtime、mobile host、maintenance、runtime_lock 与对应测试引用。
- `rg -n "os\\.kill\\(pid, 0\\)|os\\.kill\\([^,]+, 0\\)" lib/ccbd lib/cli/kill_runtime lib/process_liveness.py test/test_process_liveness.py` -> exit 0：仅 `lib/process_liveness.py:77` POSIX 分支命中。
- `git diff --check` -> exit 0。
- `python -m py_compile lib/process_liveness.py lib/ccbd/system.py lib/cli/kill_runtime/processes.py lib/cli/services/mobile_host.py lib/provider_core/runtime_lock.py lib/provider_core/session_binding_evidence_runtime/fields.py lib/terminal_runtime/tmux.py` -> exit 0。
- `git diff -U0 -- ... | rg -n "TODO|FIXME|XXX|debugger|print\\("` -> exit 1：无新增命中。
- `git diff --name-only --cached` -> exit 0：无 staged diff。

## 4. Scenario Results

- [x] QA-003 WinAPI/POSIX liveness 单测：pass
  - Evidence: 22 passed；覆盖 invalid pid fast false、WinAPI handle close、access denied/invalid/not-found/unknown/wait-failed mapping、POSIX PermissionError/ProcessLookupError/OSError、zombie dead。
- [x] QA-004 ccbd ownership/keeper/health 默认路径：pass
  - Evidence: 46 passed, 2 skipped；AF_UNIX 不可用平台的 skip 属 compatibility residual，不阻塞 native Windows process liveness。
- [x] QA-005 kill_runtime 与传递消费者：pass
  - Evidence: 73 passed；覆盖 kill service、runtime accelerator ownership、mobile host consumer。
- [x] QA-006 handoff Windows path/AF_UNIX 回归：pass
  - Evidence: 38 passed；覆盖 external Windows/Unix session path 文本保留、`~` 展开、TMUX socket ref 保留、quoted Windows legacy mobile gateway positive/negative。
- [x] QA-007 真实 Windows process smoke：pass
  - Evidence: native `sys.platform=win32` 下当前 pid alive、子进程 alive、退出后 false、pid 0 false。
- [x] QA-008/QA-009 static guard：pass
  - Evidence: `is_pid_alive` consumers 已列入 blast-radius；signal probe 只在 POSIX owner 分支保留。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- 本 feature 不实现 Windows TCP control-plane transport；native Windows production ccbd transport 仍由后续 `ccbd-windows-tcp-loopback-transport` 证明。
- 未在本 feature QA 中运行完整 `ccb -> ccbd -> rmux` full-chain smoke；该核心终点属于后续 `ccbd-windows-full-chain-smoke`。
- `scope-min.json` 保留为 feature 目录内 scope-gate 诊断输入产物；acceptance 可决定是否在不违反删除确认策略的前提下清理。

## 6. Cleanliness

- Debug output: pass。新增 diff 无 `print(` / `debugger`。
- Temporary TODO/FIXME/XXX: pass。新增 diff 无命中。
- Commented-out code: pass。未发现新增注释掉实现。
- Unused imports / dead code from this feature: pass。`lib/ccbd/system.py` 的 `os` 仍被 `current_uid()` 使用；`lib/provider_core/runtime_lock.py` 多处使用 `os`。
- Out-of-scope files: pass。implementation scope-gate 已覆盖当前 dirty/untracked 清单，`goal-state.yaml` 为 roadmap driver 元数据。

## 7. Verdict

- Status: passed
- Next: 进入 `cs-feat` acceptance 阶段；acceptance 需复核 QA passed、evidence pack/gates passed、checklist checks 和 roadmap item writeback。
