# 12：通用运行时生命周期下放 Herdr（Phase 4）

**What to build：** 把通用 workspace/pane 生命周期真正交给 Herdr：pane readiness、pane liveness、
通用 restart/backoff、workspace 清理迁移到 Herdr（若上游支持原生 `runtime.ensure` 则将兼容层
替换为原生调用）。CCB 只决定 Provider 是否允许恢复、是否 continuation、是否 job 失败或重试。
通用 pane 崩溃重启不得伪造 Provider session 已恢复。

**Blocked by：** 09（ensure_runtime 兼容层）、11（合并读模型）

**Status:** ready-for-agent

- [ ] pane readiness/liveness/通用 restart/backoff/workspace 清理由 Herdr 负责
- [ ] CCB 不再通过 shell/PowerShell/lifecycle 文件间接管理通用 pane 进程存活
- [ ] Provider session restore 仍由 CCB 的 Provider-specific contract 保护
- [ ] 通用 pane 崩溃重启不会伪造 Provider session 已恢复
- [ ] 如上游支持，则将 Phase 2 兼容层替换为原生 runtime.ensure/event 调用
