---
doc_type: approval-report
unit: .codestable/roadmap/windows-rmux-ux-parity-hardening
status: approved
reason: review-authorization
approvals:
  global-codestable-brainstorm-gate-tooling: approved
  roadmap-review: approved
  roadmap-plan: approved
approval_groups: {}
created_at: 2026-07-25
---

# Approval Report

## Decision History

- 2026-07-25：owner 在对话中回复“确认”，批准 `approval-report.md#global-codestable-brainstorm-gate-tooling`，授权修改本机全局 CodeStable workflow/tooling 以机械执行 per-item `$cs-brainstorm` design admission gate。
- 2026-07-25：owner 在 roadmap review passed 后回复“批准”，批准 `approval-report.md#roadmap-review` 与 `approval-report.md#roadmap-plan`，授权将 `windows-rmux-ux-parity-hardening` roadmap 从 `draft` 改为 `active` 并进入后续 child design batch；后续每个 pending child 仍必须先通过 `$cs-brainstorm` gate。

## Decision Needed

是否授权修改本机全局 CodeStable skill / runtime tooling，使 `windows-rmux-ux-parity-hardening` roadmap 新增的 per-item `$cs-brainstorm` design admission gate 能被自动流程机械执行。

命名授权：`approval-report.md#global-codestable-brainstorm-gate-tooling`

## Why Now

本 epic round 3 roadmap review 已变为 `changes-requested`。剩余 blocking RMR-001 指出：roadmap/items 已写入 `brainstorm_required`、`brainstorm_status`、`design_admission`，但全局 `workflow-next epic` 和 `cs-feat design` 协议尚未读取这些字段，因此 child design batch 仍可能绕过 owner 要求的 `$cs-brainstorm` gate。

## Context

需要修改的目标不在当前项目源码内，而在本机全局 CodeStable 安装位置，例如：

- `C:/Users/Administrator/.agents/skills/cs-onboard/tools/codestable-workflow-next.py`
- `C:/Users/Administrator/.agents/skills/cs-epic/SKILL.md`
- `C:/Users/Administrator/.agents/skills/cs-feat/references/design/protocol.md`

这类修改会影响本机后续所有使用这些 CodeStable skills 的项目，不只是当前 repository。

## Options

### Option A: 批准修改全局 CodeStable tooling（推荐）

修复 RMR-001：让 `workflow-next epic` 在 item `brainstorm_required: true` 且 `brainstorm_status != confirmed` 或 `design_admission != admitted` 时返回 recoverable gate，不再派发 `cs-feat design/design-review`；同时补充 `cs-epic` / `cs-feat design` 协议说明，防止手动入口绕过。

### Option B: 不批准全局 tooling 修改

保留当前项目内 roadmap/items/review 修订，但 epic 停在 `changes-requested`。后续每次推进 child design 都必须人工遵守 gate，自动流程不可信任为硬约束。

## Recommendation

选择 Option A。owner 的要求是“确保每一项子 feature 在 design 开始前使用 `$cs-brainstorm` 并明确批准/通过”；只改项目文档不能保证自动 child batch 不绕过，必须把规则落到 workflow gate。

## Risks And Tradeoffs

- 修改全局 skill/runtime 会影响本机所有 CodeStable 项目。
- 如果 workflow-next 对新增字段的兼容逻辑写得过窄，旧 roadmap 可能出现新的 blocked/user_gate 行为。
- 修复应保持向后兼容：只有 item 显式 `brainstorm_required: true` 时才启用 gate；缺字段的旧 roadmap 不应改变行为。

## Non-Automatic Actions

本授权不包含 git commit、push、merge、release、publish、deploy、npm 发布或生产环境操作。

## After You Answer

- 若 owner 明确回复“确认”或“继续”，则更新本报告的命名授权为 `approved`，再修改全局 CodeStable tooling，并重跑本 epic roadmap review。
- 若 owner 拒绝或不确认，则保持 roadmap review 为 `changes-requested`，不启动 child design batch。
