---
doc_type: goal-functional-acceptance
goal: "ordinary-pane-wheel-scroll"
status: pass
reviewer_id: "019fb31c-303d-73e0-b4e7-4caadeae8f56"
final_iteration: "iterations/001.md"
---

# ordinary-pane-wheel-scroll 功能验收

## Reviewer

- Role: Task agent terminal functional acceptance，read-only artifact verification。
- Task agent id: `019fb31c-303d-73e0-b4e7-4caadeae8f56`。
- Reviewer label: `codex-gpt5-terminal-acceptance`。
- Verdict: `pass`。
- Close result: agent result consumed; close requested after reports were written。
- Referenced final iteration: `iterations/001.md`。

## Acceptance Checks

- 默认 `mouse on` policy 与 mouse reporting 边界：通过。Task agent 复核 `config/tmux-ccb.conf:12`、`lib/terminal_runtime/rmux_backend_runtime/namespace.py`、`lib/terminal_runtime/tmux_mux_backend.py`、`lib/cli/services/runtime_launch_runtime/tmux_panes.py`，确认当前默认策略仍启用 mouse reporting；负向绑定断言不能证明 WezTerm GUI-native scroll。
- rmux fallback 负向保护边界：通过。Windows/rmux fallback 未重绑 wheel / scroll / copy-mode，`test/test_v2_tmux_ui.py` 对无 `WheelUpPane`、`WheelDownPane`、`scroll-up`、`scroll-down` 和 `copy-mode -M -t =` 有断言。这是回归保护，不证明真实前台滚轮可见滚动。
- 无运行时策略修改和无错误宣称：通过。Task agent 复核指定运行时代码与测试文件无当前 diff；evidence 声明未实现 copy-mode scroll、未关闭 mouse policy、未声明 host-native 或 pane-app passthrough。既有 tmux-capable 非 rmux fallback 的 copy-mode wheel 路径不是本 goal 新增能力，也不是 Windows/rmux 默认能力。
- UX evidence JSON 投影字段：通过。`windows-rmux-ux-parity-evidence.json` 为 `evidence_status=blocked`、`failure_class=unsupported_capability`、`parity_dimension=foreground_interaction`。
- Goal 范围：通过。本 goal complete 只代表 `ordinary-pane-wheel-scroll` 诊断闭环完成，不代表 epic 其他 child 完成，也不代表真实 ordinary wheel scroll pass。

## Functional Evidence

- Task agent 只读检查了 goal 起点、feature-local evidence、父 root-cause split、父 QA、mouse / scroll policy 相关运行时代码和 tmux UI regression tests。
- Main thread fresh evidence:
  - goal `state.yaml` YAML validate passed。
  - UX JSON precise assertion passed。
  - `$env:PYTHONPATH='lib'; python -m pytest -q -rs "test/test_v2_tmux_ui.py"`：13 passed, 2 skipped。
  - scoped cleanliness `rg` 无禁止 pass 声明命中。

## Residual Risks

- 未执行新的真实 Windows + WezTerm + rmux 前台鼠标复测；本结论依赖既有 owner 2026-07-27 前台失败记录。
- 当前没有真实前台 ordinary wheel scroll pass；结论只能是 `blocked/unsupported_capability`，不是 mouse parity pass。
- 若后续要从 blocked 改为 pass，必须另选并实现策略：tmux/rmux-like copy-mode scroll、host terminal native scroll with mouse reporting off / modifier bypass，或明确限定的 pane-app passthrough，并重新前台验收。

## Verdict

`pass`。允许 goal 标记为 complete。

## Delivery Record

`ordinary-pane-wheel-scroll` 已完成诊断闭环和终端功能验收。交回 epic 时应表达为：当前 Windows + WezTerm + rmux 默认 `mouse on` 策略下，普通 pane 滚轮仍缺少可批准的 GUI-native route，当前投影为 `blocked/unsupported_capability`。
