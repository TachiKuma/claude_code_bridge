# 环境确认

执行时间：2026-08-25 14:08-14:22 +08:00

当前 CCB 入口：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd"
```

## 环境摘要

| 项 | 结果 |
|---|---|
| PowerShell | 7.5.4 |
| OS | Microsoft Windows 10.0.19045 |
| CCB install_mode | source |
| CCB install_version | 8.6.10 |
| Python | C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe，3.14.6 |
| tmux | C:\Users\Administrator\AppData\Local\psmux\tmux.EXE，tmux 3.3.2 |
| codex | C:\Users\Administrator\AppData\Roaming\npm\codex.ps1 / codex.CMD |
| claude | C:\Users\Administrator\.local\bin\claude.exe，2.1.237.0 |

## 关键命令

```powershell
Get-Command codex
Get-Command claude
& $Ccb --help
& $Ccb doctor
```

结果：

- `codex` 和 `claude` 均来自既有用户环境，可发现。
- `ccb.cmd --help` 能从绝对路径执行。
- 在 CCB 仓库根执行 `doctor` 通过入口和 provider 发现检查，但该结果不作为外部项目验收通过证据。
- 从当前 Codex managed provider shell 直接启动外部 smoke 时，必须先清理当前进程的 `CCB*`/`CODEX*` 会话变量，并设置 `CCB_SOURCE_HOME=C:\Users\Administrator`；否则 CCB fail-closed：`cannot resolve the source user home from a managed provider environment`。

## 环境差异

- `doctor` 报告 `entrypoint_status: degraded`，原因是裸 `ccb` 解析到 `C:\Users\Administrator\AppData\Local\codex-dual\bin\ccb.exe`，不是本轮显式使用的源码入口。测试命令均使用绝对路径 `ccb.cmd`。
- `windows_x64_release_surface` 为 `degraded`，原因包含 `managed-python-degraded`，并提示 Windows/Herdr 验收仍待完成。
