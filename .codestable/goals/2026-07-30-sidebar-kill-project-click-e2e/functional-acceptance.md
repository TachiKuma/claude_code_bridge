---
doc_type: goal-functional-acceptance
goal: "sidebar-kill-project-click-e2e"
status: pass
reviewer_id: "019fb2ff-f137-7803-838b-be108884cd45"
final_iteration: "iterations/001.md"
---

# sidebar-kill-project-click-e2e 功能验收

## Reviewer

- Role: Task agent terminal functional acceptance，read-only artifact verification。
- Task agent id: `019fb2ff-f137-7803-838b-be108884cd45`。
- Reviewer label: `codex-gpt5-terminal-acceptance`。
- Verdict: `pass`。
- Close result: agent result consumed; close requested after reports were written。
- Referenced final iteration: `iterations/001.md`。

## Acceptance Checks

- Rust 内部 `x` hit-test 与 kill 子进程测试证据：通过。`header_action_at()` 对 header controls 第三列返回 `HeaderMouseAction::KillProject`；`handle_mouse_down()` 将其转为 `ExitAction::KillProject`；`run()` 调用 `run_ccb_kill()`；`run_ccb_kill_with_program()` 在 `project_root` 下执行 `ccb kill`。测试证据包含 header kill 测试和 fake `ccb kill` 子进程测试。
- 真实前台 click e2e 不能宣称通过：通过。`diagnosis.md` 明确当前不能证明 `x` click 到达 Rust/crossterm mouse event；settings 诊断记录 rmux root binding 可触发但 `send-keys -M` 未进入 Rust mouse event；routing evidence 记录普通 root binding 缺少 settings/x 级坐标或等价谓词。
- 无 broad fallback / 无不精确 kill / 未执行真实项目 kill：通过。`capability-summary.json` 将 pane-wide sidebar left-click kill fallback 标为 unsupported；UX JSON 记录 `broad_fallback_added=false`、`runtime_behavior_changed=false`、`real_project_kill_executed=false`。
- UX evidence JSON 投影字段：通过。`windows-rmux-ux-parity-evidence.json` 为 `evidence_status=blocked`、`failure_class=unsupported_capability`、`parity_dimension=foreground_interaction`。
- Goal 范围：通过。当前 goal 只代表 `sidebar-kill-project-click-e2e` 诊断闭环完成，不代表 epic 其他 child 完成，也不代表真实 x click pass。

## Functional Evidence

- Task agent 只读检查了 goal 起点、feature-local evidence、root-cause split、settings e2e 阻塞证据、Rust sidebar source 和 tmux UI regression tests。
- Main thread fresh evidence:
  - goal `state.yaml` YAML validate passed。
  - UX JSON precise assertion passed。
  - `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml --quiet`: 63 passed。
  - `python -m pytest -q -rs test/test_v2_tmux_ui.py`: 13 passed, 2 skipped。
  - scoped cleanliness `rg` 只命中既有禁止 `send-keys -t = Q` 的测试断言和 evidence 中拒绝 broad fallback 的说明。

## Residual Risks

- `project_kill_runs_ccb_kill_from_project_root` 是 `#[cfg(unix)]` 测试；它证明子进程参数和工作目录路径，不是 Windows 真实 kill 验收。
- 当前没有真实前台 x-click pass；结论只能是 `blocked/unsupported_capability`，不是 mouse parity pass。
- Epic 仍有其他 split child 未完成；本验收不关闭这些 child。

## Verdict

`pass`。允许 goal 标记为 complete。

## Delivery Record

`sidebar-kill-project-click-e2e` 已完成诊断闭环和终端功能验收。交回 epic 时应表达为：内部 KillProject 路径可复核，但 native Windows + WezTerm + rmux 前台 `x` click 仍缺少可批准的精确 mouse route，当前投影为 `blocked/unsupported_capability`。
