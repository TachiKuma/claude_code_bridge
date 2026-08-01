---
doc_type: feature-design-review
feature: 2026-07-31-native-windows-public-workflow-validation-matrix
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb953-d222-7723-b2e4-f1943478dd00
reviewed: 2026-08-01
round: 6
---

# native-windows-public-workflow-validation-matrix feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-design.md`
- Checklist: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Code facts checked: `lib/cli/parser_runtime/constants.py`, `lib/cli/parser_runtime/commands.py`, `lib/provider_core/registry.py`, `lib/provider_core/registry_runtime/builtin_backends.py`, roadmap 4.7, parent items status, docs doctor contract facts

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: 019fb953-d222-7723-b2e4-f1943478dd00
- Raw output: round 6 reviewer 返回 blocking/important 均为 none，1 个 nit 指出 report 正文 Verdict 与 frontmatter 状态不一致。
- Merge policy: 已逐条本地核验；nit 只涉及本 review 报告状态一致性，合并时一并修正。
- Gate effect: final verdict passed.

- Round 6 independent re-review completed after schema/support gate revisions. Local validation before reviewer completion: design YAML passed, checklist YAML passed, design-review frontmatter passed, roadmap items YAML passed, CMD-005 scope guard passed, scoped `git diff --check` passed; CMD-007 docs guard still fails on existing `docs/ccbd-diagnostics-contract.md` `doctor --bundle` baseline and remains an implementation target red light.

## 2. Design Summary

- Goal: 建立 Native Windows x64 public workflow validation matrix。
- Key contracts: required workflow key set、per-workflow evidence row、provider summary/detail row、source/recovery hard gate、support candidate rule、Native Windows transcript separation。
- Steps: 7 个步骤，风险热点是 required key 漏项、blocked skeleton、support claim 越界、mounted entry 映射和真机 evidence。
- Checks: checklist 当前 YAML 合法，steps/checks 均为 pending。
- Baseline / validation: 已包含 YAML 校验、matrix pytest、条件 parent refs、scope guard、docs guard 和 manual Windows transcript。

## 3. Findings

### blocking

- none

### important

- none

### nit

- none

### suggestion

- none

### learning

- Round 1 independent reviewer 返回 2 个 blocking、3 个 important、1 个 nit 和 1 个 suggestion；主 agent 已本地核验并修订 design/checklist：保留 roadmap 4.7 的 `support_tier` 字段，新增 `support_tier_is_candidate` 而不改名；明确 `mounted` workflow 的 canonical command 是 `ccb ping all`，不得新增 `ccb mounted`；收紧 parent acceptance refs 为 roadmap `depends_on -> feature -> {slug}-acceptance.md` passed frontmatter 与 artifact refs；将 `not-run` 纳入 reason fail-closed；CMD-004 改为条件消费 parent acceptance refs，不把 parent release-surface 测试变成本 feature owned tests；新增 CMD-007 清理 `doctor --bundle` 公开口径。
- Round 2 independent reviewer 返回 2 个 blocking、1 个 important、1 个 nit 和 1 个 suggestion；主 agent 已本地核验并修订 design/checklist：恢复 roadmap 4.7 顶层字段 `backend_impl/os_platform/cpu_arch/ccb_version/herdr_version/workflows/artifacts/support_tier`，将详细 row 放入扩展字段 `workflow_rows`；收窄 CMD-005，避免误杀带 `support_tier_is_candidate=true` 的合法 candidate evidence；按当前 CLI help 将 `watch` canonical transcript 改为 `ccb pend --watch <target>`，`ccb watch <target>` 作为 compatibility evidence；补齐 AC-005 coverage label 的 `failed`。
- Round 3 independent reviewer 返回 1 个 blocking、2 个 important 和 1 个 suggestion；主 agent 已本地核验并修订 design/checklist：CMD-005 改为当前 PowerShell 可执行的单引号 `python -c` 形式并已本地运行通过；`required_workflows` 恢复为 `list[RequiredWorkflow]`，`RequiredWorkflow` 是 roadmap 4.7 key set 的 `Literal[...]`；owner 越界 guard 从 snake_case 扩展为 whitespace / hyphen / snake_case 统一 regex。
- Round 4 independent reviewer 返回 0 个 blocking、2 个 important 和 1 个 suggestion；主 agent 已本地核验并修订 design/checklist：CMD-005 纳入未跟踪 `lib/test/docs/README.md` 文件内容扫描并已本地运行通过；schema/steps/CMD-003 补充 `required_workflows`、`workflows`、`workflow_rows` key set 等价和 `workflow_rows[k]["workflow"] == k` 一致性。
- Round 5 independent reviewer 返回 0 个 blocking、0 个 important、0 个 nit、0 个 suggestion；主 agent 本地核验：CMD-005 覆盖 tracked diff、staged diff 和未跟踪 `lib/test/docs/README.md` 文件内容；key set equality 与 row-key consistency 已写入 design schema 约束、S1 exit signal、checklist S1 和 CMD-003 covers；roadmap 4.7 顶层字段未漂移，`workflow_rows` 与 `support_tier_is_candidate` 只是扩展字段，不替代 roadmap 字段。
- Round 6 independent reviewer 返回 2 个 blocking、2 个 important、1 个 nit 和 1 个 suggestion；主 agent 已本地核验并修订 design/checklist：补回 roadmap 4.7 的 `ccb_source_status` 与 `herdr_auto_restore_mode` hard gate；恢复 `provider_workflow_rows[provider][workflow]=status` summary 形状，新增 `provider_workflow_detail_rows` 保存详细证据；明确公开 provider set 从 `build_default_provider_manifests(include_optional=True, include_test_doubles=False)` 或 `CORE_PROVIDER_NAMES + OPTIONAL_PROVIDER_NAMES` 恢复并归档冻结清单；CMD-004 改为可执行 parent admission pytest；CMD-006 改为带稳定 artifact path 的人工验收动作；`package.json` 的 `bin` 字段术语已修正。
- Round 6 re-review 返回 0 个 blocking、0 个 important 和 1 个 nit；主 agent 本地核验：nit 仅为本 review 报告正文状态与 frontmatter 不一致，已在本次合并中修正；design/checklist 不需再改。

