---
doc_type: issue-review
issue: 2026-08-05-herdr-ui-spike-run-findings
status: passed
reviewer: subagent+ocr
reviewed: 2026-08-05
round: 1
lane_a_state: completed
lane_a_ref: "agent:a79ad9eef7a66242a"
lane_a_reason: ""
lane_b_state: completed
lane_b_ref: "ocr:2026-08-05-herdr-ui-spike-run"
lane_b_reason: ""
---

# herdr-ui-spike-run-findings 代码审查报告

## 1. Scope And Inputs

- Issue report: `.codestable/issues/2026-08-05-herdr-ui-spike-run-findings/herdr-ui-spike-run-findings-report.md`
- Issue analysis: `.codestable/issues/2026-08-05-herdr-ui-spike-run-findings/herdr-ui-spike-run-findings-analysis.md`
- Issue fix-note: `.codestable/issues/2026-08-05-herdr-ui-spike-run-findings/herdr-ui-spike-run-findings-fix-note.md`
- Diff basis: 当前工作区 unstaged diff (5 files modified + 3 untracked)
- Review mode: initial
- Baseline dirty files: `.codestable/` spec 文件为本轮 spec 产物，非审查对象

### Independent Review

- Detection: 独立 Task agent 可用（general-purpose agent）；OCR CLI 可用（open-code-review, gpt-5.4）
- 环节 A 独立隔离 Task agent: completed — 发现 2 blocking, 3 important, 3 nit, 2 suggestion, 2 learning, 3 praise, 3 residual-risk
- 环节 B OCR CLI: completed — 5 条发现（2 bug medium, 1 security medium, 1 maintainability low, 1 bug medium）
- OCR severity mapping: High→blocking/important, Medium→nit/suggestion, Low→discarded
- Merge policy: 两环节结果均已逐条本地核验后合并；范围外发现标注为 out-of-scope
- Gate effect: `reviewer: subagent+ocr` → gate 放行

## 2. Diff Summary

- 新增：`approval-report.md`, `fix-note.md`, `unified.md` (.codestable/, spec-only)
- 修改：
  - `lib/cli/entrypoint_runtime.py` — F1: argv 诊断日志
  - `lib/ccbd/services/project_namespace_runtime/ensure_identity.py` — F2: Herdr session socket 验证
  - `.codestable/roadmap/.../run_spike.ps1` — F3: 分类逻辑 + F5: 启动文件路径
  - `.codestable/audits/.../index.md` — 状态同步
  - `.codestable/issues/.../analysis.md` — frontmatter 更新
- 删除：none
- 风险热点：ccbd 启动路径（socket 验证）、PowerShell 采集流程（分类逻辑/文件路径）、Python CLI 入口（诊断日志）

## 3. Adversarial Pass

- 假设的生产 bug：F2 socket 验证从未实际执行——`backend.list_windows({'session_name': ...})` 缺少 `namespace_id`，导致 `_logical_workspaces` 在 `namespace_id=""` 时立即返回 `[]`，从未发起 Herdr API 调用
- 主动攻击过的反例：
  - **B1**: F2 socket 验证是空操作（已修复：改用 `backend.py` 的 `list_windows()` 正确构建 namespace_ref）
  - REV-004: F5 `$ccbdFilesCollected` 单布尔值导致跨目录文件漏采（已修复：改为按文件 hashtable 跟踪）
  - F3: ping-all 成功时正确跳过 ping-ccbd → 逻辑正确；ping-all 失败回退路径的竞态属于极端边缘情况
  - F1: `CCB_DEBUG_ARGV=1` 时日志写入 stderr → gated behind env var，可接受
- 结果：2 项 blocking 已修复（B1 + REV-004），其余为 nit/suggestion 或范围外

## 4. Findings

### blocking

- [x] **B1** `ensure_identity.py:36-40` `_verify_herdr_session_socket` 是空操作——`backend.list_windows({'session_name': session_name})` 缺少 `namespace_id`，`_logical_workspaces` 在空 `namespace_id` 时立即返回 `[]`，从未实际接触 Herdr socket（来源: independent-agent, 本地核验确认）→ ✅ **已修复**
  - Evidence: `cli.py:199` 提取 `namespace_id = str(payload.get("namespace_id") or "").strip()` → 为 `""`；`cli.py:810-811` `if not namespace_anchor: return []` 在调用 `_workspaces()` 之前短路
  - Fix: 使用 `backend.py` 的 `list_windows(session_name=...)` 通过 `_mux_namespace_ref` 正确构建包含 `namespace_id` 的 payload
  - Verification: Python syntax check passed

### important

