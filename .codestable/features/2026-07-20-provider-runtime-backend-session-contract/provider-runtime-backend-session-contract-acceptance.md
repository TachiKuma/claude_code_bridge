---
doc_type: feature-acceptance
feature: provider-runtime-backend-session-contract
status: accepted
updated_at: "2026-07-22"
---

# provider-runtime-backend-session-contract Acceptance

## Acceptance Summary

本 feature 已 accepted。

完成内容：

- 共享 session writer 改为 mux-neutral canonical payload：`terminal=mux`、`backend_family`、`backend_impl`、`pane_ref`、`namespace_ref`、`compat`。
- 旧 `tmux_session`、`tmux_socket_name`、`tmux_socket_path` 保留为 compatibility alias。
- provider payload 通过 protected merge 合入，不能覆盖 shared canonical keys；冲突写入 `payload_diagnostics.protected_key_conflicts`。
- session reader、session binding evidence、`ProviderRuntimeFacts` 迁移到 canonical-first、alias-fallback。
- Codex/Gemini/OpenCode env loader 使用 `CCB_MUX_*` canonical-first，旧 `*_TMUX_SESSION` 仅作为 fallback。
- `terminal=mux` 且 `backend_family=tmux-family` 的 session 继续走 tmux-compatible pane recovery，并在 rebind 时同步 canonical `pane_ref`。

## Gate Evidence

- Checklist：`.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-checklist.yaml` 全部 `done`。
- Review：独立 Task agent Cicero 初审要求修改，closure review `pass`，未发现阻塞问题。
- QA：`.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-qa.md` 为 `pass`。
- Goal 功能验收：Task agent Poincare verdict `pass`。

## Commands

- CMD-001：checklist YAML validate 通过。
- CMD-002：roadmap items YAML validate 通过。
- CMD-003：`test/test_v2_runtime_launch_session_files.py`，`6 passed`。
- CMD-004：`test/test_v2_runtime_launch.py -k "session or payload or backend or env or tmux"`，`41 passed, 58 deselected`。
- CMD-005：`test/test_ccbd_runtime_refresh.py test/test_ccbd_health_monitor_rebind.py`，`7 passed`。
- CMD-006：`test/test_cli_runtime_launch_tmux_panes.py test/test_v2_runtime_launch.py -k "tmux or pane or detached"`，`15 passed, 89 deselected`。
- CMD-007：`test/test_provider_runtime_session_payload_guard.py`，`3 passed`。
- Closure regression：Codex/Gemini/OpenCode env merge 与 ensure_pane suites 通过。
- `python -m compileall -q "lib"`：通过。
- `git diff --check`：通过。

## Residual Risks

- 本轮未做真实 tmux/rmux 端到端启动或长稳态 soak；证据主要来自 focused tests 和 fake backend。
- 后续新增 provider launcher 时，需要同步纳入 guard，避免 canonical tmux payload leakage。
- Rmux production core、send/capture/logging 与 daemon lifecycle 仍在后续 roadmap item 中，不属于本 feature。

## Delivery Record

- Roadmap item 将回写为 `done`。
- Roadmap goal feature 状态将回写为 `accepted`。
