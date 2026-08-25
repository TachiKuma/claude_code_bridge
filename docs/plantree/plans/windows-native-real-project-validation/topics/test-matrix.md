# Windows 原生外部项目验收测试矩阵

日期：2026-08-25

## Provider 覆盖

| Provider | 本轮状态 | 验收要求 |
|---|---|---|
| `codex` | 必测 | CLI 可发现、已登录、pane 可启动、状态可观测、ask 有业务结果 |
| `claude` | 必测 | CLI 可发现、已登录、pane 可启动、状态可观测、ask 有业务结果 |
| 其他 provider | 后续白名单 | 必须先定义准入条件，再加入矩阵 |

## 项目覆盖

| 项目类型 | 目标 | 通过条件 |
|---|---|---|
| 一次性 smoke 项目 | 验证环境和安装链路 | doctor、启动、pane、状态、kill、基础 ask 通过 |
| 真实现有项目 | 验证真实项目摩擦 | 不污染业务源码，能启动、观测、ask、清理 |

## 阶段 A 到 C 硬门槛

| 编号 | 场景 | 命令入口 | 通过条件 | 失败分级 |
|---|---|---|---|---|
| A1 | 外部目录运行源码入口 | 绝对路径 `ccb.cmd --help` | 当前目录不是仓库根，命令可执行 | blocker |
| A2 | 基础诊断 | `ccb doctor` | 报告无阻塞失败 | blocker |
| A3 | 兼容诊断入口 | `ccb --diagnose` | 有诊断输出；若不支持则记录兼容差异 | major |
| A4 | runtime 启动 | `ccb` | 创建项目 runtime、窗口和两个 agent pane | blocker |
| A5 | 状态观测 | `ccb doctor ps`、`ccb ping` | ccbd 与两个 agent 状态可解释 | blocker |
| A6 | 清理 | `ccb kill` | 当前项目 runtime 停止，无可见残留 | blocker |
| B1 | 真实项目 root 绑定 | 绝对路径 `ccb.cmd` | project root 是真实项目根 | blocker |
| B2 | 真实项目写入边界 | `git status --short` | 只出现允许的 CCB 运行时文件变化 | blocker |
| C1 | Claude ask | `ccb ask win_claude -- ...` | 返回可验证业务结果 | blocker |
| C2 | Codex ask | `ccb ask win_codex -- ...` | 返回可验证业务结果 | blocker |
| C3 | job 可追踪 | `ccb pend` 或 `ccb trace` | 可看到提交、执行、完成状态 | major |

阶段 C 是本轮验收门槛。C1 与 C2 任一失败，都不能宣称 Windows 原生外部项目验收通过。

## 阶段 D 韧性矩阵

| 编号 | 场景 | 命令入口 | 通过条件 | 本轮门槛 |
|---|---|---|---|---|
| D1 | ask 取消 | `ccb ask cancel <job_id>` | job 终止状态清晰，不静默成功 | 第二阶段 |
| D2 | agent 重启 | `ccb restart <agent>` | 空闲 agent 可重启，状态重新可观测 | 第二阶段 |
| D3 | runtime 恢复 | `ccb` | 已有状态可恢复或明确拒绝 | 第二阶段 |
| D4 | runtime 重建 | `ccb -n` | 保留配置和历史，重建运行时状态 | 第二阶段 |
| D5 | clear | `ccb clear [agent]` | provider 原生命令到达，后续状态可解释 | 第二阶段 |
| D6 | compact | `ccb compact [agent]` | provider 原生命令到达，后续状态可解释 | 第二阶段 |
| D7 | followup | `ccb followup <job_id> --message ...` | 活跃 job 支持时注入成功，不支持时 fail closed | 第二阶段 |

## 证据要求

每个通过项必须至少记录：

- 执行时间；
- 当前工作目录；
- CCB 入口路径；
- 命令；
- 退出码；
- 关键输出摘要；
- 若涉及 ask，记录 job id 和最终业务结果；
- 清理后的状态。

失败记录必须包含：

- 复现命令；
- 期望行为；
- 实际行为；
- 失败分类；
- 下一步归属：环境、安装链路、窗口后端、provider 认证、CCB runtime 或业务任务。

## 不接受的证据

- 只在 CCB 仓库根执行的结果；
- 只证明 provider CLI 能单独启动，不证明 CCB 能管理 pane；
- 只看到 provider 欢迎语，没有业务结果；
- 只用 `ccb doctor` 通过替代跨 agent ask；
- 没有 `ccb kill` 或清理后状态记录；
- 隐藏 `ccb --diagnose` 入口差异。
