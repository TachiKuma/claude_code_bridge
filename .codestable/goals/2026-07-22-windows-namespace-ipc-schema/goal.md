---
doc_type: goal
goal: windows-namespace-ipc-schema
status: complete
---

# windows-namespace-ipc-schema

## Objective

继续 `windows-rmux-native-backend` epic 中的 `windows-namespace-ipc-schema`，把 ccbd 的 namespace state、ping/doctor payload 和 foreground attach 输入收敛到 mux-neutral canonical schema，同时保留旧 `tmux` alias 兼容。

## Starting Point

`mux-backend-contract` 与 `tmux-backend-contract-adapter` 已验收通过。当前 `ProjectNamespaceState` / `ProjectNamespaceEvent`、`build_ccbd_payload()`、`doctor_summary()` 和 `attach_started_project_namespace()` 仍主要依赖旧 `tmux_socket_path` / `tmux_session_name` 语义，canonical namespace schema 还没有在 state/event/payload/attach 输入上全链路铺开。

## Acceptance Criteria

- `ProjectNamespaceState` 和 `ProjectNamespaceEvent` 可读写 canonical namespace fields，并能从旧 tmux 记录恢复。
- canonical payload 可投影为完整 `MuxNamespaceRef`，并满足 `namespace_id == project_id`、`namespace_backend_family == "tmux-family"`。
- `ping('ccbd')`、doctor payload 和 render 同时输出 canonical 字段与 legacy alias，且顶层 `tmux_socket_path` 不被 namespace alias 覆盖。
- `attach_started_project_namespace()` 先读 canonical，再回退 legacy，attach 行为不变。
- 旧 fixture 与相关回归测试通过，feature/roadmap 状态完成回写。

## Non-Goals

- 不实现 `RmuxBackend` 或启动 `Rmux`。
- 不把 foreground attach 改成 `MuxBackend.attach_namespace()`。
- 不引入 named pipe 真连接、ACL、Job Object 或 process liveness 逻辑。
- 不修改 ccbd control-plane transport 或 provider session contract。
- 不执行 git commit、git push、merge、release、deploy 或生产变更。

## Decisions And Assumptions

- canonical-first，alias-fallback；旧记录必须能恢复，新记录必须继续兼容旧读者。
- `namespace_id` 固定以 `project_id` 作为身份，不引入 session-derived 变体。
- `namespace_backend_family` 固定为 `tmux-family`，`namespace_backend_impl` 对当前 tmux 路径保持 `tmux`。
- 本 feature 只改 schema 与 payload 读写，不改 attach 命令行为。

## Current State

当前代码已完成 canonical namespace schema、ping/doctor payload、foreground attach 输入与兼容回归，feature review/QA/acceptance 均已通过，roadmap item 已回写为 accepted/done。

## Next Action

见 `iterations/001.md` 与 `functional-acceptance.md`；后续工作切换到 `windows-shell-log-builder`。
