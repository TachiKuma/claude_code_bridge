---
doc_type: feature-acceptance
feature: 2026-07-31-provider-runtime-on-herdr
status: passed
audit_state: completed
audit_reason: ""
auditor_id: "019fc403-a65f-7490-8e60-c5ef99a55669"
acceptance_authorization_ref: "approval-report.md#goal-acceptance"
accepted: 2026-08-03
round: 1
---

# provider-runtime-on-herdr 验收报告

> 阶段：阶段 3（验收闭环）  
> 验收日期：2026-08-03  
> 关联方案 doc：`.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-design.md`

## 1. 接口契约核对

**接口示例逐项核对**：
- [x] `ProviderRuntimeBackendRef`：session payload 写入 backend-neutral runtime ref。代码实现已在 S3 落地，implementation 记录 `backend_impl=herdr`、`namespace_ref`、`pane_ref`、`managed_home`、`completion_source`、`completion_source_kind` 和 restore token redaction；相关 focused tests 已通过。
- [x] `CCB provider authority`：ask/pend/completion/cancellation/job terminal verdict 仍由 CCB provider execution / dispatcher / completion tracker 主导。S5/S6 tests、review 和 QA 均确认 Herdr agent state 不产生 completed verdict，cancel 只写 CCB cancelled decision。
- [x] `terminal capture fallback`：只作为 provider-declared fallback / diagnostics。S5 记录 Claude fallback diagnostics，并由 CMD-007 复核。
- [x] `Herdr agent state evidence`：只进入 diagnostics/evidence。CMD-010 guard 通过。

**名词层“现状 → 变化”逐项核对**：
- [x] Herdr provider launch 不要求 tmux binary：S2 完成，focused tests 通过。
- [x] Herdr provider session payload 不回退 tmux factory：S3 完成，backend resolver focused tests 通过。
- [x] provider session lifecycle 在 Herdr 下不做 tmux ownership/rebound：S4 完成，CMD-005 通过。
- [x] all-public-provider evidence：S7 冻结 20 个 public provider snapshot，transcript 覆盖 20 行 blocked evidence。

**流程图核对**：
- [x] launch → session payload → lifecycle → completion authority → cancel/restart → S7 evidence 的流程均有 implementation / review / QA evidence。
- [x] S7 manual evidence 明确是 blocked workflow evidence，不是 supported workflow pass。

## 2. 行为与决策核对

**需求摘要逐项验证**：
- [x] CCB 托管 provider 可在 Herdr pane runtime contract 下启动与绑定：fake Herdr / session payload / lifecycle focused tests 覆盖。
- [x] ask/pend/completion authority 仍归 CCB：CMD-006、CMD-007、CMD-010 覆盖。
- [x] cancellation/restart surface 不接管 bounded recovery：S6 tests、review 和 QA 覆盖。
- [x] public provider catalog evidence 完整：snapshot + transcript 覆盖当前 20 个 public provider。

**明确不做逐项核对**：
- [x] 不实现 bounded recovery owner / probation / circuit：S7 scoped guard 未命中 recovery owner；roadmap downstream 仍保留 `herdr-bounded-recovery-boundary`。
- [x] 不扩展 Mobile terminal、Config UI、doctor/support、package/release/update/installer/public validation matrix：S7 scoped guard 通过；roadmap downstream 仍 fail closed。
- [x] 不修改 Herdr socket schema/client owner：S7 scoped guard 通过；全局 CMD-009 命中既有 dirty `test/test_herdr_backend_client.py`，已隔离为非本轮范围。
- [x] 不把 Herdr agent state、pane liveness 或 terminal quiet 单独转成 completed：CMD-010 通过。

**关键决策落地**：
- [x] AC-012 blocked evidence 路径：design 允许逐 provider blocked evidence，S7 transcript 20/20 rows 全 blocked，acceptance 保留 residual risk。
- [x] CMD-004 baseline-risk：`evidence/cmd004-baseline-exemption.md` 明确不能解释为全量通过。
- [x] downstream fail-closed：roadmap 状态只将本 child accepted，不写 supported/release/public matrix pass。

**挂载点反向核对**：
- [x] 本 feature 挂载点集中在 provider runtime launch/session/lifecycle/completion/cancel/restart 和 CodeStable evidence/roadmap 状态。
- [x] S7 没有新增业务代码挂载点；新增只读 evidence 和状态文档。
- [x] 拔除沙盘推演：删除 S7 evidence 后只会失去 acceptance artifact，不会改变 runtime 行为。

## 3. 验收场景核对

- [x] AC-001 dependency admission：S1 passed；前置 roadmap accepted，CMD-003 admission focused pytest `224 passed`。
- [x] AC-002/003 runtime launch：S2 passed；CMD-004 全量仍有 baseline-risk，相关 Herdr focused coverage 已通过，风险见第 9 节。
- [x] AC-004/005 session payload / backend resolver：S3 passed。
- [x] AC-006 provider session lifecycle：CMD-005 `15 passed`。
- [x] AC-007 ask/pend authority：CMD-006 `48 passed`。
- [x] AC-008/009 native completion / fallback：CMD-007 `26 passed, 23 deselected`。
- [x] AC-010/011 cancellation / restart surface：CMD-008 `18 passed`，restart Herdr surface明确 unsupported/deferred。
- [x] AC-012 all-provider workflow evidence：snapshot count 20；transcript rows 20/20，全部 blocked；不宣称 supported。
- [x] AC-013 scope boundary：S7 scoped guard 通过，CMD-010 通过；全局 CMD-009 既有 dirty 已隔离。