### praise

- parent dependency guard fail-closed：parent feature 目录存在但没有 acceptance 文件时，只能生成 blocked/not-run skeleton，不把 design-review passed 当 implementation-ready。
- `pend --watch`、`doctor --output`、`doctor --bundle` unsupported、`mounted` 使用 `ccb ping all` 等 CLI 事实已经和 design 命令口径对齐。

## 4. User Review Focus

- 用户需要重点拍板：本 feature 只产出 validation matrix 和 candidate evidence，不发布最终 supported claim；Native Windows host 不可用时允许 blocked evidence。
- implement 需要重点遵守：roadmap 4.7 顶层 schema 字段、required key set、key set equality、parent acceptance fail-closed、candidate support rule、WSL/Linux evidence 分层。
- code review / QA / acceptance 需要重点复核：CMD-005 scope guard、CMD-007 docs guard、parent refs 缺失时 blocked skeleton、`package.json` 版本仍非 roadmap 目标时不得写 pass claim。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design 3.1/3.3 覆盖 AC-001..AC-015，checklist checks 可回指场景 | none |
| DoD Contract | pass | E | design 3.4 与 checklist dod.commands 覆盖 design/impl/review/QA/acceptance、manual/conditional guards、source/recovery hard gate 和 provider summary/detail consistency | none |
| Steps and checks traceability | pass | E | checklist S1..S7 与 checks 均可追溯到 design AC/DOD；round 1-6 findings 已映射到 schema/CMD/checks | none |
| Roadmap contract compliance | pass | E | roadmap 4.7 顶层字段、required workflow key set、`support_tier`、`ccb_source_status`、`herdr_auto_restore_mode` 和 `provider_workflow_rows` summary shape 均保留；扩展字段不替代 roadmap 字段 | none |
| Module interface design | pass | E | design 2.1 指定独立 matrix owner、schema invariant、consumer seam 和 local-substitutable tests | none |
| Validation and artifacts | pass | E | CMD-001/002/005 已运行通过；CMD-003/004/006/007 明确 future implementation 或条件/manual 验收边界 | implementation/QA 跟进 |

Summary: E=6, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- 当前 parent roadmap items 仍是 `in-progress`，对应 parent feature 目录没有 acceptance 产物；实现/acceptance 必须证明只能产出 blocked/not-run skeleton，不能写 pass claim。
- Native Windows x64 transcript 仍依赖真实 host 或 Windows runner；无 host 时只能 blocked，不能用 WSL/Linux 替代。
- 当前 `package.json` 是 `8.2.1`，roadmap/design 目标是 `8.5.2`；design 已要求版本不匹配时 blocked/not-run skeleton，implementation 和 acceptance 必须继续守住。
- CMD-007 在现有 docs baseline 上预期会红，因为 `docs/ccbd-diagnostics-contract.md` 仍有非 deprecated/unsupported 语境的 `doctor --bundle`；这是实现期需要修的目标红灯，不是 design gate 阻塞。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child batch loop；该 child design 保持 `draft`，等待所有 child design-review passed 后再由 epic 统一确认。

## 8. Focused Closure

- Closed findings: round 6 FDR-001、FDR-002、FDR-003、FDR-004、FDR-NIT-001，并采纳 artifact path suggestion。
- Attributed delta: 修改 design/checklist 的 schema、约束、steps、AC/DOD/CMD、provider catalog 来源、provider summary/detail shape、manual artifact path 和 review 报告状态一致性；不改变实现范围，不进入代码实现，不宣称 supported。
- Verification: `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-design.md"` passed；`python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-checklist.yaml" --yaml-only` passed；`python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-design-review.md"` passed；`python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` passed；CMD-005 scope guard passed；scoped `git diff --check -- ".codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix"` passed；CMD-007 docs guard 当前命中既有 `doctor --bundle` baseline，作为实现期目标红灯保留。
- Classification: round 6 修订改变 schema/validation 契约，已完成完整独立 re-review；最终复审无 blocking/important。
