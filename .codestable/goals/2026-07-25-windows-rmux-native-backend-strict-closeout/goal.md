---
doc_type: goal
goal: windows-rmux-native-backend-strict-closeout
status: active
---

# Windows Rmux Native Backend 严格收口 Goal

## Objective

根据整体核验报告严格完成 `windows-rmux-native-backend` 的 CodeStable 收口：修复 roadmap / goal-state / feature 报告状态漂移，补齐缺失验收产物和可解析证据，运行验证，并通过可见 Task agent 功能验收。

## Starting Point

核验报告已经确认主要实现与测试证据存在，但不能严格认定全部完成，原因集中在 CodeStable 产物层：

- `goal-state.yaml` 顶层仍为 `handoff`，`ccbd-windows-full-chain-smoke` 仍为 `pending`。
- roadmap 主文档 frontmatter 仍为 `active`，正文中仍有 `planned` 状态。
- `ccbd-windows-full-chain-smoke` 缺 review / QA / acceptance feature 报告。
- `windows-namespace-ipc-schema` 缺 feature acceptance 报告。
- full-chain smoke 功能验收引用的 PS5 / PS7 transcript 路径当前不存在，fresh parser 不能通过。

## Acceptance Criteria

- `windows-rmux-native-backend` 的 roadmap、items.yaml、goal-state.yaml 与 goal-features 状态一致，不再把已完成项标为 pending / planned / handoff。
- `ccbd-windows-full-chain-smoke` 缺失的 review、QA、acceptance feature 报告已补齐，且只引用当前存在并可解析的证据。
- `windows-namespace-ipc-schema` 缺失的 feature acceptance 报告已补齐，并与既有 goal functional acceptance、review、QA 一致。
- 最终报告引用的 native Windows rmux 证据均可由本仓库 parser fresh 验证，不引用不存在的 transcript 作为 pass 依据。
- YAML/frontmatter、相关 parser、scope guard 与 targeted pytest fresh 通过。
- `functional-acceptance.md` 记录可见 Task agent 对 strict closeout 的功能验收 `pass`。

## Non-Goals

- 不新增 Windows npm `supported` 发布入口；当前 packaging 结论仍为 `beta`。
- 不重跑真实外部 provider 凭证链路；`fake_provider` 证据只用于 backend/control-plane 链路。
- 不执行 `git commit`、`git push`、release 或 publish。
- 不扩大到 `windows-rmux-ux-parity-hardening` 后续 UX parity roadmap。

## Decisions And Assumptions

- 本 goal 是核验收口，不改变 Windows Rmux 后端公共契约。
- 对缺失 PS5 / PS7 transcript 不伪造 pass；只使用当前存在、可解析、语义覆盖 native Windows `ccb -> ccbd -> rmux` 链路的 canonical validation artifact。
- `rmux-packaging-docs-contracts` 已完成且结论为 `beta`，Windows npm 未启用不是本 goal blocker。

## Current State

Goal 已创建，下一步补齐缺失报告、状态回写和可解析证据。

## Next Action

补齐 feature 报告与 roadmap/goal-state 状态，然后运行 fresh validation。
