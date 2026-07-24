---
doc_type: issue-review
issue: 2026-07-24-rmux-pane-id-exact-target
status: blocked
reviewed: 2026-07-24
round: 1
lane_a_state: unavailable
lane_a_ref: ""
lane_a_reason: "当前会话没有可同步返回的独立 Task agent review 工具；CCB ask 为 submit-only，不适合作为本轮同步 gate。"
lane_b_state: failed
lane_b_ref: ""
lane_b_reason: "ocr llm test returned 403 Forbidden from configured endpoint."
---

# rmux-pane-id-exact-target 代码审查报告

## 1. Scope And Inputs

- Design: none
- Checklist: none
- Issue report: `.codestable/issues/2026-07-24-rmux-pane-id-exact-target/rmux-pane-id-exact-target-report.md`
- Fix note: `.codestable/issues/2026-07-24-rmux-pane-id-exact-target/rmux-pane-id-exact-target-fix-note.md`
- Implementation evidence: 当前工作区 diff
- Diff basis: `git status --short` + 目标文件 `git diff`
- Review mode: initial
- Baseline dirty files: `ccb-src.ps1`, `lib/provider_backends/claude/launcher.py`, `lib/provider_backends/claude/launcher_runtime/service.py`, `.codestable/issues/2026-07-24-ccb-src-missing-drive-candidate-path/`

### Independent Review

- Detection: Task agent review unavailable for synchronous gate; OCR CLI exists but LLM test failed with 403.
- 环节 A 独立隔离 Task agent: local-only + unavailable
- 环节 B OCR CLI: failed
- OCR severity mapping: High→blocking/important, Medium→nit/suggestion, Low→discarded
- Merge policy: 没有可合并的外部 reviewer 结果；本报告只记录本地主 agent review。
- Gate effect: blocked until independent review is completed or owner explicitly approves local-only downgrade.

## 2. Diff Summary

- 新增：`.codestable/issues/2026-07-24-rmux-pane-id-exact-target/*`
- 修改：`lib/terminal_runtime/rmux_backend_runtime/panes.py`, `lib/terminal_runtime/rmux_backend_runtime/targets.py`, `lib/ccbd/services/project_namespace_runtime/backend.py`, `test/test_rmux_backend_core.py`, `test/test_v2_project_namespace_backend.py`
- 删除：none
- 未跟踪 / staged：本 issue 目录为新增未跟踪；另有既有无关未跟踪 issue 目录。
- 风险热点：rmux split 返回值 canonicalization 与 pane target canonicalization；影响 pane identity / option / respawn target 解析。

## 3. Adversarial Pass

- 假设的生产 bug：split 返回 exact id 和 index alias 的冲突分支选错，仍会把 agent1 绑定到 Claude pane。
- 主动攻击过的反例：`split-window` 返回 split 前已存在 `%2` 但新 pane 是 index 2 的 `%3`；`split-window` 返回 split 前不存在 `%3` 且应保留 exact；后续 target `%2` exact 位于 `list-panes` 后续行；无 window_name 的全局 / session 解析。
- 结果：新增 split 前快照判断，并用测试分别覆盖 exact 新 pane 与已有 id index alias 两种路径。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- rmux `%N` 在不同命令上下文中存在 stable id 与 index alias 双重语义。split 返回值需要结合 split 前 pane 集合判断，后续 target 则应 exact id 优先。

### praise

none

## 5. Test And QA Focus

- QA 必须重点复核：重启 / 重建 rmux namespace 后，`codex, agent1; claude, agent2` 是否形成 4 个唯一 agent pane，尤其确认 `agent1` Codex CLI 显示在左下 pane。
- 建议新增或加强的测试：已有单元测试覆盖 split alias 兼容和 target exact 优先。
- 不能靠 review 完全确认的点：当前运行中 namespace 尚未用新代码重建。

## 6. Residual Risk

- 独立 reviewer gate 未完成；本地审查未发现阻塞问题，但不能按 CodeStable gate 宣告 passed。

## 7. Verdict

- Status: blocked
- Next: 完成独立 Task agent review，或由 owner 明确批准 local-only review downgrade 后再进入提交收尾。

## 8. Focused Closure

none
