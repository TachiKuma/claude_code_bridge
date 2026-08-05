---
doc_type: issue-report
issue: 2026-08-05-herdr-ui-spike-run-findings
status: confirmed
severity: P1
summary: Herdr UI spike 全量采集运行发现 6 个缺陷 — ccb8 ps 路由错误、CCB Herdr 会话 socket 缺失、采集分类竞争、Herdr 会话分叉、启动状态文件缺失 3/5、观察模板未填写
tags:
  - herdr-ui-integration
  - spike
  - ccb8-cli
  - ccbd-socket
  - run_spike.ps1
  - windows
---

# Herdr UI Spike 全量采集运行发现 Issue Report

## 1. 问题现象

在真实 Herdr UI 环境中执行 `run_spike.ps1` 默认全量采集（run-20260805-165854），共发现 6 个缺陷：

**F1 (高)：** 执行 `ccb8 ps` 命令，exit=2，stderr 输出 `command_status: invalid; error: start does not accept agent names or extra arguments; configure startup agents in .ccb/ccb.config and run ccb`。`ps` 被当作 `start` 命令的参数处理，而非独立子命令。同时 `ccb8 doctor ps` 正常工作并返回完整 agent 状态。两个 run（133244 和 165854）均稳定复现。

**F2 (高)：** 执行 `herdr api snapshot --session ccb-avaprintdesigner-575a971f`（CCB 自己的 Herdr 会话），exit=1，stderr 输出 `Error: Os { code: 2, kind: NotFound, message: "系统找不到指定的文件。" }`。该会话的 socket 文件不存在。前一个 run（133244）中同一命令 exit=0 但 stdout 为空。

**F3 (中)：** `ccb8 ping ccbd` 返回 `mount_state: unmounted, reason: lease_unmounted, pid_alive: False`，但约 4 秒后 `ccb8 ping all` 返回两个 agent 均为 `mount_state: mounted, runtime_state: idle, health: restored`。spike 分类逻辑使用 ping-ccbd 的 mount_state 作为分类依据，导致 run 被分类为 `ccb-mounted-not-proven`，但实际上所有生产负载已成功挂载。

**F4 (中)：** spike 在包装器 Herdr 会话 `ccb-herdr-avaprintdesigner-source-dev`（namespace w6）运行，CCB 启动后创建了自己的会话 `ccb-avaprintdesigner-575a971f`（namespace wB7）。包装器会话的 `api snapshot`（前后两次）均返回空：agents=[]、panes=[]、layouts=[]、workspaces=[]。CCB panes（wB7:p2, wB7:p3）仅在 CCB 自己的会话中可见。

**F5 (低)：** 5 个待采集的启动状态文件中有 3 个未能复制：`lease.json`、`keeper.json`、`lifecycle.json`（来自 `.ccb/ccbd/` 目录）和 `startup-report.json`（来自 doctor 输出）。最终仅采集到 2 个文件：`project.identity.json` 和 `runtime-root-ref.json`。无错误日志说明缺失原因。

**F6 (低)：** `manual-observation.md` 中 5 个用户填写字段均为空（尾随冒号，无内容），仅参数输入字段有值。用户尚未填写 Herdr UI 观察结果。

## 2. 复现步骤

1. 在真实 Herdr UI 环境中（CCB_HERDR_EXE、CCB_HERDR_SESSION 等环境变量已配置）
2. 进入项目根目录 `D:\C#Project\GitHub\AvaPrintDesigner`
3. 执行 `run_spike.ps1` 默认全量采集（不传 -OnlyDimension / -SkipDimension）
4. 观察命令输出和采集证据目录

**F1**：自动复现于 ccb8-layout 采集阶段。两个 run 均稳定复现。
**F2**：仅 run-165854 中出现，run-133244 中间接命令 exit=0 但 stdout 为空。
**F3**：自动复现于 ccb8-ping 采集阶段。ping-all 尝试 1 返回 "project ccbd is starting"，尝试 2 成功。
**F4**：自动复现于 herdr-api-snapshot-before 和 herdr-api-snapshot-after。
**F5**：自动复现于 startup-state-files 采集阶段。
**F6**：模板文件中字段为空，需用户手动补填。

证据目录：
- `run-20260805-133244/`（较早 run）
- `run-20260805-165854/`（最新 run，包含所有 6 个发现）

