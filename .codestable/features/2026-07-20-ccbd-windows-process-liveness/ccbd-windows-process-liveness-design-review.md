---
doc_type: feature-design-review
feature: 2026-07-20-ccbd-windows-process-liveness
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7cf0-7bae-7741-8e24-b7cda67ceaab"
reviewed: 2026-07-20
round: 1
---

# ccbd-windows-process-liveness feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: roadmap item 20；`windows-job-object-runtime-evidence` 边界；`ccbd-windows-full-chain-smoke` blocker 清单
- Code facts checked:
  - `lib/ccbd/system.py`
  - `lib/ccbd/services/ownership.py`
  - `lib/ccbd/services/health.py`
  - `lib/ccbd/keeper.py`
  - `lib/ccbd/keeper_runtime/state.py`
  - `lib/cli/kill_runtime/processes.py`
  - `test/test_cli_kill_runtime_zombies.py`
  - `test/test_v2_ccbd_mount_ownership.py`
  - `test/test_cli_daemon_keeper_runtime.py`
  - `test/test_ccbd_service_graph.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7cf0-7bae-7741-8e24-b7cda67ceaab`
- Raw output: 首轮 `changes-requested`，提出 4 个 important、1 个 nit；focused closure 后 verdict `passed`
- Merge policy: 主 agent 已核验 ccbd system/ownership/health/keeper 与 kill_runtime 代码事实；修订后由同一 reviewer 做 focused closure
- Gate effect: 独立 reviewer completed + closure verified；允许定稿 `passed`

## 2. Design Summary

- Goal: 为 ccbd 控制面提供无副作用的跨平台 pid 存活判定，Windows 不再用 `os.kill(pid, 0)`，避免误判或 Ctrl-C 副作用。
- Key contracts: 单一 owner 固定为 `lib/process_liveness.py`；Windows 用 `OpenProcess` / `WaitForSingleObject` / `CloseHandle`；错误码表固定；POSIX 保持 PermissionError alive、ProcessLookup/OSError false、zombie dead；ccbd.system 与 kill_runtime 复用同一 helper。
- Steps: 6 个步骤，覆盖 owner skeleton、Windows backend、POSIX regression、ccbd default wiring、kill_runtime sharing + blast-radius regression、scope guard。
- Checks: 11 项检查，覆盖 no-signal Windows liveness、错误码映射、invalid pid、POSIX/zombie、OwnershipGuard/keeper/HealthMonitor 默认依赖、传递消费者、scope guard。
- Baseline / validation: YAML 校验通过；`test/test_process_liveness.py` 为实现阶段新增；现有 seam 测试大量通过 `pid_exists` 注入，设计保留该 seam。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- ccbd 的 `OwnershipGuard`、`HealthMonitor`、keeper state 已有 pid liveness 注入 seam；本 feature 只需替换默认 provider，不应重写状态机。
- 共享 `cli.kill_runtime.processes.is_pid_alive` 后 blast radius 会扩到 runtime accelerator ownership、daemon runtime、mobile host、provider helper cleanup、ccbd stop-flow pid cleanup，必须在实现/QA 里显式审查或回归。

### praise

- design 明确区分 basic pid liveness 与 job-object evidence，没有把进程树 authority 偷渡进本 feature。
- Windows 错误码语义已固定成可审表格，用户 review 和后续实现都有稳定契约。

## 4. User Review Focus

- 用户需要重点拍板：本 feature 选择 stdlib `ctypes` WinAPI probe，不引入 psutil；psutil 不进入当前交付。
- implement 需要重点遵守：Windows liveness path 不得调用 `os.kill(pid, 0)`；`GetLastError()` 必须在 `OpenProcess` 失败后立即读取；所有 handle 必须关闭。
- code review / QA / acceptance 需要重点复核：共享 helper 的传递消费者清单、POSIX zombie regression、kill_pid/terminate_pid_tree 终止语义不漂移、scope 未扩入 job-object/transport/Rmux/provider parser。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 至 AC-013 | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4；YAML 校验通过 | none |
| Roadmap contract compliance | pass | E | roadmap item 20 要求替换 ccbd `process_exists` 的 Windows signal probe；design 明确 basic pid liveness 边界 | none |
| Module interface design | pass | C | ccbd.system、ownership、health、keeper、kill_runtime 代码事实已核对；默认 provider 替换 + injection seam 保留 | implementation 需保持 `lib/process_liveness.py` 为单一 owner |
| Validation and artifacts | pass | E | checklist `dod.commands` 覆盖 WinAPI mapping、POSIX/zombie、ccbd wiring、传递消费者、scope guard | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 真正的 Windows 无副作用语义最终仍需要 Windows 真机或 CI 加上 full-chain smoke 补证；当前 design review 只确认 spec 路径闭合。
- 共享 helper 可能暴露额外传递消费者；实现阶段必须以 `rg` 清单为准更新 review/QA 证据。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop，继续下一个 epic child；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004
- Attributed delta: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-design.md`、`.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml`
- Verification: reviewer `019f7cf0-7bae-7741-8e24-b7cda67ceaab` focused closure verdict `passed`；checklist YAML 与 roadmap items YAML 校验通过
- Classification: 修订只关闭 reviewer 提出的 WinAPI 错误码映射、helper 落点、传递消费者回归和 steps 原子性问题；未修改生产代码，也未改变 feature 范围或 roadmap 边界
