---
epic: ../epics/windows-native-herdr-ccb.md
phase: acceptance
approved_revision: d221483de0fa1cb1239fd24df96f42a9b6630d4b1afe0bfa8e4389112341848d
current_item: null
next_action: blocked — OCR review 揭示 ITEM-4/ITEM-7 代码缺陷，移交新 Epic windows-native-herdr-ccb-code-hardening
blocked_by: OCR review findings (2026-08-07) — herdr_config_import.py L71-73/73/115-119/138；handlers_start.py L170-175；herdr_common.py L45-52；herdr_bootstrap.py L63-71；roadmap §12 仍 in-progress
item_progression: continuous
milestone_commit: authorized
remote_publish: final
---
## 子项进度
- [x] ITEM-1 · Herdr v0.8.0 兼容性验证 + public workflow transcript 采集 ✅ 7cb9a724
- [x] ITEM-2 · 完成 §12 herdr-supportability-projection ✅ 4b4f96b4（核心模块 + 19 tests）
- [x] ITEM-3 · C2 架构 ADR ✅ 97ee84fe
- [x] ITEM-4 · A-lite 导入模式（可选 P2）✅ 505f89bf
- [x] ITEM-5 · B-lite Herdr 插件原型（可选 P2）✅ de344163
- [x] ITEM-6 · Bridge config schema（可选 P2）✅ de344163
- [x] ITEM-7 · WezTerm-launched Herdr managed startup（一键启动）✅ 2026-08-07 实现

### ITEM-7 实现完成（2026-08-07）
- **① ensure.py gate allow-list**：`_HERDR_NATIVE_VERIFIED_PROVIDERS = {codex, claude}`，
  `_herdr_explicit_gate_error()`；显式 herdr 下未验证 provider 仍 fail-closed
- **② `ccb herdr open` bootstrap**：`herdr_common.py`（exe/status/env，DRY 复用至
  `config import-herdr`）+ `herdr_bootstrap.py`（定位 exe → server 校验 → 只读探测 →
  运行时生成 capability report → 注入 `CCB_HERDR_*` env）+ daemon backend 冲突检测
  （非 herdr daemon → 指引 `ccb kill` 后重试）；默认前台 attach，`--no-attach` 后台
- **③ WezTerm 配置**：`~/.wezterm.lua` default_prog=herdr（形态 1）+ launch_menu 保留
  pwsh；文档 `docs/native-windows-herdr-managed-launch.md`（形态 2 备选 + 前台/后台切换）
- **验证**：120 tests pass（gate 51 + bootstrap 23 + cli-parser 46）；端到端
  `ccb herdr open --no-attach` 干净环境成功创建 2 pane + mounted
- **遗留**：`ccb kill` 在 herdr 模式下 CLI 侧也需 herdr env（既有行为，ITEM 范围外）；
  Herdr 侧触发 `ccb herdr open` 的快捷键/插件（B-lite）待做
- **采集脚本同步（2026-08-07）**：`herdr-ui-integration-spike/run_spike.ps1` 新增
  `ccb-herdr-open` 维度（+45/-3）：`ValidateSet` 两处补维度、`ccb-start` 互斥、
  采集块（`ccb8 herdr open --no-attach` + herdr-open-evidence.json）、startCommand
  识别 + summary `herdr_open_ref`。验证：pwsh 7 语法 OK + SelfTest passed +
  最小采集执行正常；采集脚本清理逻辑会终止 residual herdr/父 bash（既有行为）。
- **采集脚本编码修复（2026-08-07）**：`run_spike.ps1` 补 **UTF-8 BOM**。根因：脚本原为
  无 BOM UTF-8，Windows PowerShell 5.1 按 ANSI 读取导致中文错位、`L1230` 语法错误
  （HEAD 在 5.1 下同样受影响，IT-1 采集用的是 pwsh 7）。加 BOM 后 powershell 5.1
  与 pwsh 7 均 SelfTest passed。用户报的 PSReadLine Ctrl+v 崩溃是粘贴长命令的既有
  PSReadLine bug，与脚本无关。
