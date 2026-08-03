---
doc_type: issue-report
issue: 2026-08-03-ccb8-prestart-kill-hang
status: confirmed
issue_path: standard
severity: P1
summary: ccb8.cmd 启动前执行 kill -f 后故障仍旧，源码开发态 CCB 残留未被清除
tags: [windows, ccb8, kill, startup]
---

# ccb8 启动前 kill 仍未清理干扰项 Issue Report

## 1. 问题现象

在 `D:\C#Project\GitHub\AvaPrintDesigner` 外部执行 `.\\ccb8.cmd` 后，故障依旧。最新状态显示项目同时存在已安装态 `.ccb` 和源码开发态 `.ccb-source-dev` 两套 mounted daemon/keeper 记录，源码开发态残留没有被启动前清理动作清除。

## 2. 复现步骤

1. 在外部项目 `D:\C#Project\GitHub\AvaPrintDesigner` 执行 `.\\ccb8.cmd`。
2. 观察启动行为或日志。
3. 观察到：启动仍卡在已有 ccbd lease 的控制面探测路径，或者启动后 `.ccb-source-dev` 残留仍保持 mounted heartbeat。

复现频率：当前外部项目一次复现后状态仍可观察。

## 3. 期望 vs 实际

**期望行为**：`ccb8.cmd` 正常启动源码开发态 CCB 前，先清除该 wrapper 自己的源码开发态残留，且不影响已安装 CCB，包括同项目已启动的 v5 `ccb`。

**实际行为**：`.ccb-source-dev` 下的源码开发态 daemon/keeper 仍存活并继续 heartbeat；旧启动日志显示 CLI 在 daemon lease 的 TCP 控制面探测处被 Ctrl+C 中断。

## 4. 环境信息

- 涉及模块 / 功能：Windows 源码开发 wrapper、`ccb kill -f`、ccbd ownership / control-plane probe。
- 相关文件 / 函数：`D:\C#Project\GitHub\AvaPrintDesigner\ccb8.cmd`；`lib/cli/services/kill.py`；`lib/cli/services/kill_runtime/remote.py`；`lib/ccbd/services/ownership.py`；`lib/ccbd/control_plane_transport/windows_tcp.py`。
- 运行环境：Windows，外部项目 `D:\C#Project\GitHub\AvaPrintDesigner`，源码路径 `E:\GitHub开源项目\TachiKuma\claude_code_bridge`。
- 其他上下文：要求外部验证时不得在 Codex 中直接启动 CCB；本次只读取日志和状态文件。

## 5. 严重程度

**P1** — 影响源码开发态 CCB 的启动可靠性，并可能与已安装态 v5 CCB 在同一项目内产生双 daemon 干扰。

## 备注

关键日志文件：

- `D:\C#Project\GitHub\AvaPrintDesigner\ccb8-start-20260803-203345.log`
- `D:\C#Project\GitHub\AvaPrintDesigner\ccb8-start-20260803-203004.log`
- `D:\C#Project\GitHub\AvaPrintDesigner\.ccb\ccbd\ccbd.stderr.log`
