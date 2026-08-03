---
doc_type: issue-fix-note
issue: 2026-08-03-ccb8-prestart-kill-hang
status: review-passed
fix_path: standard
tags: [windows, ccb8, kill, startup]
---

# ccb8 启动前 kill 残留清理 Fix Note

## 根因

`ccb8.cmd` 之前直接在启动前调用 `ccb.py kill -f`。但 `kill -f` 在进入本地强制清理前，会先尝试连接 mounted daemon 的 control-plane endpoint。Windows 下该探测链路可能卡在 token 读取或 TCP socket 探测，导致本地 PID 清理没有执行，`.ccb-source-dev` 残留 daemon/keeper 继续存活。

外部复现失败后，进一步定位到第一次定向清理实现的 Windows 匹配条件也有缺陷：wrapper 项目根可表现为 `D:/...`，而进程命令行是 `D:\...`；同时正则没有稳定命中 `ccbd\main.py` / `ccbd\keeper_main.py`。因此脚本虽然从 `.ccb-source-dev` 状态文件识别出了 PID，但在命令行校验阶段跳过了源码态 keeper/daemon。

## 改动

- `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.cmd`
  - 默认设置 `CCB_NO_ATTACH=1`、`CCB_CCBD_FAULTHANDLER=1`、`PYTHONUNBUFFERED=1`，减少外部复现时必须额外拼环境变量的需求，并改善异常日志可读性。
  - 启动入口前先读取 `.ccb-source-dev` 隔离运行态下的 `lease.json`、`keeper.json`、`lifecycle.json`。
  - 只对这些文件中的 `ccbd_pid`、`keeper_pid`、`owner_pid` 做定向处理，并在停止前验证进程命令行必须是 `ccbd/main.py` 或 `ccbd/keeper_main.py`，且包含当前项目根。
  - 对项目根和进程命令行统一做 `/` 到 `\` 的路径归一化，并使用大小写不敏感的 `IndexOf` 判断项目归属，避免 Windows 路径分隔符差异导致漏清理。
  - 修正 `ccbd\main.py` / `ccbd\keeper_main.py` 的正则匹配，确保当前实物进程命令行可命中。
  - 清理后把 `.ccb-source-dev` lease 标记为 `mount_state=unmounted`，避免后续启动继续对旧 mounted endpoint 做探测。
  - 定向 PID 清理后再执行有超时边界的 `ccb.py kill -f` 收尾；如果 `kill -f` 超时或非零退出，记录 warning 后继续，避免再次依赖 Ctrl+C 中断排障。

## 验证

- 已运行 `cmd /d /c ""D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd" --diagnose"`。
- 结果：wrapper 能正常解析并输出隔离环境、默认诊断环境变量和 CCB 版本 `v8.5.2`。
- 已执行只读 dry-run 校验最终匹配条件，不停止进程：
  - `.ccb-source-dev` 状态文件数：3。
  - 源码态 PID `14312` / `14572`：`Regex=True`、`ProjectIndex>=0`、`WouldStop=True`。
  - 该验证未执行正常启动，也未停止任何进程。
- 独立 code review 已通过：`ccb8-prestart-kill-hang-review.md`。
- 未在 Codex 内执行正常启动，遵守“执行外部验证时严禁在 Codex 中直接启动 CCB”的约束。

## 遗留风险

- 正常启动路径仍需要用户在外部项目执行 `.\\ccb8.cmd` 验证。
- 本次只修 wrapper 的源码开发态启动前清理边界；`ccb kill -f` 主程序自身“远端探测先于本地强制清理”的通用问题尚未修复，可后续另开 issue。
