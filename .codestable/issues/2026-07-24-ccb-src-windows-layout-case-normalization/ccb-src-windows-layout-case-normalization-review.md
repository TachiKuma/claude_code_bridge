---
doc_type: issue-review
issue: 2026-07-24-ccb-src-windows-layout-case-normalization
status: passed
reviewer: subagent
reviewed: 2026-07-24
round: 1
lane_a_state: completed
lane_a_ref: "019f9421-5746-7521-bdab-b90787b3c7ec"
lane_a_reason: ""
lane_b_state: unavailable
lane_b_ref: ""
lane_b_reason: "ocr llm test failed: 403 Forbidden"
---

# ccb-src windows layout 大小写启动失败代码审查报告

## 1. Scope And Inputs

- Issue fix-note: `.codestable/issues/2026-07-24-ccb-src-windows-layout-case-normalization/ccb-src-windows-layout-case-normalization-fix-note.md`
- Implementation evidence: 本轮对话和验证命令输出
- Diff basis: 工作区 diff 中本轮可归因文件
- Review mode: initial
- Baseline dirty files: 工作区存在其他既有改动，例如 `ccb-src.ps1`、`lib/ccbd/services/project_namespace_runtime/backend.py`、`lib/terminal_runtime/rmux_backend_runtime/*` 等；本审查不覆盖这些文件。

### Independent Review

- Detection: multi-agent reviewer 可用；OCR CLI 存在但 `ocr llm test` 返回 403。
- 环节 A 独立隔离 Task agent: independent-agent completed。
- 环节 B OCR CLI: unavailable。
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion, Low->discarded。
- Merge policy: 独立 reviewer finding 已逐条本地核验；OCR 不可用不阻塞。
- Gate effect: `reviewer: subagent`，满足本轮 gate。

## 2. Diff Summary

- 新增：`.codestable/issues/2026-07-24-ccb-src-windows-layout-case-normalization/ccb-src-windows-layout-case-normalization-fix-note.md`
- 修改：`lib/agents/config_loader_runtime/parsing_runtime/topology.py`、`test/test_v2_config_loader.py`
- 删除：none
- 未跟踪 / staged：新增 issue 目录内 fix-note/review 属于本轮；其他 dirty 文件不归因本轮。
- 风险热点：配置解析规范化影响 windows topology 的 layout 渲染；无数据/权限/并发/UI 改动。

## 3. Adversarial Pass

- 假设的生产 bug：规范化 helper 可能只修 agent leaf，遗漏 tool alias 或丢失 provider/worktree/percent 信息。
- 主动攻击过的反例：mixed-case agent leaf、mixed-case `Rich` tool alias、layout plan 剪枝、provider/workspace/percent 字段保留路径。
- 结果：已补 mixed-case tool alias 测试；未发现 blocking/important。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [x] REV-001 `test/test_v2_config_loader.py:498` 独立 reviewer 建议补 mixed-case tool alias 测试。
  - Evidence: `_normalize_topology_layout_names` 同时处理 agent 和 layout tool alias。
  - Impact: 缺测试时 `Rich` 这类 mixed-case tool alias 规范化路径没有直接回归锁定。
  - Resolution: 已新增 `test_load_project_config_normalizes_mixed_case_windows_tool_alias`。

### learning

- windows topology 的内部 layout 表示必须和规范化后的 agent/tool 名保持一致，否则后续精确剪枝会出现“配置有效但启动无可见 pane”的断层。

### praise

none

## 5. Test And QA Focus

- QA 必须重点复核：mixed-case windows topology 配置启动。
- Evidence pack residual risks / gate warnings：OCR 不可用，已由独立 subagent + 本地行级审查覆盖。
- 建议新增或加强的测试：已补 mixed-case tool alias 单测。
- 不能靠 review 完全确认的点：工作区其他既有 dirty 文件与本修复的交互未审查。

## 6. Residual Risk

- 未跑全量测试；本次已跑配置解析、layout plan 和源码版启动冒烟。
- 工作区存在其他未归因改动，本 review 结论不能外推到整个工作区。

## 7. Verdict

- Status: passed
- Next: issue 修复可进入用户验收/提交收尾；不自动提交。

## 8. Focused Closure

- Closed findings: REV-001
- Attributed delta: `test/test_v2_config_loader.py`
- Targeted verification:
  - `python -m pytest test/test_v2_config_loader.py -k "mixed_case_windows_layout_names or mixed_case_windows_tool_alias or mixed_case_compact_agent_names"` passed。
  - `python -m pytest test/test_v2_layout_plan.py` passed。
- Classification: test-only 增量，不改变生产行为、公开契约、安全、数据、并发或架构。
