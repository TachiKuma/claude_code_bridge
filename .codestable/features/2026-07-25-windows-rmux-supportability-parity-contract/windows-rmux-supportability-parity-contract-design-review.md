---
doc_type: feature-design-review
feature: 2026-07-25-windows-rmux-supportability-parity-contract
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fa11e-e25d-7570-a5e2-eaaeacb7f1b2;019fa125-56dd-7d23-b1d7-b8e703d8c13b"
reviewed: 2026-07-27
round: 2
---

# windows-rmux-supportability-parity-contract feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-25-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-brainstorm.md`
- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Related docs: `.codestable/features/2026-07-25-windows-rmux-supportability-parity-contract/approval-report.md`
- Code facts checked: `lib/terminal_runtime/rmux_packaging_support.py`, `lib/terminal_runtime/rmux_packaging_support_projection.json`, `lib/cli/services/doctor.py`, `lib/cli/render_runtime/ops_views_doctor.py`, `test/test_rmux_packaging_docs_contracts.py`, `test/test_cli_doctor_rmux_packaging.py`, `test/test_doctor_rmux_packaging_summary.py`, `test/test_ccbd_diagnostics_bundle_rmux.py`, `test/test_rmux_docs_consistency_gate.py`, `test/test_install_windows_rmux_contract.py`, `test/test_rmux_packaging_release_guard.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fa11e-e25d-7570-a5e2-eaaeacb7f1b2`；round 2 `019fa125-56dd-7d23-b1d7-b8e703d8c13b`
- Raw output: round 1 reported 3 important、1 nit、1 suggestion；round 2 reported no blocking，1 important in brainstorm/approval stale wording，1 suggestion for failure_class precedence。
- Merge policy: 已逐条核验并合并成立 finding；round 2 后本地修订 admission 文档旧口径，并补最终 evidence `failure_class` precedence table。
- Gate effect: independent review completed，允许本地合并为 passed。

## 2. Design Summary

- Goal: 在 `rmux-packaging-docs-contracts` base support projection 上增加 UX parity overlay，统一 doctor、diagnostics、docs 和 support tier 表达。
- Key contracts: 5 个 upstream dimensions 输入，本 feature 输出第 6 维 `supportability` evidence；`missing_evidence` 只在私有 report，最终 roadmap §4.1 evidence 映射为合法 failure_class。
- Steps: 7 步，覆盖 base boundary、dimension loader、overlay classifier、base cap merge、doctor/diagnostics、docs consistency、supportability evidence/scope guard。
- Checks: 12 条，覆盖 brainstorm admission、5+1 evidence 边界、missing projection、tier cap、doctor/bundle/docs、final evidence、package/install/release guard。
- Baseline / validation: 复用现有 base support projection、doctor render、diagnostic bundle、docs/install/release guard tests，并新增 `test/test_windows_rmux_supportability_parity.py`。

## 3. Findings

### blocking

none

### important

- [x] FDR-001 `.codestable/features/2026-07-25-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-design.md#2.1` `missing_evidence` 是私有投影值，但最终 UX evidence failure_class 映射不够封闭。
  - Evidence: roadmap §4.1 不包含 `missing_evidence`；round 1 design 同时允许私有 projection 使用 `missing_evidence`，又要求最终 `windows-rmux-ux-parity-evidence.json` 符合 §4.1。
  - Impact: implementation 可能把私有 loader 状态泄漏到公共 evidence schema。
  - Expected fix scope: 明确 `missing_evidence` 只存在于 `supportability-parity-report.json`，最终 §4.1 evidence 映射为合法 `test_design_failure`。
  - Closure: design §2.1 已新增私有/公开映射规则和 final evidence `failure_class` precedence；checklist 增加对应 check；round 2 确认主设计边界正确。

- [x] FDR-002 `.codestable/features/2026-07-25-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-design.md#0` “5 upstream + self” 与 “6 dimensions” 混用，可能制造自消费循环。
  - Evidence: round 1 design 已部分改为 5 upstream，但术语表和 projection 类型仍可能把 `supportability` 当 loader 输入。
  - Impact: implementation 可能先读本 feature 尚未生成的 self evidence，导致循环依赖或缺失误判。
  - Expected fix scope: 统一 `upstream_dimensions=5`，`epic_dimensions=6 including supportability self evidence`；report details 只含 upstream rows，self evidence 走独立字段。
  - Closure: design §0/§2.1/§2.2、checklist 和 roadmap item 已统一为 5 upstream + self evidence；round 2 未发现主设计残留自消费。

- [x] FDR-003 `.codestable/features/2026-07-25-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-design.md#3.1` scope guard 的可执行边界不够具体。
  - Evidence: round 1 design 要求不改 npm/install/release owner，但没有列出 release/tag/publish guard 的机器断言来源。
  - Impact: acceptance 可能只能靠口头 diff review 判断 release guard，无法稳定复核。
  - Expected fix scope: 补 package/install/release guard assertions。
  - Closure: design §2.2、AC-010、DOD-IMPL-007 和 CMD-005 已纳入 `package.json.os` 不新增 `win32`、scripts 不新增 `publish|release|tag`、`install.ps1` rmux owner rules、`test/test_rmux_packaging_release_guard.py`。

