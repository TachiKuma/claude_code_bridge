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

### 2026-08-07 最新采集证据（run-20260807-002147）
- **CCB 在 Herdr v0.8.0 中功能正常**
  - ccbd healthy (generation=3), 2 agents mounted (codex+claude, idle/restored)
  - 60/60 commands exit=0, 0 failures
  - namespace_backend_impl=herdr, namespace_backend_family=herdr-native ✅
- **关键发现: Pane 内容确实存在！**
  - codex pane (wG:p3): "Sign in with ChatGPT to use Codex..."
  - claude pane (wG:p4): "Welcome to Claude Code v2.1.220 / Unable to connect to Anthropic services"
  - 根因: "无法目视 CLI" = **Herdr viewport/rendering issue**, 非 CCB 启动失败
  - observed_windows_flash=True + pane_state=unknown 均指向视觉渲染层面
- **采集脚本升级**: 13 → 19 维度 (9001d758)
  - 新增: provider-logs, ccb-lifecycle (kill/restart cycle), herdr-config-probe, provider-session-files, ccb-ask-smoke, ccb-reload-smoke
- **待下次采集运行解决**:
  - `herdr_auto_restore_mode` 仍 unknown — herdr-config-probe 维度将探测 config.toml
  - provider ask/pend/completion/cancel 链路需有效 API 凭证
  - kill/restart/reload 生命周期完整测试

### Epic 文档同步（2026-08-07）
- 永久 Epic `验收标准` 更新为实际达成状态（✅/⚠️/❌ 标注）
- 永久 Epic `ITEM-1/2` 可交付结果更新为实际交付状态
- 永久 Epic `遗留风险` 新增：Herdr viewport 渲染 + auto_restore_mode unknown + API 凭证缺失
- Work 游标 `已完成 roadmap items` 更正为 8/14 partial（非"全 blocked"）
