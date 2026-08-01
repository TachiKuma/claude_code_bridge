---
doc_type: feature-design-review
feature: 2026-07-20-rmux-supervision-recovery
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7cbd-1722-79e1-9d11-1be588e73a34"
reviewed: 2026-07-20
round: 1
---

# rmux-supervision-recovery feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-rmux-supervision-recovery/rmux-supervision-recovery-design.md`
- Checklist: `.codestable/features/2026-07-20-rmux-supervision-recovery/rmux-supervision-recovery-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: roadmap item 14；前序 Windows Job Object、provider runtime session、Rmux daemon ownership、Rmux backend、ccbd namespace lifecycle child designs
- Code facts checked:
  - `lib/ccbd/supervision/loop.py`
  - `lib/ccbd/supervision/loop_runtime.py`
  - `lib/ccbd/supervision/recovery.py`
  - `lib/ccbd/supervision/recovery_transitions.py`
  - `lib/ccbd/supervision/recovery_events.py`
  - `lib/ccbd/supervision/cmd_slot.py`
  - `lib/ccbd/supervision/store.py`
  - `lib/ccbd/services/runtime_recovery_policy.py`
  - `lib/ccbd/project_view/service.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7cbd-1722-79e1-9d11-1be588e73a34`
- Raw output: 首轮 `changes-requested`，提出 4 个 important；focused closure 后 verdict `passed`
- Merge policy: 主 agent 已核验 roadmap、代码事实和 reviewer findings，修订 design/checklist 后由同一 reviewer 做 focused closure
- Gate effect: 独立 reviewer completed + closure verified；允许定稿 `passed`

## 2. Design Summary

- Goal: 将 Rmux pane、provider process/job、namespace 和 daemon health 纳入 ccbd supervision/recovery，提供可诊断的恢复或降级路径。
- Key contracts: evidence ledger 分离 `pane_health/process_health/namespace_health/daemon_health`；runtime health labels 由 decision table 统一映射；Rmux pane id 不依赖 `%N`；namespace matching 不依赖 `tmux_socket_path`；shared daemon 不自动 kill/restart。
- Steps: 8 个步骤，覆盖 evidence ledger、backend-neutral matching、process/job split、namespace crash、daemon crash、event/project view/doctor projection、Windows recovery smoke、scope guard。
- Checks: 7 项检查，覆盖 ledger、Rmux id/namespace matching、process-vs-pane split、namespace crash、daemon ownership、diagnostics projection、scope guard。
- Baseline / validation: YAML 校验、supervision/recovery new tests、Rmux evidence/daemon tests、diagnostics/project view/doctor/ping/bundle projection、scope guard。

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

- 新 health 必须有机械映射到 `runtime.health`、recoverability、event details 和 backoff，否则 `recover_runtime()` 与 project view 容易各自发明状态名。
- shared Rmux daemon crash 只能 degraded diagnostics 或观察外部恢复 evidence；cleanup/restart 必须由 owned / generation-approved evidence 授权。

### praise

- ledger 分离 pane/process/namespace/daemon health 的方向正确，且明确不依赖 tmux `%N` 或 `tmux_socket_path` 判定 Rmux namespace，符合 roadmap item 14 的核心边界。
- design 复用 `SupervisionEvent.details`、现有 `recover_runtime` backoff/event 机制和前序 ownership/session/process evidence，没有重建一套 supervision loop。

## 4. User Review Focus

- 用户需要重点拍板：这是 post-milestone 日常可用性能力，不阻塞本轮 minimum full-chain；validation matrix 仍在后续 item。
- implement 需要重点遵守：process dead 优先于 pane alive；daemon health 不得改写 provider parser status；unowned/shared daemon 不自动 restart。
- code review / QA / acceptance 需要重点复核：health decision table 是否完整实现、SupervisionEvent details 是否包含四类 ledger key、Rmux path 是否没有 `%`/`tmux_socket_path` 依赖、scope guard 是否阻止 resolver/namespace lifecycle 越界。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.1 / §3.3 覆盖 AC-001 至 AC-008 | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4；YAML 校验通过 | none |
| Roadmap contract compliance | pass | E | roadmap item `rmux-supervision-recovery` 要求 pane/process/job evidence 边界；design 明确 post-milestone 边界 | none |
| Module interface design | pass | C | Code facts show loop_runtime/runtime_recovery_policy/recovery_transitions/cmd_slot 的 tmux-specific assumptions；design 已收束到 evidence ledger 与 backend-neutral matching | implementation 需消费前序 refs |
| Validation and artifacts | pass | E | checklist `dod.commands` 标注 new/new-or-extended，并覆盖 decision table、diagnostics projection、scope guard | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 前序 child design 多数仍处于 draft/in-progress；如果 `process_ref`、`pane_ref/namespace_ref`、`backend_daemon_*` 最终字段变化，本 feature 需要同步更新 mapping table 和 checklist commands。
- 本 feature 依赖 `ccbd-windows-process-liveness` 提供基础 process alive evidence；若该项未落地，只能实现 degraded diagnostics 或 fake evidence tests。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop，继续下一个 epic child；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004
- Attributed delta: `.codestable/features/2026-07-20-rmux-supervision-recovery/rmux-supervision-recovery-design.md`、`.codestable/features/2026-07-20-rmux-supervision-recovery/rmux-supervision-recovery-checklist.yaml`
- Verification: reviewer `019f7cbd-1722-79e1-9d11-1be588e73a34` focused closure verdict `passed`；checklist YAML 与 roadmap items YAML 校验通过
- Classification: 修订只关闭 reviewer 提出的映射表、测试状态、scope guard 和 daemon ownership 澄清问题，未修改生产代码；没有改变 feature 范围、roadmap 边界或前序接口所有权
