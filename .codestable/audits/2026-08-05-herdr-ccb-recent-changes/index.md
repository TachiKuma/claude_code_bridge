---
doc_type: audit-index
audit_date: 2026-08-05
scope: herdr-ccb-recent-changes
status: active
dimensions_scanned:
  - bug
  - maintainability
  - security
  - performance
files_scanned: 11
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

| # | 性质 | 严重度 | 置信度 | 简述 | 建议动作 |
|---|------|--------|--------|------|----------|
| 01 | bug | P0 | high | `run_spike.ps1` pane capture 使用错误的 Herdr session | cs-issue |
| 02 | bug | P1 | high | `ccb8.cmd` 去掉了 `-WindowStyle Hidden`，非 Herdr 环境中会闪窗 | cs-issue |
| 03 | bug | P1 | medium | `_attach_namespace` 前台附着错误分类粗糙 | cs-issue |
| 04 | bug | P2 | medium | `_logical_workspaces` 在 create_session 刚完成后可能返回空 | cs-issue |
| 05 | maintainability | P1 | high | `run_spike.ps1` 与 `ccb8.ps1` 重复了 ~70 行参数引用函数 | cs-refactor |
| 06 | maintainability | P1 | high | `run_spike.ps1` 行 832-906 pane verification 缩进混乱 | cs-refactor |
| 07 | maintainability | P2 | medium | `run_spike.ps1` 采集维度无法选择性启用，启动命令过长 | cs-refactor |
| 08 | maintainability | P2 | low | `_server_status_running` 新增嵌套状态路径，旧路径未标 deprecated | cs-refactor |
| 09 | security | P1 | medium | `_command_evidence` 只脱敏 argv，错误 detail 中的 token 可能泄露 | cs-issue |
| 10 | security | P2 | low | `_redacted_argv` send_text 脱敏逻辑依赖隐含的 argv 布局假设 | cs-issue |
| 11 | performance | P2 | medium | `_logical_workspaces` 在 create_session→ensure_window→list_windows 链路中重复查询 workspaces | cs-refactor |

## 下一步建议

- **立刻处理**（P0）：`run_spike.ps1` 的分类顺序和 pane 证据回退链，优先修正 `ping ccbd`、`ping all`、layout materialization、空 snapshot 放行之间的权重关系
- **本迭代修**（P1）：#02（闪窗回退）、`ccb8-ps` session 提取失效、`herdr api snapshot` 会话/根路径不一致、#06（pane verification 证据链混乱）、#09（detail 脱敏）
- **排期修**（P2）：#04、#07、#08、#10、#11

## 复核结论

以下结论来自最新真实 Herdr UI 采集 `run-20260805-165854`，用于覆盖对 `run_spike.ps1` 的最新判断：

- `summary.json` 显示 `classification=ccb-mounted-not-proven`，但同一轮同时满足 `ping_all_success=true`、`layout_materialization_complete=true`、`observed_herdr_agents_panel_text=claude`。
- `ccb8-ps` 在真实环境中返回 `command_status: invalid`，而 `ccb8-doctor-ps` 已成功给出 `session_name=ccb-avaprintdesigner-575a971f` 与 `wB7:p2 / wB7:p3` 的绑定信息。
- `herdr-api-snapshot-ccb-namespace` 返回 `NotFound`，`herdr-api-snapshot-after` 虽成功，但快照为空，`pane_count=0`、`workspace_count=0`。
- 因此，当前应优先修正的是 `run_spike.ps1` 的分类逻辑和 pane 验证回退策略，而不是继续沿用旧的“pane capture 取错 session”结论。
