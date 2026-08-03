---
doc_type: feature-acceptance
feature: 2026-07-31-herdr-user-surfaces-parity
status: passed
audit_state: completed
audit_reason: ""
auditor_id: "019fc5e6-2df2-7672-995d-ae52f088f649"
acceptance_authorization_ref: ".codestable/roadmap/windows-native-herdr-ccb/approval-report.md#goal-acceptance"
accepted: 2026-08-03
round: 1
---

# herdr-user-surfaces-parity 验收报告

> 阶段：阶段 3（验收闭环）  
> 验收日期：2026-08-03  
> 关联方案 doc：`.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-design.md`

## 1. 接口契约核对

- [x] `HerdrSurfaceProjection`：shared projection 输出 `backend_impl`、`capability_status`、`support_tier_projection/source`、`beta_gaps`、`blocking_gaps`、`degraded_next_action` 与 redacted `evidence_refs`。代码落点：`lib/ccbd/herdr_surface_projection.py`。
- [x] `herdr_surface_projection_passes_gate()`：Config UI supported hard gate 要求 backend/capability/support tier/source/gaps/next action 全部满足，partial/degraded 不 pass。
- [x] ProjectView / ping source of truth：ProjectView 与 ping 均消费同一 Herdr projection；doctor/mounted/diagnostics 透传或渲染同名字段。
- [x] Terminal target abstraction：Mobile history/message/websocket 对 Herdr 使用 backend-neutral target，不要求 tmux socket/session/%pane；blocked path 返回 structured `terminal_blocked`。
- [x] Diagnostics bundle source：bundle 只记录 redacted/generated projection source，不归档 raw Herdr refs、provider secret 或 terminal buffer 全量。

## 2. 行为与决策核对

- [x] 需求摘要：foreground attach、Mobile terminal、Config UI、doctor、ping、mounted、project view、diagnostics bundle 都能显示 Herdr backend identity、capability/support tier projection、beta/blocking gaps 和 next action。
- [x] supported/blocked gate：Mobile terminal 与 Config UI partial/degraded 均是 blocked evidence，不会被后续 supportability 当作 supported。
- [x] 明确不做：未改 provider completion、package/release/update/installer/npm metadata/support final claim、Herdr socket schema/client owner。
- [x] 关键决策落地：Herdr 不伪装为 tmux；缺真实 Herdr production adapter 时 fail closed 为 structured blocked，不回退 tmux 503。
- [x] 挂载点反向核对：实际落点覆盖 design 2.3 的 projection、foreground、Mobile、Config UI、doctor/diagnostics、path/redaction helper 与 tests；未发现清单外 release/support/package owner 变更。
- [x] 拔除沙盘推演：删除 shared projection 与 surface hook 后会移除本 feature 用户可见证据，不会影响 provider completion 或 package/release owner。

## 3. 验收场景核对

- [x] AC-001 upstream admission：CMD-003 passed；`provider-runtime-on-herdr` 与 `herdr-bounded-recovery-boundary` 已 accepted 且 artifacts 可验证。
- [x] AC-002 ProjectView：CMD-004 `130 passed, 29 deselected` 覆盖 Herdr projection 与 redaction。
- [x] AC-003 ping：CMD-004 与 CMD-008 ping excerpt 显示 projection/source/next action 一致。
- [x] AC-004 foreground attach supported：CMD-005 与 CMD-008 pass 样例显示 backend-neutral attach，`tmux_fallback=not_called`。
- [x] AC-005 foreground attach blocked：CMD-008 blocked error 含 beta gap、blocking gap、next action，不要求 tmux。
- [x] AC-006 Mobile supported：CMD-005 与 CMD-008 supported samples 覆盖 history/message/websocket Herdr target。
- [x] AC-007 Mobile blocked：CMD-008 blocked samples 均返回 `status=blocked` / `terminal_blocked`。
- [x] AC-008 doctor/mounted/diagnostics：CMD-004 与 CMD-008 doctor/mounted excerpt 覆盖 projection/source/gaps/next action。
- [x] AC-009 Config UI readonly：CMD-005 与 CMD-008 覆盖 partial -> blocked、supported projection -> pass；config edit/apply contract 未改变。
- [x] AC-010 tmux/rmux regression：CMD-006 `231 passed`。
- [x] AC-011 scope boundary：CMD-007 passed，无 provider completion/package/release/update/installer/support final claim/Herdr socket schema-client owner 越界。
- [x] AC-012 Native Windows transcript：CMD-008 transcript 覆盖 foreground、Mobile、Config UI、doctor、ping、mounted、project view；明确不声明 final supported。

**review 报告重点复核**：
- [x] Test And QA Focus 已由 QA 报告覆盖。
- [x] `REV-006` 作为非阻塞文案精度 residual 保留，不影响 gate 语义。

