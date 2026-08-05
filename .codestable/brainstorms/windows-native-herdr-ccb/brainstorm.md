---
doc_type: brainstorm
slug: windows-native-herdr-ccb
created: 2026-07-30
status: active
summary: 探索以 CCB v8.5.2 为基底、借助 Herdr 实现 Native Windows CCB 全功能的可行路径
tags: [windows, native-windows, herdr, ccb-v8.5.2, multiplexer, epic-candidate]
---

# Native Windows CCB via Herdr

> 创意空间 | 2026-07-30 | 下一步：cs-epic

## 出发点

owner 提出两个前置要求：

- 先暂停 `windows-rmux-ux-parity-hardening` 线，不继续沿 rmux/WezTerm UX parity hardening 推进。
- 以 CCB 最新版本 `v8.5.2` 为基底，研究是否可以利用 Herdr 在 Native Windows 平台实现 CCB 全功能。

本地事实需要单独标注：当前工作区 `package.json` 显示 `8.2.1`，但 git tag 已存在 `v8.5.2`，且 `v8.5.2:package.json` 为 `8.5.2`。因此后续若进入实现，应先从 `v8.5.2` tag 或等价 release 基线起步，不应把当前未同步工作区直接视为基底。

## 聊过的方向

### 方向 A：Herdr 作为 CCB 的 Native Windows mux backend

CCB 保持现有控制面、provider 隔离、ask/pend/watch、Mobile、Config UI、更新与诊断体系；Herdr 只承担 Native Windows 下的 session/pane/PTTY/布局/attach 运行时。

价值：最符合 KISS 和最小替换面，避免把 CCB 的 agent 协作控制面重写成 Herdr 插件体系。

代价：需要写一个稳定的 `MuxBackend`/`PaneRuntime` 适配层，把 CCB 当前 tmux/rmux 语义映射到 Herdr socket API。Herdr Windows beta 的不支持项必须显式降级，不能承诺为 fully supported。

### 方向 B：CCB 作为 Herdr 插件或插件集合

把 CCB 的 agent orchestration 投影到 Herdr 插件系统中，让 Herdr 成为用户可见主 shell，CCB 成为控制面/agent 插件。

价值：能复用 Herdr 的 agent detection、session restore 和 UI 机制，用户体验可能更 native。

代价：边界更重。CCB 现有能力不是单纯终端插件：它包含 provider 私有 home、completion 判定、daemon、Mobile relay、config/update/support tier、bounded recovery 等。直接插件化容易出现“双控制面”和“双状态源”。

### 方向 C：复制或嵌入 Herdr Windows terminal primitive

只借用 Herdr 的 ConPTY/Windows pane 低层实现，继续保留 CCB 自己的 mux 行为。

价值：理论上控制权最大。

代价：违反 DRY，后续要跟 Herdr upstream 行为漂移对齐；也会绕开 Herdr 已经提供的 socket API、session state 和 restore 机制。除非 socket API 无法满足 CCB 基础语义，否则不应作为首选。

## 当前倾向

倾向于选择方向 A：Herdr 作为 Native Windows mux backend，CCB 继续作为 control plane 和 provider runtime authority。

这不是“把 Herdr 接上就全功能完成”，而是一个多 feature epic：先验证 Herdr 是否能满足 CCB 的最小 backend contract，再逐步恢复 CCB 的全部 public workflow。第一阶段不应该承诺 stable Windows support，只能以 beta/experimental support tier 起步。

## 已敲定的点

- 已确认：暂停 `windows-rmux-ux-parity-hardening`，不继续在 rmux UX parity 线上投入。
- 已确认：目标基底是 CCB `v8.5.2`，不是当前工作区显示的 `8.2.1` 状态。
- 已确认：这是多 feature 规模，适合后续拆 `cs-epic`，不适合塞进单个 feature。
- 倾向：优先把 Herdr 作为 backend adapter，而不是把 CCB 重写成 Herdr 插件。
- 约束：Native Windows “全功能”应定义为 CCB public workflow parity；Herdr 当前不支持或 beta 的能力必须在 CCB support projection 中明确表达，不能伪装成 Linux/macOS fully supported。

## 2026-08-04 外部项目 / Herdr UI 观察

