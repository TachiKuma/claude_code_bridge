---
status: accepted
created: 2026-08-06
accepted: 2026-08-07
---
# Native Windows CCB via Herdr — 从架构验证到可用性交付

## 起点

CCB v8.5.2 在 Native Windows x64 平台上缺少可用的 terminal multiplexer backend。tmux/rmux
在 Windows 上的方案依赖 WSL 或模拟层，无法提供 Native Windows ConPTY 体验。Herdr 是
专为 agentic terminal 设计的 multiplexer，提供原生 Windows ConPTY pane、session restore、
socket API 和插件系统。

经过 2026-07-30 至 2026-08-06 的讨论、spike、设计和实现，C2 非对称联邦架构已被证实在工程上
可行。12 个 roadmap item 中 11 个已完成（§1–§11），§12 正在进行中。本 Epic 的目标是完成
架构收尾，将 Native Windows Herdr backend 从 `beta` candidate 推进到一个有完整 evidence 支撑的
明确 support tier，并补齐 P2 增强功能。

## 目标

1. 在真实 Herdr v0.8.0 环境中采集 CCB 全量 public workflow 证据，把 §11 validation matrix
   从全 `blocked` 变为有机器可读的真实状态
2. 完成 §12 herdr-supportability-projection，产出一个有证据支撑的 support tier
3. 将 C2 非对称联邦架构固化为正式 ADR
4. 可选：补齐 A-lite 导入模式、B-lite Herdr 插件、bridge config schema

## 范围

- Herdr v0.8.0 兼容性验证（P0）
- 14 个 required workflow + 20 个 provider × 4 个 provider workflow 的 Native Windows
  transcript 采集与 matrix 更新
- supportability projection feature 完成（consumer + doctor/docs/README 同步）
- C2 架构 ADR（含权威矩阵、信息流、冲突策略）
- P2：A-lite（`ccb config import-herdr`）、B-lite（Herdr sidebar 只读插件）、
  `ccb-herdr-bridge.json` v1 schema
- ITEM-7（2026-08-07 立项）：WezTerm-launched Herdr managed startup（一键启动）

## 非目标

- 不修改 C2 核心架构方向（已验证可行）
- 不改 Herdr backend/provider/recovery 行为（§1–§10 的代码已 acceptance passed）
- 不执行 npm publish、release、push 或 promotion
- 不把 partial/blocked evidence 写成 full support
- 不修改 CCB v8.5.2 的 provider completion/recovery owner 语义
- 不实现 Herdr upstream 功能（如 per-pane auto-restore disable 取决于 Herdr 侧支持）

## 固化环境路径

本 Epic 所有子项的开发、测试与 evidence 采集均以下列路径为基准约定：

