---
doc_type: feature-acceptance
feature: 2026-07-20-rmux-supervision-recovery
status: passed
updated_at: 2026-07-23
---

# rmux-supervision-recovery 验收

## Acceptance Checks

- `namespace_ref`、`pane_ref`、`process_ref`、`daemon_ref` 已进入 runtime authority 和 supervision evidence ledger。
- Rmux pane id 支持 backend-local id，例如 `pane-a`，不依赖 `%N`。
- Process/job death 与 pane death 分开建模；pane alive + process dead 不判 healthy。
- Namespace crash/missing/foreign 通过 backend-neutral namespace evidence 触发 reflow 或 hard diagnostics。
- Rmux daemon crash 使用 ownership evidence；shared daemon 不自动 kill/restart/refresh，owned/project daemon 才可 recover。
- `SupervisionEvent`、project view、ping、doctor 和 diagnostics bundle 展示 evidence ledger 与 recovery action。
- Scope guard 证明未修改 provider parser、backend resolver、namespace lifecycle、process liveness implementation 或 validation matrix scope。

## Task Agent Evidence

- 初次 code review：`codex-task-readonly-rmux-supervision-recovery-20260723`，verdict `changes_requested`，两个 blocking finding 已修复。
- 二次 code review：`codex-gpt5-readonly-secondary`，verdict `pass`。
- 初次 functional acceptance：`codestable-functional-acceptance-task-20260723-rmux-supervision-recovery`，verdict `fail`，指出 shared daemon degraded action 缺少 event evidence。
- 二次 functional acceptance：`task-agent-rmux-supervision-recovery-fa2-20260723`，verdict `pass`。
- 窄范围 diagnostics ledger acceptance：`codex-functional-acceptance-diagnostics-ledger`，verdict `pass`。

## Roadmap Writeback

- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 中 `rmux-supervision-recovery` 已从 `in-progress` 更新为 `done`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml` 中 `rmux-supervision-recovery` 已更新为 `accepted`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-features/rmux-supervision-recovery.md` 已更新为 `accepted`。

## Residual Risks

- 真实 Windows/Rmux destructive kill smoke 未在当前项目执行；其风险和多项目真机覆盖留给 `rmux-windows-validation-matrix`。当前 feature 的自动恢复语义已由 fake evidence 单元/集成测试和 Task agent 功能验收覆盖。

## Verdict

`passed`。本 feature 可视为 accepted。
