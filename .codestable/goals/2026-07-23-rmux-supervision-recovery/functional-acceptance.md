---
doc_type: goal-functional-acceptance
goal: "rmux-supervision-recovery"
status: pass
reviewer_id: "task-agent-rmux-supervision-recovery-fa2-20260723; codex-functional-acceptance-diagnostics-ledger"
final_iteration: "iterations/002.md"
---

# rmux-supervision-recovery 功能验收

## Reviewer

- 主功能验收 Task agent：`task-agent-rmux-supervision-recovery-fa2-20260723`。
- 窄范围 diagnostics ledger 复核 Task agent：`codex-functional-acceptance-diagnostics-ledger`。
- Task agents 已消费结果并关闭；关闭未报告异常。

## Scope

按 owner acceptance criteria 验收当前 working tree 中 Rmux pane、provider process/job、namespace、daemon supervision/recovery 与 diagnostics projection。

## Acceptance Checks

- Pass：runtime health 输入已迁移到 backend-neutral `namespace_ref`、`pane_ref`、`process_ref`、`daemon_ref`。
- Pass：`pane-dead` / `pane-missing` / `pane-foreign` 支持 Rmux backend-local pane id，不要求 `%N`。
- Pass：provider process/job death 与 pane death 分开建模；pane alive + process dead 不判 healthy。
- Pass：namespace crash/missing/foreign 使用 backend-neutral namespace evidence 触发 reflow 或 hard diagnostics。
- Pass：Rmux daemon crash 使用 daemon ownership evidence；shared daemon 不被误杀，owned/project daemon 才走 recovery。
- Pass：`SupervisionEvent`、project view、ping、doctor 和 diagnostics bundle 展示 evidence ledger；generated `supervision-ledger.json` 直接包含 `action`、`reason`、`ownership` 和 daemon evidence。
- Pass：scope guard 未发现 provider parser、backend resolver、namespace lifecycle、process liveness implementation 或 validation matrix scope drift。

## Functional Evidence

- Focused rmux supervision 二次验收：`20 passed`。
- Aggregated supervision/diagnostics aliases：`38 passed`。
- Narrow diagnostics bundle acceptance：`10 passed`。
- 本地最终 DoD：goal 相关 `137 passed`，v2 regression `63 passed`，两个 YAML validate passed。
- Code review 二次复核：`codex-gpt5-readonly-secondary` verdict `pass`。

## Residual Risks

- 真实 Windows/Rmux destructive kill smoke 未在当前项目执行；后续由 `rmux-windows-validation-matrix` 在 disposable true-host 场景补足。
- Diagnostics bundle generated summary 只导出带 `evidence_ledger` 的 supervision events；无 ledger 的普通事件仍由 raw event source 提供。

## Delivery Record

- Final iteration：`iterations/002.md`。
- Feature reports：`rmux-supervision-recovery-review.md`、`rmux-supervision-recovery-qa.md`、`rmux-supervision-recovery-acceptance.md`。
- Verdict：`pass`。
