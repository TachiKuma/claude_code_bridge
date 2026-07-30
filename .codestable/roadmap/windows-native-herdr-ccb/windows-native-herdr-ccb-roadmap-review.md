---
doc_type: roadmap-review
roadmap: windows-native-herdr-ccb
status: passed
review_state: passed
created: 2026-07-30
reviewer: 019fb3a9-e22f-7d23-83dd-88137f91832c
tags: [windows, native-windows, herdr, x64, roadmap-review]
---

# windows-native-herdr-ccb roadmap 审查报告

## 审查对象

- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Items: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Brainstorm: `.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`
- Feasibility: `.codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md`

## 结论

`review_state: passed`。

该 roadmap 适合 epic，不是 single feature / brainstorm。模块拆分和接口契约整体足够 deep，可作为后续 feature-design 的硬约束。Herdr / Native Windows x64 / `os=win32,cpu=x64` 口径一致。CCB authority 与 Herdr terminal primitive 边界清楚，双 authority 风险已被 provider completion、agent state、recovery owner contract 显式约束。

## Findings

### Blocking

none

### Important

- RMR-001：Goal Coverage Matrix 对 `watch` 的覆盖偏粗。
  - 处理：已补 `watch` 独立覆盖行，要求由 `provider-runtime-on-herdr`、`herdr-user-surfaces-parity`、`native-windows-public-workflow-validation-matrix` 共同覆盖，并以 Native Windows x64 watch transcript / streaming evidence 验证。

- RMR-002：`windows-x64-v852-baseline-gate` 与 `windows-x64-release-surface` 的 install/update/doctor/package gate 边界有轻微重叠。
  - 处理：已明确 baseline gate 只产出 platform gate contract、版本/位宽探测和 startup/doctor 基础诊断；release surface 只消费该 gate 做 npm metadata、install/update、native helper packaging、release-surface projection 和 support 文档。

- RMR-003：最小 spike 相比 feasibility input 少写 `kill_pane` / provider CLI dry run。
  - 处理：已把 spike 范围扩展为 session/pane/send/capture/kill/restore 和 provider CLI dry-run pane；仍不要求完整 provider parity。

### Nit

- RMR-004：`WindowsHerdrPublicWorkflowEvidence.workflows` 是自由 dict。
  - 处理：已增加 `required_workflows` 最低 key set，包含 `ccb`、`ask`、`pend`、`watch`、`ping`、`mounted`、`kill`、`restart`、`reload`、`foreground_attach`、`mobile_terminal`、`config_ui`、`doctor_update`、`support_projection`。后续 feature-design 可继续将 `workflows` 收紧为枚举 key。

## 机械检查

- items 数量：11
- `minimal_loop: true`：恰好一条，`herdr-backend-contract-spike`
- 依赖检查：无未知依赖
- DAG 检查：无循环
- YAML 校验：roadmap frontmatter 通过，items YAML 通过

## Residual Risk

- Herdr 版本与 socket API schema 尚未锁定，正式 implementation 前仍需要 spike 证据。
- 当前工作区 `package.json` 显示 `8.2.1`，实现前必须选择 `v8.5.2` tag 或同步等价基线。
- Native Windows x64 真机证据不可由 WSL/Linux 替代。
