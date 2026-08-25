# 12：通用运行时生命周期职责收束（Phase 4）

**What to build：** 按 ADR 0002 收束通用 workspace/pane 生命周期职责：pane readiness/liveness 可消费
Herdr runtime fact；agent 身份与 restart/backoff 策略恒属 CCB，不再等待 Herdr 接管。CCB 决定
Provider 是否允许恢复、是否 continuation、是否 job 失败或重试。
通用 pane 崩溃重启不得伪造 Provider session 已恢复。

**Blocked by：** 09（ensure_runtime CCB 收敛职责）、11（合并读模型）

**Status:** partial-blocked

**Implementation:** `3b4f75b4`

**Evidence:** `lib/platforms/windows/herdr/runtime/manifest.py`、
`lib/platforms/windows/herdr/runtime/ensure.py`、`lib/cli/phase2_runtime/handlers_start.py`、
`test/test_herdr_runtime_contracts.py`

**Notes:** CCB 已改为声明 manifest 并通过 `ensure_runtime(manifest)` 收敛 runtime；ADR 0002 已判定
agent 身份与 restart/backoff 策略不下放 Herdr。

补充：`refresh_provider_binding` 现在会读取 Herdr `runtime_snapshot` 的 pane 归属，至少不再把目标 pane
缺失的情况盲目视为 healthy；缺 pane 时会降为 `pane-missing`。

**Split after architecture/code comparison（2026-08-24）：** 当前实现仍是 CCB 收敛 runtime：
`ensure_runtime(manifest)`、`refresh_provider_binding()` 和 `project_namespace_runtime` 仍承担大量通用
pane/workspace 生命周期判断。优化后目录具备 Herdr runtime contract 入口，优化前目录缺少这些模型。
ADR 0002 修正了原下放假设，后续只保留可观测事实消费与 CCB 权威边界：

- `12A-herdr-native-capability-contract.md`：保留 runtime fact 能力探测和 fail-closed 分支。
- `12B-herdr-readiness-liveness-adapter.md`：把 readiness/liveness 从 CCB shell/pane 事实迁到 Herdr snapshot/事件事实。
- `12C-herdr-restart-backoff-cleanup-handoff.md`：经源码验证判为 `wontfix`，不再等待 Herdr 接管 restart/backoff。

- [ ] pane readiness/liveness/通用 restart/backoff/workspace 清理由 Herdr 负责（由 12B/12C 承接）
- [ ] CCB 不再通过 shell/PowerShell/lifecycle 文件间接管理通用 pane 进程存活（由 12B/12C 承接）
- [x] Provider session restore 仍由 CCB 的 Provider-specific contract 保护
- [x] 通用 pane 崩溃重启不会伪造 Provider session 已恢复
- [x] ADR 0002 已明确不再等待 Herdr 原生 ensure 接管 CCB 收敛职责
