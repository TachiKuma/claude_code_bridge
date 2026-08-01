---
doc_type: feature-qa
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: failed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-07-27
round: 3
---

# windows-rmux-wezterm-native-interaction-parity QA 报告

## Round 4 Owner Foreground Retest（2026-07-27）

Owner 在 native Windows + WezTerm + rmux 前台完成 Round 3 QA-fix 后复测，结果为 1 PASS / 5 FAIL：

- 普通 pane 单击聚焦：PASS，能正常切换 pane。
- 普通 pane 拖拽选区：FAIL，拖拽无法选中任何字符串。
- 普通 pane 右键行为：FAIL，没有反应；即使先在其他软件复制，pane 中也无法粘贴。
- 普通 pane 滚轮行为：FAIL，WezTerm 中未观察到任何滚动行为。
- 侧栏 settings 点击：FAIL，没有反应。
- 侧栏 `x` KillProject 点击：FAIL，没有反应。

结论：QA 状态从 `blocked` 改为 `failed`。当前不是缺少证据，而是 owner 前台证据证明五条交互路径仍失败。下一步进入根因审查与 feature 拆分，不应继续把这六项压在单个 feature 内反复修。

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml`
- Review: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-review.md`（Round 3 `status: passed` / `reviewer: subagent`）
- Evidence pack: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-gate-results.json`
- DoD results: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-dod-results.json`
- Root-cause review: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/root-cause-review-and-feature-split.md`
- Diff basis: 当前工作区 diff；QA 范围为本 feature 的 mouse binding / sidebar TUI 测试与 evidence 更新。
- Baseline dirty files: `.codestable/reference/agent-conventions.md` 来自 runtime sync；`bin/ccb-agent-sidebar.exe` 为进入本轮前已有 binary dirty；不纳入本 QA verdict。
- Feature type: mixed，含用户可见 Windows/rmux/WezTerm 前台交互核心路径。
- Core evidence gate: AC-001 至 AC-006 已有自动化或 live rmux 证据；AC-007 中 sidebar `⚙`、sidebar `x`、拖选行偏移重新归因仍需要 owner 真实前台复测。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | AC-001/002/003/004/006/008 | core-functional | Windows/rmux fallback mouse binding：sidebar passthrough、ordinary focus、无 copy-mode/paste-buffer/header c/Q 模拟 | unit | `python -m pytest -q -rs test/test_v2_tmux_ui.py` | targeted UI tests pass | pass |
| QA-002 | CMD-006 / review focus | core-functional | live rmux root binding 接受 `if-shell -F -t =`，sidebar left/wheel 透传，ordinary 不进入 copy-mode/scroll/paste-buffer | live integration | `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings` | live test pass, not skip | pass |
| QA-003 | AC-005 | core-functional | Q / Shift+Q 均映射 KillProject | unit | `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml shifted_q_is_project_kill_across_terminal_key_encodings --quiet` | test pass | pass |
| QA-004 | AC-004/008 | core-functional | Rust sidebar header hit-test 与 settings/x 派发路径在 Windows 也参与测试 | unit | `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml --quiet` | header tests and full sidebar suite pass | pass |
| QA-005 | review gate | core-functional | Round 3 independent review 无 blocking / important | review artifact | review report frontmatter | `status: passed`, `reviewer: subagent` | pass |
| QA-006 | AC-007 | core-functional | native Windows + WezTerm + rmux 前台复测 sidebar `⚙`、sidebar `x`、拖选行偏移 | manual | owner foreground operation transcript | 新实现真实观察并记录 | failed |
| QA-007 | cleanliness | supporting | 无新增 debug/TODO/FIXME/XXX/临时输出 | static scan | `rg -n ...` | no new matches | pass |

## 3. Command Results

- `python -m pytest -q -rs test/test_v2_tmux_ui.py` -> exit 0：`13 passed, 2 skipped in 0.86s`。
- `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings` -> exit 0：`1 passed, 14 deselected in 0.51s`。
- `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml --quiet` -> exit 0：`56 passed`。
- `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml shifted_q_is_project_kill_across_terminal_key_encodings --quiet` -> exit 0：`1 passed`。
- `python -m py_compile lib/cli/services/tmux_ui_runtime/service.py test/test_v2_tmux_ui.py` -> exit 0。
- `validate-yaml.py --file ...checklist.yaml --yaml-only` -> exit 0：`1 passed, 0 failed`。
- 清洁度 `rg` -> 命中 `tools/ccb-agent-sidebar/src/tui.rs:2440` 的既有测试 fixture `print('ccb')` 字符串；本轮 diff 未新增 debug/TODO/FIXME/XXX。
- 未运行：native Windows + WezTerm + rmux 前台手工复测。原因：当前 agent 不能物理执行/观察 GUI 鼠标操作；这是 AC-007 核心用户路径，阻塞 QA passed。

## 4. Scenario Results

- [x] QA-001 fallback binding 内容：pass。
  - Evidence: fake backend 断言 `MouseDown1Pane`、`MouseDown1Border`、`WheelUpPane`、`WheelDownPane` 均为 `if-shell -F -t = '#{==:#{@ccb_role},sidebar}' 'select-pane -t = ; send-keys -t = -M' 'select-pane -t ='`；不含 `#{mouse_x}`、`#{mouse_y}`、`send-keys -t = c`、`send-keys -t = Q`、`select-pane -M`、`paste-buffer`、`scroll-up/down`。
