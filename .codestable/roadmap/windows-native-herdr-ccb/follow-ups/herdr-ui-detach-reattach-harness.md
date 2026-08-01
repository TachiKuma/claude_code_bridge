---
doc_type: follow-up
slug: herdr-ui-detach-reattach-harness
status: pending
created: 2026-08-01
source_feature: 2026-07-31-herdr-backend-contract-spike
---

# herdr-ui-detach-reattach-harness

## 背景

Restore Capability Matrix v2 已证明 Herdr dedicated server restart 可以恢复 workspace/pane identity，但不能证明旧 pane process continuity，也不能恢复 sentinel output history。当前普通 CLI harness 不在 Herdr UI client 内，`HERDR_ENV`、`HERDR_PANE_ID`、`HERDR_SESSION` 均不可用，因此不能安全验证真实 UI detach/reattach。

## 后续验证目标

- 从真实 Herdr UI client pane 内运行 harness，要求 `HERDR_ENV=1` 且存在当前 pane/session context。
- 使用 dedicated test session，不控制或停止用户默认 Herdr session。
- 验证 UI client detach 后再 reattach 时，workspace/pane identity、pane process identity、sentinel output 可见性分别是什么状态。
- 将结论写回 `herdr-contract-spike-evidence.json` 或后续 validation matrix，不能用 server restart 结果替代 UI detach/reattach。

## 验收信号

- harness 记录 `HERDR_ENV=1`、caller pane id、session id 和 dedicated target session。
- detach/reattach 操作有 Herdr UI client transcript 或等价可审计 artifact。
- process continuity 使用 `pane process-info --pane <id>` 前后 pid 证明。
- output 可见性使用 `pane read --source recent-unwrapped` 与 sentinel marker 证明。
- 若 Herdr UI client 无法自动化，产出 `needs-upstream-test-hook` 或 manual runbook，不阻塞 layout-only adapter work。
