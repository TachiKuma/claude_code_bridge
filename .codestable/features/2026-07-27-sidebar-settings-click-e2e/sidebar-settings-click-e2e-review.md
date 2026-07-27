---
doc_type: feature-review
feature: 2026-07-27-sidebar-settings-click-e2e
status: blocked
reviewer: subagent
reviewed: 2026-07-27
round: 3
lane_a_state: completed
lane_a_ref: "019fa415-c647-7602-b089-93ed5edb1529"
lane_a_reason: "完整复审；独立 reviewer Pauli 返回 changes-requested。主 agent 已本地核验并修复 args-id snapshot 假阳性与 probe token 泄露；owner 拒绝 broad rmux fallback，当前按 rmux 缺坐标/不透传 mouse capability blocked。"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "ocr CLI 可用且 llm test 通过，但当前 workspace 含多项 unrelated dirty/untracked；ocr review 不支持按文件列表限定未提交 diff，按协议跳过裸 workspace OCR，改为本地行级审查 scoped files。"
---

# sidebar-settings-click-e2e 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-design.md`
- Checklist: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-checklist.yaml`
- Evidence pack: `evidence/manual-foreground-retest.md`、`evidence/windows-rmux-ux-parity-evidence.json`、`evidence/sidebar-mouse-probe.json`
- Gate results: none
- DoD results: 本轮命令结果见第 5 节。
- Implementation evidence: 真实 Windows + WezTerm + rmux 前台点击 transcript；当前 scoped diff。
- Diff basis: 工作区 dirty；本 review 只审 sidebar settings click e2e 相关代码和证据。
- Review mode: full-rereview
- Baseline dirty files: roadmap/旧 feature 文档、父 feature evidence、其它未跟踪文件存在既有 dirty；不纳入本轮代码质量结论。

### Independent Review

- Detection: multi-agent subagent 可用；OCR CLI 可用，`ocr llm test` 通过。
- 环节 A 独立隔离 Task agent: independent-agent completed，ref `019fa415-c647-7602-b089-93ed5edb1529`。
- 环节 B OCR CLI: skipped-scope-ambiguous。
- OCR severity mapping: High→blocking/important, Medium→nit/suggestion, Low→discarded。
- Merge policy: Pauli findings 已逐条本地核验；REV-003/REV-005 已修复，REV-004 通过回退 broad fallback 关闭。
- Gate effect: 不放行 QA/acceptance；当前 blocked 在 rmux 缺坐标且 `send-keys -M` 不透传，需要另拆/深挖 settings 专用通道。

## 2. Diff Summary

- 新增：`tools/ccb-agent-sidebar/src/mouse_probe.rs`、`lib/ccbd/services/project_namespace_runtime/sidebar_settings_evidence.py`、`test/test_ccbd_sidebar_settings_evidence.py`、`evidence/manual-foreground-retest.md`。
- 修改：`lib/cli/services/start.py`、`lib/ccbd/services/project_namespace_pane.py`、`lib/ccbd/services/project_namespace_runtime/materialize_topology.py`、`lib/cli/services/tmux_ui_runtime/service.py`、`tools/ccb-agent-sidebar/src/tui.rs`、相关测试与 evidence/checklist。
- 删除：none。
- 未跟踪 / staged：scoped feature 目录和新增代码/测试未跟踪；staged diff 为空。
- 风险热点：Windows/rmux mouse fallback、sidebar helper respawn、用户可见 settings/config UI、evidence 可信度。

## 3. Adversarial Pass

- 假设的生产 bug：真实 rmux 不传坐标且 `send-keys -M` 不透传，导致原 design 的 settings click 仍不可实现。
- 主动攻击过的反例：helper 指纹当前但 launch args 缺参、rmux backend 被误构造成 tmux、`send-keys -M` 不透传、probe 假造 mouse event、config UI token 泄露、KillProject/x 被 settings fallback 覆盖。
- 结果：helper refresh、args-id snapshot、token redaction 已闭合；broad rmux fallback 已按 owner 决策回退；原 settings click 能力仍 blocked。

## 4. Findings

### blocking

- [ ] REV-007 `evidence/windows-rmux-ux-parity-evidence.json:8` 原 design 的 Windows/rmux settings click 仍 blocked。
  - Evidence: 真实前台探针记录 rmux root binding 可触发，但 `coordinate_probe=",,41,0,0,sidebar"`，`event_observed=false`，`settings_action_observed=false`；owner 已拒绝 broad fallback。
  - Impact: settings shortcut 和 config UI 路径健康，但不能证明点击 `⚙` 这个控件能到达 Rust mouse event/action；不能进入 QA/acceptance。
  - Expected fix scope: 另拆/深挖 rmux 专用坐标、mouse passthrough 或不影响 KillProject/普通 sidebar click 的 settings-only 通道。

### important

none

### nit

none

### suggestion

- [ ] REV-006 `test/test_v2_start_service.py:170` 可再补一个 `backend_impl='rmux'` 的 namespace_ref 断言，增强 start refresh 防退化覆盖。当前生产路径已用真实 rmux 手工验证，故不阻塞。

### learning

- rmux 在本机真实前台环境中 root mouse binding 会触发，但 `#{mouse_x}` / `#{mouse_y}` 为空，`send-keys -M` 不进入 Rust/crossterm mouse event。
- `@ccb_sidebar_helper_id` 只能证明 helper binary 版本，不能证明 launch args 完整；`@ccb_sidebar_helper_args_id` 需要与 binary fingerprint 一起作为 refresh 判定。
- Probe 现在对 config UI URL token 脱敏，同时不伪造 mouse event：键盘/fallback settings 只设置 `settings_action_observed=true`。

