# 领域术语表（CONTEXT）

本文件是**术语表**，只定义领域词汇，不含实现细节、规格或临时笔记。
实现方案见 `plans/`，决策见 `docs/adr/`。

---

## CCB Runtime Context（provider 运行时配置边界）

> 以下术语来自上游既有 `CONTEXT.md`，保留其原始英文表述，未机翻。

**Project Config**:
The user-authored declaration of agents, provider credentials, model selection, and runtime preferences for a CCB project.
_Avoid_: generated home config, provider home, manual home edits

**Managed Provider Home**:
A provider-specific runtime home materialized by CCB from project configuration and inherited provider assets.
_Avoid_: user-managed home, source config

**Provider Profile Drift**:
A mismatch between the current project config and the provider profile or launch state already recorded for an agent.
_Avoid_: stale home, config cache bug

**Provider Authority**:
The remote account or API endpoint identity a provider session is bound to.
_Avoid_: model, provider name

---

## 三层职责

### Frontend Surface（前台事实源）

用户可见的 GUI 终端前台，在 Native Windows 上即 **WezTerm**。它是唯一入口、可见 attach 面,
提供**前台可见性事实**：mux（多路复用器 GUI）是否在运行、attach 落到哪个窗口/工作区。

- 它**不是**运行时事实源，也不是业务完成权威。
- 前台不可用（如 mux 未运行）必须**显式暴露**，不得静默降级为「已 attach」。

关联：`Host Runtime`、`Collaboration Control Plane`、`attach`、`WezTerm workspace`。

### Host Runtime（运行时事实源 / 宿主运行时）

即 **Herdr**。负责让终端、workspace、pane 和 agent 状态长期存在，并作为 **physical pane
owner** 管理 pane 进程的启动、就绪、退出、attach、布局、焦点。

提供 agent 运行时状态：`idle`、`working`、`blocked`、`done`、`unknown`。

- 它是**运行时事实源**，**不是业务完成权威**。`done` 只表示「运行时完成」，不表示业务成功。
- `unknown` 表示 Herdr 无法可靠分类，**不等于 `idle`**。
- 它是**观测式状态聚合器**（见下），**不铸造 agent 身份**，也无 agent 级 restart/backoff 策略：
  agent 退出后仅 `respawn_shell_on_exit` 重开 shell 保住 pane，并清除瞬态身份。

关联：`Collaboration Control Plane`、`physical pane owner`、`observational state aggregator`、
`agent identity authority`、`runtime generation`。

### Collaboration Control Plane（协作控制面 / 业务完成权威）

即 **CCB**。掌握 provider 命令、provider home、凭据、原生 session；掌握 ask、job、队列、
取消、回复、协作图、memory；掌握 provider completion、resume/fork、continuation、恢复策略。

- 它是**业务完成权威**：只有 CCB 能判定 job/ask 成败、是否可恢复、是否 continuation。
- 它**消费并校验** Host Runtime 的运行时事实与 Frontend Surface 的前台事实，但不把二者
  当作业务完成的依据。

关联：`runtime fact source vs business completion authority`、`runtime generation`。

---

## 核心区分

### runtime fact source vs business completion authority（运行时事实源 vs 业务完成权威）

本项目的核心边界原则：

- **运行时事实源**（Herdr / WezTerm）报告「现在运行时/前台是什么状态」——是**事实**。
- **业务完成权威**（CCB）判定「这件工作是否真的完成/成功/可恢复」——是**判定**。

事实**不能**替代判定：Herdr 的 `done`、`idle`、WezTerm 的「已 spawn tab」都不足以关闭 job 或
声明业务成功。判定必须由 CCB 结合 provider 事实做出。

关联 ADR：`docs/adr/0001-三层运行时权威边界.md`。

### physical pane owner（物理 pane 所有者）

指对终端 pane 拥有**真实进程/生命周期所有权**的一方，本项目中是 **Herdr**。CCB 只**声明策略**
（哪个 slot 跑哪个 provider 等），不直接持有通用 pane 进程存活。

