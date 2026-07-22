---
doc_type: goal-functional-acceptance
goal: "mux-backend-contract"
status: pass
reviewer_id: "019f89b3-7b81-7571-8be7-8431d1545a27"
final_iteration: "iterations/004.md"
---

# mux-backend-contract Functional Acceptance

## Reviewer

- Task agent role：terminal functional acceptance。
- Task agent id：`019f89b3-7b81-7571-8be7-8431d1545a27`。
- 关闭结果：已关闭。

## Acceptance Checks

- pass：`MuxNamespaceRef`、`MuxPaneRef`、`MuxCapabilities`、`MuxCommandError` 已定义在 `lib/terminal_runtime/mux_backend_contract.py`，contract module 未导入 tmux implementation。
- pass：`MuxBackend` 由 `NamespaceLifecycle`、`WindowLayout`、`PaneIO`、`PanePresentation`、`PaneLogging`、`DiagnosticsCapability` 组合，public protocol 未暴露 `_tmux_run(args)`。
- pass：`FakeMuxBackend` 有 namespace/window/pane 状态、`event_log`、lifecycle/layout/io/presentation/logging/capabilities/failure injection 覆盖。
- pass：leakage inventory 已记录 `_tmux_run` / tmux argv 泄漏组，覆盖后续 adapter 需要的主要输入面。
- pass：核心验证命令已通过，feature checklist 已更新为 `done`，goal iteration 已记录验证证据。

## Functional Evidence

```text
python -m pytest -q test/test_mux_backend_contract.py
python -m pytest -q test/test_backend_selection_diagnostics.py test/test_agent_window_reflow.py test/test_v2_phase2_entrypoint.py -k "tmux or layout or runtime"
python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-checklist.yaml" --yaml-only
python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"
```

验收 agent 记录的结果：

- `test/test_mux_backend_contract.py`：8 passed。
- CMD-004：7 passed, 82 deselected。
- checklist YAML 校验通过，且 checklist steps/checks 为 `done`。
- `iterations/003.md` 记录 reviewer closure pass 与主线验证证据。

## Verdict

pass。

## Residual Risks

- 回归命令是目标抽样，不代表全仓全量测试。
- psmux/rmux 兼容层当前对 tmux UI/policy 命令采取保守跳过；后续 adapter 应基于真实 capability report 细化。

## Delivery Record

Final iteration：`iterations/004.md`。
