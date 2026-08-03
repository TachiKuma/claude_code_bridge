---
doc_type: feature-review
feature: 2026-07-31-native-windows-public-workflow-validation-matrix
status: passed
reviewer: subagent+ocr
reviewed: 2026-08-03
round: 15
lane_a_state: completed
lane_a_ref: "019fc6f6-371b-7201-be78-625288834767"
lane_a_reason: "final independent subagent rereview: no blocking or important findings"
lane_b_state: completed
lane_b_ref: "72b92f6f-3c23-4bc8-a46a-bb93529c3a24"
lane_b_reason: "final OCR closure: 0 findings"
---

# native-windows-public-workflow-validation-matrix 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-design.md`
- Checklist: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-gate-results.json`
- DoD results: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-dod-results.json`
- Implementation evidence: `.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/native-windows-public-workflow-validation-matrix-implementation.md`
- Diff basis: 当前 workspace diff；本报告只覆盖本 feature 可归因文件。
- Review mode: full-rereview
- Baseline dirty files: `.codestable/gates/roadmap-goal-gates.yaml`、`.codestable/reference/agent-conventions.md`、`笔记.md` 为本轮外 baseline。

### Independent Review

- Detection: Task subagent 可用；OCR CLI 可用。
- 环节 A 独立隔离 Task agent: independent-agent + completed。
- 环节 B OCR CLI: completed。
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded。
- Merge policy: 所有 subagent/OCR findings 均已逐条本地核验；blocking/important 已修复并通过 closure。
- Gate effect: `reviewer: subagent+ocr`，满足 Goal feature code review gate。

## 2. Diff Summary

- 新增：`lib/terminal_runtime/windows_herdr_public_workflow_matrix.py`、`test/test_windows_herdr_public_workflow_matrix.py`、feature evidence/gate/implementation artifacts。
- 修改：`docs/ccbd-diagnostics-contract.md`、feature checklist、goal-state。
- 删除：none。
- 未跟踪 / staged：本 feature 新增文件未 staged；无 staged diff。
- 风险热点：证据 schema、repo-root path validation、parent admission fail-closed 语义、support projection gate。

## 3. Adversarial Pass

- 假设的生产 bug：matrix 或 parent acceptance 通过伪造 refs 被后续 supportability projection 当作可信 pass evidence。
- 主动攻击过的反例：缺失/未知 schema 字段、嵌套 row 漂移、非法 scalar、缺 artifact、path escape、absolute/rooted/drive/UNC refs、否定语境 parent refs、裸 CMD refs、CMD + missing evidence 混合行、provider subset、pass provider 缺 pane、Mobile/Config summary drift。
- 结果：上述反例均已补代码和负测；当前 artifact 仍保持 blocked candidate。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] REV-SUG-001 `test/test_windows_herdr_public_workflow_matrix.py` 可后续补 mixed/backslash traversal 负测，提升非 Windows CI 上的 path 语义显式性。当前 Windows 主机与现有 root-aware helper 已覆盖 escape、absolute、rooted、drive、UNC refs，本项不阻塞。

### learning

- Parent admission 不能只做关键词扫描；必须绑定 repo-root 内可验证 artifact 或可解析 command evidence file。
- Candidate matrix 的 `support_tier` 字段必须和 `support_tier_is_candidate`、`support_projection_allowed` 一起消费。

### praise

- Schema owner 集中在单模块，避免 docs/doctor/support projection 各自解释 evidence。
- 当前 artifact 明确是 blocked candidate，没有发布 final Native Windows support claim。

## 5. Test And QA Focus

- QA 必须重点复核：`validate_windows_herdr_public_workflow_artifacts()` 对当前 matrix artifact 返回 ok；`support_projection_allowed=false`；所有 workflow/provider rows 当前为 blocked。
- Evidence pack residual risks / gate warnings：当前 matrix 不是真实 Native Windows x64 full pass transcript；这是后续 supportability projection 的输入风险。
- 建议新增或加强的测试：none blocking；可选补 mixed/backslash traversal。
- 不能靠 review 完全确认的点：真实 Native Windows full workflow/provider pass transcript。

## 6. Residual Risk

- 当前 matrix 是 blocked candidate，不是真实全量 Native Windows pass transcript。
- 本轮外 dirty files 后续 commit 必须 scoped 排除。

## 7. Verdict

- Status: passed
- Next: Goal feature 进入 QA 阶段。

## 8. Focused Closure

- Closed findings: 多轮 subagent/OCR changes-requested findings 已在 implementation Round 1-14 记录并通过验证。
- Attributed delta: `lib/terminal_runtime/windows_herdr_public_workflow_matrix.py`、`test/test_windows_herdr_public_workflow_matrix.py`、feature implementation/gate artifacts。
- Targeted verification: `python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 68 passed；scope-gate passed；DoD runner passed；evidence-pack passed；OCR final closure 0 findings；final subagent rereview no blocking/important。
- Classification: 完整复审后 passed；非 focused-only 复用。