注：pane 存活所有权归 Herdr，但 **agent 身份与 agent 级重启/backoff 策略归 CCB**（见
`agent identity authority`）——Herdr 无 agent restart 策略，仅有 shell 级 `respawn_shell_on_exit`。

关联：`Host Runtime`、`agent identity authority`、`managed 模式`。

### observational state aggregator（观测式状态聚合器）

对 **Herdr** 角色的精确表述（经 Herdr 源码验证）：Herdr 通过**查进程**（`process_agent_hint`）与
**屏幕模式匹配**（detection manifest，如 `live_prompt_box`）**观测**每个 pane 里跑的是哪种 agent、
处于什么状态，并**聚合**来自多个**权威来源**的上报。它**不铸造 agent 身份**、不决定业务成败、
无 agent 级 restart 策略。

关联：`Host Runtime`、`agent identity authority`、`runtime fact source vs business completion authority`。

### agent identity authority（agent 身份权威）

判定「某 pane 里是哪个具体 agent 实例、归属哪个 project/slot/provider/generation」的一方，本项目中
是 **CCB**（经源码验证）。Herdr 侧 `Agent` 仅是种类枚举、无实例 id 且 respawn 即清；CCB 通过
`report_pane_agent` 把身份**报告**给 Herdr——这与 agent 自带的 hook 上报是**对等来源**，是 Herdr
设计中受支持的正规路径，**非需删除的历史补丁**。

关联：`physical pane owner`、`observational state aggregator`、`managed 模式`、`Runtime Binding`。

### 观测聚合协作模型（Observational-Aggregation Cooperation）

WezTerm / Herdr / CCB 三者配合方式的目标模型，锚点 **「CCB 权威 · Herdr 观测 · WezTerm 呈现」**：
CCB 是身份与业务完成权威、独立上报状态（`source=ccb`）；Herdr 是观测式状态聚合器，从对等来源
接收状态、以原生 events 对外发布；WezTerm 是呈现层与 attach 落点，非与 Herdr 竞争的 mux。它是
ADR 0001「三层权威边界」在**配合方式**层的落地，纠正了原 v2「下放给 Herdr」的方向性误设。

关联 ADR：`docs/adr/0002-观测聚合协作模型.md`。
关联：`observational state aggregator`、`agent identity authority`、`Frontend Surface`。

---

## 运行时锚点与身份

### runtime generation（运行时代次）

单调递增的整数，标识一次运行时实例化。用于事件去重与状态归属校验：`pane_id` 变化或
`runtime_generation` 变化都视为新的运行时所有权，旧状态不得沿用。

关联：`Runtime Binding`、`project_view`。

### Runtime Binding（运行时绑定）

CCB 持久化的、指向某次 Herdr 运行时实例的唯一锚点（`.ccb/runtime/herdr-binding.json`）。
用于重连、teardown、`project_view` 投影与事件去重。可含可选 `frontend` 段记录前台事实
（如 WezTerm mux 是否可用、workspace 寻址目标）。

关联：`runtime generation`、`Frontend Surface`。

### managed 模式（受管模式）

Native Windows 上正确的分层：由 CCB 创建并标识 pane（Host Runtime 承载、CCB 标识身份），
而非让前台配置（如 WezTerm `default_prog`）直接长期拉起 provider CLI（后者会退化为
`attached` 模式，绕过 CCB 的身份与恢复权威）。

关联：`physical pane owner`、`Frontend Surface`。

---

## 前台专有词汇

### WezTerm workspace（WezTerm 工作区）

WezTerm 的一等寻址原语，用于按名称定位一组窗口/tab。相比易变的 `window_id`（进程重启即
失效），workspace 名可作为重连后的稳定寻址锚点。计划用作「单一权威 mux + 寻址 tab」升级的
寻址主键。

关联：`Frontend Surface`、`Runtime Binding`。

### attach（附着）

把可见前台连接到某个既存运行时 session 的动作。在 Native Windows 上通过 WezTerm 承载
（`wezterm cli spawn -- herdr session attach <session>`）。attach 是用户体感的唯一入口，其
成败必须可观测，不得静默失败。

关联：`Frontend Surface`、`Host Runtime`。
