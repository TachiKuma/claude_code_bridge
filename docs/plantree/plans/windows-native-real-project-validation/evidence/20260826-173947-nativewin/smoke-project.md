# Smoke 项目验证

执行时间：2026-08-26 17:39-18:05 +08:00

Smoke 根目录：

```text
C:\Users\Administrator\Desktop\ccb-smoke-20260826-173947-nativewin
```

配置：

```toml
version = 2
entry_window = "main"

[windows]
main = "win_codex:codex, win_claude:claude"

[ui.sidebar]
mode = "off"
```

## 启动回路

### `ccb.cmd --help`

退出码：0

结论：通过。命令可执行，且入口列表完整。

### `ccb.cmd doctor`

退出码：0

结论：通过。识别到 smoke 项目根、`win_codex` 和 `win_claude`。

### `ccb.cmd --diagnose`

退出码：2

关键输出：

```text
command_status: invalid
error: invalid start command
```

结论：未通过，按计划记录为兼容入口差异，不阻断本轮启动根因验证。

### `ccb.cmd`

退出码：0

关键输出：

- `start_status: ok`
- `ccbd_started: true`
- `agents: win_codex, win_claude`
- `layout_summary_status: ok`

结论：通过。当前树已不再复现旧的 `mux backend capability unsupported for create_session` 启动 blocker。

### `ccb.cmd doctor ps`

退出码：0

关键输出：

- `ccbd_state: mounted`
- `agent: name=win_codex state=idle`
- `agent: name=win_claude state=idle`
- `binding: status=bound`
- 刚启动后曾短暂显示 `pane_state: missing`，后续 heartbeat 和 Herdr snapshot 显示 `pane_state: alive`

结论：通过。

### `ccb.cmd ping ccbd / win_codex / win_claude`

退出码：0

结论：通过。两个 agent 都可被识别并返回健康状态。

### `ccb.cmd kill`

退出码：0

关键输出：

- `kill_status: ok`
- `state: unmounted`

结论：通过。