**review 报告重点复核**：
- [x] Test And QA Focus 已覆盖：catalog freshness、all-provider blocked evidence、CMD-004 baseline-risk、scope dirty 隔离。
- [x] residual risk 已进入本报告第 9 节。

**QA 报告重点复核**：
- [x] 验证证据来源：`.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-qa.md`，status passed。
- [x] QA matrix 覆盖 design AC-012、review focus 和 residual risk。
- [x] failed / blocked 项为 none。
- [x] residual-risk 不承载未说明的核心缺口；真实 provider workflow 未运行是 design 允许的 per-provider blocked evidence。

## 4. 术语一致性

- `ProviderRuntimeBackendRef`：实现、review、QA、acceptance 中语义一致。
- `CCB provider authority`：未被 Herdr agent state 替代。
- `completion_source_kind`：保持 provider manifest 精确语义。
- `blocked evidence`：全链路使用为“证据完整性 / fail closed”，未写成 supported。
- 防冲突：S7 scoped guard 未发现 support/release/public matrix/Herdr schema client owner 误用。

## 5. 领域影响盘点

- [x] `ProviderRuntimeBackendRef`：已有 design 术语，本 feature 将其落地到 runtime/session payload。可作为 `cs-domain` 术语候选，不在 acceptance 里直接改 CONTEXT。
- [x] `Herdr agent state diagnostics-only`：稳定流程约束，可作为 ADR/CONTEXT 候选；不阻塞 acceptance。
- [x] `blocked evidence不得support投影`：稳定 supportability 约束，可由后续 supportability feature 或 `cs-keep` 沉淀。
- [x] 结构性选择：Provider authority 留在 CCB，Herdr 只提供 terminal primitive/evidence。这已在 roadmap/design 中表达；本 child 不新写 ADR。

## 6. requirement delta / clarification 回写

- requirement: `.codestable/requirements/native-windows-ccb-via-herdr.md`
- 判定：已有 draft requirement，当前 child 是整体能力的一个 provider-runtime 子项，不改变用户可见能力边界，也不把 Windows supported 状态提前完成。
- 结论：不在 acceptance 阶段自由回写 requirement。后续只有 validation matrix / supportability projection 完成后，才应按 owner-approved delta 更新 requirement `implemented_by` 或状态。

## 7. roadmap 回写

- [x] frontmatter `roadmap=windows-native-herdr-ccb`、`roadmap_item=provider-runtime-on-herdr` 成对存在。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`：`provider-runtime-on-herdr` 已从 `in-progress` 改为 `done`。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml`：feature status 已改为 `accepted`；`handoff_next` 指向 `herdr-bounded-recovery-boundary`。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`：子 feature 状态已改为 `accepted`。
- [x] downstream features 仍保持 in-progress / pending，不投影 supported。

## 8. attention.md 候选盘点

- 候选：provider all-workflow blocked evidence 可以满足 S7 evidence 完整性，但不得投影为 supported。
- 候选：CMD-004 Codex bridge bootstrap `input.fifo/output.fifo` 是当前基线风险，不能当作全量 pass。
- 当前不直接写 `attention.md`；如后续同类 feature 仍会反复踩，建议走 `cs-note` 追加短规则。

## 9. 遗留

- 所有 20 个 public provider 的 Native Windows x64 Herdr workflow 仍是 blocked evidence；任何 support/release/public matrix 投影必须继续 fail closed。
- CMD-004 全量 runtime launch bundle 仍有 Codex bridge bootstrap baseline-risk，不能当作全量 pass。
- 全局 CMD-009 仍命中既有 dirty `test/test_herdr_backend_client.py`；本 child 只确认 S7 scoped guard 通过。
- 后续 `herdr-bounded-recovery-boundary` 必须继续处理 single recovery owner；本 child 不接管 recovery。

## 10. 最终审计

- 验证证据来源：`provider-runtime-on-herdr-qa.md`
- Evidence sources：implementation、review、QA、S7 evidence files、roadmap state。
- 聚合命令：
  - checklist YAML validation：passed
  - roadmap items YAML validation：passed
  - goal-state YAML validation：passed
  - public provider snapshot JSON validation：passed
  - catalog focused tests：`9 passed`
  - CMD-005：`15 passed`
  - CMD-006：`48 passed`
  - CMD-007：`26 passed, 23 deselected`
  - CMD-008：`18 passed`
  - CMD-010 guard：passed
  - scoped S7 content guard：passed
  - scoped `git diff --check`：passed，只有 CRLF/LF warning
- 场景复核：re-verified 13 / trust-prior-verify 0。
- 交付物复核：
  - code：S1-S6 runtime changes already reviewed and QA-passed。
  - evidence：snapshot、all-provider transcript、CMD-004 baseline-risk evidence present。
  - docs/state：checklist、implementation、review、QA、acceptance、roadmap state present。
  - requirement：unchanged by design。
  - roadmap：provider-runtime item done/accepted, downstream fail-closed。
- 完整工作区复核：工作区 dirty 很大；本 acceptance 覆盖 provider-runtime-on-herdr 和 roadmap current scope，未声称全局 clean。
- diff 清洁度：S7/acceptance scope 无 debug/TODO/commented-out code/forbidden owner。
- 知识沉淀出口：attention candidates recorded in 第 8 节；domain/keep candidates recorded in 第 5 节。
- 结论：通过。Feature accepted with residual risk；不得把 all-provider blocked evidence 投影为 provider supported、Windows supported、release-ready 或 public validation matrix pass。