- **采集脚本 3 处修复（2026-08-07，基于 run-20260807-135403 分析）**：
  - **ask-smoke agent 名解析**：原依赖后定义的 `$pingAllText`（执行顺序 bug → 恒
    fallback `agent1`，与 `agent_1` 不符）→ 改为自行读取 ping-all 输出解析
    （模拟验证得到 `agent_1`）
  - **启动前预清理**：ccb-start/ccb-herdr-open 前运行 `ccb8 kill -f`（不记入
    $commands），缓解 "old ccbd did not shut down in time"
  - **restart 后轮询**：ping-after-restart 改为最多 3 次重试（attempt 不记入
    $commands，仅保留 canonical），缓解 "ccbd is starting" 时序
  - 验证：pwsh 7 + powershell 5.1 SelfTest 均 passed

## 临时决策与证据

### 策略确认（2026-08-06 owner gate）
- `item_progression: continuous` — 子项串行自动推进，不暂停
- `milestone_commit: authorized` — 每个子项完成并验证通过后自动创建语义原子 commit
- `remote_publish: final` — 全部子项完成 + final acceptance 通过后一次性推送
- DEC-5/6/7 已确认，路线清晰，无待决策项

### 输入来源
- `.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`（450 行，含 2026-08-06 代码状态评估）
- `.codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md`（165 行，含 2026-08-06 实现后回顾）
- `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`（§1–§12 roadmap items）
- `.codestable/audits/2026-08-05-herdr-ccb-recent-changes/`

### 代码资产
- `lib/terminal_runtime/herdr_backend.py`（809 行）
- `lib/terminal_runtime/herdr_backend_runtime/client.py`（795 行）
- `lib/terminal_runtime/herdr_backend_runtime/capabilities.py`（269 行）
- `lib/terminal_runtime/backend_selection.py`（183 行）
- `lib/terminal_runtime/mux_backend_contract.py`（269 行）
- 19 个 provider session/execution 适配

### 已完成 roadmap items（§1–§11）
- §1 baseline-gate ✅ | §2 contract-spike ✅ | §3 mux-contract-v2 ✅
- §4 backend-client ✅ | §5 control-plane-transport ✅ | §6 namespace-lifecycle ✅
- §7 provider-runtime ✅ | §8 recovery-boundary ✅ | §9 user-surfaces-parity ✅
- §10 release-surface ✅ | §11 validation-matrix ✅（8/14 partial, 6 blocked）

### Epic 子项完成（§12 部分）
- §12 herdr-supportability-projection ✅ 4b4f96b4（核心模块 + 19 tests，doctor/docs 集成待后续）

### 2026-08-07 herdr_auto_restore 双验证 ← 最新
- **文档验证**: `herdr --default-config` 证实 `[session] resume_agents_on_restore = true`（默认启用）
- **实证验证**: `config.toml` 写入 `resume_agents_on_restore = false` + `server reload-config applied`
- **结论**: herdr_auto_restore_mode = **disabled** ✅
- CCB 为唯一 recovery owner（C2 DEC-7），Herdr agent auto-restore 显式禁用，互不冲突
- 原始 config.toml 备份: `config.toml.bak-20260807`

### 2026-08-07 Herdr 配置权威审计 ← 最新
- **完整默认配置已读取**：Herdr v0.8.0-preview.2026-08-04；Windows 实际用户配置路径为
  `%APPDATA%\herdr\config.toml`。
- **配置边界结论**：
  - Herdr `config.toml` 是用户可编辑的 Herdr authority，继续管理 theme、terminal、
    update、keys、worktrees、ui、toast、sound、session、remote、experimental、advanced。
  - `.ccb/ccb.config` 继续管理 CCB 项目 agent/provider/role/model/MCP、workflow、
    queue/completion/cancel/recovery、期望拓扑和 `runtime.mux.backend = "herdr"`。
  - bridge/runtime projection 只保存脱敏的 Herdr session/pane/capability 绑定和 owner
    metadata，不复制 Herdr 全量配置，也不自动双向写入。
