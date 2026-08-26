# 失败与根因

执行时间：2026-08-26 17:39-18:05 +08:00

## 历史启动 blocker

旧 blocker：

```text
mux backend capability unsupported for create_session
```

当前复测结论：**未复现**。

根因定位：

1. `lib/platforms/windows/herdr/bootstrap.py` 旧实现会在 bootstrap 成功后清掉 `CCB_HERDR_CAPABILITY_REPORT`。
2. 没有 capability report 时，Herdr backend 的兼容层只能回退到旧的核心能力集合。
3. `create_session` 需要 `session_attach`、`workspace_create`、`workspace_metadata`、`pane_metadata`。
4. 旧兼容集合只覆盖核心项，导致 `create_session` 被 gate 判成不支持。

对应修复提交：

- `45b213c0 fix: preserve herdr capability report for native runtime`

本轮现状：

- `ccb.cmd` 从外部 smoke 目录启动成功；
- `doctor ps` 可见两个 agent 已绑定并处于 `idle/alive`；
- `kill` 可正常收敛。

## 其他当前阻塞

`win_claude` 的 ask 未完成，是因为 Claude Code 停在登录选择界面，需要 OAuth 登录前置条件，不属于 CCB 启动根因。

`ccb.cmd --diagnose` 仍返回：

```text
command_status: invalid
error: invalid start command
```

退出码为 2。该项属于 CLI 兼容入口差异，不属于本轮 `ccb.cmd` 启动失败根因。

## 说明

`fb797383` 解决的是 Windows 后台守护进程的 venv 重定向器和 PID 栅栏问题，是另一条历史修复线，不是本轮 `create_session` blocker 的直接根因。

## MewUI 前台 UI 不显示

用户在 `E:\GitHub开源项目\TachiKuma\MewUI` 运行：

```powershell
E:\GitHub开源项目\TachiKuma\NativeWin_CCB_Herdr\ccb.cmd
```

现象是 PowerShell 提示符返回，但没有出现 Herdr UI。

本轮新增根因结论：

1. 本机没有 `wezterm` 在 PATH 中，CCB 进入 `fallback_reason=wezterm_cli_unavailable` 的裸 Herdr fallback。
2. fallback 路径把 `herdr session attach <session>` 用 `CREATE_NO_WINDOW` 启动，并把 stdout/stderr 重定向到 `DEVNULL`，导致 TUI 被隐藏。
3. manifest 层还允许复用不匹配当前项目的 `CCB_HERDR_SESSION` / `CCB_HERDR_SOCKET_REF`，曾把 MewUI 的 `namespace_ipc_ref` 写成旧 smoke session。
4. snapshot/health 观测层只接受 `{snapshot: ...}` 包装形状，并且 persisted namespace backend 依赖 ambient Herdr env，导致 `doctor ps` 误报 `pane_state=missing`。

已修复：

- Herdr fallback 改用 `CREATE_NEW_CONSOLE`，不再重定向 stdout/stderr；
- Herdr env 只有匹配当前 manifest session 时才复用；
- `runtime_snapshot()` 兼容包装形状和原始 snapshot 形状；
- persisted namespace backend 按 `namespace_ref.session_name` 绑定 adapter。

复测结果：

```text
start_status: ok
ccbd_started: true
layout_agent: name=agent1 ... pane=w7:p1 ... runtime_state=idle
layout_agent: name=agent2 ... pane=w7:p2 ... runtime_state=idle
herdr_namespace_ref: ... ipc_ref=herdr://ccb-mewui-1aa66360,namespace_id=w7,session_name=ccb-mewui-1aa66360
agent1 pane_state=alive
agent2 pane_state=alive
```

详见：

- `mewui-frontend-root-cause.md`
- `mewui-wezterm-env-fallback.md`
