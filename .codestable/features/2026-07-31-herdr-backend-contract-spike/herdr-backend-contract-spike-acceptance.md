---
doc_type: feature-acceptance
feature: 2026-07-31-herdr-backend-contract-spike
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: approval-report.md#goal-acceptance
accepted: 2026-08-01
round: 1
---

# herdr-backend-contract-spike 验收报告

> 阶段：Goal feature acceptance
> 验收日期：2026-08-01
> 关联方案 doc：`.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design.md`

## 1. 接口契约核对

- [x] 本 feature 只新增 spike runner、runbook、machine evidence、gate evidence、evidence pack 和 focused tests，未把 Herdr 注册进 production mux/backend resolver。
- [x] `herdr-contract-spike-evidence.json` 是后续设计唯一可消费的机器证据，包含 host、platform gate、Herdr schema/status、operation、provider dry-run、restore isolation、capability projection 和 route recommendation。
- [x] 当前 machine evidence 已按 Restore Capability Matrix v2 重跑：`verdict=partial`、`failure_class=windows-beta-gap`、`adapter_recommendation=continue-with-gaps`。
- [x] 前置 platform gate 已通过：`.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/platform-gate-summary.json` 记录 v8.5.2 source admission、64-bit Python、Native Windows x64 Herdr 与 x64 CCB helper PE evidence 均满足；当前阻塞来自 Herdr CLI primitive 语义未全部证明。

## 2. 行为与决策核对

- [x] platform gate 通过后只在 dedicated session `ccb-herdr-spike` 内执行 Herdr operation；schema/status/session_attach/pane_spawn/send_input/read_output/kill_pane/server_restart_layout_restore 为 pass，server_restart_process_continuity 与 server_restart_output_history 为 blocked/windows-beta-gap，ui_detach_reattach 为 needs_harness。
- [x] validator 覆盖并拒绝 fake pass：blocked verdict 却 continue、pass operation 缺 trace refs、artifact refs 缺失、duplicate core operation、unknown URI、restart isolation 缺 socket/config/server identity/stop ref、fallback 冒充 provider dry-run。
- [x] provider CLI dry-run 与 fallback terminal smoke 分离，`public_provider_parity_claimed=false`，fallback 不作为 completion authority。
- [x] server restart restore 只允许 dedicated/disposable server 或 isolated session/socket/config；当前已有 server identity、stop-command trace、process-info trace，workspace/pane identity restore 通过，但旧 process 与 output history 未恢复。
- [x] spike 结论是基础 adapter 可按 layout-only restart restore 继续，但不得宣称 Herdr restart process/output continuity 或 Windows supported。

## 3. 验收场景核对

- [x] AC-001 host admission：machine evidence 在 Native Windows x64 + supported platform gate 下运行，只使用 dedicated session。
- [x] AC-002 schema/status：Herdr `api schema --json` 与 `status --json` 均采集并通过。
- [x] AC-003/AC-004 session/pane I/O：session_attach、pane_spawn、send_input、read_output 均有 pass evidence，`pane wait-output` 观察到 sentinel。
- [x] AC-005 provider dry-run：当前 blocked，provider dry-run 不被 fallback 替代。
- [x] AC-006 kill pane：spike-created pane close 返回 ok，未误删 session。
- [x] AC-007 detach/reattach：当前记录为 needs_harness，已将 `herdr-ui-detach-reattach-harness` 作为后续步骤落盘，未用 server restart 结果替代 UI detach/reattach。
- [x] AC-008 restart isolation：当前 dedicated session 已记录，server identity / stop command trace / process-info trace 存在；workspace/pane identity restore 通过，旧 process 与 output history 未恢复。
- [x] AC-009 production no-change：scope gate 与 no-production-route tests 通过。
- [x] AC-010 recommendation truth table：`adapter_recommendation=continue-with-gaps` 与 host/platform、operation、provider、restart、capability 状态一致。

## 4. Review / QA 复核

- [x] Review report status passed，`reviewer: subagent+ocr`，最终独立 reviewer `019fbb68-cccf-7a91-ab93-b1c25064cda3` passed，blocking / important / nit 均为 none。
- [x] QA report status passed，明确当前证据是 valid fail-closed blocked evidence，不证明 Herdr capability support。
- [x] Evidence pack、scope gate、DoD results、evidence-pack gate 均为 passed。
- [x] Provider warnings 为 archguard/meta-cc skipped，已在 evidence pack 和 QA 中解释。

## 5. DoD Contract 核对

- [x] DOD-IMPL-001：未修改 production terminal_runtime、ccbd、provider_backends 或 package metadata。
- [x] DOD-IMPL-002：Herdr schema/status/session/pane/send/read/kill/detach/restart/provider dry-run 均有 operation evidence 或 blocked reason。
- [x] DOD-IMPL-003：restore evidence 区分 detach persistence 与 server restart restore；restart 未隔离时 blocked。
- [x] DOD-IMPL-004：provider dry-run 与 fallback 分离，未声明 all-provider parity。
- [x] DOD-IMPL-005：validator 覆盖 fake pass、artifact refs、host/platform gate、restart isolation、fallback split 和 blocking gap truth table。
- [x] DOD-IMPL-006：production mux contract 不含 Herdr native route。
- [x] DOD-REVIEW-001：code review passed。
- [x] DOD-QA-001：QA passed。
- [x] DOD-ACCEPT-001：roadmap item 已回写为 done，并给出后续 contract V2 的 route recommendation：continue-with-gaps。

## 6. Roadmap / Requirement 回写

- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml` 中 `herdr-backend-contract-spike` 已回写为 `done`。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md` 子 feature 清单状态已回写为 `accepted`，并记录 fail-closed / stop 结论。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml` 中当前 feature 已回写为 `accepted`，`current_feature_index` 前进到 2。
- [x] 因 `adapter_recommendation=continue-with-gaps`，goal-state 顶层已恢复 `ready-to-dispatch`；下游 Herdr adapter 只能按 layout-only restart restore、`old_process_expected_to_survive=false`、`output_history_restored=false` 继续，UI detach/reattach 进入 follow-up。

## 7. 遗留

- 真实 Herdr active-host 能力仍仅部分证明；UI detach/reattach 未在 Herdr UI client 内验证，restart restore 不恢复旧 process 或 sentinel 输出历史。
- 后续可以推进 `mux-backend-contract-herdr-v2`、`herdr-backend-client` 等基础 adapter feature，但必须把 restore 能力声明为 layout-only + CCB-side recovery，不得声明 process/output continuity 或 Windows supported。
- 本地 scoped commit 已获 `approval-report.md#goal-commits` 授权；该授权不包含 push、merge、release、publish、deploy 或 promotion。

## 8. 最终审计

- Acceptance authorization: `approval-report.md#goal-acceptance` 已 approved。
- Commit authorization: `approval-report.md#goal-commits` 已 approved；提交仍只允许本 feature scoped commit，不包含 push。
- Checklist steps: done。
- Checklist checks: passed。
- Roadmap item: done。
- Goal state: feature accepted，`current_feature_index` 前进到 2，top-level status 为 `ready-to-dispatch`。
- 结论：通过；route recommendation 已调整为 `continue-with-gaps`，Goal driver 可继续下游 adapter 工作，但必须保留 v2 restore 缺口与 follow-up。