- **恢复约束**：Herdr 默认 `resume_agents_on_restore = true`；CCB-owned pane 的 recovery
  supported 路径要求用户显式设置 `false`。CCB 启动/reload/reconcile 不得静默改写 Herdr
  配置文件。
- **A-lite 审计结果**：`ccb config import-herdr` 已有 parser/handler/dispatch 接线，
  但当前生成的 `version = 3` + `agents` 草稿会被现行 v3 parser 以
  `v3_static_layout_field_forbidden` 拒绝。后续应改为合法 v2 `[windows]` 草稿或完整
  v3 `workflow` 文档；在此之前不能把导入命令标记为可用的配置迁移路径。
- **依据**：`.codestable/adr/001-c2-asymmetric-federation-ccb-herdr.md`；
  `docs/ccb-config-layout-contract.md`；`lib/agents/config_loader_runtime/parsing_runtime/workflow_v3.py`；
  `lib/cli/services/herdr_config_import.py`；实际执行 `herdr --default-config`。

### 2026-08-07 采集证据 v2（run-20260807-004015）
- **19/19 维度全部执行，0 command failures**
  - classification: mounted-with-herdr-panel-observation ✅
- **pane_state 修复证实**: unknown → **alive**（Herdr liveness fix 在真实环境生效）
- **Kill/Restart 全周期**: kill=ok → unmounted → restart=mounted (gen 4→5) ✅
- **Ask smoke**: pipeline accepted (job created for agent1) ✅
- **Reload smoke**: noop stable (agents remain mounted) ✅
- **Pane 内容**: 两次采集一致 — codex/claude 持续在 pane 中运行并输出 ✅
- **herdr config**: config.toml 存在但无 auto_restore 字段 → mode=unknown ⚠️
- **新发现**: Herdr workspace 累积（6 个同名 workspace from repeated kill/restart）
- **矩阵**: blocked 3 → 11, partial 8 → 11 (ask/pend/watch 从 blocked 升级)

### 2026-08-07 采集证据 v1（run-20260807-002147）
- CCB 在 Herdr 中功能正常，pane 内容证实存在
- "无法目视 CLI" 根因 = Herdr viewport/rendering issue
- 采集脚本 13 → 19 维度升级 (9001d758)

### Epic 文档同步（2026-08-07）
- 永久 Epic `验收标准`: 标注实际达成状态（✅/⚠️/❌）
- 永久 Epic `ITEM-1`: 更新为 11/14 partial + 3 blocked + pane_state=alive 证实
- 永久 Epic `遗留风险`: 新增 viewport 渲染 + auto_restore unknown + workspace 累积 + API 凭证
- 验证矩阵: run-20260807-004015 证据更新 (e2ab233e)

### Final acceptance review 结论（2026-08-07）
- **Epic 文档审查**：通过（2 轮，8 finding → 全部 resolved）
- **代码 OCR review**：揭示 ITEM-4/ITEM-7 代码缺陷，阻塞 acceptance
  - `herdr_config_import.py:71-73` — `--output` 已存在时静默覆盖
  - `herdr_config_import.py:73` — 输出 JSON 但 CCB 链路是 TOML
  - `herdr_config_import.py:115-119` — 不检查 returncode，键类型假设不安全
  - `herdr_config_import.py:138` — 生成非法 v3 schema
  - `handlers_start.py:170-175` — daemon inspection 异常被吞，冲突检测 fail-open
  - `herdr_common.py:45-52` — 无条件清除 XDG_*，非 Windows 平台读错配置
  - `herdr_bootstrap.py:63-71` — 不处理嵌套 server shape
  - roadmap §12 `herdr-supportability-projection` 仍 `in-progress`
- **处置**：不标记 `accepted`；移交新 Epic `windows-native-herdr-ccb-code-hardening`
