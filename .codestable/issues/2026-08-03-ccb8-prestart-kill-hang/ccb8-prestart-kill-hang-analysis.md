---
doc_type: issue-analysis
issue: 2026-08-03-ccb8-prestart-kill-hang
status: confirmed
root_cause_type: logic
related: [ccb8-prestart-kill-hang-report.md]
tags: [windows, ccb8, kill, startup]
---

# ccb8 启动前 kill 仍未清理干扰项根因分析

## 1. 问题定位

| 关键位置 | 说明 |
|---|---|
| `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.cmd:91` | wrapper 只是在启动入口前调用源码 CLI 的 `kill -f`。 |
| `lib/cli/services/kill.py:75` | `kill_project()` 先收集项目 authority PID 候选。 |
| `lib/cli/services/kill.py:76` | `kill_project()` 在本地清理前先调用 `_request_remote_stop()`。 |
| `lib/cli/services/kill.py:77` | 本地 shutdown 准备和 PID 清理候选收集在远端 stop 之后才执行。 |
| `lib/cli/services/kill_runtime/remote.py:19` | `_request_remote_stop()` 首先调用 `connect_mounted_daemon_fn()` 连接已有 mounted daemon。 |
| `lib/ccbd/services/ownership.py:53` | `inspect()` 会计算 lease 信号，包括 socket 是否可连接。 |
| `lib/ccbd/services/ownership.py:197` | mounted lease 会通过 control-plane endpoint 做 socket probe。 |
| `lib/ccbd/control_plane_transport/windows_tcp.py:73` | TCP probe 连接前先读取 token 文件。 |
| `lib/ccbd/control_plane_transport/windows_tcp.py:80` | TCP probe 创建 socket 并连接，日志中的 Ctrl+C 落在 token/socket 探测路径。 |

## 2. 失败路径还原

**正常路径**：用户执行 `.\\ccb8.cmd` → wrapper 设置 `.ccb-source-dev` 隔离环境 → 启动前执行 `ccb.py kill -f` → 源码开发态残留被停止 → wrapper 再执行 `ccb.py` 正常启动。

**失败路径**：用户执行 `.\\ccb8.cmd` → wrapper 执行 `ccb.py kill -f` → `kill_project()` 先尝试连接 mounted daemon → ownership inspect 进入 control-plane TCP 探测 → token/socket 同步调用卡住或被 Ctrl+C 中断 → 后续本地 PID 清理没有执行 → `.ccb-source-dev` daemon/keeper 继续存活并 heartbeat。

**分叉点**：`lib/cli/services/kill.py:76` — force kill 的远端 stop 探测位于本地强制清理之前；当 mounted lease 的控制面探测不可用或阻塞时，`kill -f` 无法进入真正的本地清理。

## 3. 根因

**根因类型**：logic

**根因描述**：`kill -f` 被设计成项目级清理，但当前执行顺序仍把“优雅远端停机 / mounted daemon 探测”放在“强制本地清理”之前。Windows 下 control-plane endpoint 探测依赖 token 文件读取和 TCP socket 创建/连接，日志证明外部复现正卡在这条路径。wrapper 前置调用 `kill -f` 因此没有获得预期的“先清残留”效果；它复用了会卡住的同一套 CCB 启动检查逻辑。

**是否有多个根因**：是。

主因：`kill -f` 的远端探测优先级不适合作为启动前强制清理动作。

次因 1：外部项目同时存在两套 mounted 状态：

- `.ccb/ccbd/lease.json`：`ccbd_pid=12652`，`keeper_pid=12720`，端口 `127.0.0.1:54129`。
- `.ccb-source-dev/.../ccbd/lease.json`：`ccbd_pid=14572`，`keeper_pid=14312`，端口 `127.0.0.1:59837`。

这会让“只按项目根清理”的策略存在误伤 v5 的风险；wrapper 必须按 `.ccb-source-dev` 自己的 lease 文件定向清理，而不是泛化为项目级 process scan。

次因 2：首次 wrapper 定向清理实现里，Windows 路径匹配条件没有真正命中当前源码态进程。

- wrapper 中的项目根可能经由 `cmd /d /c ""D:/.../ccb8.cmd" ..."` 以正斜杠形式进入 PowerShell。
- 当前活跃源码态进程命令行使用反斜杠：`--project D:\C#Project\GitHub\AvaPrintDesigner`。
- dry-run 结果显示旧条件识别到 `.ccb-source-dev` 的 PID `14312/14572` 后，`ProjectLike=False`，因此清理循环跳过了目标进程。
- 同一次 dry-run 还暴露正则写法对 `ccbd\main.py` / `ccbd\keeper_main.py` 的反斜杠匹配不稳定，导致 `Regex=False`。

