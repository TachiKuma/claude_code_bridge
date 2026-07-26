---
doc_type: feature-qa
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: blocked
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-07-26
round: 2
---

# windows-rmux-wezterm-native-interaction-parity QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml`
- Review: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-review.md`（Round 2 当前为 `blocked`：focused re-check pending）
- Evidence pack: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-dod-results.json`
- Diff basis: 当前工作区 diff；QA 仅覆盖本 feature scope。
- Baseline dirty files: 工作区存在其他 roadmap/design、binary、provider runtime 改动；未纳入本 QA 裁决。
- Feature type: mixed，含用户可见 Windows/rmux/WezTerm 前台交互核心路径。
- Core evidence gate: AC-001 至 AC-006 有自动化或 live rmux 证据；AC-007 需要真实前台 WezTerm 手工操作 transcript。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | AC-001/002/003/004/006/008 | core-functional | Windows/rmux fallback mouse binding：外层 `if-shell -F -t =`、ordinary pane focus、sidebar 透传、不劫持 copy-mode/paste-buffer | unit | `python -m pytest -q -rs test/test_v2_tmux_ui.py` | targeted UI tests pass | pass |
| QA-002 | CMD-006 / review focus | core-functional | rmux 接受 root mouse bindings，且 live `list-keys` 含 `if-shell -F -t =` / `select-pane -t =` / `send-keys -t = -M` | live integration | `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings` | live test pass, not skip | pass |
| QA-003 | AC-005 | core-functional | Q / Shift+Q 均映射 KillProject | unit | `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" shifted_q_is_project_kill_across_terminal_key_encodings --quiet` | test pass | pass |
| QA-004 | AC-007 | core-functional | native Windows + WezTerm + rmux 新实现前台单击、sidebar settings、sidebar `x`；右键/滚轮/拖选残留分类 | manual | human foreground operation transcript | 新实现直接观察并记录 | blocked |
| QA-005 | cleanliness | supporting | 无 debug/TODO/FIXME/XXX/临时输出 | static scan | `rg -n "TODO|FIXME|XXX|print\\(|console\\.log|console\\.error|fmt\\.Println" ...` | no matches | pass |
| QA-006 | review gate | core-functional | code review focused re-check 已返回并关闭 B1/B2 | review artifact | `windows-rmux-wezterm-native-interaction-parity-review.md` | status passed | blocked |

## 3. Command Results

- `python -m pytest -q -rs test/test_v2_tmux_ui.py` -> exit 0：`13 passed, 2 skipped in 0.87s`。
- `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings` -> exit 0：`1 passed, 14 deselected in 0.49s`。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" shifted_q_is_project_kill_across_terminal_key_encodings --quiet` -> exit 0：`1 passed`。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --quiet` -> exit 0：`54 passed`。
- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"` -> exit 0。
- 清洁度 `rg` -> exit 1：无匹配，视为 pass。
- 未运行：新实现真实前台鼠标手工操作 transcript。原因：当前 agent 能运行命令和 live rmux list-keys，但不能物理执行或观察 GUI 鼠标交互；这是核心功能路径，阻塞 QA passed。
- Code review：Round 2 independent focused re-check 已启动但尚未返回，阻塞 QA passed。

## 4. Scenario Results

- [x] QA-001 普通 pane wheel/right-click/left-click fallback：pass。
  - Evidence: unit test 精确断言 fallback 外层条件为 `if-shell -F -t =`；ordinary pane action 为 `select-pane -t =`；sidebar branch 为 `select-pane -t = ; send-keys -t = -M`；不含 `select-pane -M`、`copy-mode -e`、`scroll-up/down`、`paste-buffer -p`。
- [x] QA-002 live rmux binding：pass。
  - Evidence: live rmux test passed，`evidence/live-binding-snapshot.txt` 已更新为当前 `list-keys` 输出，四个 scoped binding 均包含 `if-shell -F -t =`。
- [x] QA-003 KillProject 键盘编码：pass。
  - Evidence: Rust targeted test passed。
- [ ] QA-004 WezTerm GUI foreground manual：blocked。
  - Evidence: `evidence/manual-wezterm-runbook.md` status 为 `partial`，记录的是旧实现观测；QA Disposition 明确要求新实现完成后重测。
  - Notes: 不能用 unit/live binding 替代真实用户前台鼠标路径；新实现至少需要单击聚焦、sidebar `⚙`、sidebar `x` 直接观察为 pass。
- [ ] QA-006 Code review gate：blocked。
  - Evidence: `windows-rmux-wezterm-native-interaction-parity-review.md` Round 2 为 `status: blocked`，lane A focused re-check pending。

## 5. Findings

### failed

none

### blocked

- [ ] QA-004 AC-007 缺新实现真实前台 GUI 手工 transcript。
  - Evidence: `evidence/manual-wezterm-runbook.md` 仍为 `status: partial`，且 QA Disposition 写明“AC-007 待新方案实现完成后重测”。
  - Impact: design 将 AC-007 标为 core；QA 协议禁止把功能性核心路径未运行写成 residual-risk 后 passed。
  - Expected fix scope: 需要 human/operator 在 native Windows + WezTerm + rmux 前台执行并记录：单击聚焦、sidebar `⚙` settings、sidebar `x` KillProject 应 pass；右键粘贴、滚轮、拖选起点行 off-by-one 按 design 残留分类记录。
- [ ] QA-006 code review focused re-check 未返回。
  - Evidence: review 报告 Round 2 lane A ref `agent:019fa074-b8cb-73e0-ba8c-b6a383e41718/submission:019fa079-6e46-7bf3-bf7f-8fa075d42502` 仍 pending。
  - Impact: 已启动独立 reviewer 时，不得在 reviewer 返回前定稿 QA passed。
  - Expected fix scope: 等待 focused re-check；若 changes-requested，先修复；若 passed，再解除该 QA blocker。

### residual-risk

- 右键粘贴、原生滚轮、拖选起点行 off-by-one 按 revised design 作为 GUI-native / rmux 外部残留记录；但仍需前台手工 runbook 对新实现结果重新归类。

## 6. Cleanliness

- Debug output: pass。
- Temporary TODO/FIXME/XXX: pass。
- Commented-out code: pass。
- Unused imports / dead code from this feature: pass。
- Out-of-scope files: pass for QA scope；全工作区存在既有 dirty/untracked，不归入本 feature QA。

## 7. Verdict

- Status: blocked
- Next: 等待 code review focused re-check 返回；补齐新实现 native Windows + WezTerm + rmux 前台手工 runbook 后重跑 QA。QA passed 前不得进入 acceptance、不得 scoped commit。
