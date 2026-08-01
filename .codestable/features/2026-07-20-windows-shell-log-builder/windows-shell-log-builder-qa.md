---
doc_type: feature-qa
feature: windows-shell-log-builder
status: passed
updated_at: "2026-07-22"
---

# windows-shell-log-builder QA

## Scope

QA 覆盖 Windows shell/log builder、shell resolution diagnostic、stderr redirection、respawn service wiring、pane log manager wiring、clipboard command de-dup、YAML 产物与调用层 leakage guard。

## Commands

```text
git diff --check
python -m pytest -q "test/test_terminal_runtime_windows_shell_log_builder.py"
python -m pytest -q "test/test_terminal_runtime_tmux_respawn.py" "test/test_terminal_runtime_tmux_respawn_service.py" "test/test_terminal_runtime_tmux_logs.py"
python -m pytest -q "test/test_v2_project_namespace_backend.py" "test/test_v2_project_namespace_state.py" "test/test_v2_runtime_launch.py" -k "clipboard or copy-pipe or set-clipboard"
python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-windows-shell-log-builder/windows-shell-log-builder-checklist.yaml" --yaml-only
python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"
rg -n "sh -lc|tee -a|powershell\\.exe|pwsh|cmd /" "lib/ccbd/services/project_namespace_runtime/backend.py" "lib/cli/services/runtime_launch_runtime/tmux_panes.py" "lib/terminal_runtime/tmux_logs.py"
```

## Evidence

- diff whitespace check：clean。
- builder tests：`12 passed`。
- tmux respawn/log focused tests：`18 passed`。
- clipboard focused tests：`10 passed, 139 deselected`。
- checklist YAML：passed。
- roadmap items YAML：passed。
- caller-layer leakage guard：no matches。

## Notes

Iteration 001 中 clipboard focused tests 曾被 Codex bridge bootstrap artifact 缺失遮蔽；Iteration 002 已在测试内准备最小 `input.fifo` / `output.fifo` artifacts，当前 focused selector 全绿。
