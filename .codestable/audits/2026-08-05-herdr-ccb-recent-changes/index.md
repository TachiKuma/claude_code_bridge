---
doc_type: audit-index
audit_date: 2026-08-05
scope: herdr-ccb-recent-changes
status: partially-fixed
dimensions_scanned:
  - bug
  - maintainability
  - security
  - performance
files_scanned: 11
findings_fixed: ["01", "06", "07"]
findings_new_from_spike: ["F1", "F2", "F3"]
unified_doc: .codestable/issues/2026-08-05-herdr-ui-spike-run-findings/herdr-ui-spike-run-findings-unified.md
last_spike_run: run-20260805-165854
---

# 审计：Herdr / CCB 近期代码改动

## 范围

近 5 次提交涉及的全部改动文件（`HEAD~5..HEAD`，含已 staged + 未 staged），共 **11 个文件**。

| 区域 | 文件 | 改动行 |
|------|------|--------|
| Wrapper 启动 | `ccb8.cmd`, `ccb8.ps1` | start alias、prestart cleanup ACL 刷新、闪窗处理 |
| Herdr CLI 适配 | `cli.py` | workspace 回验、server 参数序、nested status、destroy 容错、foreground attach |
| 采集脚本 | `run_spike.ps1` | CCB namespace session 提取、扩展采集维度 |
| 存储层 | `atomic.py`, `jsonl_store.py` | Windows 原子写重试、JSONL tail 严格模式开关 |
| 状态服务 | `stores.py` | load_latest 尾行优化 |
| 测试 | 4 个 test 文件 | 补强覆盖 |

## 总评

改动质量整体良好——6 项根因修复覆盖了 Herdr 前台附着、ACL 刷新、闪窗、session 提取等关键路径，测试覆盖同步跟进。结合真实 Herdr UI 环境的最新采集结果看，当前主要风险已经收敛到 `run_spike.ps1` 的证据链判定：`ccb8-ps` 失效、`ping ccbd` 过早卡死分类、`herdr api snapshot` 退回空快照仍被放行，导致最终结论偏保守且 pane 证据不可直接信任。存储层和 wrapper 的改动本身较稳健。

## 发现清单

| # | 性质 | 严重度 | 置信度 | 简述 | 状态 | 建议动作 |
|---|------|--------|--------|------|------|----------|
| 01 | bug | P0 | high | `run_spike.ps1` pane capture 使用错误的 Herdr session | ✅ 已修复 | — |
| 02 | bug | P1 | high | `ccb8.cmd` 去掉了 `-WindowStyle Hidden`，非 Herdr 环境中会闪窗 | ⬜ 待处理 | cs-issue |
| 03 | bug | P1 | medium | `_attach_namespace` 前台附着错误分类粗糙 | ⬜ 待处理 | cs-issue |
| 04 | bug | P2 | medium | `_logical_workspaces` 在 create_session 刚完成后可能返回空 | ⬜ 待处理 | cs-issue |
| 05 | maintainability | P1 | high | `run_spike.ps1` 与 `ccb8.ps1` 重复了 ~70 行参数引用函数 | ⬜ 待处理 | cs-refactor |
| 06 | maintainability | P1 | high | `run_spike.ps1` 行 832-906 pane verification 缩进混乱 | ✅ 已修复 | — |
| 07 | maintainability | P2 | medium | `run_spike.ps1` 采集维度无法选择性启用，启动命令过长 | ✅ 已修复 | — |
| 08 | maintainability | P2 | low | `_server_status_running` 新增嵌套状态路径，旧路径未标 deprecated | ⬜ 待处理 | cs-refactor |
| 09 | security | P1 | medium | `_command_evidence` 只脱敏 argv，错误 detail 中的 token 可能泄露 | ⬜ 待处理 | cs-issue |
| 10 | security | P2 | low | `_redacted_argv` send_text 脱敏逻辑依赖隐含的 argv 布局假设 | ⬜ 待处理 | cs-issue |
| 11 | performance | P2 | medium | `_logical_workspaces` 在 create_session→ensure_window→list_windows 链路中重复查询 workspaces | ⬜ 待处理 | cs-refactor |
| 🆕 F1 | bug | P1 | high | `ccb8 ps` 子命令路由错误——被当作 `start` 命令参数处理（根因在外部项目包装器层） | 🆕 新增 | cs-issue |
| 🆕 F2 | bug | P1 | high | CCB Herdr 会话 socket 生命周期不稳定——两次 run 之间 socket 丢失 | 🆕 新增 | cs-issue |
| 🆕 F3 | bug | P2 | high | 分类逻辑 `ping-ccbd` vs `ping-all` 竞争——前者读到过渡态 `unmounted` 导致误分类 | 🆕 新增 | cs-issue |

## 下一步建议

- **已修复**（✅）：#01（pane capture session）、#06（pane verification 缩进）、#07（选择性采集维度）——已通过 code review + spike 真实环境运行确认
- **立刻处理**（P1 新增）：🆕F1（`ccb8 ps` 路由——检查外部项目包装器版本）+ 🆕F2（CCB Herdr socket 可用性验证）
- **本迭代修**（P1）：#02（闪窗回退）、#05（共享模块提取，本轮明确未修）、#09（detail 脱敏）
- **排期修**（P2）：#03、#04、#08、#10、#11、🆕F3（分类竞争）
- **低优先级**（P3）：spike F5（启动文件路径）、F6（用户填写）、F4（会话分叉文档说明）
- **下次采集验证**：F1+F2 修复后在 Herdr UI 环境重新运行默认全量采集，确认真实 CCB 会话 pane capture 证据完整性

## 复核结论

以下结论来自最新真实 Herdr UI 采集 `run-20260805-165854`，用于覆盖对 `run_spike.ps1` 的最新判断：

- `summary.json` 显示 `classification=ccb-mounted-not-proven`，但同一轮同时满足 `ping_all_success=true`、`layout_materialization_complete=true`、`observed_herdr_agents_panel_text=claude`。→ **F3 新增**：分类逻辑竞争问题。
- `ccb8-ps` 在真实环境中返回 `command_status: invalid`，而 `ccb8-doctor-ps` 已成功给出 `session_name=ccb-avaprintdesigner-575a971f` 与 `wB7:p2 / wB7:p3` 的绑定信息。→ **F1 新增**：`ccb8 ps` 路由错误，根因在外部包装器层。
- `herdr-api-snapshot-ccb-namespace` 返回 `NotFound`，`herdr-api-snapshot-after` 虽成功，但快照为空，`pane_count=0`、`workspace_count=0`。→ **F2 新增**：CCB Herdr 会话 socket 缺失。
- **审计#01、#06、#07 的修复已被 spike 真实运行确认有效**：pane capture session 现在正确跟随 snapshot source，缩进已重排，选择性维度参数工作正常。

详细交叉引用和统一优先级排序见：[统一文档](.codestable/issues/2026-08-05-herdr-ui-spike-run-findings/herdr-ui-spike-run-findings-unified.md)
