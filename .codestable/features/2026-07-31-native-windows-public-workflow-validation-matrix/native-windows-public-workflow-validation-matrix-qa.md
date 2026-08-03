---
doc_type: feature-qa
feature: 2026-07-31-native-windows-public-workflow-validation-matrix
status: passed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-08-03
round: 1
---

# native-windows-public-workflow-validation-matrix QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-design.md`
- Checklist: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-checklist.yaml`
- Review: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-review.md`
- Evidence pack: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-gate-results.json`
- DoD results: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-dod-results.json`
- Diff basis: 当前 workspace diff；本报告只覆盖本 feature 可归因文件。
- Baseline dirty files: `.codestable/gates/roadmap-goal-gates.yaml`、`.codestable/reference/agent-conventions.md`、`笔记.md` 为本轮外 baseline。
- Feature type: mixed
- Core evidence gate: 核心功能路径是 schema/admission/artifact validator 的可证伪行为；当前 feature 不要求真实 full pass transcript，因为 design 明确允许 blocked candidate evidence，且不得发布 final support claim。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | checklist CMD-001 | supporting | checklist YAML 合法 | static | `python ".codestable/tools/validate-yaml.py" --file "...checklist.yaml" --yaml-only` | exit 0 | pass |
| QA-002 | checklist CMD-002 | supporting | roadmap items YAML 合法 | static | `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` | exit 0 | pass |
| QA-003 | design AC-001..AC-015 | core-functional | matrix schema、provider catalog、candidate rule、parent admission、artifact refs fail-closed | unit | `python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` | all pass | pass |
| QA-004 | review QA focus | core-functional | parent admission / blocked skeleton 重点回归 | unit | `python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "parent_admission or blocked_skeleton"` | all pass | pass |
| QA-005 | design scope guard | supporting | 不发布、不 push/tag、不越界 provider/recovery/final support claim | diff/static | checklist CMD-005 scope guard | exit 0 | pass |
| QA-006 | design CMD-006 | core-functional | evidence files 存在，当前 matrix 保持 blocked candidate | function | checklist CMD-006 evidence check | exit 0 | pass |
| QA-007 | review QA focus | core-functional | root-aware artifact validation 对当前 matrix ok，parent admission ready | function | Python import probe | exit 0 | pass |
| QA-008 | design docs guard | supporting | `doctor --bundle` 不作为当前公开命令 | static | checklist CMD-007 docs guard | exit 0 | pass |
| QA-009 | cleanliness | supporting | diff 清洁度、无临时 debug/TODO、py_compile | static | `git diff --check`、`rg`、`py_compile` | no blocking | pass |

## 3. Command Results

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-checklist.yaml" --yaml-only` -> exit 0：1 passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` -> exit 0：1 passed。
- `python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> exit 0：68 passed。
- `python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "parent_admission or blocked_skeleton"` -> exit 0：22 passed, 46 deselected。
- checklist CMD-005 scope guard -> exit 0。
- checklist CMD-006 evidence check -> exit 0。
- checklist CMD-007 docs guard -> exit 0。
- root-aware artifact/admission probe -> exit 0：`matrix artifacts ok; parent admission ready`。
- `git diff --check -- ...` -> exit 0：仅 `docs/ccbd-diagnostics-contract.md` LF->CRLF warning。
- `rg -n "TODO|FIXME|XXX|print\\(|pdb|debugger|console\\.log" ...` -> only design cleanliness rule text；无临时实现项。
- `python -m py_compile "lib/terminal_runtime/windows_herdr_public_workflow_matrix.py"` -> exit 0。

## 4. Scenario Results

- [x] QA-001 checklist YAML：pass
  - Evidence: validate-yaml exit 0。
- [x] QA-002 roadmap items YAML：pass
  - Evidence: validate-yaml exit 0。
- [x] QA-003 matrix validator core behavior：pass
  - Evidence: 68 unit tests passed。
- [x] QA-004 parent admission / blocked skeleton：pass
  - Evidence: 22 targeted tests passed。
- [x] QA-005 scope boundary：pass
  - Evidence: scope guard exit 0，无 publish/push/tag/final support/provider completion/recovery owner 越界。
- [x] QA-006 blocked candidate artifact：pass
  - Evidence: matrix `support_projection_allowed=false`，required workflows/provider workflows 全 blocked。
- [x] QA-007 current artifact root-aware load：pass
  - Evidence: root-aware validator returned ok，parent admission returned ready。
- [x] QA-008 docs guard：pass
  - Evidence: no unsupported `doctor --bundle` current-command usage。
- [x] QA-009 cleanliness：pass
  - Evidence: diff check and py_compile passed；清洁度扫描只命中 design 规则文本。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- 当前 matrix 是 blocked candidate evidence，不是真实 full Native Windows workflow/provider pass transcript；后续 supportability projection 必须重新执行 root-aware artifact validation。
- 本轮外 dirty files 后续 acceptance/commit 必须 scoped 排除。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass
- Out-of-scope files: pass，已记录 baseline dirty files。

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段。
