# 12：通用运行时生命周期下放 Herdr（Phase 4）

**What to build：** 把通用 workspace/pane 生命周期真正交给 Herdr：pane readiness、pane liveness、
通用 restart/backoff、workspace 清理迁移到 Herdr（若上游支持原生 `runtime.ensure` 则将兼容层
替换为原生调用）。CCB 只决定 Provider 是否允许恢复、是否 continuation、是否 job 失败或重试。
通用 pane 崩溃重启不得伪造 Provider session 已恢复。

**Blocked by：** 09（ensure_runtime 兼容层）、11（合并读模型）

**Status:** partial-blocked

**Implementation:** `3b4f75b4`

**Evidence:** `lib/platforms/windows/herdr/runtime/manifest.py`、
`lib/platforms/windows/herdr/runtime/ensure.py`、`lib/cli/phase2_runtime/handlers_start.py`、
`test/test_herdr_runtime_contracts.py`

**Notes:** CCB 已改为声明 manifest 并通过兼容层收敛 runtime；真正把通用生命周期下放给 Herdr
仍依赖上游原生 `runtime.ensure/event/agent_id` 能力与 Windows live validation。

补充：`refresh_provider_binding` 现在会读取 Herdr `runtime_snapshot` 的 pane 归属，至少不再把目标 pane
缺失的情况盲目视为 healthy；缺 pane 时会降为 `pane-missing`。

**Split after architecture/code comparison（2026-08-24）：** 当前实现仍是 CCB 兼容层收敛 runtime：
`ensure_runtime(manifest)`、`refresh_provider_binding()` 和 `project_namespace_runtime` 仍承担大量通用
pane/workspace 生命周期判断。优化后目录具备 Herdr runtime contract 入口，优化前目录缺少这些模型。
真正下放必须按 Herdr 上游能力分三步推进：

- `12A-herdr-native-capability-contract.md`：先把上游 `runtime.ensure/event/agent_id` 能力探测和 fail-closed 分支固化。
- `12B-herdr-readiness-liveness-adapter.md`：把 readiness/liveness 从 CCB shell/pane 事实迁到 Herdr snapshot/事件事实。
- `12C-herdr-restart-backoff-cleanup-handoff.md`：把 restart/backoff/workspace cleanup 的通用决策权交给 Herdr。

- [ ] pane readiness/liveness/通用 restart/backoff/workspace 清理由 Herdr 负责（由 12B/12C 承接）
- [ ] CCB 不再通过 shell/PowerShell/lifecycle 文件间接管理通用 pane 进程存活（由 12B/12C 承接）
- [x] Provider session restore 仍由 CCB 的 Provider-specific contract 保护
- [x] 通用 pane 崩溃重启不会伪造 Provider session 已恢复
- [ ] 如上游支持，则将 Phase 2 兼容层替换为原生 runtime.ensure/event 调用（由 12A/12C 承接）
