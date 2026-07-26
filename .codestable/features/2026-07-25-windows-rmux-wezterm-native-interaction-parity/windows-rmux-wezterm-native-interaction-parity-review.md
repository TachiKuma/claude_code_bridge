---
doc_type: feature-review
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: blocked
reviewed: 2026-07-27
round: 2
lane_a_state: pending
lane_a_ref: "agent:019fa074-b8cb-73e0-ba8c-b6a383e41718/submission:019fa079-6e46-7bf3-bf7f-8fa075d42502"
lane_a_reason: "focused re-check pending after fixing independent reviewer B1/B2"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "ocr CLI 可用，但当前工作区存在范围外 dirty/untracked，且 ocr review 不能限定到本 feature 文件；按协议跳过裸 workspace OCR，改为本地行级核验当前 scope。"
---

# windows-rmux-wezterm-native-interaction-parity 代码审查报告

## Round 2 Status（2026-07-27）

当前状态：`blocked`，等待同一独立 reviewer 的 focused re-check 返回。

### Independent Review Delta

- Round 2 独立 reviewer `019fa074-b8cb-73e0-ba8c-b6a383e41718` 返回 `changes-requested`。
- Blocking B1：Windows/rmux fallback 外层 `if-shell` 缺 `-t =`，导致 sidebar / ordinary pane 分流仍按当前活动 pane 求值。
- Blocking B2：fake/live 测试把缺 `-t =` 固化为通过条件，不能证明 AC-008。
- 已修复：`lib/cli/services/tmux_ui_runtime/service.py` 四个 fallback mouse key 均改为 `if-shell -F -t = '#{==:#{@ccb_role},sidebar}' ...`；`test/test_v2_tmux_ui.py` fake/live 断言均要求 `if-shell -F -t =`、`select-pane -t =`、`send-keys -t = -M`，并禁止 `select-pane -M`。
- 已验证：`python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings` -> pass；`python -m pytest -q -rs test/test_v2_tmux_ui.py` -> pass；`python -m py_compile ...` -> pass。

Verdict 暂不定稿为 passed：已启动的独立 focused re-check 尚未返回，按 gate 规则必须等待匹配 lane ref。

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-dod-results.json`
- Implementation evidence: checklist steps 全 done、live/manual evidence、DoD runner passed。
- Diff basis: 当前工作区 diff；审查实现文件为 `lib/cli/services/tmux_ui_runtime/service.py` 与 `test/test_v2_tmux_ui.py`，配套 CodeStable 产物在 feature 目录。
- Review mode: initial。
- Baseline dirty files: 工作区存在其他 roadmap/design、binary、provider runtime 改动；本 review 只审本 feature scope。

### Independent Review

- Detection: Claude Task agent 可用并返回 `claude:20260726-213942-418-15916-1`；OCR CLI 可用但因 workspace scope ambiguous 跳过。
- 环节 A 独立隔离 Task agent: independent-agent completed。
- 环节 B OCR CLI: skipped。
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded。
- Merge policy: 独立 reviewer 结论已按仓库事实核验后合并；OCR 未运行，不影响 Task agent gate。
- Gate effect: reviewer 字段为 `subagent`，满足 review gate。

## 2. Diff Summary

- 新增：`evidence/live-binding-snapshot.txt`、`evidence/manual-wezterm-runbook.md`、DoD/scope/evidence-pack gate artifacts。
- 修改：`lib/cli/services/tmux_ui_runtime/service.py`、`test/test_v2_tmux_ui.py`、feature checklist、evidence pack。
- 删除：none。
- 未跟踪 / staged：本 feature 产物未跟踪；无 staged diff。
- 风险热点：Windows/rmux 前台交互、mouse binding、manual GUI evidence。

## 3. Adversarial Pass

- 假设的生产 bug：普通 pane wheel 虽不再进入 copy-mode，但仍只执行 `select-pane -t =` 聚焦，用户可能期待 WezTerm 原生内容滚动。
- 主动攻击过的反例：普通 pane wheel/right-click/left-click、sidebar wheel/header/KillProject、rmux live binding syntax、manual GUI transcript 缺失。
- 结果：代码实现满足 approved design 的第一版“不劫持到 copy-mode/paste-buffer/普通 send-keys -M”边界；manual GUI 缺口进入 QA/acceptance residual risk。

## 4. Findings

### blocking

none

### important

none

独立 reviewer 提出的两个 important 均已处理为证据/QA 事实：

- I-1：`evidence-pack.md` 原 `Residual Risks: none` 与 manual runbook partial 矛盾；已补充 AC-007 human foreground verification residual risk。
- I-2：旧 Round 1 普通 pane wheel fallback 仍用 `select-pane -M` 消费事件；Round 2 已改为 `select-pane -t =`，但 WezTerm 原生内容滚动仍未被前台手工证实，交给 QA/acceptance 显式裁决。

### nit

- [ ] REV-001 `test/test_v2_tmux_ui.py:384` `send-keys -M` 断言位于复合 if-shell 字符串中，可读性一般；现有 `MouseDown1Pane` bare binding 负向断言已覆盖普通 pane 不裸透传，故不阻塞。

### suggestion

- 后续若 rmux 支持 per-pane mouse off 或 passthrough，可另开 feature 探索普通 pane wheel 不绑定而完全交给 WezTerm 原生滚动。

### learning

- Windows/rmux GUI-native parity 的第一版验收要明确区分“不进入 CCB/rmux copy-mode 劫持”和“宿主 GUI 内容滚动完全可达”。

### praise

- 实现 diff 小，复用既有 fallback 分流，没有新增交互模式配置。
- 测试从旧正向 copy-mode 断言改为精确禁止普通 pane copy-mode/scroll/paste-buffer。

## 5. Test And QA Focus

- QA 必须重点复核 AC-007：native Windows + WezTerm + rmux 前台单击聚焦、拖选、右键、滚轮、sidebar 设置、sidebar `x`。
- Evidence pack residual risks / gate warnings：manual GUI 为 partial；ordinary pane wheel 不再 copy-mode / scroll command / `select-pane -M`，但 WezTerm 原生内容滚动仍未被前台手工证实。
- 建议新增或加强的测试：本轮无需新增自动化测试；manual GUI 需要真实前台 transcript。
- 不能靠 review 完全确认的点：真实鼠标拖选、右键粘贴/menu、滚轮在 WezTerm 前台的体感结果。

## 6. Residual Risk

- AC-007 manual GUI evidence 仍为 partial；QA/acceptance 不得仅凭 unit/live binding 替代证据判定 full pass。
- 普通 pane wheel 不再触发 copy-mode/scroll command，也不再使用旧的 no-target `select-pane -M`；但 WezTerm 原生内容滚动仍未被前台手工证实，这是 design 允许的第一版残留，acceptance 需知情。

## 7. Verdict

- Status: passed
- Next: Goal feature 进入 `cs-feat` QA；若 QA 将 AC-007 判为 failed/blocked，回 implementation 或 handoff 获取人工前台 evidence。

## 8. Focused Closure

none
