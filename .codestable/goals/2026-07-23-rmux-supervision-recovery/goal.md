---
doc_type: goal
goal: rmux-supervision-recovery
status: complete
---

# rmux-supervision-recovery

## Objective

将 Rmux pane、provider process/job、namespace 和 daemon health 纳入 ccbd supervision/recovery，并提供可诊断的恢复或降级路径。

## Starting Point

`ccbd-rmux-namespace-lifecycle` 已 accepted；`rmux-supervision-recovery` design / design-review / checklist 已存在并批准。当前 supervision 仍以 tmux socket 和 `%` pane id 为核心假设，process/job、namespace、daemon evidence 尚未形成统一 ledger。

## Acceptance Criteria

- runtime health 输入从 tmux-only socket/pane id 迁移到 backend-neutral `namespace_ref`、`pane_ref`、`process_ref`、`daemon_ref`。
- `pane-dead` / `pane-missing` / `pane-foreign` 判定支持 Rmux backend-local pane id，不要求 `%N`。
- provider process/job death 与 pane death 分开建模；pane alive + process dead 不得判 healthy。
- namespace crash 通过 backend-neutral namespace evidence 触发 reflow/remount 或 hard diagnostics。
- Rmux daemon crash 使用 daemon ownership evidence；shared daemon 不被误杀。
- `SupervisionEvent`、project view、doctor / diagnostics bundle 展示 pane/process/job/namespace/daemon evidence 和 recovery action。
- scope guard 证明不修改 provider parser、backend resolver、namespace lifecycle、process liveness implementation 或 validation matrix scope。
- 独立 Task agent code review passed，独立 Task agent 功能验收 passed，feature checklist/review/QA/acceptance/roadmap/final iteration 全部回写。

## Non-Goals

- 不实现 `ccbd-windows-process-liveness`。
- 不重新定义 provider completion parser 或 provider-specific health parser。
- 不实现 Rmux backend primitive、namespace lifecycle、send/capture/logging。
- 不改变 route approval、backend resolver、foreground attach 或 `ccb kill` ordering。
- 不承诺多 agent / 多项目 validation matrix。

## Current State

Goal 已完成。最终实现覆盖 evidence ledger、backend-neutral pane/namespace matching、process/job recovery split、namespace crash reflow、daemon ownership diagnostics/recovery、diagnostics projection 和 scope guard；功能验收见 `functional-acceptance.md`。

## Next Action

无需继续本 goal。真实 Windows/Rmux destructive kill smoke 留给 `rmux-windows-validation-matrix`。
