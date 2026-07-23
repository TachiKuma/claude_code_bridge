---
doc_type: feature-review
feature: 2026-07-20-rmux-supervision-recovery
status: passed
reviewer_id: codex-gpt5-readonly-secondary
updated_at: 2026-07-23
---

# rmux-supervision-recovery 代码审查

## Scope

审查当前 working tree 中 `rmux-supervision-recovery` 的实现 diff，范围包括 runtime authority evidence、supervision recovery、diagnostics projection、project view、doctor/ping/bundle 输出和新增测试。

## 初次审查结论

初次只读 Task agent `codex-task-readonly-rmux-supervision-recovery-20260723` 返回 `changes_requested`，发现两个 blocking 问题：

- shared / unowned daemon crash 没有写 degraded evidence event，导致 diagnostics bundle 无法反查 `degraded_only` action。
- `generation_approved` / `owner_approved` 可绕过 shared daemon scope，存在 shared daemon 被自动 recovery 的误杀风险。

本轮已修复：

- `recover_runtime()` 在 shared / unowned daemon health 下进入 `mark_daemon_degraded()`，只写 `daemon_degraded` 事件，不调用 provider refresh，不增加 `restart_count`。
- `daemon_recovery_allowed()` 只允许 `scope` / `ownership` 为 `project` 或 `owned`，不再用 `generation_approved` 放行 shared daemon。
- diagnostics bundle generated `supervision-ledger.json` 直接输出 `action`、`reason`、`ownership` 和 `evidence_ledger`。

## 复核结论

二次只读 Task agent `codex-gpt5-readonly-secondary` 返回 `pass`，无 blocking findings。

复核证据：

- focused Rmux supervision set：`16 passed`。
- diagnostics projection suite：`90 passed`。
- tmux / recovery regression：`31 passed`。
- checklist、goal-state、roadmap items YAML validate：passed。
- inline assertion：shared / unowned + `owner_approved` 仍不允许 daemon recovery。

## Residual Risks

- 未执行真实 Windows/Rmux destructive kill smoke；当前结论基于 fake evidence 单元/集成测试和 diagnostics bundle 证据。真实多项目/多 agent/真机 destructive smoke 留给 `rmux-windows-validation-matrix`。
- `git diff --check` 仅有 CRLF/LF normalization warning，无 whitespace error。

## Verdict

`passed`。无 unresolved blocking findings。