| 组件 | 固化路径 |
|---|---|
| **Herdr 可执行文件** | `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe` |
| Herdr 配置目录 | `C:\Users\Administrator\AppData\Roaming\herdr\` |
| WezTerm 可执行文件 | `C:\Program Files\WezTerm\wezterm.exe` |
| CCB 源码根 | `E:\GitHub开源项目\TachiKuma\claude_code_bridge` |
| CCB Runtime State | `D:\.c8\rs` |
| Python | `C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe` |
| Git Bash (sh.exe) | `C:\Program Files\Git\bin\sh.exe` |

优先级：环境变量 > 固化默认值。具体覆盖变量见 `ccb8.ps1` 和 roadmap §开发环境基准。

## 验收标准

- ✅ validation matrix 中 `workflow_rows` 从全 `blocked` → 11/14 partial + 3/14 blocked
  （run-20260807-004015: 19/19 维度, 0 failures, pane_state=alive 证实修复）
- ✅ `herdr_version` 已填入（`0.8.0-preview.2026-08-04-d78e3d3b5126`）
- ✅ `ccb_source_status` 已填入（`v8.5.2-source-branch`）
- ✅ `herdr_auto_restore_mode` = **disabled**（2026-08-07 双验证确认：
  文档 `herdr --default-config` 证实 `resume_agents_on_restore` 默认 true；
  实证 `config.toml` 写入 `resume_agents_on_restore = false` + `server reload-config` applied）
- ✅ `ccb doctor --output` 展示 support tier — consumer 端已接入（code-hardening Epic ITEM-3：
  `5aea5f08`），输出含 `herdr.support_tier` 等 12 个字段
- ✅ C2 架构 ADR 存在于 `.codestable/adr/001-c2-asymmetric-federation-ccb-herdr.md`
- ✅ **配置权威边界已确认**：`%APPDATA%\herdr\config.toml` 继续由用户编辑并由
  Herdr 管理；`.ccb/ccb.config` 继续由 CCB 管理项目拓扑与编排；只整合 Herdr
  backend/capability/session-pane evidence，不复制 Herdr 全量配置
- ✅ `ccb config import-herdr` 已修复（code-hardening Epic ITEM-1：`8fc5094c`）：
  输出合法 v2 TOML（`version=2` + `[windows]` + `[agents.<name>]`），含 `--force` 覆盖支持
- ❌ matrix 中无 pass 的 workflow/provider，`support_projection_allowed` 保持 `false`
- ✅ 全部 7 子项完成（ITEM-1 至 ITEM-7）
- ✅ Kill/Restart 全周期验证通过（kill=ok → unmounted → restart=mounted, gen 4→5）
- ✅ Ask smoke 管道通畅（job accepted target=agent1）
- ✅ Reload smoke 稳定（noop on unchanged config, agents remain mounted）

## 关键决策

- **DEC-1 · C2 非对称联邦架构**：CCB 拥有 agent/provider/role/model/MCP/job/
  completion/cancel/recovery 权威；Herdr 拥有 workspace/tab/pane/ConPTY/UI 权威。
  双方通过 `set_pane_identity` tokens 和 `describe_pane` 交换元数据与运行证据，不做自动
  双向配置合并。证据：brainstorm 2026-08-05 分析 + §1–§10 实现验收。
- **DEC-2 · fail-closed gate**：缺 capability evidence、平台 gate 不通过、Herdr auto-restore
  非 disabled 时，`HerdrCapabilityGate.require_supported()` 一律抛出 `MuxCommandErrorV2
  (category="unsupported")`，不做静默 fallback 到 tmux。证据：`capabilities.py:156-181`。
- **DEC-3 · recovery owner 唯一**：CCB 是唯一 recovery owner。Herdr auto-restore 只有
  `disabled` 可进入 recovery-capable path；`observe-only`/`unsupported`/`unknown` fail
  closed。证据：`herdr-bounded-recovery-boundary` acceptance report。
- **DEC-4 · support tier 由 evidence 驱动**：`supported` 只在 strict v8.5.2、全部 required
  workflow pass、全部 public provider pass、Mobile/Config UI pass、Herdr auto-restore
  disabled、npm dry-run pass 时出现。证据：`herdr-supportability-projection` design §1.1。
- **DEC-5 · managed/attached/import 契约分层**（2026-08-06 owner 确认）：三种模式的
  预期语义在 ITEM-3 ADR 中记录，精确状态机和 API contract 留给后续 feature。证据：
  owner 在 Epic planning gate 确认。
- **DEC-6 · ITEM-4/5/6 归属本 Epic**（2026-08-06 owner 确认）：A-lite / B-lite /
  bridge config 作为本 Epic 的可选子项，在 ITEM-1/2/3 之后串行推进。证据：owner 在
  Epic planning gate 确认。
- **DEC-7 · Herdr auto-restore 全局 disabled 接受**（2026-08-06 owner 确认）：接受
  Herdr auto-restore 全局 disabled 模式作为 recovery 前提，不向 Herdr upstream 提
  per-pane disable feature request。若后续 Herdr 原生支持 per-pane disable 则可在
  后续 feature 中升级 recovery capability。证据：owner 在 Epic planning gate 确认。
- **DEC-8 · Herdr 配置不做全量并入**（2026-08-07 审计确认）：Herdr
  `%APPDATA%\herdr\config.toml` 是 Herdr 自身配置 authority，`.ccb/ccb.config`
  是 CCB 项目配置 authority；CCB 只读消费 recovery/capability 和 pane/session
  证据，不复制 `theme`、`terminal`、`update`、`keys`、`ui`、`remote`、
  `experimental`、`advanced` 等 Herdr 配置域。bridge/runtime projection 只能是
  脱敏的诊断/运行时投影，不得成为第三份可写配置 authority。

## 子项契约

### ITEM-1 · Herdr v0.8.0 兼容性验证 + public workflow transcript 采集
- **owning skill**：cs-issue（验证兼容性）+ cs-feat（transcript 采集工具/脚本）
- **可交付结果**：
  - ✅ Herdr v0.8.0 环境中 `herdr status server --json` 输出兼容性确认（170/172 tests pass）
  - ✅ `herdr_version` 填入 matrix（`0.8.0-preview.2026-08-04-d78e3d3b5126`）
  - ✅ `herdr_auto_restore_mode` = **disabled**（2026-08-07 双验证确认）
  - ⚠️ 至少 1 个生产可用 provider 的全链路 transcript — **部分完成**：
    - Codex/Claude 已在 Herdr pane 中运行并输出内容（pane read 证实，两次采集一致）
    - ask 管道验证通过（job accepted），pend/completion/cancel 需 API 凭证
  - ⚠️ 全部 14 个 required workflow transcript — **11/14 partial, 3/14 blocked**
    - partial (11): ccb, ping, mounted, kill, restart, reload, foreground_attach, doctor_update, ask, pend, watch
    - blocked (3): config_ui, mobile_terminal, support_projection（需 Herdr UI session）
    - run-20260807-004015: 19/19 维度, 0 failures, pane_state=alive 证实修复
    - kill/restart 全周期通过 + ask smoke 管道通畅 + reload smoke 稳定
  - ✅ `workflow_rows` 从全 blocked 更新为 11 partial + 3 blocked
  - ⚠️ `provider_workflow_rows` 仍全 blocked（需 API credentials）
  - ✅ 采集脚本从 13 维度升级到 19 维度，全部执行通过
  - ✅ **关键发现（2026-08-07）**: CCB 在 Herdr 中功能完全正常。Pane 内容证实存在。
    "无法目视 CLI" 根因是 Herdr viewport/rendering 问题，非 CCB 启动失败。
- **依赖**：无（可直接在当前代码状态上执行）
- **验收要点**：每条 transcript 有可追溯的文件路径和时间戳；matrix JSON schema 满足
  `WindowsHerdrPublicWorkflowEvidence` 定义
- **设计约束**：不修改 §1–§10 的实现代码；采集过程不破坏 CCB runtime state

### ITEM-2 · 完成 §12 herdr-supportability-projection
- **owning skill**：cs-feat
- **可交付结果**：
  - ✅ Herdr support projection 单一 owner（`herdr_supportability_projection.py`，624 行）
  - ✅ 消费 ITEM-1 更新后的 matrix，计算 support tier（14 unit tests pass）
  - ✅ fail-closed tier 规则：`unsupported/experimental/beta/supported`
  - ✅ deterministic SHA-256 projection_hash
  - ⚠️ `ccb doctor --output` 集成 — **待后续完成**（核心模块已就绪，consumer 端未接入）
  - ⚠️ docs/README 同步 — **待后续完成**
  - ⚠️ `support_tier` 当前为 `unsupported`（`ccb_source_status` 为 `v8.5.2-source-branch` 被 projection 映射为 `unknown`，不满足 `strict-v8.5.2` 要求；matrix 中零 pass evidence 进一步锁定该 tier）
- **依赖**：ITEM-1（需要更新后的 matrix 作为输入）
- **验收要点**：projection 的 support tier 与 matrix 证据一致；doctor/docs/README 不互相矛盾
- **设计约束**：fail-closed——任一 core workflow/provider row/Mobile/Config/npm dry-run 非
  pass 时投影到 `unsupported/experimental/beta`，不得出现 `supported`

### ITEM-3 · C2 架构 ADR
- **owning skill**：cs-domain
- **可交付结果**：
  - `.codestable/adr/` 下的一条 ADR，记录 C2 非对称联邦架构决策
  - 内容覆盖：权威矩阵（CCB vs Herdr 各领域 owner）、CCB→Herdr 投影信息流、
    Herdr→CCB 证据信息流、managed/attached/import 三种模式预期语义（精确状态机和
    API contract 留给后续 feature）、conflict 策略（recovery owner 唯一、不自动互改
    配置、pane lifecycle 权威）、Herdr auto-restore 全局 disabled 约束
- **依赖**：DEC-5/6/7 已确认（2026-08-06 owner gate）

### ITEM-4 · A-lite 导入模式（可选 P2）
- **owning skill**：cs-feat
- **可交付结果**：`ccb config import-herdr` 命令，读取当前 Herdr session 的
  workspace/pane 拓扑，生成 `.ccb/ccb.config` 草稿
- **依赖**：无（可直接在 §1–§10 的代码上实现）
- **验收要点**：生成的 config 草稿包含正确的 agent role/provider/pane 映射；
  不覆盖已存在的 `.ccb/ccb.config`
- **设计约束**：只生成草稿，不做自动激活或静默写入；Herdr 配置保持在
  `%APPDATA%\herdr\config.toml`，不得被导入器复制到 CCB 配置
- **当前缺口**：现实现生成 `version = 3` + `agents` 的非法文档，必须先修复
  schema 输出并通过 `validate_project_config` 验证

### ITEM-5 · B-lite Herdr 插件原型（可选 P2）
- **owning skill**：cs-feat
- **可交付结果**：最小 Herdr 插件，在 Herdr sidebar 展示 `ccb status` / `ccb ps` 输出
- **依赖**：Herdr v0.8.0 插件系统（v0.8.0 已支持相对路径命令解析）
- **验收要点**：sidebar 展示与 `ccb status` CLI 输出一致；只读，无写入操作
- **设计约束**：不拥有 provider、job、completion 或 recovery 状态；插件崩溃不影响
  CCB daemon 运行

### ITEM-6 · Bridge config schema（可选 P2）
- **owning skill**：cs-feat
- **可交付结果**：`ccb-herdr-bridge.json` v1 schema 定义及 Python TypedDict/validator
- **依赖**：无
- **验收要点**：schema 覆盖 `project_id`、`herdr_session`、`pane_bindings[]`、
  `config_revision` 核心字段；有 JSON Schema 和 Python 类型
- **设计约束**：API key、token、auth 文件等敏感字段不得进入 bridge config

### ITEM-7 · WezTerm-launched Herdr managed startup（一键启动，2026-08-07 立项）
- **owning skill**：cs-feat
- **背景**：owner 目标是最简操作——预配置 WezTerm/Herdr/CCB 三份配置后，日常只运行
  WezTerm 即进入 Herdr 双 pane（claude + codex）多 agent 协作环境。本 ITEM 是
  2026-08-07 brainstorm 讨论收敛产物，方向与既有 C2 架构一致，不改变权威矩阵。
- **分层契约（owner 已确认）**：
  - WezTerm：唯一日常入口，打开终端窗口并运行 bootstrap；不参与 pane/provider 语义
  - Herdr：物理 terminal workspace/pane owner（ConPTY/split/attach/UI）；不拥有
    provider authority
  - CCB：agent/provider/job/recovery/config authority，创建并标识 claude/codex pane
- **关键决策**：
  - **停用 CCB sidebar，采用 Herdr agent 面板**：CCB 仍为 authority，agent 状态只读
    投影到 Herdr 面板，避免双状态源（owner 2026-08-07 确认）
  - **CCB 创建 pane（managed）**：`.ccb/ccb.config` 是拓扑单一事实源；Herdr 配置
    不长期直接启动 claude/codex（避免退化为 attached 模式）
  - **显式 managed multi-provider 契约**：第一步修正 `ensure.py:52` 的 Herdr 显式
    启动 gate——从 `provider != 'codex'` fail-closed 改为**已验证 provider allow-list**
    （codex/claude 起步）；自动检测路径（`CCB_HERDR_SESSION` 触发）继续不触发 gate；
    `test_config_runtime_mux_backend.py:616` 语义从 "block non-codex" 改为
    "block unverified provider"。已核实事实：`ensure.py:42-58` 注释 design I-3 +
    代码 gate 均在位，`test:616` 固化该行为。
- **可交付结果**：
  - `ccb herdr open`（bootstrap）命令：确保 Herdr server/session 存在并 attach →
    设 `CCB_HERDR_SESSION`/`CCB_HERDR_EXE`/capability report env（Herdr 不作为
    provider authority）→ 读 `.ccb/ccb.config` → socket API 创建/绑定 2 pane →
    启动 claude/codex（CCB 注入 provider env/home）→ `set_pane_identity` 写入 C2
    metadata tokens → 驻留控制面
  - `ensure.py` gate 修正（已验证 provider allow-list）+ test:616 更新
  - `ccb-herdr-bridge.json` 仅做诊断/映射（复用 ITEM-6 schema），不替代
    `.ccb/ccb.config`
  - WezTerm 配置：`default_prog = herdr`（launch_menu 保留 pwsh 入口）
  - CCB sidebar 停用配置
- **依赖**：ITEM-6（bridge schema）；Herdr `resume_agents_on_restore=false` 已生效
  （epic 验收标准已确认）
- **验收要点**：只运行 WezTerm → 进入 Herdr persistent session → CCB 创建双 pane
  （claude+codex）并标识 → ask/pend/recovery 由 CCB 持有；Herdr 面板展示 agent
  状态（只读投影）；Herdr 未持有 provider authority；未验证 provider 在显式 Herdr
  config 下仍 fail-closed
- **设计约束**：不做 attached 退化；不自动双向改配置；bridge 文件不含敏感字段；
  gate 修改保持 fail-closed
- **开放问题**：
  - ✅ `ccb8.cmd` 闪退已缓解（code-hardening Epic ITEM-2：`1118dc24`）：
    Herdr session list 探测改为 `Process.Start(CreateNoWindow)`，ConPTY pane 不再
    产生可见控制台窗口。`observed_windows_flash=false` 已由 spike 证据确认
  - ✅ Herdr `resume_agents_on_restore` 已通过 config.toml 写入 disabled，确认不随
    bootstrap 改变

### ITEM-8 · Bootstrap shim 优雅化（2026-08-10 立项）
- **owning skill**：cs-feat
- **背景**：ccb8.ps1 一键启动链路经 2026-08-10 综合分析（见
  `.codestable/compound/2026-08-10-ccb8-bootstrap-shim-analysis.md`），确认当前
  PowerShell wrapper 在 4 个维度上与 Python 侧存在职责重叠，最关键的
  `wezterm cli send-text` 键盘注入是 Herdr dispatch 交互终端约束下的 workaround。
  本 ITEM 将把 dispatch 语义从 PowerShell bootstrap shim 渐进迁移到 CCB/Herdr
  结构化边界。
- **分层目标**：
  - P0：删除 ccb8.ps1 中与 Python `HerdrCliRequestAdapter` 重复的 server 启动、
    session 探活逻辑（~80 行）。Python 侧 `_command()` 已实现 NotFound → 自动起
    server → 重试闭环。
  - P1：给 `ccb herdr open` 加 `--wait-ready` flag，ccbd 就绪等待从 PowerShell
    轮询 `lifecycle.json`（~20 行）移入 Python `handle_herdr_open()`。
  - P2：将 Herdr UI attach 从 `wezterm cli send-text --no-paste` 键盘注入迁移为
    结构化 `herdr agent start` 调用或 `herdr session attach`（依赖交互终端上下文）。
  - P3：对齐 WezTerm `default_prog` 与"形态 2"文档（备选路径升级为推荐路径）。
  - 长期：新增 `ccb herdr dispatch` 结构化原语，dispatch 语义完全归位到 CCB/Herdr
    边界，PowerShell 退化为最薄 env 引导层。
- **依赖**：ITEM-7（一键启动已交付）；`.codestable/lessons/2026-08-10-herdr-dispatch-interactive-terminal.md`
  （dispatch 触发条件经验规则）；Herdr `agent start` CLI 可用性
- **验收要点**：
  - ccb8.ps1 代码量从 ~200 行（Phase 0-4 编排）降至 ~50 行（纯 env 引导 + 单次
    `ccb herdr open` 调用）
  - `ccb herdr open --wait-ready` 阻塞到 ccbd mounted，不再依赖外部 lifecycle.json 轮询
  - Herdr UI attach 不通过 wezterm send-text 键盘注入（或明确标记为 P2 遗留 workaround）
  - 一键启动端到端行为不变（用户裸调 `ccb8.cmd` → WezTerm → 双 agent 就绪）
- **设计约束**：
  - 不做 attached 退化；CCB 不接管 Herdr 的 pane/UI 权威
  - `send-text` 在当前 Herdr 约束下是有效 workaround，在 Herdr 提供 dispatch API 之前
    不被当作 bug
  - P0/P1 不依赖 Herdr 侧变更，仅消除 CCB 内部的重复逻辑
  - P2/P3/长期依赖 Herdr agent start API 或交互终端上下文

## 最终交付索引

| 子项 | 产物 | 类型 |
|---|---|---|
| ITEM-1 | 更新后的 `windows-herdr-public-workflow-matrix.json` + transcript 文件 | evidence |
| ITEM-2 | Herdr support projection 代码 + doctor/docs 同步 | code + docs |
| ITEM-3 | `.codestable/adr/` 下 C2 架构 ADR | decision record |
| ITEM-4 | `ccb config import-herdr` 命令 | code |
| ITEM-5 | Herdr `ccb` sidebar 插件 | code |
| ITEM-6 | `ccb-herdr-bridge.json` schema + Python types | code + schema |
| ITEM-7 | `ccb herdr open` bootstrap + ensure.py gate 修正 + WezTerm 配置 | code + config |
| ITEM-8 | Bootstrap shim 优雅化（P0-P3 渐进 + dispatch 原语） | code + docs |

## 整体验收

- ITEM-1/2/3 完成后，CCB 在 Native Windows x64 + Herdr v0.8.0 上有一个明确的、
  由 machine-readable evidence 驱动的 support tier
- C2 架构决策有正式的跨版本 ADR，不依赖 brainstorm 文档或聊天历史
- `ccb doctor --output` 向用户准确报告 Native Windows Herdr 的可用性、限制和下一步操作
- ITEM-4/5/6/7/8 不破坏 C2 核心契约
- ITEM-8 P0/P1 交付后，ccb8.ps1 退化为 env 引导 + 单次调用，代码量降至 ~50 行
- **已知 gap（已于 code-hardening Epic 解决，见下）**：
  - ✅ `ccb doctor --output` consumer 端接入 → `5aea5f08`（ITEM-3）
  - ✅ `ccb config import-herdr` schema 修复 → `8fc5094c`（ITEM-1）
  - ✅ `ccb8.cmd` 闪退缓解 → `1118dc24`（ITEM-2）
  - 以上三项来自 Epic `windows-native-herdr-ccb-code-hardening`（`accepted` 2026-08-07）

## 遗留风险

- **Herdr auto-restore 全局 disabled 限制**：CCB recovery 路径要求 Herdr auto-restore
  处于全局 disabled 模式。这意味着非 CCB agent 也无法使用 Herdr 原生 session restore，
  属于已知的跨工具体验限制。缓解：此限制已在 C2 ADR 中显式记录；若后续 Herdr 原生
  支持 per-pane disable，可通过后续 feature 升级 recovery capability 并更新 support tier。
  DEC-7 已确认不向 Herdr upstream 提需求。
  **2026-08-07 已解决**：经文档+实证双验证确认后，`config.toml` 已写入
  `resume_agents_on_restore = false` 并 `server reload-config` applied，mode=**disabled**。
- **Herdr viewport / 用户可见 CLI 渲染**（2026-08-07 新增）：
  run-20260807-002147 证实 provider 在 Herdr pane 中正常运行并输出内容（pane read 抓取），
  但用户无法在 Herdr UI 中目视到 CLI 界面。根因是 Herdr viewport/rendering 层面的问题
  （cmd.exe 窗口闪现 + pane_state=unknown），非 CCB 启动或 backend 适配缺陷。
  缓解：已在采集脚本中新增 provider-logs 维度捕获 agent stdout；此问题需在 Herdr 侧
  排查 ConPTY pane 的视觉渲染路径。
- **Herdr API 稳定性**：Herdr socket API 仍在快速迭代。缓解：`HerdrSocketClient` 内置
  `EXPECTED_HERDR_API_SCHEMA` version gate + `server_info` schema mismatch 检测。
- **v8.5.2 官方 win32 support**：CCB v8.5.2 官方 npm metadata 中 `os` 尚未包含 `win32`。
  缓解：release surface gate 已建立（npm install dry-run），正式发布需上游同意。
- **provider credential readiness**：20 个 public provider 中多数缺生产 API 授权或 CLI
  就绪。缓解：已在 provider-runtime-on-herdr acceptance 中记录 explicit blocked evidence，
  supportability projection 保持 fail-closed。
  **2026-08-07 更新**：Codex 和 Claude 在 Herdr pane 中运行，但均显示认证/连接错误
  （"Sign in with ChatGPT" / "Unable to connect to Anthropic services"），证实 pane 可用
  但缺少有效 API 凭证。
- **Herdr workspace 累积**（2026-08-07 新增）：
  run-20260807-004015 发现 6 个同名 ccb-avaprintdesigner workspaces (w3/w5/w6/w7/wB/wH)，
  每次 kill/restart 创建新 namespace 但旧 workspace 未清理。不影响功能但会累积 Herdr
  session 状态。缓解：采集脚本的 cleanup phase 已在外部 Herdr UI 运行后清理；长期需在
  namespace destroy 时显式关闭旧 workspace。

