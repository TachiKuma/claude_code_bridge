# 将运行时托管下放给 Herdr

日期：2026-08-20

## 背景

Herdr `v0.8.2` 增强了 Agent 生命周期能力，包括启动就绪等待、
idle/working/blocked 状态识别、Windows 原生 Agent 支持、远程客户端，
以及绕过 pane/API 流量的服务端停止处理。

CCB 当前虽然将 Herdr 作为终端后端，但仍承担了大量宿主运行时启动工作：

- `ccb.py` 提前执行 Native Windows Herdr 门禁检查；
- `handle_start()` 探测 Herdr、启动 server、注入 capability 证据；
- `platforms/windows/herdr/bootstrap.py` 发现 session、启动 server、等待就绪、
  探测能力并写入临时 capability 报告；
- `HerdrCliRequestAdapter` 将大量 CCB 操作转换成独立的 Herdr CLI 调用；
- CCB 维护 Herdr operation 白名单，并额外负责 pane Agent 注册和状态上报。
- CCB 与 Herdr 之间的状态投影仍不完整，Agents 面板无法始终可靠地跟踪
  Agent 从启动、就绪、工作、空闲、阻塞到退出的完整生命周期；尤其是在
  pane 重启、重新 attach、快速状态切换、事件乱序或连接短暂中断后，容易出现
  pane/Agent 身份映射丢失、状态滞后或状态与实际运行时不一致。

代表性证据：

- `ccb.py:42-60, 159-171`
- `lib/cli/phase2_runtime/handlers_start.py:89-114, 175-252`
- `lib/platforms/windows/herdr/bootstrap.py:38-159`
- `lib/platforms/windows/herdr/runtime/cli.py:23-116`
- `lib/cli/services/runtime_launch_runtime/tmux_runtime.py:289-319`
- Herdr `v0.8.2`，发布时间：2026-08-19

## 决策

将职责边界调整为：

> Herdr 负责宿主运行时，CCB 负责协作控制面。

Herdr 应负责：

- server、session、workspace、tab/window 和 pane 生命周期；
- 进程启动、就绪、退出、重启、attach、焦点和布局；
- 通用 Agent 状态识别和运行时事件；
- 为托管 Agent 提供稳定的 `agent_id`、`pane_id` 和 `runtime generation`，并对
  状态变更提供可排序事件、当前状态快照以及断线后的重同步能力；
- 通用 pane 清理、重启退避和资源所有权；
- 终端 UI、远程连接和宿主窗口展示。

CCB 保留负责：

- `ccbd`、keeper、startup fence 和项目控制面状态；
- Provider 命令、隔离的 Provider home、凭据和原生 session；
- ask、job、队列、回复、取消、协作图和 memory；
- Provider 特定的完成、resume/fork、continuation 和恢复策略；
- 授权、命令审批和业务层失败判定。
- 将 Herdr 运行时状态与 Provider/job/ask 业务状态合并为 Agents 面板使用的
  单一状态投影；不得把 Herdr 的 `idle/working/blocked` 直接等同于 Provider
  turn 或 job 的完成、失败和可恢复性。

目标启动契约是：CCB 生成声明式运行时 manifest，并提交给 Herdr 的单一运行时操作：

```text
CCB manifest
    -> Herdr ensure_runtime()
    -> workspace/session/pane handles 和 readiness events
    -> CCB 连接 ccbd 和 Provider 业务状态
```

首版契约应一次性返回稳定的 server/session/workspace/pane handle、
runtime generation、readiness 和 capability 数据。正常启动不应再依赖
临时的 `CCB_HERDR_CAPABILITY_REPORT` 文件。

## 影响

正面影响：

- CCB 启动流程不再承担平台相关的 server 发现和重复 Herdr CLI 编排；
- Herdr 可以对所有托管 pane 应用统一的生命周期策略；
- CCB 可以消费运行时事件，不再通过轮询或解析终端文本判断通用进程状态；
- capability 和 readiness 证据统一为一个运行时契约。

约束：

- Provider session 语义必须继续由 CCB 管理；移入 Herdr 会形成两个耦合的业务权威；
- 现有启动契约和 Provider 隔离契约仍然优先；
- 迁移必须继续对 project、namespace、pane、session 和 runtime generation
  执行 fail-closed 身份校验；
- manifest 不应携带原始凭据；CCB 保留凭据权威，只传递经过授权的引用或受限环境投影。
- Agents 面板在运行时事件契约、快照重同步和重启代次投影完成前，不能宣称具备
  完整状态跟踪能力；未知、断线或过期状态必须显式保留，不能静默降级为正常空闲。

## 迁移顺序

1. 引入持久化 Herdr runtime client，以及一次性返回 server info、capability
   和 generation 的握手；
2. 增加声明式 runtime manifest 和 `ensure_runtime` 风格的 Herdr 契约，
   保留当前 bootstrap 作为兼容适配层；
3. 将通用 workspace/pane 就绪、存活和重启处理迁移到 Herdr，Provider
   恢复仍由 CCB 负责；
4. 用运行时契约校验替代 CCB capability 临时文件和导入阶段 Herdr 检查；
5. 增加 Herdr runtime event，让 `ccbd` 消费 pane/Agent 生命周期投影；
6. 为 Agents 面板建立基于 `agent_id`、`pane_id` 和 `generation` 的统一读模型，
   覆盖启动、就绪、工作、空闲、阻塞、退出、重启、重新 attach、断线和重同步，
   并验证事件乱序及重复投递不会产生错误状态；
7. 契约稳定并完成验证后，再简化或移除旧的 `HerdrCliRequestAdapter`
   和 bootstrap 路径。

## 非目标

本决策不把 CCB 的 message bureau、Provider session 权威、ask 取消语义、
凭据或 Provider 特定恢复逻辑迁移到 Herdr。
