---
doc_type: approval-report
issue: 2026-08-05-herdr-ui-spike-run-findings
checkpoint: ConfirmFixPlan
created: 2026-08-05
status: approved
---

# Fix Plan Approval：Herdr UI Spike 运行发现

## 决策概要

根因分析覆盖 6 项发现（F1–F6），每项均有 2–3 种修复方案及推荐。以下按优先级汇总，**请逐项确认或选择替代方案**。

---

## P1 — 本迭代修（2 项需代码改动）

### F1：`ccb8 ps` 子命令路由错误

- **根因**：config — Python CLI 代码正确，外部项目包装器层参数传递不一致
- **推荐**：方案 A — 检查外部项目 `ccb8.ps1`/`ccb8.cmd` 实际版本，同步修复参数传递；同时在 Python CLI `entrypoint_runtime.py` 增加 argv 诊断日志（防御层）
- **影响面**：`ccb8.ps1`、`ccb8.cmd`（外部项目）+ `lib/cli/entrypoint_runtime.py`（本仓库，仅加日志）
- **替代**：方案 B — 仅 Python CLI 加诊断日志，不修包装器（不直接修复，只改善下次定位能力）

### F2：CCB Herdr 会话 socket 缺失

- **根因**：concurrency — Herdr server socket 在 ccbd 重启周期间生命周期不稳定
- **推荐**：方案 A — `CcbdApp.serve_forever()` 后增加 socket 可用性显式验证 + 重试（最多 N 次）
- **影响面**：`lib/ccbd/main.py`、`lib/ccbd/services/project_namespace_runtime/ensure_identity.py`
- **替代**：方案 B — 仅在 spike 脚本增加 socket 等待/重试（改动小但不解决根本问题）

---

## P2 — 排期修（2 项需代码改动 + 1 项文档）

### F3：分类逻辑 ping-ccbd vs ping-all 竞争

- **根因**：concurrency — `ping-ccbd` 在 ccbd 完全启动前被调用，读到过渡态 `unmounted`
- **推荐**：方案 A — 将分类决策改用 `ping-all` 的 agent 级状态（`$pingAllSuccess`），替换 `ping-ccbd` 的守护进程级状态
- **影响面**：仅 `run_spike.ps1:1230-1244`
- **替代**：方案 B — 延迟 `ping-ccbd` 调用时机到 `ping-all` 成功后

### F5：启动状态文件采集路径错误

- **根因**：config — `CCB_RUNTIME_STATE_HOME` 重定位后文件在 `D:\.c8\rs\{project_id}\ccbd\`，脚本仍假设 `.ccb/ccbd/`
- **推荐**：方案 A — 从 `runtime-root-ref.json` 提取 `project_id`，构建正确路径
- **影响面**：仅 `run_spike.ps1:973-1018`
- **替代**：方案 B — 仅记录缺失原因，不改路径逻辑（不实际修复）

### F4：Herdr 会话分叉

- **根因**：config — 结构性设计，非 bug
- **推荐**：仅文档说明 — 在 spike 报告 Interpretation 节标注包装器会话为空是预期行为
- **影响面**：无代码改动

---

## P3 — 非代码

### F6：用户观察字段为空

- **根因**：missing-guard — 用户尚未填写
- **推荐**：提醒用户在下次 Herdr UI 运行 spike 后补填 `manual-observation.md`

---

## 推荐执行顺序

1. **先修 F1 + F2**（P1，阻塞后续验证）
2. **再修 F3 + F5 + F4 文档**（P2，改善采集准确性）
3. **F6** 下次运行时提醒用户补填
4. **全部修复后**：在 Herdr UI 环境重新运行默认全量采集，确认真实 CCB 会话 pane capture 证据完整性

---

## 需用户确认

请对每项回复：
- ✅ 同意推荐方案
- 🔄 选替代方案（如 "F1 用方案 B"）
- ❌ 暂不修（如 "F3 排到下个迭代"）
- 💬 其他意见
