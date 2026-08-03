---
doc_type: feature-acceptance
feature: 2026-07-31-herdr-bounded-recovery-boundary
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: ".codestable/roadmap/windows-native-herdr-ccb/approval-report.md#goal-acceptance"
accepted: 2026-08-03
round: 1
---

# herdr-bounded-recovery-boundary 验收报告

> 阶段：阶段 3（验收闭环）  
> 验收日期：2026-08-03  
> 关联方案 doc：`.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-design.md`

## 1. 接口契约核对

- [x] `HerdrRecoveryPolicy`：owner 固定 `ccb`，`herdr_auto_restore_mode` 仅 `disabled` 可恢复，probation 90 秒，circuit threshold 3。代码落点：`lib/ccbd/services/runtime_recovery_policy.py`，测试 `test_herdr_recovery_policy_keeps_ccb_as_owner` / `test_herdr_auto_restore_must_be_disabled_for_recovery`。
- [x] `HerdrRecoveryEvidence`：public ledger 输出 `restore_token_present`、sanitized refs、action/reason，不输出 raw restore token。代码落点：`lib/ccbd/supervision/recovery_events.py`，测试覆盖 nested details redaction 与 runtime record redaction。
- [x] Probation / circuit transition：Herdr 3 次不稳定后 `recover_blocked` / `circuit_open`，probation 语义保留。代码落点：`recovery.py`、`recovery_transitions.py`、`runtime_recovery_policy.py`。
- [x] Lifecycle start gate：`tick_jobs()` 常规扫描路径对 Herdr capability-blocked degraded runtime 写 durable `recover_blocked` evidence，且第二次 tick 不重复写事件。代码落点：`slots.py`。
- [x] Provider pane primitive：Herdr pane_ref 不要求 tmux `%pane`，不调用 tmux ownership/identity，仍受 CCB gate 控制。代码落点：`provider_backends/pane_log_support/lifecycle_recovery.py`。

## 2. 行为与决策核对

- [x] CCB recovery owner 单一：Herdr auto restore 非 `disabled` 时 blocked，不调用 `refresh_provider_binding(recover=True)`。
- [x] 短暂 pane alive / Herdr agent state 不作为 `recover_succeeded` authority；恢复成功仍由 CCB health/probation/circuit 约束。
- [x] Provider auth revoked / provider recovery blocked 仍 hard-block；回归命令覆盖 crash reason / recovery block。
- [x] 明确不做逐项核对：未改 provider completion、Mobile/Config UI、doctor/support、package/release/update/installer/public matrix、Herdr socket schema/client owner；CMD-007 scope guard passed。
- [x] 挂载点反向核对：本 feature 实际代码 diff 限于 design 2.3 的 recovery policy/supervision/lifecycle start/pane lifecycle/tests 范围；拔除沙盘推演对应删除这些挂载点后 feature 行为消失，无额外 public surface 残留。

## 3. 验收场景核对

- [x] AC-001 provider runtime admission：CMD-003 passed。
- [x] AC-002 / AC-006 ledger redaction：Herdr focused tests + CMD-008 passed。
- [x] AC-003 auto restore non-disabled blocked：Herdr focused tests passed；lifecycle-start direct helper和 `tick_jobs()` production path 均覆盖。
- [x] AC-004 backoff/drop 不调用 restore/respawn：existing recovery regression passed；R4 fix 未改 `drop` 分支。
- [x] AC-005 pane/process recovery routing：Herdr focused tests passed。
- [x] AC-007 probation/circuit：Herdr focused tests passed，包含 circuit threshold。
- [x] AC-008 auth revoked / recovery blocked：pane crash reason regression passed。
- [x] AC-009 tmux/rmux regression：recovery/restore/crash regression 20 passed。
- [x] AC-010 Native Windows Herdr recovery：S7 artifact shows Herdr binary exists but server `not_running` / `capabilities=null`; accepted as blocked evidence only, not recovery pass.
- [x] Review focus：round 5 review passed; R4-001 closed; `REV-005` retained as residual risk.
- [x] QA report：`.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-qa.md` status passed; failed/blocked findings none.

