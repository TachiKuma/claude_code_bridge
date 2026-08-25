# 失败记录

执行时间：2026-08-25 14:08-14:22 +08:00

## F1 managed provider shell 缺少 source home

复现命令：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd"
```

实际行为：

```text
command_status: failed
error: cannot resolve the source user home from a managed provider environment
```

期望行为：在用户原生 PowerShell 中应能解析用户 home，并继承既有 provider 登录态。

分类：环境前置条件差异。

处理：本轮使用子进程级环境清理和显式覆盖继续测试：

```powershell
Get-ChildItem Env:CCB*,Env:CODEX* -ErrorAction SilentlyContinue | Remove-Item
$env:CCB_SOURCE_HOME = $env:USERPROFILE
```

## F2 `ccb --diagnose` 兼容入口不可用

复现命令：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" --diagnose
```

实际行为：

```text
command_status: invalid
error: invalid start command
```

期望行为：输出诊断信息；若不支持，也应有可解释的兼容提示。

分类：major，CLI 兼容入口。

下一步归属：CCB CLI。

## F3 smoke runtime 无法创建窗口后端 session

复现命令：

```powershell
Get-ChildItem Env:CCB*,Env:CODEX* -ErrorAction SilentlyContinue | Remove-Item
$env:CCB_SOURCE_HOME = $env:USERPROFILE
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd"
```

实际行为：

```text
command_status: failed
error: mux backend capability unsupported for create_session
```

`doctor` 摘要：

```text
ccbd_startup_last_status: failed
ccbd_startup_last_desired_agents: ['win_claude', 'win_codex']
ccbd_startup_last_failure_reason: mux backend capability unsupported for create_session
agent: name=win_claude health=stopped provider=claude
agent: name=win_codex health=stopped provider=codex
```

tmux driver 复核：在独立 psmux/tmux pane 内存在 `TMUX` 和 `TMUX_PANE`，但启动仍返回同一错误。

期望行为：创建 smoke 项目 runtime、窗口和两个 agent pane。

分类：blocker。

下一步归属：窗口后端 / CCB runtime。需要确认当前 Windows 原生环境应使用 Herdr、tmux/psmux，还是需要显式能力证据或后端选择修正。

## 清理状态

最终清理命令：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" kill
```

实际行为：

```text
kill_status: ok
state: unmounted
forced: false
```

真实项目 `E:\GitHub开源项目\TachiKuma\MewUI` 未执行 CCB 启动，`git status --short` 仍无输出。

## 修复后复测补充

执行时间：2026-08-25 16:46-16:52 +08:00

本轮已在真实项目 `E:\GitHub开源项目\TachiKuma\MewUI` 重新执行 `doctor`、`doctor storage`、`ping`、`trace` 和 `pend`。

未再复现前一轮 `mux backend capability unsupported for create_session` blocker。

观察到但未阻断的差异：

- `entrypoint_status: degraded`，裸 `ccb` 仍解析到安装目录外的 `C:\Users\Administrator\AppData\Local\codex-dual\bin\ccb.exe`
- `ccbd_herdr_namespace_ref.ipc_ref` 仍显示 smoke 会话引用 `herdr://ccb-ccb-smoke-20260825-143734-15830fa4`
- `doctor ps` 中 `pane_state` 仍为 `missing`，但 job 已能正常完成并返回回复

这些项当前不阻断阶段 B/C 验收，但建议后续继续观察。
