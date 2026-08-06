# ADR-001 · C2 非对称联邦架构：CCB × Herdr Native Windows 集成

- **状态**：accepted
- **日期**：2026-08-06（决策于 2026-08-05 brainstorm，2026-08-06 Epic planning gate 正式确认）
- **决策者**：owner
- **领域**：architecture, integration, native-windows
- **取代**：无（首次架构决策）
- **关联**：
  - Epic: `.codestable/epics/windows-native-herdr-ccb.md`（DEC-1, DEC-5, DEC-7）
  - Brainstorm: `.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`
  - Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`

## 背景

CCB v8.5.2 在 Native Windows x64 上需要 terminal multiplexer backend。经过 2026-07-30 至 2026-08-06 的探索、spike、设计和实现，确认 Herdr 作为 Native Windows multiplexer backend 在工程上可行。关键问题不是"能不能接"，而是"谁拥有什么权威"——CCB 和 Herdr 都拥有 agent state、session lifecycle 和 pane recovery 的概念，必须在架构层面划清边界，避免双控制面和双状态源。

## 决策

采用 **C2 非对称联邦模式**：CCB 和 Herdr 各自保留独立配置和核心权威，通过版本化 metadata 和运行证据互相感知，不做自动双向配置合并。

核心原则：
- 每个配置域只有一个写入者
- Herdr observed runtime state 不静默覆盖 `.ccb/ccb.config`
- CCB-owned pane 只有一个 lifecycle/recovery owner

### 权威矩阵

| 领域 | 权威方 | 理由 |
|---|---|---|
| agent / provider / role / model / MCP 定义 | **CCB** | CCB 是 agent 编排的 source of truth；Herdr 不知道 Codex/Claude/Gemini 等 provider 的语义 |
| provider home / auth / session | **CCB** | 凭证隔离、私有 HOME、session binding 是 CCB 核心安全边界 |
| job / completion / cancel / queue | **CCB** | completion authority 是 CCB 的 correctness 基础；Herdr agent state 仅 diagnostics |
| 期望的项目 agent 拓扑 | **CCB** | `.ccb/ccb.config` 是 topology 的 canonical source |
| pane / provider recovery 决策 | **CCB** | bounded recovery + 90s probation + 3 次 circuit threshold |
| workspace / tab / pane / ConPTY 实例 | **Herdr** | 物理终端 primitive 的创建、分割、布局、关闭 |
| 实际尺寸、焦点和 UI 状态 | **Herdr** | 终端用户交互的物理事实 |
| 主题、快捷键、shell 和插件 | **Herdr** | Herdr UX 配置的独立域 |
| session / layout primitive restore | **Herdr** | 终端 session 和布局的物理恢复 |

### 信息流

```
CCB desired topology ──投影──> Herdr physical topology
     (set_pane_identity tokens: ccb_agent, ccb_role, ccb_provider,
      lifecycle_owner=ccb, recovery_owner=ccb, ccb_project_id, …)

CCB runtime truth    <──证据── Herdr observed state
     (describe_pane / list_panes_by_user_options:
      pane_id, workspace_id, terminal_title, agent_status, tokens, …)
