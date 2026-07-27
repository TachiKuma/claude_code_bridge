---
doc_type: approval-report
unit: .codestable/features/2026-07-25-windows-rmux-supportability-parity-contract
status: approved
reason: interview
approvals:
  design-admission: approved
approval_groups: {}
created_at: 2026-07-25
---

# Approval Report

## Decision History

- 2026-07-27：owner 回复“批准”，批准 `approval-report.md#design-admission`，授权 `windows-rmux-supportability-parity-contract` 按 UX parity overlay first 的 brainstorm 结论进入 feature design。

## Decision Needed

是否批准 `windows-rmux-supportability-parity-contract` 按本次 brainstorm 收敛方向进入 feature design。

命名授权：`approval-report.md#design-admission`

## Why Now

`windows-rmux-ux-parity-hardening` epic 的 child batch 当前停在该 item 的 per-item `$cs-brainstorm` gate。只有 owner 明确批准本 item 的 brainstorm 结论并允许进入 design 后，才能把 roadmap item 更新为 `brainstorm_status: confirmed` / `design_admission: admitted`，并由 `cs-feat` 起草 design。

## Context

已选定方向：

- 主轴：UX parity overlay first。
- support tier 规则：只能消费 base support projection 与 5 个上游 child 的 `evidence/windows-rmux-ux-parity-evidence.json`，并由本 item 生成第 6 维 `supportability` evidence；不能绕过 base projection 升级。
- 缺失 core dimension 时投影为 `missing`，不得用 Markdown 摘要或人工印象替代。

设计应复用 `rmux-packaging-docs-contracts` 的 base support projection、doctor/install/docs/npm gate 结果，不重复定义 `install.ps1`、npm win32、release guard 或发布策略。

## Options

### Option A: 批准进入 design（推荐）

把本 item 设计为 UX parity overlay：读取 base projection 和 5 个上游 UX parity evidence JSON，生成 supportability projection、doctor/diagnostics/docs consistency 表达，并输出本 item 的第 6 维 supportability evidence；support tier 上 fail closed。

### Option B: 继续 brainstorm

暂不进入 design，继续讨论 support tier 算法、doctor 展示范围、docs 更新边界或 base projection owner。

### Option C: 重新定义 packaging/install 支持契约

推翻当前边界，把 npm、`install.ps1`、release guard 和 support tier base rules 都放进本 item 重做。该选项会和 `rmux-packaging-docs-contracts` 形成双 owner，风险较高。

## Recommendation

选择 Option A。现有代码已经有 `rmux_packaging_support_summary()`、doctor render、diagnostic bundle 和 docs consistency gate；本 item 的增量应是 UX parity overlay 和一致表达，而不是发布/安装规则重写。

## Risks And Tradeoffs

- 任一 UX core dimension `failed|blocked|missing` 时不得宣称 `supported`。
- `partial` 可以允许 `beta`，但 doctor/docs 必须列 residual risks。
- 如果 base projection 低于 UX overlay 推导结果，最终 support tier 以更保守者为准。
- npm win32 和 `install.ps1` gate 仍由 `rmux-packaging-docs-contracts` 决定；本批准不含发布授权。

## Non-Automatic Actions

本批准不包含 git commit、push、merge、release、publish、deploy、npm 发布、修改生产环境、远端操作或跳过后续 epic 统一 design 确认。

## After You Answer

- 若 owner 明确回复“批准”“确认”或“继续”，则记录 `approval-report.md#design-admission: approved`，落盘 confirmed feature brainstorm，更新 roadmap items.yaml 的该 item admission 字段，然后在当前 run 继续加载 `cs-feat` design。
- 若 owner 选择继续讨论，则保持 pending，不更新 roadmap item。
- 若 owner 改选 packaging/install rewrite，则更新 brainstorm 方向后重新请求 design admission。
