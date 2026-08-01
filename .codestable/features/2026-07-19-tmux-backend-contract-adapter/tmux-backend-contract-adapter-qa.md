---
doc_type: feature-qa
feature: tmux-backend-contract-adapter
status: passed
updated_at: "2026-07-22"
---

# tmux-backend-contract-adapter QA

## Scope

QA 覆盖 tmux mux adapter、contract guard、namespace/layout/runtime launch/reflow 代表 seam、backend selection、project namespace backend，以及 CodeStable YAML 产物。

## Commands

```text
python -m pytest -q test/test_tmux_mux_backend_adapter.py
python -m pytest -q test/test_agent_window_reflow.py test/test_cli_runtime_launch_tmux_panes.py test/test_ccbd_project_clear.py
python -m pytest -q test/test_tmux_mux_backend_adapter.py test/test_mux_backend_contract.py test/test_agent_window_reflow.py test/test_cli_runtime_launch_tmux_panes.py test/test_ccbd_project_clear.py
python -m pytest -q test/test_backend_selection_diagnostics.py test/test_terminal_runtime_backend_selection.py test/test_v2_project_namespace_backend.py
python -m pytest -q test/test_backend_selection_diagnostics.py test/test_agent_window_reflow.py test/test_v2_phase2_entrypoint.py -k "tmux or layout or runtime"
python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-19-tmux-backend-contract-adapter/tmux-backend-contract-adapter-checklist.yaml" --yaml-only
python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"
python -m pytest -q test/test_v2_runtime_launch.py test/test_ccbd_start_runtime_layout.py -k "tmux or layout or namespace"
```

## Evidence

- adapter tests：`19 passed`。
- reflow/runtime launch/project clear：`17 passed`。
- adapter + mux contract + representative seam：`44 passed`。
- backend selection / terminal runtime selection / project namespace backend：`53 passed`。
- tmux/layout/runtime selector：`7 passed, 83 deselected`。
- refreshed final selector：`83 passed` across adapter, reflow, runtime launch, backend selection, terminal runtime selection, and project namespace backend suites.
- checklist YAML：passed。
- roadmap items YAML：passed。

## Documented Baseline

`CMD-005` 仍有既有红灯：`python -m pytest -q test/test_v2_runtime_launch.py test/test_ccbd_start_runtime_layout.py -k "tmux or layout or namespace"` 结果为 4 failed、6 passed、91 deselected。

失败集中在 Codex runtime bootstrap 缺 `input.fifo` / `output.fifo` artifacts，以及 legacy explicit session archive 断言；当前 adapter 变更未扩大这些 baseline failure。

## Notes

`test_v2_phase2_entrypoint` selector 曾出现一次 Windows `os.replace` PermissionError，单独重跑与 selector 重跑均通过，记录为本地文件系统瞬时问题。
