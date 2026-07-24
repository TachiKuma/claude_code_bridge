---
doc_type: issue-review
issue: 2026-07-24-rmux-pane-scroll-history
status: passed
reviewer: subagent
reviewed: 2026-07-24
round: 5
lane_a_state: completed
lane_a_ref: "019f9439-f41c-7402-bc96-bd4fa07b1580, 019f94a2-6c50-70f2-9999-d24a2c2e793f, 019f959b-f8e0-7201-9b6a-805d45d45fdd"
lane_a_reason: "round 5 针对 Codex pane 空 scrollback 与右键粘贴劫持追加复审；初审无 blocking，2 个 important 测试缺口已 closure"
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

## 9. Round 3 追加复审

### Scope

- 用户复测反馈：sidebar 焦点下按 `Q` 只关闭 sidebar，滚轮历史问题仍无改善。
- 追加 diff：`lib/cli/services/tmux_ui_runtime/service.py`、`test/test_v2_tmux_ui.py`、`tools/ccb-agent-sidebar/src/tui.rs`、本 fix-note。
- Review mode: full-rereview for material behavior change。

### Independent Review

- 环节 A：subagent `019f9439-f41c-7402-bc96-bd4fa07b1580` completed。
- 环节 B：OCR CLI 不可用，`ocr llm test` 返回 403 Forbidden。
- Gate effect：`reviewer: subagent`，可放行；OCR 不可用不阻塞。

### Findings

#### blocking

none

#### important

none

已关闭的 important：

- REV-003 `tools/ccb-agent-sidebar/src/tui.rs:149`：`KeyModifiers::SHIFT` 原先用 `contains()`，会把 `Ctrl+Shift+q` / `Alt+Shift+q` 也映射到 `KillProject`。已改为精确 `modifiers == KeyModifiers::SHIFT`，并补 `Ctrl+q`、`Alt+q`、`Ctrl+Shift+q` 回归断言。
- REV-004 `test/test_v2_tmux_ui.py`：原测试只验证 argv 字符串，不能证明 rmux 接受 `#{mouse_pane}` 绑定。已新增 `test_rmux_accepts_mouse_pane_project_ui_bindings`，检测到 rmux 时创建临时 session，调用真实 `_apply_sidebar_mouse_controls(... shell_commands_supported=False)`，并断言 `list-keys -T root` 包含 `-t "#{mouse_pane}"`。

#### nit

none

已处理的 nit：

- fix-note 旧段落仍描述 `-t =`。已在追加修复章节开头标注首次修复记录里的 `-t =` 方案已被 `#{mouse_pane}` 最终实现取代。

#### suggestion

- `service.py` 同时维护 `mouse_target` / `quoted_mouse_target`，后续可再收敛为更小 helper；本轮不为单点建议额外抽象。

### Test And QA Focus

- QA 必须重点复核：当前 WezTerm 前台真实滚轮事件中，agent pane 可进入 copy-mode 并滚动历史；重启 sidebar helper 后 `Shift+Q` / header `×` 触发 project kill，而普通 `q` 仍只关 sidebar。
- 不能靠 review 完全确认的点：真实 mouse event 下 `#{mouse_pane}` 是否始终为用户鼠标所在 pane；本轮已证明 rmux 0.9.0 接受绑定定义，但真实前台事件仍需手工复测。

### Targeted Verification

- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"`：通过。
- `python -m pytest -q "test/test_v2_tmux_ui.py"`：`13 passed, 2 skipped`。
- `cargo fmt --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --check`：通过。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" shifted_q_is_project_kill_across_terminal_key_encodings --quiet`：通过。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --quiet`：`54 passed`。
- `git diff --check -- ...`：通过，仅有 Windows 换行提示。

### Verdict

- Status: passed
- Next: 回到 issue fix 收尾；当前 live rmux session 的 mouse binding 已刷新，Rust sidebar helper 需要释放正在运行的 exe 后重建/重启才能让 `Shift+q` 修复进入当前 TUI。

## 10. Round 4 Windows rmux fallback 复审

### Scope

- 用户复测反馈：pane 需要双击才能定位；pane 中选择文档时鼠标实际位置与被选中文本错开一行。
- 追加 diff：`lib/cli/services/tmux_ui_runtime/service.py`、`test/test_v2_tmux_ui.py`、本 fix-note。
- Review mode: full-rereview for material behavior change + focused closure。

### Independent Review

- 环节 A：subagent `019f94a2-6c50-70f2-9999-d24a2c2e793f` completed。
- 环节 B：OCR CLI 不可用，`ocr llm test` 返回 403 Forbidden。
- Gate effect：`reviewer: subagent`，closure 后可放行；OCR 不可用不阻塞。

### Findings

#### blocking

none

已关闭的 blocking：

- REV-005 `lib/cli/services/tmux_ui_runtime/service.py`：Windows + rmux fallback 继续显式依赖 `-t =`，无法证明真实 mouse event target 可靠。已改为 mouse event context 方案，fallback 不再使用 `#{mouse_pane}` 或显式 `-t =`。

#### important

none