owner 在外部项目中从 Herdr 内置 PowerShell 直接运行 `.\ccb8.cmd`：没有出现 `.ccb/ccb.config` 中定义的两个 agent CLI 对话界面，只看到一批 `cmd` 窗口短暂闪现后关闭。闪退前一瞬间，Herdr 左侧 agents 面板中曾出现 `claude` 字样。该现象目前是 owner 观察，尚未形成可审计 transcript，需要后续区分“agent pane 已创建但 provider 命令立即退出”和“provider 没有被 CCB runtime 正确启动”。

对照观察：在 Herdr 中手动启动 `claude` 表现正常，但这只证明 Herdr 可以承载 Claude CLI 交互；它不证明 CCB 的 provider home/env、completion、ask/pend/cancel、bounded recovery、Mobile/Config UI 等 control-plane 能力已经接入。

这条观察把 sidebar 关系提升为后续设计问题：

- 方向 1：CCB full-feature sidebar 替代 Herdr 左侧面板。价值是 CCB 语义最完整；风险是和 Herdr 原生 agent/session UI 形成双 UI、双状态源。
- 方向 2：Herdr 左侧面板替代 CCB sidebar。价值是体验更 native；风险是 Herdr agent detection 不能直接成为 CCB provider/completion/runtime authority。
- 方向 3：Herdr 负责原生 pane/agent 面板展示，CCB sidebar 能力降为 Herdr 可消费的 project surface / layout projection。价值是边界清晰：Herdr owns terminal/UI shell，CCB owns provider/control-plane truth；代价是需要定义 CCB pane layout config 到 Herdr workspace/tab/pane 的稳定转换和状态回写口径。

当前倾向：优先探索方向 3，而不是让任一 sidebar 全面替代另一方。关键事实问题是 Herdr 是否能接受 CCB 的 pane layout 配置，或是否能稳定消费 CCB 转换后的 workspace/tab/pane layout 与 agent metadata。

## 2026-08-05 配置与生命周期权威方案 A/B/C

本节的 A/B/C 是针对“配置与生命周期由谁拥有”的第二组候选，不同于上文最初的 backend 技术路线命名。

### 方案 A：Herdr workspace/pane 配置取代 `ccb.config`

设想：Herdr 的 workspace/tab/pane、命令与布局直接决定 CCB 启动哪些 agent；CCB 不再维护独立的 `.ccb/ccb.config`。

优势：

- 用户只维护一份 Herdr 侧拓扑，启动入口直观。
- pane 布局与实际终端状态天然一致，避免重复描述窗口和分屏。

主要问题：

- Herdr 终端拓扑不能完整表达 CCB 的 agent/provider/role/model/thinking、provider profile、凭证继承、MCP、managed home、workspace/worktree、heartbeat、loop capacity、completion/cancel/queue/recovery 等编排语义。
- 如果把这些 CCB 语义全部塞入 Herdr pane metadata，实质上只是把 `ccb.config` 迁移成一套表达能力更弱、与 Herdr 强耦合的新配置。
- pane 被用户手动删除时，无法稳定区分“修改持久配置”“停止 agent”与“临时关闭 UI”。
- CCB 会失去独立运行于 tmux/rmux/headless/Mobile 等其他承载面的可移植性。

可保留的窄化形式是 `A-lite`：

- 显式执行 `ccb config import-herdr`，把当前 Herdr 布局转换为 CCB 配置草稿。
- 或通过 `ccb start --adopt-herdr-layout` 绑定已有 pane，但明确标为 attached/degraded 模式。
- 导入或绑定后，CCB 仍需生成自己的规范化配置和运行态；Herdr observed state 不能长期作为 CCB 配置权威。

判断：适合 onboarding、导入和临时绑定，不适合作为长期主架构。

### 方案 B：CCB 退化为 Herdr 插件

设想：Herdr 成为唯一用户可见 shell 和生命周期 owner；CCB 作为 Herdr 插件提供 agent orchestration。

优势：

- 可以获得最原生的 Herdr UX：从 sidebar 启动、查看状态、ask/cancel/restart、跳转 pane 和打开 Config UI。
- 可以直接复用 Herdr session、pane、agent detection 和 UI 扩展能力。

主要问题：

