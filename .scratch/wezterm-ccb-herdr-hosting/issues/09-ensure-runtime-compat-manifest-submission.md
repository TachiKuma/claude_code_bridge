# 09：ensure_runtime(manifest) 兼容层 + start/herdr-open 改提交 manifest（Phase 2）

**What to build：** 在 CCB 内实现 `ensure_runtime(manifest, restore_token)` 兼容层——内部仍可调用
既有 create/ensure/pane 操作，但对外只暴露「声明拓扑、收敛 runtime」的语义。`handle_start` 与
`handle_herdr_open` 改为提交 manifest，不再直接触发运行时证据注入。bootstrap 降级为兼容层：
只解析 Herdr 可执行文件与启动初始 server，capability 证据来自握手/binding，不再写临时 capability
文件。

**Blocked by：** 08（manifest 模型）、06（握手对象）

**Status:** ready-for-agent

- [ ] `ensure_runtime(manifest, restore_token)` 兼容层落地，内部复用既有操作
- [ ] `handle_start`/`handle_herdr_open` 改为提交 manifest
- [ ] bootstrap 不再写临时 capability 文件；capability 来自握手/binding
- [ ] 启动/restore/attach/teardown 的持久 namespace 状态仍兼容旧字段
- [ ] `ccb herdr open --wait-ready` 语义仍能等到 ccbd mounted
