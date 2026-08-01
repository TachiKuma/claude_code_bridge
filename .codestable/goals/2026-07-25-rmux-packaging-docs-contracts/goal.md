---
doc_type: goal
goal: rmux-packaging-docs-contracts
status: active
---

# rmux-packaging-docs-contracts

## Objective

将 Windows Rmux 后端的安装、打包、诊断和文档契约收口为证据驱动的 `blocked` / `experimental` / `beta` / `supported` 支持档，并让 `package.json`、`install.ps1`、doctor / diagnostics bundle、README / docs、roadmap 状态保持一致。

## Starting Point

已有 feature 产物：

- `.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-design.md`
- `.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-design-review.md`
- `.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-checklist.yaml`
- `.codestable/roadmap/windows-rmux-native-backend/goal-features/rmux-packaging-docs-contracts.md`

design-review 已 `passed`。当前没有已存在的 goal 目录，本目录作为 goal driver 的持久起点。前置 `rmux-windows-validation-matrix` 仍是支持档输入，证据不足时必须 fail closed，不能通过文档单独宣布 `supported`。

## Acceptance Criteria

- support projection owner/classifier 绑定 route approval、capability gate、validation matrix 机器字段、local install smoke、可选 npm gate，并在证据不足时 fail closed。
- validation matrix 未满足 `selection_scope=full` + `full_matrix_status=pass` + true-host/manual core rows observed 前不得声明 `supported`；`support_tier` 枚举 `blocked` / `experimental` / `beta` / `supported` 被 doctor/docs/tests 统一消费。
- `install.ps1` rmux 行为明确为 `detect_only` / `warn` / `fail_fast`，默认不自动下载 rmux。
- npm `win32` gate 与 `package.json.os`、`artifactForHost` win32、artifact/checksum strategy、postinstall、package files/docs strategy、README 文案一致；未启用时有 no-change rationale。
- doctor / diagnostics bundle 输出 rmux support/version/capability/validation/install_entry/fallback 字段。
- README/docs/support contract 通过 parser/snapshot gate，无 beta/supported/experimental、入口映射、release note 未来承诺冲突。
- troubleshooting 覆盖 route/capability/rmux missing/provider auth/validation incomplete。
- release guard 证明没有发布、tag、push、npm publish、release upload。
- 核心 DoD 命令通过；独立 Task agent code review passed；独立 Task agent 功能验收 passed；feature review/QA/acceptance 和 roadmap item 回写完成。

## Non-Goals

- 不重新实现 Rmux backend、Windows validation matrix、ccbd transport、provider parser 或 supervision recovery。
- 不自动下载或安装 rmux。
- 不发布 npm、不 push、不 tag、不上传 release artifact。
- 不把 Windows Rmux 设为全平台默认 backend。
- 不把未完成 full validation 的路线描述为 `supported`。

## Decisions And Assumptions

- 本 goal 消费现有 feature design 的 owner 决策，不重新打开 design 范围。
- 默认 npm `win32` 不启用，除非仓库已有 gate 证据满足 design 中的硬条件；若不启用，必须记录 no-change rationale。
- 文档正文用中文；机器状态、schema、枚举、frontmatter 字段保持机读英文。
- 工作区已有与本 goal 无关的未跟踪/已修改文件；本 goal 不回滚这些改动。

## Current State

Goal active，尚未实施。`current_iteration=0`。

## Next Action

实现 support projection owner/classifier，并用测试锁定 fail-closed support tier 规则。