### praise

- `start.py` 已复用项目 mux backend 配置和 `build_backend_for_namespace()`，修掉了 rmux namespace 被错误连到 default tmux/psmux 的根因。
- 真实 foreground evidence 保留了 `event_observed=false`，没有把快捷键 fallback 伪装成 Rust mouse hit-test pass。

## 5. Test And QA Focus

- QA 必须重点复核：当前不进入 QA；下一步应验证 rmux 是否存在 settings-only mouse 坐标或 passthrough 能力。
- Evidence pack residual risks / gate warnings：UX parity JSON 当前为 `pass`，但 residual risk 明确写明 rmux 不传坐标且不透传 `-M`。
- 建议新增或加强的测试：若接受降级，补 design/acceptance 对“sidebar left-click fallback opens settings”的显式测试与文档；若不接受，新增 x/KillProject 不被 settings fallback 覆盖的测试。
- 不能靠 review 完全确认的点：未来 rmux 版本是否会提供 mouse coordinates 或修复 `send-keys -M` 透传。

已运行验证：

- `$env:PYTHONPATH='lib'; python -m pytest -q -rs test/test_v2_tmux_ui.py`：13 passed, 2 skipped。
- `$env:PYTHONPATH='lib'; python -m pytest -q -rs test/test_v2_start_service.py -k sidebar`：1 passed。
- `$env:PYTHONPATH='lib'; python -m pytest -q -rs test/test_ccbd_sidebar_helper.py test/test_ccbd_sidebar_settings_evidence.py`：19 passed。
- `$env:PYTHONPATH='lib'; python -m pytest -q -rs test/test_ccbd_sidebar_helper.py test/test_ccbd_startup_pane_snapshot.py`：28 passed。
- `$env:PYTHONPATH='lib'; python -m pytest -q -rs test/test_v2_tmux_ui.py test/test_v2_start_service.py -k "sidebar or rmux or mouse_context"`：4 passed, 1 skipped。
- `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml --quiet`：63 passed。
- `python -m py_compile ...`：passed。
- UX parity JSON validator：passed。
- `codestable-workflow-next.py feature ... --epic-child-batch --json`：回退 broad fallback 前 checklist done；回退后 S7/AC-003 pending。

## 6. Residual Risk

- 当前 direct `c` 可打开 settings/config UI，但真实 settings mouse click 在 rmux 前台仍 blocked。

## 7. Verdict

- Status: blocked
- Next: 回到 epic 拆分新 feature，深挖 rmux 坐标/passthrough 或 settings-only 通道；本 feature 不进入 QA。

## 8. Focused Closure

none
