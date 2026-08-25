# Windows 原生外部项目验收测试路线图

日期：2026-08-25

## 当前状态

计划已收敛测试对象、外部项目定义、provider 覆盖范围、成功标准、环境写入边界、
产物路径和术语定义。尚未执行实机验收。

## 阶段 0：测试前确认

目标：确认测试运行在 Windows 原生环境，而不是 WSL、Git Bash 模拟层或 CI
兼容层。

验收项：

- `pwsh` 或 Windows PowerShell 可执行；
- 从非仓库目录能运行绝对路径 `ccb.cmd`；
- `codex` 与 `claude` CLI 使用已有用户环境能启动并处于已登录状态；
- CCB 所需终端/窗口后端满足 `ccb doctor` 报告；
- 隔离 prefix 路径已选定，并与本仓库源码目录分离；
- 测试日志目录已创建。

退出条件：

- 阶段 0 的所有环境事实都有命令输出证据；
- 缺失项被标记为 blocker，而不是进入阶段 A 后再解释。

## 阶段 A：一次性 smoke 项目

目标：用自动创建的一次性外部项目验证环境和安装链路。

建议项目根：

```text
%USERPROFILE%\Desktop\ccb-smoke-YYYYMMDD-HHMMSS
```

验收项：

- 外部项目目录不是 CCB 仓库源码目录；
- `.ccb/ccb.config` 使用 `win_codex:codex` 与 `win_claude:claude`；
- 从外部项目目录运行绝对路径 `ccb.cmd doctor` 通过；
- `ccb --diagnose` 被执行并记录结果；若入口不存在，作为兼容差异记录；
- `ccb` 能启动窗口和 pane；
- `ccb doctor ps` 能识别 ccbd、窗口、pane、agent 状态；
- `ccb kill` 能正常停止当前项目 runtime；
- `ccb kill -f` 只在普通 kill 后仍有 CCB 项目残留时使用。

退出条件：

- 阶段 A 可以重复执行，且不会依赖 CCB 仓库工作目录；
- smoke 项目的失败可以定位到环境、安装链路、窗口后端、provider 认证或 CCB
  runtime 四类之一。

## 阶段 B：真实现有项目

目标：在真实项目摩擦下验证 CCB 的目录识别、运行时写入、provider home 继承和
清理边界。

真实项目准入条件：

- 项目已有版本控制或明确备份；
- 允许 CCB 写入 `.ccb/`、provider home、日志和运行时状态；
- 不允许 CCB 修改业务源码、依赖锁文件、数据库或生产配置；
- 执行前记录 `git status --short` 或等价文件清单。

验收项：

- 从真实项目根运行绝对路径 `ccb.cmd`；
- CCB 识别的 project root 与真实项目根一致；
- CCB 写入集中在允许范围；
- agent pane 均能启动，并绑定到真实项目目录；
- `ccb doctor`、`ccb doctor ps` 和必要时 `ccb doctor storage` 可解释当前状态；
- `ccb kill` 后不存在本项目仍被占用的窗口、daemon 或可见 pane 残留。

退出条件：

- 真实项目运行不污染 CCB 仓库源码状态；
- 真实项目业务文件没有非预期 diff；
- 运行时残留可通过普通清理命令收敛。

## 阶段 C：真实跨 agent ask

目标：把“能启动”提升为“能协作”。这是本轮发布/验收门槛。

验收项：

- 从外部项目目录发起 `ccb ask win_claude -- <任务>`；
- `win_claude` 返回可验证业务结果；
- 从外部项目目录发起 `ccb ask win_codex -- <任务>`；
- `win_codex` 返回可验证业务结果；
- 至少一次 agent 间任务要求读取外部项目文件并产出结论；
- `ccb pend <job_id>` 或 `ccb trace <job_id>` 能看到 job 进入、执行、完成链路；
- 失败时能区分 provider 认证失败、pane 未就绪、runtime 绑定失败和业务任务失败。

退出条件：

- 两类 provider 各至少一次真实业务结果通过；
- 结果不只来自 provider 启动横幅或空响应；
- 证据中包含提交命令、job id、最终状态、业务结果摘要和清理结果。

## 阶段 D：韧性验收

目标：覆盖中断、重启、恢复、clear、compact、followup 等恢复能力。该阶段不阻塞
本轮阶段 C 验收，但必须在宣布 Windows 原生外部项目长期可用前完成。

验收项：

- 活跃 ask 期间中断 provider 或 runtime 后，状态可观测且不会静默成功；
- `ccb restart <agent>` 只作用于空闲或可安全重启的 agent；
- `ccb` 或 `ccb -n` 能按预期恢复或重建 runtime；
- `ccb clear [agent]` 发送 provider 原生命令并有可观测结果；
- `ccb compact [agent]` 发送 provider 原生命令并有可观测结果；
- `ccb followup <job_id> --message <text>` 对活跃 job 的结果符合当前 active-turn
  支持边界；
- 普通失败路径不会要求用户手工删除未知运行时文件。

退出条件：

- 每个韧性场景都有成功证据或明确失败记录；
- 失败记录包含复现命令、状态观察、预期行为、实际行为和下一步修复归属。

## 后续白名单路线

本轮只测 `codex` 和 `claude`。后续 provider 白名单应作为独立实现项推进：

- 新增 provider 前先定义准入条件；
- 每个 provider 必须有 provider CLI 登录态检查、最小 ask、pane 状态识别和
  清理证据；
- 白名单失败必须 fail closed，不允许退化为“未知 provider 也尝试启动”。