- [x] FDR-004 `.codestable/features/2026-07-25-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-brainstorm.md` / `approval-report.md` admission 记录仍残留“6 个输入 evidence”旧口径。
  - Evidence: round 2 reviewer 指出 brainstorm summary/正文和 approval context/options 仍写读取 6 个 UX evidence。
  - Impact: implementation/QA 回读 admission evidence 时可能重新引入 self evidence 作为 loader 输入。
  - Expected fix scope: 只修 admission 文档旧表述，不改 design 主契约。
  - Closure: brainstorm 和 approval-report 已改为“读取 5 个上游 UX evidence，生成第 6 维 supportability self evidence”；精确搜索旧 6-input 口径无命中。

### nit

- [ ] FDR-005 `CMD-006` 使用 `<本 feature 实际触碰的 Python modules>` 占位符。
  - Evidence: design/checklist 在设计阶段无法预知 implementation 最终 Python module 列表。
  - Impact: 不阻塞 design；implementation 必须展开为真实模块列表后执行。

### suggestion

- [x] FDR-006 `failure_class` precedence 建议显式化。
  - Evidence: round 2 reviewer 建议列出 base/upstream failure 并存时的 final §4.1 mapping。
  - Closure: design §2.1 已新增最终 evidence `failure_class` precedence table。

### learning

- 现有 base boundary 清晰：`doctor_summary()` 注入 `rmux_packaging_support_summary()`，`render_doctor()` 渲染 payload 字段，diagnostics bundle 保存 doctor JSON。overlay 应保持同样模式，不让 doctor/render 层读取 evidence 文件。
- `missing_evidence` 作为私有 loader 状态是有价值的，但必须在公共 roadmap evidence 出口映射回合法 enum。

### praise

- design 明确把 base packaging/install/npm/release owner 与 UX overlay 分开，避免双 owner。
- steps 原子性较好，loader、classifier、base cap、doctor/diagnostics、docs、self evidence/scope guard 分离。

## 4. User Review Focus

- 用户需要重点拍板：supportability 只读 5 个上游 UX evidence，本 feature 输出第 6 维 self evidence；缺失上游 evidence 不阻塞 design，但实现/验收必须 fail closed。
- implement 需要重点遵守：base projection 是 support tier 上限；doctor/docs/diagnostics 只渲染同一 projection，不各自重算。
- code review / QA / acceptance 需要重点复核：`missing_evidence` 不得出现在最终 §4.1 evidence；package/install/release guard 必须有机器断言。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-001 到 AC-010 覆盖 base cap、missing/blocked/partial、doctor、diagnostics、docs、supportability evidence 和 scope guard | none |
| DoD Contract | pass | E | DOD-IMPL-001 到 DOD-IMPL-007 覆盖 report、missing projection、tier cap、doctor/bundle/docs、final evidence 和 guard | none |
| Steps and checks traceability | pass | E | checklist S1-S7 与 12 条 checks 可追溯到 design §2/§3 | none |
| Roadmap contract compliance | pass | E/C | design 遵守 roadmap §4.1 和 §4.7；supportability self evidence 固定 `parity_dimension=supportability` | none |
| Module interface design | pass | C | overlay loader/classifier 与 base projection 分层；doctor/docs/diagnostics 只消费 projection | implementation 保持 base/overlay owner 分离 |
| Validation and artifacts | pass | E/C | CMD-003 到 CMD-005 覆盖新 overlay test、base support、doctor、diagnostics、docs、install、release guard | implementation 创建真实 tests/artifacts |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- 上游 5 个 child evidence 当前尚未实现/accepted；implementation 和 QA 必须把缺失投影为 `missing`，不能用 design-review passed 或 Markdown 摘要替代。
- `test/test_windows_rmux_supportability_parity.py` 是待实现测试；本 design-review 只确认其契约覆盖，不代表代码已存在。

## 7. Verdict

- Status: passed
- Next: epic child batch 可返回 `cs-epic`，进入所有 child feature design 的统一确认 gate。

## 8. Focused Closure

- Closed findings: FDR-001, FDR-002, FDR-003, FDR-004, FDR-006
- Attributed delta: design/checklist 的 5 upstream + self evidence 契约、`missing_evidence` 私有/公开映射、Tier merge table、package/install/release scope guard、brainstorm/approval 旧 6-input 口径修正。
- Verification: checklist YAML validate passed；items YAML validate passed；round 2 independent reviewer reported no blocking；旧 6-input 口径精确搜索无命中。
- Classification: FDR-001 到 FDR-003 改变 evidence/roadmap contract，已通过第二轮完整独立复审；FDR-004 是 admission 文档一致性修订；FDR-006 是非阻塞实现歧义收口。最终 verdict 为 passed。
