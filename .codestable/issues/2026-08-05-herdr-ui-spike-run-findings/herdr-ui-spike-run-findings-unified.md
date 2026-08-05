---
doc_type: issue-unified
issue: 2026-08-05-herdr-ui-spike-run-findings
status: active
summary: 统一合并 herdr-ccb-recent-changes 审计（11项发现）与 Herdr UI spike 全量采集运行发现（6项发现），交叉引用、状态同步、优先级重排
sources:
  - .codestable/audits/2026-08-05-herdr-ccb-recent-changes/index.md
  - .codestable/issues/2026-08-05-herdr-ui-spike-run-findings/herdr-ui-spike-run-findings-report.md
  - .codestable/issues/2026-08-05-herdr-ui-spike-run-findings/herdr-ui-spike-run-findings-analysis.md
  - .codestable/issues/2026-08-05-run-spike-audit-findings/run-spike-audit-findings-fix-note.md
  - .codestable/issues/2026-08-05-run-spike-audit-findings/run-spike-audit-findings-review.md
related:
  - herdr-ui-spike-run-findings-report.md
  - herdr-ui-spike-run-findings-analysis.md
tags:
  - unified
  - cross-reference
  - herdr-ui-integration
  - spike
  - audit
---

# 统一视图：herdr-ccb-recent-changes 审计 × Herdr UI Spike 运行发现

## 概述

本文档将两个来源的发现合并为单一优先级排序的行动清单：

- **审计来源**：`herdr-ccb-recent-changes`（近5次提交，11个文件，4个维度扫描）——11项发现
- **Spike 来源**：真实 Herdr UI 环境全量采集 `run-20260805-165854`——6项发现（F1–F6）

交叉引用后，去重合并得到 **15 项独立发现**（3项已修复、3项新增、9项待处理）。

---

## 一、发现映射表

### 1.1 审计 → Spike 交叉引用

| 审计# | 性质 | 严重度 | 状态 | Spike 交叉 | 说明 |
|-------|------|--------|------|-----------|------|
| 01 | bug | P0 | ✅ **已修复** | F3 相关 | pane capture session 已跟随 snapshot source；F3 暴露了分类逻辑中剩余的竞争问题 |
| 02 | bug | P1 | ⬜ 待处理 | — | `ccb8.cmd` 去掉 `-WindowStyle Hidden`，非 Herdr 环境闪窗 |
| 03 | bug | P1 | ⬜ 待处理 | — | `_attach_namespace` 前台附着错误分类粗糙 |
| 04 | bug | P2 | ⬜ 待处理 | — | `_logical_workspaces` 在 create_session 刚完成后可能返回空 |
| 05 | maint | P1 | ⬜ 待处理 | — | `run_spike.ps1` 与 `ccb8.ps1` 共享函数重复（本轮明确未修） |
| 06 | maint | P1 | ✅ **已修复** | — | pane verification 段缩进已重排 |
| 07 | maint | P2 | ✅ **已修复** | F5 相关 | `-OnlyDimension`/`-SkipDimension` 已实现；F5 暴露了运行时状态路径假设问题（独立于维度选择） |
| 08 | maint | P2 | ⬜ 待处理 | — | `_server_status_running` 嵌套状态路径，旧路径未标 deprecated |
| 09 | security | P1 | ⬜ 待处理 | — | `_command_evidence` 只脱敏 argv，错误 detail 中的 token 可能泄露 |
| 10 | security | P2 | ⬜ 待处理 | — | `_redacted_argv` send_text 脱敏逻辑依赖隐含的 argv 布局假设 |
| 11 | perf | P2 | ⬜ 待处理 | — | `_logical_workspaces` 在 create_session→ensure_window→list_windows 链路中重复查询 |

### 1.2 Spike → 审计交叉引用