- [x] QA-002 live rmux binding：pass。
  - Evidence: `evidence/live-binding-snapshot.txt` 记录 rmux 接受 `MouseDown1Pane`、`MouseDown1Border`、`WheelUpPane`、`WheelDownPane` 四条 scoped binding。
- [x] QA-003 / QA-004 Rust sidebar TUI：pass。
  - Evidence: full Cargo suite 56 passed；header hit-test 测试已在 Windows 运行，`Q` / `Shift+Q` KillProject targeted test passed。
- [x] QA-005 review gate：pass。
  - Evidence: Round 3 review `status: passed` / `reviewer: subagent`。
- [ ] QA-006 WezTerm GUI foreground manual：failed。
  - Evidence: owner 在 2026-07-27 前台复测记录 1 PASS / 5 FAIL；`evidence/root-cause-review-and-feature-split.md` 已把失败拆成六个细粒度 feature。
  - Notes: 当前不是缺少复测，而是复测已经证明原 feature 未达到验收。继续处理前必须进入根因拆分后的子 feature，不得直接进入 acceptance。

## 5. Findings

### failed

- [ ] QA-006 AC-007 native Windows + WezTerm + rmux 前台复测失败。
  - Evidence: owner 前台复测结果为 1 PASS / 5 FAIL；根因审查见 `evidence/root-cause-review-and-feature-split.md`。
  - Impact: 该 feature 的原验收目标过宽，且自动化只证明绑定字符串与负向命令断言，不能证明 WezTerm GUI-native 行为或 sidebar e2e mouse dispatch。
  - Expected fix scope: 拆成 `ordinary-pane-single-click-focus-baseline`、`sidebar-settings-click-e2e`、`sidebar-kill-project-click-e2e`、`ordinary-pane-drag-selection-native`、`ordinary-pane-right-click-paste`、`ordinary-pane-wheel-scroll` 后分别设计、修复、review、QA。

### blocked

none

### residual-risk

- 右键粘贴与 ordinary pane 原生滚轮不能再按 approved design 作为 GUI-native residual 记录；前台证据已证明它们失败，需要独立策略选择。
- 拖选行偏移不能直接归为 rmux 外部 residual；需要在 `ordinary-pane-drag-selection-native` 中验证 mouse off / Shift bypass / copy-mode 方案。
- sidebar settings/x 不能先归因到 Rust hit-test；需要在 e2e 诊断 feature 中确认 rmux `send-keys -M` 是否到达 crossterm `Event::Mouse`。

## 6. Cleanliness

- Debug output: pass；清洁度扫描仅命中既有测试 fixture 字符串。
- Temporary TODO/FIXME/XXX: pass。
- Commented-out code: pass。
- Unused imports / dead code from this feature: pass；Python fallback helper已删除。
- Out-of-scope files: pass for QA scope；工作区存在前序 runtime sync 和既有 binary dirty，不纳入本 verdict。

## 7. Verdict

- Status: failed
- Next: 独立根因审查 WezTerm/rmux/CCB mouse event 链路，并把六项交互验收拆成更细 feature；修复后必须重新 code review，再重跑 QA。QA passed 前不得进入 acceptance。
