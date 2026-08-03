---
doc_type: feature-acceptance
feature: 2026-07-31-native-windows-public-workflow-validation-matrix
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: "approval-report.md#goal-acceptance"
accepted: 2026-08-03
round: 1
---

# native-windows-public-workflow-validation-matrix 验收报告

> 阶段：阶段 3（验收闭环）  
> 验收日期：2026-08-03  
> 关联方案 doc：`.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-design.md`

## 1. 接口契约核对

- [x] `WindowsHerdrPublicWorkflowEvidence` schema 已落地到 `lib/terminal_runtime/windows_herdr_public_workflow_matrix.py`，并由单元测试覆盖 required workflow key set、summary/detail row 一致性、未知字段拒绝和 nullable scalar 校验。
- [x] public provider catalog 通过 `build_default_provider_manifests(include_optional=True, include_test_doubles=False)` 冻结，拒绝子集与 test double；所有公开 provider 均有 `ask`、`pend`、`completion`、`cancel` 行。
- [x] parent admission 从 roadmap `depends_on` 解析到 parent feature acceptance，并要求 `doc_type=feature-acceptance`、`status=passed` 与 repo-root 内可验证 evidence refs。
- [x] artifact validator 是 root-aware：覆盖顶层 `artifacts`、workflow/provider detail refs、parent refs，并拒绝 repo root 逃逸、absolute/rooted、Windows drive 与 UNC refs。

## 2. 行为与决策核对

- [x] 当前 matrix 是 blocked candidate evidence：`support_projection_allowed=false`、`support_tier=beta`、`support_tier_is_candidate=true`，不构成最终 Native Windows supported 宣称。
- [x] support projection hard gate 要求 required workflows、provider workflows、Mobile terminal、Config UI、Windows npm install dry-run、`ccb_source_status=strict-v8.5.2`、`herdr_auto_restore_mode=disabled`、parent refs 和 `beta_gaps=[]` 全部满足。
- [x] blocked/partial/failed/not-run 不能被升级为 supported；provider pass detail row 必须有 `pane_ref`，workflow/provider pass row 必须有 `artifact_ref` 与 `host_evidence_ref`。
- [x] docs 只说明 matrix 字段与 doctor artifact 读取方式，并清理旧 `doctor --bundle` 当前命令口径；未发布 README、doctor、installer 或 release supported 文案。

## 3. 验收场景核对

- [x] S1/S3：required workflow rows 与 provider workflow rows 完整，summary/detail key/status 一致，缺 key 或未知状态 fail closed。
- [x] S2：parent acceptance refs 缺失、否定语境、裸 CMD refs、CMD+missing evidence 混合行均 fail closed；当前 parent admission probe 返回 ready。
- [x] S4：support tier candidate rule 对 workflow/provider/Mobile/Config/npm/source/restore/beta gap 逐项硬门控。
- [x] S5：Native Windows transcript、provider transcript、blocked evidence、provider freeze 和 matrix JSON 均归档到本 feature `evidence/` 目录；当前缺真实 full pass 条件时只记录 blocked evidence。
- [x] S6/S7：diagnostics contract delta 与 scope guard 通过，未修改 provider completion、recovery owner、publish/promotion 或 final support claim。
- [x] Review/QA focus：`reviewer: subagent+ocr` 已 passed；QA passed；final subagent rereview 无 blocking/important finding，OCR closure 为 0 findings。

## 4. 术语一致性

- `support_tier_is_candidate` 表示矩阵候选状态，不等于最终支持等级发布。
- `support_projection_allowed` 是下游 supportability projection 的硬门控结果。
- `public_providers`、`provider_workflow_rows`、`provider_workflow_detail_rows` 在代码、tests、evidence 和报告中保持一致。

## 5. 领域影响盘点

- 新术语候选：`WindowsHerdrPublicWorkflowEvidence`、`support_tier_is_candidate`、`support_projection_allowed`、`parent admission`。
- 结构性选择候选：root-aware evidence validator 作为 supportability projection 前置 gate。
- 流程级约束候选：blocked candidate matrix 可被验收为证据完整，但不能转化为 supported 宣称。

## 6. requirement delta / clarification 回写

- Requirement: `native-windows-ccb-via-herdr`。
- 本 feature 只建立 Native Windows public workflow validation matrix 的 schema、证据完整性与 blocked candidate artifact，不改变 owner-level capability boundary。
- 最终 support tier 和 README/doctor/docs supported 文案仍归后续 `herdr-supportability-projection`。

## 7. roadmap 回写

- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml` 中 `native-windows-public-workflow-validation-matrix` 更新为 `done`。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md` 子 feature 清单中对应状态更新为 `accepted`。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml` 中当前 feature 更新为 `accepted`，`current_feature_index` 前进到 11，并交接到 `herdr-supportability-projection`。

## 8. attention.md 候选盘点

- 候选：Windows 下运行 `.codestable` Python 工具时同时设置 `PYTHONDONTWRITEBYTECODE=1` 与 `PYTHONUTF8=1`，减少 Python 3.14 + Windows 工具链异常和编码漂移。
- 不在 acceptance 内直接写 attention；后续可用 `cs-note` 归档。

## 9. 遗留

- 当前 matrix 不是 full Native Windows workflow/provider pass transcript；真实全量 public workflow/provider transcript 仍需后续 supportability projection 或实际证据捕获重新判断。
- 当前所有 workflow/provider 行保持 blocked；这满足本 feature 的证据完整性目标，但不能声明 Windows x64 CCB supported。
- 本轮外 dirty files `.codestable/gates/roadmap-goal-gates.yaml`、`.codestable/reference/agent-conventions.md`、`笔记.md` 不属于本 feature 提交范围。

## 10. 最终审计

- 验证证据来源：`.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-qa.md`。
- Evidence sources：evidence pack、gate results、DoD results、matrix JSON、provider freeze、Native Windows transcript、provider transcript、blocked evidence。
- 聚合命令：
  - checklist YAML：passed。
  - roadmap items YAML：passed。
  - `python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py`：68 passed。
  - `python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "parent_admission or blocked_skeleton"`：22 passed, 46 deselected。
  - scope guard、DoD runner、evidence pack：passed。
  - root-aware artifact/admission probe：`matrix artifacts ok; parent admission ready`。
  - `git diff --check` scoped feature files：passed with CRLF warnings only。
- 交付物复核：代码、tests、docs delta、checklist、review、QA、acceptance、evidence 和 roadmap/goal-state 回写均存在。
- 结论：通过。Goal driver 可进入 feature accepted 状态回写与 scoped commit 授权核验。