- CCB 不只是终端插件。它还拥有 `ccbd`、provider 私有 home/auth/session、dispatcher、job/queue、completion、cancel、Mobile relay、Config UI、update、doctor/support tier 和 bounded recovery。
- 把完整生命周期交给 Herdr，需要把大部分 CCB daemon 和持久状态机重写进 Herdr plugin runtime，迁移面与长期耦合都很大。
- Herdr session/pane 恢复与 CCB provider/job 恢复不是同一语义；插件启动成功不能代替 CCB 的原子 mount、completion 和 durable state 保证。
- CCB 将难以脱离 Herdr 独立运行，并可能形成 Herdr runtime state 与 CCB runtime state 双控制面。

可保留的窄化形式是 `B-lite`：

```text
Herdr CCB Plugin
├── ensure / attach CCB
├── 展示 project / agent / job 状态
├── 调用 ask / cancel / restart / config
└── 跳转到对应 pane
```

插件只作为 CCB API 客户端和原生 UI，不拥有 provider、job、completion 或 recovery 状态。

判断：适合作为可选 Herdr-native shell，不适合作为 CCB 内核或生命周期权威。

### 方案 C：非对称双向感知

原始设想：Herdr 知道自己承载了 CCB，CCB 知道自己运行在 Herdr 中；配置互通，但双方保留独立配置。

分析后建议将其收紧为 `C2：非对称联邦模式`：

- 双方交换意图、标识和运行证据。
- 每个配置域只有一个写入者。
- 不做配置文件自动双向合并，不让 observed runtime state 静默覆盖 source config。

建议权威矩阵：

| 领域 | 权威方 |
|---|---|
| agent/provider/role/model/MCP | CCB |
| provider home/auth/session | CCB |
| job/completion/cancel/queue | CCB |
| 期望的项目 agent 拓扑 | CCB |
| workspace/tab/pane/ConPTY 实例 | Herdr |
| 实际尺寸、焦点和 Herdr UI 状态 | Herdr |
| Herdr 主题、快捷键、shell 和插件 | Herdr |
| pane/provider recovery 决策 | CCB |
| session/layout primitive restore | Herdr |

核心信息流：

```text
CCB desired topology ──投影──> Herdr physical topology
CCB runtime truth    <──证据── Herdr observed state
```

CCB 可向 Herdr 投影不含敏感信息的 pane metadata：

```json
{
  "ccb_project_id": "...",
  "ccb_config_revision": "...",
  "ccb_agent": "reviewer",
  "ccb_provider": "codex",
  "ccb_role": "agentroles.code_reviewer",
  "lifecycle_owner": "ccb",
  "recovery_owner": "ccb"
}
```

Herdr 可向 CCB 返回物理运行证据：

```json
{
  "workspace_id": "...",
  "tab_id": "...",
  "pane_id": "...",
  "process_state": "running",
  "dimensions": [160, 48],
  "focused": true
}
```

API key、token、provider auth 文件、完整 provider profile、dispatcher/job payload 等敏感或内部状态不得进入 Herdr metadata。

### C2 的冲突策略

Herdr session/agent restore 与 CCB bounded recovery 可能同时恢复同一个 provider。CCB-owned pane 必须明确 `recovery_owner=ccb`；如果 Herdr 不能按 pane 禁用 agent process resume，则 Native Windows supported 路径需要禁用 Herdr agent auto-restore，只允许 Herdr 恢复 session/layout primitive，由 CCB 重新绑定并决定是否恢复 provider。

用户在 Herdr 中手动拖动、关闭或新增 pane 时，应通过显式模式决定语义：

| 模式 | 行为 |
|---|---|
| `managed` | `ccb.config` 拥有期望拓扑；reload/reconcile 恢复 CCB 布局 |
| `attached` | CCB 绑定现有 Herdr pane，不修改布局，能力明确降级 |
| `import` | 用户显式把当前 Herdr 布局转换为 CCB 配置草稿 |

不得自动把每次 Herdr UI 操作写回 `.ccb/ccb.config`。

### 当前推荐

当前讨论推荐：

1. 以 `C2` 作为核心集成架构。
2. 以 `B-lite` 作为可选 Herdr 原生插件/UI。
3. 以 `A-lite` 作为显式导入或绑定模式。
4. 保留 `.ccb/ccb.config`，CCB 定义期望 agent 拓扑，Herdr 负责物理终端实现。
5. 双方通过版本化 metadata 和运行证据互相感知，不自动互改配置。
6. CCB-owned pane 必须只有一个 lifecycle/recovery owner。