- [x] **REV-004** `run_spike.ps1:1011-1022` `$ccbdFilesCollected` 在首个文件成功复制后 break 外层目录循环——分散在不同目录的文件漏采（来源: ocr, 本地核验确认）→ ✅ **已修复**
  - Fix: 改为 `$copiedCcbdFiles` hashtable 按文件跟踪
  - Verification: PowerShell `-SelfTest` passed

### nit

- [x] **REV-003** `ensure_identity.py:113` `timeout_s <= 0` 不会禁用等待（来源: ocr, 本地核验确认）→ ✅ **已修复**

- [ ] **N1** `entrypoint_runtime.py:232` 函数体内 `import os`——非惯用写法，建议提升到文件级别（来源: independent-agent）
  - Impact: 仅风格问题，`os` 是标准库，`os.environ.get` 开销可忽略

- [ ] **N2** `ensure_identity.py:127-131` 超时 warning 不含最后异常上下文，事后诊断困难（来源: independent-agent）

### suggestion

- [ ] **REV-001** `entrypoint_runtime.py:235` argv 诊断日志无脱敏——`CCB_DEBUG_ARGV=1` 时完整 argv 写入 stderr（来源: ocr）
  - Suggestion: 对已知敏感 flag 做值替换为 `***`；或保持现状并在注释中标注"仅开发诊断"

- [ ] **REV-002** `ensure_identity.py:36-40` `_verify_herdr_session_socket` 返回值被忽略，socket 验证超时后后续 `ensure_window` 仍执行（来源: ocr）
  - 当前设计（软验证）符合分析阶段"不阻塞启动"的决策；短期可返回 bool 供调用侧记录状态

- [ ] **S1** `run_spike.ps1:1003` `catch { }` 空块——`runtime-root-ref.json` JSON 解析失败时静默回退，无诊断日志（来源: independent-agent）
  - Suggestion: catch 块中向 manifest 写入 `failed to parse runtime-root-ref.json : $_`

### learning

- F3 分类逻辑修复模式（权威信号优先 → 辅助信号回退）值得在其他时序敏感的分类场景复用
- `_logical_workspaces` 在 `namespace_id=""` 时返回 `[]` 是设计如此（无法为未知 namespace 过滤），但给调用者创造了"无声空返回"的陷阱——B1 发生的机制性原因

### praise

- F2 `_verify_herdr_session_socket` 的 docstring 清晰解释了设计意图（软验证、不阻塞启动）
- F5 的 "skipped" manifest 条目包含搜索路径列表，便于事后排查

## 5. Test And QA Focus

- QA 必须重点复核：真实 Herdr UI 环境默认全量采集，验证：
  1. **F2 真实 socket 验证**：B1 修复后，`herdr-api-snapshot-ccb-namespace` 不再返回 `NotFound`（需 Herdr UI 环境）
  2. **F3 分类结果**：`summary.json` `classification` 为 `mounted-with-herdr-panel-observation` 而非 `ccb-mounted-not-proven`
  3. **F5 文件采集完整性**：`startup-state-files-manifest.txt` 包含 `lease.json`、`keeper.json`、`lifecycle.json`
- 建议新增或加强的测试：
  - `_verify_herdr_session_socket` 单元测试（mock 后端验证正确 payload 发送到 `list_windows`）
  - `CCB_DEBUG_ARGV=1 ccb8 ps` 诊断日志端到端验证
- 不能靠 review 完全确认的点：
  - B1 修复后的 socket 验证在真实 Windows Herdr 环境中的效果（需现场测试）
  - F1 主修复仍在外部项目 `.ps1`/`.cmd` 中，防御性日志仅为诊断辅助

## 6. Residual Risk

- **范围外 blocking — B2** `cli.py:758-760` `_attach_namespace` 的 `herdr session attach` 调用无 timeout/capture_output，可能无限期挂起 ccbd（来源: independent-agent）。此为审计 finding 03，非本轮 diff 范围，但应在该 finding 修复时处理
- **范围外 important — I2** `run_spike.ps1:1278-1280` 部分维度运行时 `partial-dimension-*` 无条件覆盖真实分类。此为既有行为，非本轮修改
- F2 socket 验证是软验证（失败仅 warning 不阻塞启动），不能 100% 保证 Herdr socket 可用
- F1 仅加了防御性诊断日志，主修复在外部项目
- `_verify_herdr_session_socket` 的 `except Exception` 仍较宽泛（I3），建议后续收窄为 `MuxCommandErrorV2` + `OSError`

## 7. Verdict

- Status: passed
- Next: 修复闭环 → 按 cs-issue fix 协议进入 ConfirmFixCompletion checkpoint → 用户确认后 commit

## 8. Focused Closure

none