| Spike# | 严重度 | 状态 | 审计交叉 | 说明 |
|--------|--------|------|----------|------|
| F1 | P1 | 🆕 **新增** | — | `ccb8 ps` 子命令路由错误：Python CLI 代码正确，根因在外部项目包装器层参数传递 |
| F2 | P1 | 🆕 **新增** | — | CCB Herdr 会话 socket 生命周期不稳定：两次 run 之间 socket 丢失 |
| F3 | P2 | 🆕 **新增证据** | 01（已修复）相关 | 分类逻辑 `ping-ccbd` vs `ping-all` 竞争：`ping-ccbd` 在 ccbd 完全启动前被调用，读到过渡态 `unmounted` |
| F4 | P2 | 📋 **已确认（设计）** | 01（已修复）相关 | Herdr 会话分叉是结构性设计——CCB 创建独立会话隔离 pane/workspace 管理。spike 已正确处理此场景，但依赖 F2 修复才能完成 CCB 会话采集 |
| F5 | P3 | 🆕 **新增证据** | 07（已修复）相关 | 启动状态文件 3/5 缺失：`CCB_RUNTIME_STATE_HOME` 重定位导致文件在 `D:\.c8\rs\{project_id}\ccbd\` 而非 `.ccb/ccbd/` |
| F6 | P3 | 📋 **非代码** | — | `manual-observation.md` 用户填写字段为空，需用户在 Herdr UI 运行后补填 |

---

## 二、统一优先级行动清单

### 🔴 P0 — 立即处理

| # | 来源 | 简述 | 动作 |
|---|------|------|------|
| — | — | **无当前 P0**（审计#01 已修复） | — |

### 🟠 P1 — 本迭代修复（5项）

| # | 来源 | 简述 | 推荐方案 |
|---|------|------|----------|
| **F1** | Spike 新增 | `ccb8 ps` 路由到 `start` 命令处理器 | 检查外部项目 `ccb8.ps1`/`ccb8.cmd` 实际版本，确认参数传递正确；在 Python CLI 增加 argv 诊断日志 |
| **F2** | Spike 新增 | CCB Herdr 会话 socket 缺失 | `CcbdApp.serve_forever()` 后增加 socket 可用性验证 + 重试 |
| **02** | 审计 | `ccb8.cmd` 去掉 `-WindowStyle Hidden` 导致非 Herdr 环境闪窗 | 恢复 `-WindowStyle Hidden` 或条件判断 Herdr 环境 |
| **05** | 审计 | `run_spike.ps1` 与 `ccb8.ps1` 共享函数重复 ~70行 | 提取到 `ccb8-shared.psm1`，本轮明确未修 |
| **09** | 审计 | 错误 detail 中的 restore_token 可能泄露到日志 | `_command_evidence` 增加通用脱敏 |

### 🟡 P2 — 排期修复（6项）

| # | 来源 | 简述 | 推荐方案 |
|---|------|------|----------|
| **F3** | Spike 新增 | 分类逻辑 `ping-ccbd` vs `ping-all` 竞争 | 分类决策链改用 `ping-all` agent 级状态（`$pingAllSuccess`）替代 `ping-ccbd` 守护进程级状态 |
| **03** | 审计 | `_attach_namespace` 错误分类粗糙 | 解析 stderr JSON 结构化错误；或扩展关键词匹配 |
| **04** | 审计 | `_logical_workspaces` create_session 后可能返回空 | 增加重试/轮询或直接使用 create_session 返回值 |
| **08** | 审计 | `_server_status_running` 嵌套状态旧路径未标 deprecated | 添加 deprecation warning / 注释 |
| **10** | 审计 | `_redacted_argv` 脱敏依赖隐含布局假设 | 显式定义 argv 布局契约或改用结构化匹配 |
| **11** | 审计 | `_logical_workspaces` 重复查询 | 在调用链中缓存 workspace 列表 |

### 🟢 P3 — 低优先级 / 非代码（3项）

| # | 来源 | 简述 | 推荐方案 |
|---|------|------|----------|
| **F5** | Spike 新增 | 启动状态文件采集路径错误（`CCB_RUNTIME_STATE_HOME` 重定位） | 从 `runtime-root-ref.json` 提取 `project_id` 构建正确路径 |
| **F6** | Spike | 用户观察字段为空 | 提醒用户在 Herdr UI 运行后填写 |
| **F4** | Spike | Herdr 会话分叉（设计确认） | spike 报告 Interpretation 增加说明；依赖 F2 修复后 CCB 会话采集可用 |

---

## 三、已修复项复核

| 审计# | 修复内容 | 复核来源 | 复核结论 |
|-------|----------|----------|----------|
| 01 | pane capture session 跟随 snapshot source | code review (passed) + spike run 确认 | ✅ 修复有效。Spike F3 暴露的是分类逻辑的独立竞争问题，非 pane capture session 问题 |
| 06 | pane verification 段重新缩进 | code review (passed) | ✅ 修复有效 |
| 07 | `-OnlyDimension` / `-SkipDimension` 参数 + 部分采集分类 | code review (passed) + SelfTest + 冒烟测试 | ✅ 修复有效。Spike F5 暴露的是独立于维度选择的运行时状态路径问题 |

---

## 四、新增发现详细说明

### F1: `ccb8 ps` 路由错误（P1）

- **现象**：`ccb8 ps` → exit=2, stderr=`start does not accept agent names or extra arguments`
- **定位**：Python CLI 代码（`SUBCOMMANDS`、`_COMMAND_PARSERS`、dispatch 表）均正确。`ccb8 doctor ps` 正常工作证明底层实现正确。根因在外部项目包装器层——`ccb8.ps1`/`ccb8.cmd` 的参数传递或 `ccb.cmd` shim 的 PATH 解析。
- **影响**：所有 `ccb8 ps` 使用者。替代命令 `ccb8 doctor ps` 可用。
- **方案**：A) 检查并同步外部项目包装器；B) Python CLI 增加 argv 诊断日志。

### F2: CCB Herdr 会话 socket 缺失（P1）

- **现象**：`herdr api snapshot --session ccb-avaprintdesigner-575a971f` → exit=1, `NotFound`。Run 133244 中 socket 存在但 stdout 为空，Run 165854 中 socket 完全不存在。
- **定位**：两次 run 之间 socket 生命周期不稳定——可能被 `ccb kill -f` prestart cleanup 销毁，或 Herdr server 进程在第一次 run 后崩溃。
- **影响**：CCB Herdr 会话对外不可查询，影响诊断、监控、spike 采集。
- **方案**：`CcbdApp.serve_forever()` 后增加 socket 可用性显式验证 + 重试。

### F3: 分类逻辑竞争（P2，新增证据）

- **现象**：`ping-ccbd` 返回 `mount_state: unmounted`，但 4 秒后 `ping-all` 返回两个 agent 均为 `mounted`。分类使用前者导致误判 `ccb-mounted-not-proven`。
- **定位**：`run_spike.ps1:1234` 用 `ping-ccbd`（守护进程级）而非 `ping-all`（agent 级，带重试）判断挂载状态。`ping-ccbd` 在 ccbd 启动中期（elapsed=2510ms）被调用，读到过渡态。
- **与审计#01 的关系**：审计#01（pane capture session 错位）已修复，但 F3 暴露的是**同一个分类决策链中的独立竞争问题**——即使 session 正确，分类结果仍可能因时序错误。
- **方案**：分类改用 `$pingAllSuccess`；或将 `ping-ccbd` 调用延迟到 `ping-all` 成功后。

### F5: 启动状态文件路径错误（P3，新增证据）

- **现象**：5 个待采集文件中 3 个缺失（`lease.json`, `keeper.json`, `lifecycle.json`）。无错误日志。
- **定位**：`CCB_RUNTIME_STATE_HOME=D:\.c8\rs` 将 ccbd 状态文件重定位到 `D:\.c8\rs\{project_id}\ccbd\`，但 spike 脚本仍假设在 `.ccb/ccbd/`。
- **与审计#07 的关系**：审计#07 关注采集维度选择性，已修复。F5 是独立的路径假设问题，不因维度选择而改变。
- **方案**：从 `runtime-root-ref.json` 提取 `project_id`，构建正确路径；失败时记录跳过原因。

---

## 五、审计 index.md 状态同步建议

审计 `index.md` 需更新以下条目以反映当前状态：

| # | 当前状态 | 建议更新 |
|---|----------|----------|
| 01 | P0 / cs-issue | ✅ **已修复** — pane capture session 跟随 snapshot source |
| 06 | P1 / cs-refactor | ✅ **已修复** — pane verification 段缩进已重排 |
| 07 | P2 / cs-refactor | ✅ **已修复** — `-OnlyDimension`/`-SkipDimension` 已实现 |
| — | — | 🆕 **新增 F1** — `ccb8 ps` 路由错误（P1 / cs-issue） |
| — | — | 🆕 **新增 F2** — CCB Herdr socket 缺失（P1 / cs-issue） |
| — | — | 🆕 **新增 F3** — 分类逻辑 ping-ccbd vs ping-all 竞争（P2 / cs-issue） |

---

## 六、下一步

1. **立即**：处理 F1（检查外部项目包装器版本）+ F2（socket 可用性验证）
2. **本迭代**：审计#02（闪窗）、#05（共享模块提取）、#09（detail 脱敏）
3. **排期**：审计#03、#04、#08、#10、#11 + F3（分类竞争）
4. **低优先级**：F5（启动文件路径）、F6（用户填写提醒）、F4（会话分叉文档）
5. **下次 spike 全量采集**：在 F1+F2 修复后重新运行默认全量采集，验证 CCB 会话 pane capture 证据完整性