已关闭的 important：

- REV-006 普通 pane 左键语义不清。已明确本轮目标为一次点击选中 pane 并避免普通 pane 左键 mouse event 透传导致选区错位；fallback 默认动作改为 `select-pane -M`。
- REV-007 `MouseDown3Pane` fallback 全局 paste。已改为按 sidebar role 分流：sidebar 透传，非 sidebar 先 `select-pane -M` 再 paste。
- REV-008 live binding 测试只证明 `list-keys` 接受字符串。已调整为验证 fallback 不包含 `#{mouse_pane}` / 显式 `-t =`，并保留真实 WezTerm 前台复测为 residual risk。

#### residual-risk

- 真实 WezTerm 前台鼠标选择是否完全消除一行错位仍只能靠人工复测确认；当前 diff 已修正最直接的 fallback 绑定错误并刷新 live session。

### Targeted Verification

- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"`：通过。
- `python -m pytest -q "test/test_v2_tmux_ui.py" -k "windows_rmux_project_ui_avoids_shell_status_commands or rmux_accepts_mouse_context_project_ui_bindings"`：`2 passed, 13 deselected`。
- `python -m pytest -q "test/test_v2_tmux_ui.py"`：`13 passed, 2 skipped`。
- `cargo fmt --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --check`：通过。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" shifted_q_is_project_kill_across_terminal_key_encodings --quiet`：通过。
- `git diff --check -- ...`：通过，仅有 Windows 换行提示。
- 已刷新当前 live rmux session `ccb-claude_code_bridge-b72b0116` 的 root mouse 绑定；`list-keys` 确认目标绑定使用 `select-pane -M` / `copy-mode -e`，不使用 `#{mouse_pane}` 或显式 `-t =`。

### Verdict

- Status: passed
- Next: 用户在当前 WezTerm 前台复测 pane 单击定位、滚轮历史和文本拖选行对齐。

## 11. Round 5 Codex pane 空 scrollback 与右键粘贴复审

### Scope

- 用户复测反馈：非 sidebar pane 滚轮显示 `[0/0]`；只有 Claude pane 能滚历史，三个 Codex pane 不能滚；WezTerm 右键粘贴被非预期内容替代。
- 追加 diff：`lib/cli/services/tmux_ui_runtime/service.py`、`test/test_v2_tmux_ui.py`、本 fix-note。
- Review mode: full-rereview for material behavior change + focused closure。

### Independent Review

- 环节 A：subagent `019f959b-f8e0-7201-9b6a-805d45d45fdd` completed。
- 环节 B：OCR CLI 不可用，`ocr llm test` 返回 403 Forbidden。
- Gate effect：`reviewer: subagent`，closure 后可放行；OCR 不可用不阻塞。

### Findings

#### blocking

none

#### important

none

已关闭的 important：

- REV-009 live rmux 测试对 `MouseDown3Pane` 的不存在断言只检查过滤后的 `scoped_text`，有假阳性空间。已改为基于全量 `bind-key -T root` 行断言不存在 `MouseDown3Pane` / `M-MouseDown3Pane`。
- REV-010 测试只精确检查 `WheelUpPane`，不能证明 `WheelDownPane` 同样具备 `history_size` / `alternate_on` 分流。已分别提取 `WheelUpPane` / `WheelDownPane`，单元和 live 测试均断言两者包含 `pane_in_mode`、`history_size`、`alternate_on`、`copy-mode -e`，并分别匹配 `scroll-up` / `scroll-down`。

#### residual-risk

- `history_size=0` 的 Codex pane 是否能滚动取决于 Codex TUI 是否消费 mouse wheel；当前修复只能确认 CCB 不再把它错误送入 rmux 空 copy-mode。
- 右键粘贴是否完全恢复还取决于 WezTerm + rmux mouse mode 对未绑定 `MouseDown3Pane` 的处理；当前代码已移除 CCB 的 `paste-buffer -p` 劫持路径。

### Targeted Verification

- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"`：通过。
- `python -m pytest -q "test/test_v2_tmux_ui.py" -k "windows_rmux_project_ui_avoids_shell_status_commands or rmux_accepts_mouse_context_project_ui_bindings"`：`2 passed, 13 deselected`。
- `python -m pytest -q "test/test_v2_tmux_ui.py"`：`13 passed, 2 skipped`。
- `cargo fmt --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --check`：通过。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" shifted_q_is_project_kill_across_terminal_key_encodings --quiet`：通过。
- `git diff --check -- ...`：通过，仅有 Windows 换行提示。
- 已刷新当前 live rmux session `ccb-claude_code_bridge-b72b0116` 的 root mouse 绑定；`list-keys` 确认 `WheelUpPane` / `WheelDownPane` 包含 `history_size` / `alternate_on` 分流，且 `MouseDown3Pane` 不再由 CCB fallback 重新绑定。

### Verdict

- Status: passed
- Next: 用户在当前 WezTerm 前台复测 Codex pane 滚轮不再出现 `[0/0]`、Claude pane 仍可滚 rmux 历史、CLI 输入框右键粘贴恢复预期内容。