## 4. 术语一致性

- `CCB recovery owner`、`Herdr restore evidence`、`bounded recovery`、`recovery probation`、`Herdr auto restore mode` 均在代码/报告中沿用 design 术语。
- 禁止边界核对：raw `restore_token` 仅作为 private fixture/key 构造进入 sanitizer 测试；public payload 使用 `restore_token_present`。

## 5. 领域影响盘点

- 候选：Herdr recovery owner / auto restore disabled fail-closed 是稳定流程约束，后续 `herdr-user-surfaces-parity`、validation matrix、supportability 必须消费。建议后续如需长期归档，走 `cs-domain` 或 `cs-keep`，本 acceptance 不直接改 CONTEXT/ADR。
- 候选：真实 Herdr recovery supported 仍未成立；support projection 必须继续 fail closed。该约束已写入 roadmap notes 和 QA residual risk。

## 6. requirement delta / clarification 回写

- Requirement：`.codestable/requirements/native-windows-ccb-via-herdr.md`。
- 结论：本 feature 不新增用户可见能力，不改变 requirement 边界；只实现 roadmap 已批准的 recovery boundary 子项。Requirement unchanged，无需 req delta。

## 7. roadmap 回写

- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`：`herdr-bounded-recovery-boundary` 已从 `in-progress` 改为 `done`，notes 写入 accepted 摘要和 blocked evidence 边界。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`：第 8 个子 feature 状态已改为 `accepted`，备注同步。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml`：当前 feature status 已改为 `accepted`，`current_feature_index` 前进到 8，`handoff_next` 指向 `herdr-user-surfaces-parity`。

## 8. attention.md 候选盘点

- 本 feature 未暴露需要加入 `.codestable/attention.md` 的新通用命令或环境坑。已有 `PYTHONDONTWRITEBYTECODE=1` 规则仍适用。

## 9. 遗留

- `REV-005`：真实 production `herdr_auto_restore_mode=disabled` producer 未在本 feature 证明；当前行为 fail-closed，后续 user-surface/validation/supportability 不得宣称 supported recovery。
- Native Windows Herdr real recovery pass 未采集；当前 S7 只有 server not_running / capabilities null 的 blocked evidence。
- 后续 `herdr-user-surfaces-parity` 必须把 blocked/fail-closed recovery evidence 投影到用户可见诊断，不得升级为 supported。

## 10. 最终审计

- 验证证据来源：`herdr-bounded-recovery-boundary-qa.md`。
- Evidence sources：implementation report、review report、QA report、S7 blocked evidence。
- 聚合命令：
  - checklist YAML：exit 0。
  - roadmap items YAML：exit 0。
  - provider-runtime admission：exit 0。
  - Herdr focused tests：28 passed。
  - recovery/restore/crash regression：20 passed, 24 deselected。
  - runtime refresh/rebind focused：3 passed, 3 deselected。
  - scope/content guard：exit 0。
  - probation/circuit/raw-token guard：exit 0。
  - `git diff --check` scoped files：exit 0，只有 Markdown LF/CRLF warning。
- 场景复核：re-verified 11 / trust-prior-verify 1。trust-prior item is S7 manual Herdr blocked evidence from the captured artifact.
- 交付物复核：代码、测试、implementation、review、QA、acceptance、roadmap items/main doc、goal-state 均已落盘。
- 完整工作区复核：dirty files are scoped to this feature and roadmap state writebacks; no staged files.
- diff 清洁度：通过；无 debug output、TODO/FIXME/XXX、方案外文件。
- 知识沉淀出口：无 attention 候选；residual risk 已写入 roadmap / QA / acceptance。
- 结论：通过。该 child feature 已 accepted，但真实 Herdr recovery supported 仍不得声明。
