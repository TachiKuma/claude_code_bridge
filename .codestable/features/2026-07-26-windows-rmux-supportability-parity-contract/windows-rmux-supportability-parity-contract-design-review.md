---
doc_type: feature-design-review
feature: 2026-07-26-windows-rmux-supportability-parity-contract
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f9e64-cce3-7822-82ff-46b04a69d096"
reviewed: 2026-07-26
round: 2
---

# windows-rmux-supportability-parity-contract feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-design.md`
- Checklist: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-26-windows-rmux-supportability-parity-contract/windows-rmux-supportability-parity-contract-brainstorm.md`
- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Related docs: `rmux-packaging-docs-contracts` design / acceptance / QA / review, roadmap §4.1 / §4.7.
- Code facts checked: `lib/terminal_runtime/rmux_packaging_support.py`, `lib/terminal_runtime/rmux_packaging_support_projection.json`, `lib/cli/services/doctor.py`, `lib/cli/render_runtime/ops_views_doctor.py`, base packaging tests.

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019f9e58-13d0-73b1-8553-0ee0970848cc`; round 2 `019f9e64-cce3-7822-82ff-46b04a69d096`
- Raw output: round 1 reported one blocking, two important, one nit；round 2 reported no blocking/important and confirmed closure。
- Merge policy: 已逐条核验 reviewer finding，并用 design / checklist / roadmap / code facts 确认成立项和 closure。
- Gate effect: independent review completed，允许本地合并为 passed。

## 2. Design Summary

- Goal: 聚合前 5 个 Windows/rmux UX parity dimensions 与 base packaging projection，生成 fail-closed supportability overlay。
- Key contracts: `windows-rmux-ux-support-projection.json` 使用 canonical `support_tier`；`windows-rmux-ux-parity-evidence.json` 固定 `parity_dimension=supportability`；doctor/bundle seam 固定为 `rmux_supportability`。
- Steps: 7 步，风险热点是 upstream evidence missing、base tier cap、Windows npm disabled、doctor/docs visible consistency 和 scope guard。
- Checks: 11 条，覆盖 5 upstream input、roadmap DAG、canonical `support_tier`、missing/partial/blocked/failure、base tier cap、install entry、doctor seam 和 forbidden owner changes。
- Baseline / validation: 复用 `rmux-packaging-docs-contracts` accepted base projection 和现有 packaging/docs/doctor tests；新增 `test/test_windows_rmux_supportability_parity_contract.py` 作为 UX overlay validator 入口。

## 3. Findings

### blocking

- [x] FDR-001 `WindowsRmuxUxSupportProjection` 字段偏离 roadmap §4.7 canonical contract。
  - Evidence: round 1 design 只定义 `base_support_tier` / `ux_overlay_tier` / `effective_support_tier`，但 roadmap §4.7 的对外字段是 `support_tier`。
  - Impact: doctor/docs/acceptance 可能读取不同“支持档”语义，导致 supported/beta 口径分叉。
  - Expected fix scope: 保留 `support_tier` 作为唯一对外支持档字段，其他 tier 字段仅作解释性 detail。
  - Closure: design §1 / §2.1 已规定 canonical `support_tier` 是 roadmap §4.7、doctor、diagnostics、docs consistency 和 acceptance 唯一读取字段；checklist 已加入硬检查。round 2 reviewer confirmed no blocking。

### important

- [x] FDR-002 roadmap/items 的依赖图和设计输入集不一致。
  - Evidence: design 要读取 5 个 upstream UX dimensions，包含 `foreground_interaction`；round 1 items.yaml supportability `depends_on` 只有 4 项。
  - Impact: epic 调度会把 supportability 当成四依赖收口，和设计的五输入 fail-closed 不一致。
  - Closure: items.yaml 已把 `windows-rmux-wezterm-native-interaction-parity` 加入 supportability `depends_on`；checklist 增加 roadmap DAG 检查。round 2 reviewer confirmed。

- [x] FDR-003 doctor/docs consumer seam 未钉死。
  - Evidence: 当前代码只有 `rmux_packaging_support` payload/render；round 1 design 没指定 UX overlay 接入 key、adapter 和 real-path snapshot。
  - Impact: 实现可能只生成 synthetic projection，doctor/docs 仍显示旧状态或自行推导。
  - Closure: design §2.2 / §2.3 / §2.4 指定 `doctor_summary()` payload key 为 `rmux_supportability`，`render_doctor()` 和 diagnostics bundle 必须展示/保留该 seam；CMD-003/CMD-005 和 checklist 已覆盖 real-path seam。round 2 reviewer confirmed。