## 3. 期望 vs 实际

**期望行为 (F1)**：`ccb8 ps` 应返回 CCB 进程/agent 状态，与 `ccb8 doctor ps` 行为一致或产出对等输出。

**实际行为 (F1)**：命令被路由到 `start` 命令处理器，返回 `start does not accept agent names or extra arguments`。

**期望行为 (F2)**：`herdr api snapshot --session ccb-avaprintdesigner-575a971f` 应连接到 CCB Herdr 会话的 socket 并返回快照数据。

**实际行为 (F2)**：命令返回 "系统找不到指定的文件"，CCB Herdr 会话的 socket 不存在。

**期望行为 (F3)**：spike 分类应反映 CCB 的实际挂载状态——所有 agent 为 mounted/idle/restored 时，应分类为 `mounted-*` 而非 `ccb-mounted-not-proven`。

**实际行为 (F3)**：分类依赖先到达的 ping-ccbd 结果（unmounted），忽略后续 ping-all 的成功结果。

**期望行为 (F4)**：Herdr 包装器会话中应能观察到 CCB 创建的 panes，或 spike 应完全使用 CCB 自己的会话进行 pane 验证。

**实际行为 (F4)**：包装器会话 api snapshot 完全为空，CCB panes 仅在其自有会话中可见，且 CCB 会话的 socket 可能不可达。

**期望行为 (F5)**：`lease.json`、`keeper.json`、`lifecycle.json`、`startup-report.json` 应能成功复制，如不存在应有跳过原因记录。

**实际行为 (F5)**：3/5 文件缺失且无诊断日志。

**期望行为 (F6)**：用户在 Herdr UI 中执行后应填写所有观察字段。

**实际行为 (F6)**：5 个问题字段均为空，仅参数输入字段有值。

## 4. 环境信息

- 涉及模块 / 功能：ccb8 CLI（Python 路由）、ccbd Herdr socket 创建、run_spike.ps1 采集分类与 Herdr 会话选择、.ccb/ccbd/ 状态文件
- 相关文件 / 函数：
  - F1：ccb8 CLI 入口/Python 子命令路由（待定位具体文件）
  - F2：`lib/ccbd/main.py` ccbd 启动与 Herdr socket 创建
  - F3：`run_spike.ps1:1230-1244` 分类逻辑
  - F4：`lib/ccbd/main.py` Herdr session 管理 + `run_spike.ps1:1024-1104` pane verification 逻辑
  - F5：`run_spike.ps1:973-1018` startup-state-files 采集逻辑
  - F6：`run_spike.ps1:700-723` `New-ManualObservationTemplate`
- 运行环境：Windows 10 Pro 10.0.19045, PowerShell 5.1.19041.6157, Python 3.14, Herdr 0.7.5-preview
- 项目路径：`D:\C#Project\GitHub\AvaPrintDesigner`
- 其他：两次采集 run 均已落盘证据目录

## 5. 严重程度

**P1** — F1（ccb8 ps 路由错误）和 F2（CCB Herdr socket 缺失）影响核心功能路径，其他为中等或轻微但需同步处理。

分级明细：
- F1: **P1** — ccb8 CLI 子命令不可用，影响所有使用者
- F2: **P1** — CCB Herdr 会话外部不可查询，影响监控和诊断
- F3: **P2** — 分类误导但采集数据完整
- F4: **P2** — 会话分叉是结构性模式，暂有绕行方案
- F5: **P3** — 启动状态文件采集不完整
- F6: **P3** — 用户填写提醒

## 备注

- 所有证据位于 `.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260805-165854/`
- `ccb8 ps` 错误信息指向 start 命令，暗示路由表或 CLI 调度器缺少 `ps` 子命令注册
- CCB Herdr 会话 socket 路径预期为 `C:\ccb8v\.ccb-source-dev\state\xdg-config\herdr\sessions\ccb-herdr-avaprintdesigner-source-dev\herdr.sock`（来自 herdr status server 输出），但 CCB 自用会话 `ccb-avaprintdesigner-575a971f` 的 socket 可能在不同路径
- 前一个 run（133244）中 CCB 会话 snapshot 命令 exit=0（socket 存在），本 run 中 exit=1（socket 不存在），暗示 socket 生命周期不稳定
