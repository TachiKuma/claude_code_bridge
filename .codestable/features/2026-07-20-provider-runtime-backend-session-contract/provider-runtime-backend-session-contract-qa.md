---
doc_type: feature-qa
feature: provider-runtime-backend-session-contract
status: pass
updated_at: "2026-07-22"
---

# provider-runtime-backend-session-contract QA

## Scope

本轮 QA 覆盖 provider runtime backend-neutral session contract 的 focused DOD：

- shared session writer canonical mux payload 与旧 tmux alias。
- provider payload protected merge 与冲突 diagnostics。
- provider launcher canonical tmux payload cleanup。
- pane log session reader、session binding evidence、ProviderRuntimeFacts canonical-first / alias-fallback。
- provider env canonical `CCB_MUX_*` 优先与旧 `*_TMUX_*` fallback。
- tmux compatibility 与 detached pane focused regression。

## Verification Evidence

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-checklist.yaml" --yaml-only`
  - 结果：通过，`1 passed, 0 failed`。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`
  - 结果：通过，`1 passed, 0 failed`。
- `python -m compileall -q "lib"`
  - 结果：通过。
- `python -m pytest -q "test/test_v2_runtime_launch_session_files.py"`
  - 结果：通过，`6 passed`。
- `python -m pytest -q "test/test_v2_runtime_launch.py" -k "session or payload or backend or env or tmux"`
  - 结果：通过，`41 passed, 58 deselected`。
- `python -m pytest -q "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_health_monitor_rebind.py"`
  - 结果：通过，`7 passed`。
- `python -m pytest -q "test/test_cli_runtime_launch_tmux_panes.py" "test/test_v2_runtime_launch.py" -k "tmux or pane or detached"`
  - 结果：通过，`15 passed, 89 deselected`。
- `python -m pytest -q "test/test_provider_runtime_session_payload_guard.py"`
  - 结果：通过，`3 passed`。
- `python -m pytest -q "test/test_codex_session_fields.py" "test/test_gemini_session_runtime.py" "test/test_opencode_session_runtime.py"`
  - 结果：通过，`24 passed`，覆盖 env branch 从 canonical mux session file 补齐缺失字段。
- `python -m pytest -q "test/test_codex_session_ensure_pane.py" "test/test_gemini_session_ensure_pane.py" "test/test_opencode_session_ensure_pane.py"`
  - 结果：通过，`21 passed`，覆盖 canonical mux session 下 tmux-compatible recovery 与旧 tmux recovery。
- `git diff --check`
  - 结果：通过，无 whitespace error 输出。

## QA Notes

- 曾出现 `test_tmux_backend_direct_dependency_stays_in_adapter_boundary` 失败；根因是 guard 仓库级扫描既有 ccbd/tmux 控制面，超出本 feature 边界。
- 已将 guard 收窄到 provider-runtime/session contract 直接边界：session writer、provider launchers、session readers、runtime facts 与 env loaders。
- 该收窄保留了契约约束：provider-runtime/session payload 路径不得重新把 `TmuxBackend` 作为 canonical truth。
- 独立 review 曾发现 env loader、recovery 和 rebind writeback 三个 blocking；已补定向测试并修复，closure review 通过。

## Verdict

QA 通过。当前 focused DOD 命令、review closure 回归和 `diff --check` 均为 green。
