---
doc_type: feature-qa
feature: mux-backend-contract
status: passed
updated_at: "2026-07-22"
---

# mux-backend-contract QA

## Scope

QA 覆盖 contract/fake backend、backend selection diagnostics、agent window reflow、phase2 tmux/layout/runtime 抽样、Windows TCP loopback token ACL 回归，以及 CodeStable YAML 产物。

## Commands

```text
python -m pytest -q "test/test_mux_backend_contract.py"
python -m pytest -q "test/test_v2_project_namespace_backend.py"
python -m pytest -q "test/test_v2_tmux_ui.py::test_apply_project_tmux_ui_skips_project_ui_for_psmux_compat_tmux_path"
python -m pytest -q "test/test_backend_selection_diagnostics.py" "test/test_agent_window_reflow.py" "test/test_v2_phase2_entrypoint.py" -k "tmux or layout or runtime"
python -m pytest -q "test/test_ccbd_windows_tcp_loopback_transport.py"
python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-checklist.yaml" --yaml-only
python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"
```

## Evidence

- contract/fake backend：`8 passed`。
- namespace backend policy：`19 passed`。
- psmux UI compatibility regression：`1 passed`。
- CMD-004：`7 passed, 82 deselected`。
- Windows TCP loopback transport：`34 passed`。
- checklist YAML：passed。
- roadmap items YAML：passed。

## Notes

CMD-004 曾出现一次 Windows TCP `kill` connection abort，立即复跑通过；当前无稳定复现证据。