以上是分析后的推荐，owner 尚未正式拍板。若选定 `C2`，该决策满足难回退、非显然且存在真实权衡的 ADR 条件，应通过 `cs-domain` 单独记录，不在 brainstorm 中冒充已确认 ADR。

## 遗留问题 & 下一步

- 需要锁定 Herdr 具体版本、安装方式和 socket API schema，避免依赖未稳定文档。
- 需要确认 Herdr socket API 是否覆盖 CCB 需要的 pane create/split/resize/focus/send/capture/kill/session restore/agent status 语义。
- 需要做 5-30 分钟 spike：用 Python 调 Herdr socket API 创建 session、启动一个 provider CLI pane、发送输入、捕获输出、重启后恢复 session。
- 若 spike 通过，进入 `cs-epic` 规划 Native Windows Herdr backend；若失败，记录具体缺口，再决定补 Herdr upstream、保留 rmux 线，或缩小 Native Windows 支持范围。
- 需要新增/补充 UI integration spike：在真实 Herdr UI client 中运行外部项目 `.\ccb8.cmd`，记录 pane/window 变化、短暂 `cmd` 窗口来源、Herdr agents 面板状态、CCB runtime state、provider stdout/stderr 与退出码。
- 需要验证 Herdr layout/metadata 能力：能否由 CCB 创建或转换 workspace/tab/pane layout，能否标注 agent/provider/role，Herdr sidebar 是否只读展示还是可触发 CCB action。
- 需要 owner 确认是否正式选择 `C2 + B-lite + A-lite`，以及是否随后通过 `cs-domain` 写 ADR。
- 需要在 design 中定义版本化 integration protocol、managed/attached/import 模式、配置 revision、pane binding 和冲突解决规则。

## 2026-08-05 Herdr v0.8.0 评估 + spike 采集结果综合

### Herdr v0.8.0 (2026-08-04 发布) 关键变化

**直接影响 CCB 集成判断的变化：**

| 领域 | v0.8.0 变化 | 对 CCB 的影响 |
|------|------------|--------------|
| 集成报告 | 简化 Kimi / Qoder / Cursor 的 lifecycle / session reporting | **正面**：Herdr 正在标准化第三方集成的状态报告模式。CCB 可以直接复用这套模式，而非自己发明 |
| 插件系统 | 支持从插件根目录解析相对路径命令 | **正面**：B-lite 插件的技术可行性提升 |
| API | `api workspace close` 在关闭最后一个 tab 时自动关闭 workspace | **中性**：CCB 的 pane 生命周期管理需要注意这个行为 |
| Session restore | Grok CLI 原生 session restore 集成 | **正面**：说明 Herdr 愿意为 AI 工具提供原生集成，CCB 可以作为下一个 |
| Sidebar | 改进 worktree 层级和排序 | **中性**：CCB 如果要做 sidebar 集成，底层能力更成熟 |
| 性能 | 跳过隐藏 PTY 渲染、spinner→静态标记 | **正面**：更多 CCB agent pane 时渲染压力更小 |
| 许可证 | 切换为 Apache-2.0 | **正面**：消除许可证不确定性 |

**尚未出现在 v0.8.0 的能力（CCB 仍需要的）：**

- 原生插件 SDK / API（插件目前仅为 CLI 包装）
- 按 pane 禁用 agent auto-restore（C2 冲突策略要求）
- Herdr metadata 中标注 `recovery_owner` / `lifecycle_owner`（C2 信息流需要）
- CCB 可消费的 pane metadata write API（投影 CCB agent 信息到 Herdr）

### Spike 采集最终结果（run-20260805-203140）

| 指标 | 结果 |
|------|------|
| `classification` | `mounted-with-herdr-panel-observation` |
| `command_failure_count` | **0** |
| `ping_all_success` | true |
| `layout_materialization_complete` | true |
| 执行维度 | 11/11 全覆盖 |
| ccbd health | `last_failure_reason: null`, phase=mounted, generation=44 |
| startup state files | 5/5 完整采集（含 lease/keeper/lifecycle） |

### 修复闭环确认

