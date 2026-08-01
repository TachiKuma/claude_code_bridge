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
- [x] 当前 machine evidence 为 fail-closed blocked：`verdict=blocked`、`failure_class=platform-gate-blocked`、`adapter_recommendation=stop`。
- [x] blocked 原因可追溯到前置 platform gate：`.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/platform-gate-summary.json`，detail reason 为 `ccb-version-mismatch`。

## 2. 行为与决策核对

- [x] platform gate blocked 时未执行 Herdr operation，所有核心 operation 均为 `status=blocked` 且 `command_ref=not-run`。
- [x] validator 覆盖并拒绝 fake pass：blocked verdict 却 continue、pass operation 缺 trace refs、artifact refs 缺失、duplicate core operation、unknown URI、restart isolation 缺 socket/config/server identity/stop ref、fallback 冒充 provider dry-run。
- [x] provider CLI dry-run 与 fallback terminal smoke 分离，`public_provider_parity_claimed=false`，fallback 不作为 completion authority。
- [x] server restart restore 只允许 dedicated/disposable server 或 isolated socket/config；当前因 platform gate blocked 未执行 restart。
- [x] spike 结论是停止正式 adapter 路线，不是 Herdr support pass。

## 3. 验收场景核对

- [x] AC-001 host admission blocked：machine evidence 输出 blocked，不运行 destructive 操作。
- [x] AC-002 schema/status：当前因 platform gate blocked 未采集，证据以 blocked reason 和 platform gate ref 表达，不伪造 schema pass。
- [x] AC-003/AC-004 session/pane I/O：当前 blocked，operation evidence 保留每个核心 primitive 的 blocked 状态。
- [x] AC-005 provider dry-run：当前 blocked，provider dry-run 不被 fallback 替代。
- [x] AC-006 kill pane：当前 blocked，未误删 session 或其他 pane。
- [x] AC-007 detach/reattach：当前 blocked，未夸大 live detach 或 server restart 后存活。
- [x] AC-008 restart isolation：当前 blocked-not-isolated，restart 未授权且未执行。
- [x] AC-009 production no-change：scope gate 与 no-production-route tests 通过。
- [x] AC-010 recommendation truth table：`adapter_recommendation=stop` 与 host/platform、operation、provider、restart、capability 状态一致。

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
- [x] DOD-ACCEPT-001：roadmap item 已回写为 done，并给出后续 contract V2 的 route recommendation：stop。

## 6. Roadmap / Requirement 回写

- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml` 中 `herdr-backend-contract-spike` 已回写为 `done`。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md` 子 feature 清单状态已回写为 `accepted`，并记录 fail-closed / stop 结论。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml` 中当前 feature 已回写为 `accepted`，`current_feature_index` 前进到 2。
- [x] 因 `adapter_recommendation=stop`，goal-state 顶层已进入 `handoff`，要求回到 epic planning/update 修复 platform gate evidence 或重规划后续 Herdr adapter features。

## 7. 遗留

- 真实 Herdr active-host 能力未被证明；当前结论是安全停止。
- 后续不得把 `mux-backend-contract-herdr-v2`、`herdr-backend-client` 等正式 adapter feature 当作 implementation-ready supported path，除非先修复 strict v8.5.2 platform gate evidence 并重跑 spike，或由 owner 批准新的 epic route。
- 本地 scoped commit 已获 `approval-report.md#goal-commits` 授权；该授权不包含 push、merge、release、publish、deploy 或 promotion。

## 8. 最终审计

- Acceptance authorization: `approval-report.md#goal-acceptance` 已 approved。
- Commit authorization: `approval-report.md#goal-commits` 已 approved；提交仍只允许本 feature scoped commit，不包含 push。
- Checklist steps: done。
- Checklist checks: passed。
- Roadmap item: done。
- Goal state: feature accepted，`current_feature_index` 前进到 2，top-level status 为 `handoff`。
- 结论：通过；因 route recommendation 为 `stop`，Goal driver 应停止并交回 epic 路线修订。