### nit

- [x] FDR-004 `install_entry` 在 `blocked/experimental` 时映射未写死。
  - Closure: design §2.1 新增 Install entry rule：`blocked|experimental` 固定 `diagnostic_only`，Windows npm disabled 时不得为 `npm`；checklist 已同步。

- [x] FDR-005 brainstorm 中一处“6 个 parity feature 的 evidence JSON”表述有歧义。
  - Closure: brainstorm 已改为读取前 5 个 upstream parity feature evidence，并输出第 6 个 supportability evidence。

### suggestion

- 实现阶段建议保留迁移期兼容测试：当前代码仍暴露 `rmux_packaging_support`，新增 `rmux_supportability` 时应验证不会让 doctor/render 新旧 payload 分叉。

### learning

- base packaging/docs contract 已 accepted，且已把 npm/install/release guard owner 固定在 `rmux-packaging-docs-contracts`；supportability overlay 不能重复拥有这些 gate。
- 收口类 feature 应保持 `support_tier` 单一对外字段，解释性字段可以存在，但不能成为下游读取入口。

### praise

- 设计明确避免循环依赖：输入只有前 5 个 upstream UX dimensions，supportability 自己的 evidence 是输出。
- fail-closed 规则清晰：missing/partial/blocked/failed 都有可测试 tier 映射，base beta 会封顶最终 support tier。

## 4. User Review Focus

- 用户需要重点拍板：接受 base packaging tier 仍是上限；即使 UX upstream 全 pass，只要 base projection 仍 beta，canonical `support_tier` 也不能 supported。
- implement 需要重点遵守：新增 `rmux_supportability` doctor/bundle seam，但不得复制 tier rule 到 render/docs；render 只消费 projection。
- code review / QA / acceptance 需要重点复核：上游缺 evidence JSON 时必须 missing；Windows npm disabled 时不能推荐 npm；release/npm/install owner 不得被本 feature越界修改。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-001 到 AC-009 覆盖 base projection、missing/partial/blocked/pass/base cap/npm disabled/doctor seam/scope guard | none |
| DoD Contract | pass | E | DOD-IMPL-001 到 DOD-IMPL-007 与 CMD-003/CMD-004/CMD-005 已覆盖核心 evidence 和 seam | none |
| Steps and checks traceability | pass | E | checklist steps/checks 已映射 design §2.4、§3.1、§3.4；YAML validate passed | none |
| Roadmap contract compliance | pass | E/C | design 对齐 roadmap §4.1/§4.7；items.yaml 依赖图已补 5 upstream | none |
| Module interface design | pass | C | base owner 保留；UX overlay seam 固定在 feature-local builder 和 `rmux_supportability` doctor/bundle key | implementation 做真实 adapter |
| Validation and artifacts | pass | E/C | 新增测试入口是计划文件；base packaging tests 当前存在 | implementation 创建 CMD-003/CMD-005 入口 |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- `scripts/windows_rmux_supportability_projection.py` 和 `test/test_windows_rmux_supportability_parity_contract.py` 仍是计划新增入口；implementation 必须真实创建并覆盖 schema、tier rule、cycle guard、doctor/render seam。
- 当前生产代码仍只有 `rmux_packaging_support` seam；新增 `rmux_supportability` 时要用 real-path snapshot 验证 doctor summary、render 和 diagnostics bundle 不分叉。
- 前 5 个 upstream UX evidence 可能在 implementation 时尚未 accepted；本 feature必须如实输出 missing/partial，而不是为了完成 epic 提高 support tier。

## 7. Verdict

- Status: passed
- Next: epic child batch 可返回 `cs-epic`；所有 child design-review 已 passed 时进入统一 design confirmation checkpoint。

## 8. Focused Closure

- Closed findings: FDR-001, FDR-002, FDR-003, FDR-004, FDR-005
- Attributed delta: design/checklist/items.yaml/brainstorm 中的 canonical `support_tier`、5 upstream DAG、`rmux_supportability` seam、install entry rule 和 5/6 evidence input wording。
- Verification: checklist YAML validate passed；design frontmatter validate passed；roadmap items YAML validate passed；round 2 independent reviewer reported no blocking/important。
- Classification: FDR-001 到 FDR-004 的修订改变 public contract / roadmap DAG / consumer seam，已通过第二轮完整独立复审；FDR-005 是非契约措辞修正。
