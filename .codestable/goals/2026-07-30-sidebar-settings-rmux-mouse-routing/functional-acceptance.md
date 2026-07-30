---
doc_type: goal-functional-acceptance
goal: "sidebar-settings-rmux-mouse-routing"
status: pass
reviewer_id: "019fb2ec-6457-7d70-959f-ce43f4187a79"
final_iteration: "iterations/001.md"
---

# sidebar-settings-rmux-mouse-routing 功能验收

## Reviewer

- Role: Task agent terminal functional acceptance，read-only artifact verification。
- Task agent id: `019fb2ec-6457-7d70-959f-ce43f4187a79`。
- Reviewer label: `codex-gpt5-terminal-acceptance-2026-07-30`。
- Verdict: `pass`。
- Close result: agent result consumed; close requested after reports were written.
- Referenced final iteration: `iterations/001.md`。

## Acceptance Checks

- 产物链完整性：通过。`design.status=approved`，`design-review.status=passed/review_state=passed`，code review `status=passed`，QA `status=passed`。
- UX JSON 精确投影：通过。`evidence_status=blocked`、`failure_class=unsupported_capability`、`selected_route=unsupported_capability`、`runtime_behavior_changed=false`、`broad_fallback_added=false`。
- direct `c` 语义：通过。现有表述均将 direct `c` 限定为 settings action 健康诊断，不计为 mouse click parity pass。
- broad fallback：通过。未发现新增或接受 broad sidebar-left-click settings fallback 的证据；相关命中均为拒绝、禁止或未新增说明。
- goal 终态语义：通过。当前产物支持将 child 作为 evidence-complete `unsupported_capability` 交回，而不是 `settings mouse parity passed`。

## Functional Evidence

- `goal.md` 明确目标是 evidence-complete `unsupported_capability`，不是 parity passed。
- `windows-rmux-ux-parity-evidence.json` 精确给出 `blocked/unsupported_capability` 投影。
- `capability-summary.json` 明确 `unsupported_capability.supported=true`，并拒绝 broad fallback。
- `foreground-reverse-validation.md` 明确 settings click blocked，direct `c` 不计为 mouse pass。
- Main thread fresh validation:
  - goal `state.yaml` YAML validate passed。
  - feature checklist YAML validate passed。
  - precise UX JSON assertion passed。
  - `python -m pytest -q -rs test/test_v2_tmux_ui.py`: 13 passed, 2 skipped。
  - `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml --quiet`: 63 passed。

## Residual Risks

- `x`、普通 sidebar、普通 pane 行为本 feature 未重新完整前台手测；结论依赖无 runtime 行为变更与无 broad fallback 的 scope guard。
- 若未来 rmux 或 WezTerm 新版本提供精确坐标或 settings-only 通道，需要重新跑 capability probe，并可能开启新的 implementation/review/QA loop。
- Epic `windows-rmux-ux-parity-hardening` 仍有其他 pending / handoff child；本验收只关闭 `sidebar-settings-rmux-mouse-routing` 的 evidence-complete unsupported capability 目标。

## Verdict

`pass`。允许 goal 标记为 complete。

## Delivery Record

`sidebar-settings-rmux-mouse-routing` 已完成终端功能验收和 goal 终态记录。交回 epic 时应表达为：该 child 证明当前 Windows + WezTerm + rmux 不存在已批准的 settings-only mouse route，正确投影是 `blocked/unsupported_capability`；不要宣称 settings mouse parity passed。
