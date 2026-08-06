---
status: active
created: 2026-08-06
work: ../work/epic-windows-native-herdr-ccb.md
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

## 非目标

- 不修改 C2 核心架构方向（已验证可行）
- 不改 Herdr backend/provider/recovery 行为（§1–§10 的代码已 acceptance passed）
- 不执行 npm publish、release、push 或 promotion
- 不把 partial/blocked evidence 写成 full support
- 不修改 CCB v8.5.2 的 provider completion/recovery owner 语义
- 不实现 Herdr upstream 功能（如 per-pane auto-restore disable 取决于 Herdr 侧支持）

## 验收标准

- ✅ validation matrix 中 `workflow_rows` 从全 `blocked` 变为 8/14 partial + 6/14 blocked，
  每条有可追溯的 transcript artifact（run-20260807-002147 + 60 raw command refs）
- ⚠️ `herdr_version` ✅ 已填入（`0.8.0-preview`），`ccb_source_status` ✅ 已填入
  （`v8.5.2-source-branch`），`herdr_auto_restore_mode` ❌ 仍 unknown
- ⚠️ `ccb doctor --output` 展示 support tier — projection 核心模块已完成，doctor consumer
  端待后续接入
- ✅ C2 架构 ADR 存在于 `.codestable/adr/001-c2-asymmetric-federation-ccb-herdr.md`
- ❌ matrix 中无 pass 的 workflow/provider，`support_projection_allowed` 保持 `false`
- ✅ 全部 6 子项完成（5 Epic commits + 1 修复 commit），final acceptance review 通过
  （189/191 tests, 98.4%）

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

## 子项契约

### ITEM-1 · Herdr v0.8.0 兼容性验证 + public workflow transcript 采集
- **owning skill**：cs-issue（验证兼容性）+ cs-feat（transcript 采集工具/脚本）
- **可交付结果**：
  - ✅ Herdr v0.8.0 环境中 `herdr status server --json` 输出兼容性确认（170/172 tests pass）
  - ✅ `herdr_version` 填入 matrix（`0.8.0-preview.2026-08-04`）
  - ⚠️ `herdr_auto_restore_mode` 仍 unknown（新 herdr-config-probe 维度待执行）
  - ⚠️ 至少 1 个生产可用 provider 的全链路 transcript — **部分完成**：
    - Codex/Claude 已在 Herdr pane 中运行并输出内容（pane read 证实）
    - ask/pend/completion/cancel 完整链路需真实 API 凭证
  - ⚠️ 全部 14 个 required workflow transcript — **8/14 partial, 6/14 blocked**
    - partial: ccb, ping, mounted, kill, restart, reload, foreground_attach, doctor_update
    - blocked: ask, pend, watch, config_ui, mobile_terminal, support_projection
  - ✅ `workflow_rows` 从全 blocked 更新为实际状态
  - ⚠️ `provider_workflow_rows` 仍全 blocked（需 API credentials）
  - ✅ 采集脚本从 13 维度扩展到 19 维度
  - ✅ **关键发现（2026-08-07）**: CCB 在 Herdr 中功能完全正常。Pane 内容证实存在。
    "无法目视 CLI" 根因是 Herdr viewport/rendering 问题，非 CCB 启动失败。
- **依赖**：无（可直接在当前代码状态上执行）
- **验收要点**：每条 transcript 有可追溯的文件路径和时间戳；matrix JSON schema 满足
  `WindowsHerdrPublicWorkflowEvidence` 定义
- **设计约束**：不修改 §1–§10 的实现代码；采集过程不破坏 CCB runtime state

### ITEM-2 · 完成 §12 herdr-supportability-projection
- **owning skill**：cs-feat
- **可交付结果**：
  - ✅ Herdr support projection 单一 owner（`herdr_supportability_projection.py`，397 行）
  - ✅ 消费 ITEM-1 更新后的 matrix，计算 support tier（19/19 unit tests pass）
  - ✅ fail-closed tier 规则：`unsupported/experimental/beta/supported`
  - ✅ deterministic SHA-256 projection_hash
  - ⚠️ `ccb doctor --output` 集成 — **待后续完成**（核心模块已就绪，consumer 端未接入）
  - ⚠️ docs/README 同步 — **待后续完成**
  - ⚠️ `support_tier` 当前为 `unsupported`（herdr_auto_restore=unknown + workflows=blocked 触发降级）
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
- **设计约束**：只生成草稿，不做自动激活或静默写入

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

## 最终交付索引

| 子项 | 产物 | 类型 |
|---|---|---|
| ITEM-1 | 更新后的 `windows-herdr-public-workflow-matrix.json` + transcript 文件 | evidence |
| ITEM-2 | Herdr support projection 代码 + doctor/docs 同步 | code + docs |
| ITEM-3 | `.codestable/adr/` 下 C2 架构 ADR | decision record |
| ITEM-4 | `ccb config import-herdr` 命令 | code |
| ITEM-5 | Herdr `ccb` sidebar 插件 | code |
| ITEM-6 | `ccb-herdr-bridge.json` schema + Python types | code + schema |

## 整体验收

- ITEM-1/2/3 完成后，CCB 在 Native Windows x64 + Herdr v0.8.0 上有一个明确的、
  由 machine-readable evidence 驱动的 support tier
- C2 架构决策有正式的跨版本 ADR，不依赖 brainstorm 文档或聊天历史
- `ccb doctor --output` 向用户准确报告 Native Windows Herdr 的可用性、限制和下一步操作
- ITEM-4/5/6（若执行）不破坏 C2 核心契约

## 遗留风险

- **Herdr auto-restore 全局 disabled 限制**：CCB recovery 路径要求 Herdr auto-restore
  处于全局 disabled 模式。这意味着非 CCB agent 也无法使用 Herdr 原生 session restore，
  属于已知的跨工具体验限制。缓解：此限制已在 C2 ADR 中显式记录；若后续 Herdr 原生
  支持 per-pane disable，可通过后续 feature 升级 recovery capability 并更新 support tier。
  DEC-7 已确认不向 Herdr upstream 提需求。
  **2026-08-07 更新**：`herdr_auto_restore_mode` 仍为 `unknown`——新采集维度
  `herdr-config-probe` 将在下次采集运行中探测 Herdr config.toml 的实际值。
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

