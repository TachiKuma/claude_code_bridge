# Smoke 项目验证

执行时间：2026-08-25 14:08-14:22 +08:00

本轮使用过两个 smoke 目录：

- `C:\Users\Administrator\Desktop\ccb-smoke-20260825-140840`
- `C:\Users\Administrator\Desktop\ccb-smoke-20260825-141810`

第二个目录用于避免第一次失败后证据混杂，最终结论以第二个目录为准。

## 配置

```toml
version = 2
entry_window = "main"

[windows]
main = "win_codex:codex, win_claude:claude"

[ui.sidebar]
mode = "off"
```

## A1 外部目录运行源码入口

命令：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" --help
```

退出码：0

结果：通过。命令可执行，输出包含 `ccb` 主工作流、`ask`、`doctor`、`ping`、`pend`、`trace`、`kill` 等入口。

## A2 基础诊断

命令：

```powershell
Get-ChildItem Env:CCB*,Env:CODEX* -ErrorAction SilentlyContinue | Remove-Item
$env:CCB_SOURCE_HOME = $env:USERPROFILE
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" doctor
```

退出码：0

结果：部分通过。`doctor` 能识别 smoke project root、两个 agent 和 provider：

- project：`C:\Users\Administrator\Desktop\ccb-smoke-20260825-140840`
- `win_codex`：provider `codex`，health/state `stopped`
- `win_claude`：provider `claude`，health/state `stopped`

差异：

- `entrypoint_status: degraded`，裸 `ccb` 指向另一个安装入口；本轮仍使用绝对源码入口。
- `ccbd_state` 在启动前为 `unmounted`。

## A3 兼容诊断入口

命令：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" --diagnose
```

退出码：1

实际结果：

```text
command_status: invalid
error: invalid start command
```

结论：未通过，按计划记录为 major 兼容差异。当前 CLI 未暴露 `ccb --diagnose` 兼容诊断入口。

## A4 runtime 启动

命令：

```powershell
Get-ChildItem Env:CCB*,Env:CODEX* -ErrorAction SilentlyContinue | Remove-Item
$env:CCB_SOURCE_HOME = $env:USERPROFILE
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd"
```

退出码：1

第一次直接在 managed provider shell 中执行，实际结果：

```text
command_status: failed
error: mux backend capability unsupported for create_session
```

随后在独立 psmux/tmux driver pane 中执行同一启动命令。driver pane 环境确认：

```text
TMUX=/tmp/psmux-1864/default,64445,0
TMUX_PANE=%1
TERM=xterm-256color
tmux display-message: %1 /dev/pty1 client0
```

tmux driver 中仍失败：

```text
command_status: failed
error: mux backend capability unsupported for create_session
```

结论：未通过，blocker。未能创建项目 runtime、窗口和两个 agent pane。

## A5 状态观测

启动失败后执行：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" doctor ps
```

退出码：0

摘要：

```text
ccbd_state: mounted
agent: name=win_claude state=stopped provider=claude queue=0
agent: name=win_codex state=stopped provider=codex queue=0
```

结论：未通过，blocker。状态可解释，但不是成功运行状态；两个 agent 均未启动，不能执行 `ping win_codex` / `ping win_claude` 作为通过证据。

## A6 清理

命令：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" kill
```

退出码：0

摘要：

```text
kill_status: ok
state: unmounted
forced: false
```

结论：通过。普通 `kill` 能关闭失败后挂载的 smoke runtime，不需要 `kill -f`。

## 失败分级

| 编号 | 结论 | 分级 | 归属 |
|---|---|---|---|
| A1 | 通过 | - | - |
| A2 | 部分通过，有入口 degraded 差异 | major | 安装链路/入口解析 |
| A3 | 未通过 | major | CLI 兼容入口 |
| A4 | 未通过 | blocker | 窗口后端 / CCB runtime |
| A5 | 未通过 | blocker | A4 后续影响 |
| A6 | 通过 | - | - |