**QA 报告重点复核**：
- [x] 验证证据来源：`.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-qa.md`，status passed。
- [x] QA matrix 覆盖 AC-001..AC-012，failed/blocked 项为 none。
- [x] residual-risk 不承载核心验收缺口；CMD-008 被明确限定为 surface parity/pass-blocked gate evidence。

## 4. 术语一致性

- `public surface`：本报告、design、QA 中均指 foreground/Mobile/Config UI/doctor/ping/mounted/project view/diagnostics bundle。
- `Herdr evidence projection`：实现统一为 shared projection，不分散在 renderer 中解释支持等级。
- `degraded next action`：持续作为 actionable diagnostic，不等同 backend available。
- `terminal target abstraction`：Mobile Herdr target 不要求 tmux `%pane`。
- 防冲突：未使用 `Windows x64 CCB supported` 作为本 feature 结论；`support_tier_projection` 仅是 projection，不是 final support tier。

## 5. 领域影响盘点

- 候选：Herdr public surface projection 是稳定支持面概念，可后续走 `cs-domain` / `cs-keep` 沉淀；当前 roadmap/design 已表达，acceptance 不直接写 CONTEXT/ADR。
- 候选：Mobile terminal 与 Config UI 是 supported hard gate；后续 validation/supportability feature 必须消费该约束。
- 当前仓库无 `requirements/CONTEXT.md`，存在 `.codestable/requirements/native-windows-ccb-via-herdr.md`；本 acceptance 不创建新的领域文档。

## 6. requirement delta / clarification 回写

- Requirement：`.codestable/requirements/native-windows-ccb-via-herdr.md`，当前 `status: draft`。
- 判定：本 feature 是 draft requirement 下 roadmap 的用户可见面子项，未改变最终 Windows supported 目标和边界；仍禁止把 partial/blocked 投影为 supported。
- 结论：Requirement unchanged；不在 acceptance 阶段自由回写 requirement，也不生成 req delta。

## 7. roadmap 回写

- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`：`herdr-user-surfaces-parity` 已从 `in-progress` 改为 `done`，notes 写入 accepted 摘要和“不声明 final supported”边界。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`：第 9 个子 feature 状态已改为 `accepted`，备注同步。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml`：当前 feature status 已改为 `accepted`，`current_feature_index` 前进到 9，`handoff_next` 指向 `windows-x64-release-surface`。
- [x] 后续 `windows-x64-release-surface`、validation matrix、supportability projection 仍未 accepted；整个 roadmap goal 不标 complete。

## 8. attention.md 候选盘点

- 本 feature 未暴露必须加入 `.codestable/attention.md` 的新通用命令或环境坑。
- 既有 `PYTHONDONTWRITEBYTECODE=1` 规则继续适用；pytest 64-bit 可用性已在 QA 中记录。

## 9. 遗留

- `REV-006`：Config UI blocked reason 对非 capability 字段失败时文案可更精确；完整 projection 已暴露失败字段，不阻塞。
- CMD-008 是本 feature harness + 同 roadmap true-host upstream evidence 的组合；它证明 surface projection 与 pass/blocked gate，不是最终 supportability 证据。
- Windows x64 CCB final supported 仍必须等待 release surface、public workflow validation matrix 和 supportability projection。
- `笔记.md` 是无关 dirty baseline；不属于本 feature 交付物。

## 10. 最终审计

- 验证证据来源：`herdr-user-surfaces-parity-qa.md`。
- Evidence sources：implementation report、review report、QA report、CMD-008 transcript、roadmap state。
- 聚合命令：
  - checklist YAML：exit 0。
  - roadmap items YAML：exit 0。
  - upstream admission：exit 0。
  - CMD-004：130 passed, 29 deselected。
  - CMD-005：106 passed, 1 skipped, 74 deselected。
  - CMD-006：231 passed。
  - CMD-007 scope/redaction guard：exit 0。
  - py_compile touched files：exit 0。
  - `git diff --check`：exit 0，只有 CodeStable Markdown LF->CRLF warning。
  - acceptance auditor `019fc5e6-2df2-7672-995d-ae52f088f649`：初次指出缺 acceptance/checklist/roadmap/goal-state 机械收口；本报告与状态回写已处理。
- 场景复核：re-verified 12 / trust-prior-verify 1。trust-prior item 是 CMD-008 manual transcript artifact。
- 交付物复核：代码、测试、implementation、review、QA、acceptance、CMD-008 evidence、roadmap items/main doc、goal-state 均已落盘。
- 完整工作区复核：工作区仍有本 feature dirty/untracked artifacts 和无关 `笔记.md` dirty baseline；staged none。验收只覆盖本 feature 可归因 diff。
- diff 清洁度：通过；未发现 debug output、TODO/FIXME/XXX、commented-out code、unused import 或方案外 release/support owner 变更。
- 知识沉淀出口：领域/keep 候选已在第 5 节登记；attention 无必写候选。
- 结论：通过。该 child feature 已 accepted，但不得声明 Windows x64 CCB final supported。
