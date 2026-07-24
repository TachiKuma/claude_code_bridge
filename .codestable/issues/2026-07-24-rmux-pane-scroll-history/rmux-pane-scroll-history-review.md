---
doc_type: issue-review
issue: 2026-07-24-rmux-pane-scroll-history
status: passed
reviewer: subagent
reviewed: 2026-07-24
round: 2
lane_a_state: completed
lane_a_ref: "019f9385-25e5-7df0-b7b8-9ab468f18930, 019f938b-6bb7-7e70-86e7-7e2feab55099"
lane_a_reason: "第一轮发现条件未显式 target 鼠标 pane；closure 修复后第二轮复审 blocking none"
lane_b_state: unavailable
lane_b_ref: ""
lane_b_reason: "ocr llm test 返回 403 Forbidden"
---

# rmux-pane-scroll-history 代码审查报告

## 1. Scope And Inputs

- Issue fix-note: `.codestable/issues/2026-07-24-rmux-pane-scroll-history/rmux-pane-scroll-history-fix-note.md`
- Implementation evidence: 当前对话、git diff、rmux session 现场绑定刷新与 list-keys 验证
- Diff basis: `git status --short` + `git diff -- lib/cli/services/tmux_ui_runtime/service.py test/test_v2_tmux_ui.py .codestable/issues/2026-07-24-rmux-pane-scroll-history/rmux-pane-scroll-history-fix-note.md`
- Review mode: initial + focused closure
- Baseline dirty files: `ccb-src.ps1` 为此前源码路径中文目录修复；`笔记.md` 为未跟踪文件。本审查未纳入。

### Independent Review

- Detection: subagent 可用；OCR CLI 存在但 `ocr llm test` 失败，返回 403。
- 环节 A 独立隔离 Task agent: subagent completed。第一轮 verdict 为 changes-requested，第二轮确认 blocking 已关闭。
- 环节 B OCR CLI: unavailable。
- OCR severity mapping: 未执行；原因是 provider 403。
- Merge policy: subagent finding 已逐条用本地 diff、测试和 rmux 命令核验。
- Gate effect: `reviewer: subagent`，可放行；OCR 不可用不阻塞。

## 2. Diff Summary

- 新增：`.codestable/issues/2026-07-24-rmux-pane-scroll-history/rmux-pane-scroll-history-review.md`
- 修改：`lib/cli/services/tmux_ui_runtime/service.py`、`test/test_v2_tmux_ui.py`、`.codestable/issues/2026-07-24-rmux-pane-scroll-history/rmux-pane-scroll-history-fix-note.md`
- 删除：none
- 未跟踪 / staged：`笔记.md` 未跟踪；无 staged diff
- 风险热点：tmux/rmux 鼠标事件、pane target、Windows + WezTerm 前台交互

## 3. Adversarial Pass

- 假设的生产 bug：鼠标事件发生在 agent pane，但绑定条件仍按 sidebar 焦点 pane 求值，导致 wheel/header 分流错误。
- 主动攻击过的反例：sidebar 有焦点时在 agent pane 滚轮；点击 sidebar header 时事件透传不到 Rust TUI；nested `if-shell` 漏掉 `-t =`；Windows rmux 不支持 shell status command。
- 结果：第一轮 subagent 找到 `if-shell` 条件未显式 target 鼠标 pane 的 blocking；已修为外层和内层条件均使用 `if-shell -F -t =`，并补测试断言。

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

- rmux/tmux 鼠标绑定中，动作命令带 `-t =` 还不够；格式条件本身也要用 `if-shell -F -t =`，否则可能按焦点 pane 求值。

### praise

- 修复复用了 Rust sidebar 现有键盘入口：`⚙` 映射 `c`，`×` 映射 `Q`，没有新增并行的 Python 行为路径。

## 5. Test And QA Focus

- QA 必须重点复核：在 WezTerm 前台 TUI 中，用鼠标点击 sidebar `⚙`，并在 agent pane 使用滚轮查看聊天历史。
- Evidence residual risks / gate warnings：OCR provider 不可用；真实鼠标事件仍需前台手工确认。
- 建议新增或加强的测试：当前单测已断言外层 `if-shell -F -t =`、内层 wheel action、header nested 分支的 `-t =` 出现次数；无需为本次再加 live rmux 集成测试。
- 不能靠 review 完全确认的点：WezTerm 前台实际鼠标事件是否按 rmux 0.9.0 预期触发。

## 6. Residual Risk

- `×` 的现有语义是 `KillProject`，不是关闭 sidebar。若用户期望关闭 sidebar，应另开 feature / UX 调整。
- 本地已刷新当前 rmux session 绑定，但最终仍需用户在正在使用的 WezTerm TUI 里确认鼠标点击和滚轮行为。

## 7. Verdict

- Status: passed
- Next: 回到 issue fix 收尾；等待用户在前台 TUI 做最终手工确认。

## 8. Focused Closure

- Closed findings: 第一轮 subagent blocking“滚轮/header 条件未显式绑定鼠标所在 pane”；第一轮 important“fix-note 未记录本轮范围”；第二轮 important“border header 测试断言有轻微假阳性空间”。
- Attributed delta: `service.py` 为所有相关 `if-shell` 条件补 `-t =`；`test_v2_tmux_ui.py` 增加 argv 结构和 nested command 断言；fix-note 补记录。
- Targeted verification:
  - `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"`：通过。
  - `python -m pytest -q "test/test_v2_tmux_ui.py"`：`12 passed, 2 skipped`。
  - `rmux -L <session> if-shell -F -t %1 "#{pane_id}" "display-message ok" "display-message no"`：通过。
  - `rmux -L <session> list-keys -T root`：确认相关绑定包含 `if-shell -F -t =`。
- Classification: closure 只收紧本轮修复行为和测试证据，没有改变公开 API、数据、安全或并发边界。