| 问题 | 根因 | 修复 |
|------|------|------|
| `ccb8 ps` 路由错误 | PowerShell `[char[]]` 参数拆分 | `@($CcbArgs)` + char-array 检测 |
| ccbd 多实例并发 PermissionError | Windows `file_lock()` 空操作 | `msvcrt.locking()` 实现跨进程互斥 |
| stale lifecycle StartupFenceError | 崩溃后 phase 残留 "mounted" | `dataclasses.replace()` + dead PID 检测 |
| prestart cleanup 残留进程 | kill -f 超时后未验证 | 二次 process sweep + installed PID 保护 |
| foreground attach 阻塞/崩溃 | `herdr session attach` 在 Herdr UI 中无 terminal | timeout 5s + 非致命降级 |
| startup state files 2/5 | `runtime_state_root` 路径重复 project_id | 直接 `$runtimeStateRoot\ccbd` |

### 综合推荐工作方向（更新版）

基于 Herdr v0.8.0 能力 + spike 证据 + 修复经验，以下按优先级排列：

#### P0 — 立即：部署验证闭环

- [ ] 在 Herdr UI 中安装/升级到 **Herdr v0.8.0**
- [ ] 重新运行默认全量 spike 采集，验证 v0.8.0 的 session reporting 简化是否影响 CCB 的 `herdr-api-snapshot-ccb-namespace`
- [ ] 验证已修复的 file_lock + prestart cleanup 在多次 `ccb8.cmd` / `ccb8.cmd --kill f` 压力下稳定

理由：Herdr v0.8.0 的 "简化 lifecycle/session reporting" 可能改变 CCB 的 `herdr status server --json` 输出格式——需要先确认兼容性。

#### P1 — 本迭代：C2 信息流落地

- [ ] **CCB → Herdr 投影**：在 CCB pane 创建时，通过 Herdr `set_pane_identity` / token 写入 `ccb_agent`, `ccb_provider`, `lifecycle_owner=ccb` 等 metadata（v0.8.0 插件系统已支持相对路径命令，token 写入路径应更稳定）
- [ ] **Herdr → CCB 证据**：标准化从 `herdr api snapshot` 提取物理 pane 证据的路径（spike 已验证可行）
- [ ] **Bridge config**：定义 `ccb-herdr-bridge.json` 的 v1 schema（核心字段：`project_id`, `herdr_session`, `pane_bindings[]`, `config_revision`）

理由：这两条信息流是 C2 联邦模式的最小可行骨架。spike evidence 已经验证了"从 Herdr 读"的方向，"写到 Herdr"是下一步。

#### P2 — 短期：B-lite 原型 + A-lite 导入

- [ ] **B-lite**：写一个最小 Herdr 插件 `ccb`，展示 `ccb status` / `ccb ps` 输出到 Herdr sidebar
  - v0.8.0 的插件改进（相对路径命令解析）降低了门槛
  - 最低可行版本：只读展示，不写入
- [ ] **A-lite**：实现 `ccb config import-herdr`——读取当前 Herdr session 的 workspace/pane 拓扑，生成 `ccb.config` 草稿

理由：这两个是 C2 的补充模式。B-lite 给 Herdr 用户一个原生入口看到 CCB 状态；A-lite 降低 onboarding 成本。

#### P3 — 远期：C2 冲突策略 + 正式 ADR

- [ ] 在 Herdr 侧确认是否能按 pane 禁用 agent auto-restore（C2 冲突策略前提）
- [ ] 定义 `managed` / `attached` / `import` 三种模式的正式行为契约和状态机
- [ ] 通过 `cs-domain` 写 ADR，固化为跨版本的架构决策

### 和原有推荐的对齐

原推荐（2026-08-05）是 `C2 + B-lite + A-lite`。Herrd v0.8.0 **没有推翻这个方向，而是让它更容易落地**：

- C2 的信息流（CCB→Herdr 投影 + Herdr→CCB 证据）在 v0.8.0 的集成简化趋势下更自然
- B-lite 的插件可行性因 v0.8.0 的插件改进而提升
- A-lite 的导入模式仍然是最低风险的 onboarding 路径

唯一需要警惕的是：v0.8.0 的 "简化 session reporting" 可能改变我们已验证的 `herdr status server --json` 输出格式——这是 P0 验证的首要原因。