因此，用户外部复现失败不是因为推荐方案方向错误，而是方案 A 的第一次 batch/PowerShell 实现没有通过 Windows 实际命令行格式校验。

## 4. 影响面

- **影响范围**：所有把 `ccb kill -f` 作为启动前清理动作的 Windows 源码开发 wrapper；也影响 Windows 下 mounted lease 控制面不可用时的 `kill -f` 恢复能力。
- **潜在受害模块**：`ccb8.cmd` wrapper、`cli.services.kill`、`ccbd.services.ownership`、Windows TCP control-plane transport。
- **数据完整性风险**：低。问题主要是进程残留和启动阻塞；但双 daemon 同时 mounted 可能造成运行状态混乱。
- **严重程度复核**：维持 P1。核心开发验证路径受阻，但用户仍可通过外部手工清理恢复。

## 5. 修复方案

### 方案 A：wrapper 定向清理 `.ccb-source-dev` lease PID

- **做什么**：在 `ccb8.cmd` 的预启动阶段，先读取 `.ccb-source-dev\state\runtime-state\*\ccbd\lease.json` 和 `keeper.json` 中的 PID，只终止这些 PID；再调用 `ccb.py kill -f` 作为状态收尾，最后启动。
- **优点**：最小改动；强边界，不碰项目 `.ccb` 中 v5 lease；直接解决当前 wrapper 目标。
- **缺点 / 风险**：这是 wrapper 专用恢复逻辑，不修复 CCB 主程序 `kill -f` 的通用顺序问题。
- **影响面**：只改 `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.cmd`。

### 方案 B：修复 CCB 主程序 `kill -f` 的执行顺序

- **做什么**：在 `kill_project()` 中，当 `command.force` 为 true 时，先执行本地 shutdown 准备 / PID 清理，再尝试 remote stop 或把 remote probe 做成短超时可跳过。
- **优点**：修到根实现，所有 Windows 项目受益。
- **缺点 / 风险**：影响 `kill -f` 的全局语义和测试面；当前仓库已有多处未归属改动，直接改主程序需要更完整回归。
- **影响面**：`lib/cli/services/kill.py`、`lib/cli/services/kill_runtime/*`、相关测试。

### 方案 C：wrapper 绕过 CCB CLI，完全用隔离状态文件清理

- **做什么**：移除启动前 `ccb.py kill -f`，改为 PowerShell 定向读取 `.ccb-source-dev` PID 并 `Stop-Process`，同时保留 `.ccb-source-dev` 状态目录。
- **优点**：不会进入 CCB 自身卡住的 control-plane probe。
- **缺点 / 风险**：没有 CCB 的状态收尾逻辑，可能留下 stopped/mounted JSON 不一致，需要后续启动自行 takeover。
- **影响面**：只改 wrapper，但语义偏离“先做 kill -f 动作”的原始要求。

### 推荐方案

**推荐方案 A**。理由：当前用户目标是让 `ccb8.cmd` 启动前清除源码开发态干扰项，同时明确不能影响已安装 CCB/v5。按 `.ccb-source-dev` lease PID 定向清理是最小、边界最清楚的修法；保留后续 `ccb.py kill -f` 作为收尾动作，可以继续满足“启动前做 kill -f”的要求。

### 方案 A 的实现修正

定向清理必须在匹配进程命令行前做路径归一化：

- `$project=$env:CCB_PROJECT_ROOT.TrimEnd('\').Replace('/','\')`
- `$cmdNorm=$cmd.Replace('/','\')`
- 用 `$cmdNorm.IndexOf($project, [StringComparison]::OrdinalIgnoreCase) -ge 0` 判断是否属于当前项目。
- 用能匹配 Windows 反斜杠路径的正则识别 `ccbd\main.py` / `ccbd\keeper_main.py`。

最终只读 dry-run 已确认当前 `.ccb-source-dev` PID `14312/14572` 满足 `Regex=True`、`ProjectIndex>=0`、`WouldStop=True`；项目 `.ccb` 的 v5 PID `12652/12720` 仍只作为保护 PID 读取，不进入停止候选。