```

**CCB → Herdr 投影**（`set_pane_identity`）

CCB 在创建 pane 后写入以下 metadata tokens：

| Token | 含义 | 敏感级别 |
|---|---|---|
| `ccb_project_id` | CCB 项目标识 | 低 |
| `ccb_config_revision` | 配置版本号 | 低 |
| `ccb_agent` / `ccb_agent_label` | Agent 标签 | 低 |
| `ccb_provider` / `ccb_provider_kind` | Provider 标识 | 低 |
| `ccb_role` | Agent 角色 | 低 |
| `ccb_slot` | Slot key | 低 |
| `ccb_window` / `ccb_logical_window` | 逻辑窗口名 | 低 |
| `ccb_sidebar_instance` | Sidebar 实例标识 | 低 |
| `ccb_session_id` | CCB session ID | 低 |
| `ccb_namespace_epoch` | Namespace epoch | 低 |
| `ccb_managed_by` | 管理层标识（如 `ccbd`） | 低 |
| `lifecycle_owner` | **固定为 `ccb`** | 低 |
| `recovery_owner` | **固定为 `ccb`** | 低 |

**不得**进入 Herdr metadata 的字段：API key、token、provider auth 文件、完整 provider profile、dispatcher/job payload。

**Herdr → CCB 证据**（`describe_pane` / `list_panes_by_user_options`）

CCB 从 Herdr 回读物理运行证据：

- `pane_id`、`workspace_id`、`session_name`
- `terminal_title`、`agent_status`
- `pane_dead` 标志
- 所有 `ccb_*` 前缀的 token 值

### 三种运行模式

| 模式 | 行为 | 实现状态 |
|---|---|---|
| `managed` | `.ccb/ccb.config` 拥有期望拓扑；reload/reconcile 恢复 CCB 布局。CCB 创建 Herdr workspace/pane。 | ✅ 已实现（默认模式） |
| `attached` | CCB 绑定现有 Herdr pane，不修改布局，能力明确降级。pane 不由 CCB 创建/销毁。 | 🟡 ADR 记录预期语义，精确 contract 留给后续 feature |
| `import` | 用户显式把当前 Herdr 布局转换为 CCB 配置草稿。生成 `.ccb/ccb.config` candidate，不自动激活。 | 🟡 ADR 记录预期语义（对应 Epic ITEM-4 A-lite） |

模式切换必须是**显式用户操作**，不得自动把 Herdr UI 操作写回 `.ccb/ccb.config`。

### 冲突策略

1. **Recovery owner 唯一**：CCB-owned pane 必须标注 `recovery_owner=ccb`。Herdr agent auto-restore 只有 `disabled` 可进入 CCB recovery-capable path。`observe-only` / `unsupported` / `unknown` 一律 fail closed。

2. **Herdr auto-restore 全局 disabled**：接受全局 disabled 模式作为 CCB recovery 前提。非 CCB agent 也无法使用 Herdr 原生 session restore，属于已知的跨工具体验限制。不向 Herdr upstream 提 per-pane disable feature request。若后续 Herdr 原生支持 per-pane disable，可通过后续 feature 升级 recovery capability。

3. **不自动互改配置**：Herdr UI 操作（拖动、关闭、新增 pane）不自动写回 `.ccb/ccb.config`。CCB config 变更不自动修改 Herdr workspace/tab/pane 结构。

4. **Pane lifecycle 权威**：CCB-owned pane 的创建、销毁、命令注入由 CCB 控制。用户在 Herdr 中手动关闭 CCB-owned pane 后，CCB 的 `is_alive` 检测到 pane 不存在时清理内部状态。

5. **Completion authority**：Herdr 的 agent detection / agent_status 仅作为 diagnostics 输入，不作为 provider completion 的判定依据。各 provider 的 completion contract 由 CCB 独立验证。

## 后果

### 正面

- **边界清晰**：CCB 和 Herdr 各自拥有明确的权威域，不存在双控制面冲突
- **可移植性**：CCB 保持独立于 Herdr 的运行能力，可在 tmux/rmux/headless/Mobile 等其他承载面运行
- **fail-closed**：Herdr capability 缺失时，`HerdrCapabilityGate.require_supported()` 抛出 `MuxCommandErrorV2`，不做静默 fallback
- **12 个 roadmap item 已实现验收**：证明了 C2 架构在工程上的可行性

### 负面

- **Herdr auto-restore 全局 disabled**：非 CCB agent 无法使用 Herdr 原生 session restore
- **managed 模式耦合**：CCB 通过 `set_pane_identity` tokens 依赖 Herdr 的 metadata 能力；若 Herdr 改变 token 机制，CCB adapter 需要跟进
- **不支持 live handoff**：Herdr Windows beta 的 `live_handoff` 能力不可用（`capabilities.live_handoff: false`）

### 风险缓解

- `HerdrSocketClient.server_info()` 内置 `EXPECTED_HERDR_API_SCHEMA` version gate + schema mismatch 检测
- `HerdrCapabilityGate` fail-closed：缺 evidence → `MuxCommandErrorV2(category="unsupported")`
- `herdr_supportability_projection.compute_projection()` 纯函数 fail-closed：任何 gate 不通过 → tier 降级

## 替代方案

### 方案 A：Herdr 完全替代 CCB 配置（已拒绝）

将 `.ccb/ccb.config` 替换为 Herdr workspace/pane 拓扑。问题：Herdr 终端拓扑不能完整表达 CCB 的 agent/provider/role/model/MCP/provider home/completion/cancel/recovery 等编排语义。保留窄化形式 A-lite 作为显式导入模式。

### 方案 B：CCB 退化为 Herdr 插件（已拒绝）

将 CCB 完整生命周期交给 Herdr。问题：CCB 不只是终端插件——它拥有 daemon、job/queue、completion、Mobile relay、Config UI、update、doctor/support tier 和 bounded recovery。全部重写进 Herdr plugin runtime 迁移面过大。保留窄化形式 B-lite 作为可选 Herdr sidebar 只读插件。

## 相关 ADR

无。本 ADR 是 Native Windows Herdr 集成的首次架构决策。
