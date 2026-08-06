---
epic: ../epics/windows-native-herdr-ccb.md
phase: acceptance
approved_revision: d221483de0fa1cb1239fd24df96f42a9b6630d4b1afe0bfa8e4389112341848d
current_item: null
next_action: Final acceptance review — 全部 6 子项完成，进入 acceptance phase
blocked_by: null
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
