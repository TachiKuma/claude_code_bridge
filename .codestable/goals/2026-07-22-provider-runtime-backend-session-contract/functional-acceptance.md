---
doc_type: goal-functional-acceptance
goal: "provider-runtime-backend-session-contract"
status: pass
reviewer_id: "019f8ace-ea96-7620-86fb-b9ff44cfa5dc"
final_iteration: "iterations/001.md"
---

# provider-runtime-backend-session-contract 功能验收

## Reviewer

- Task agent：Poincare
- Agent id：`019f8ace-ea96-7620-86fb-b9ff44cfa5dc`
- Role：终端功能验收 Task agent
- 模式：只读功能验收；未修改文件，未执行 commit/push/reset。
- 生命周期：验收结论已消费，agent 已关闭。

## Acceptance Checks

- `pass`：shared writer 生成 `terminal=mux`、`backend_family`、`backend_impl`、`pane_ref`、`namespace_ref`、`compat`，并保留 `tmux_session` / socket alias。
- `pass`：provider-specific payload 不能覆盖 protected shared keys，冲突写入 `payload_diagnostics.protected_key_conflicts`。
- `pass`：session readers、binding evidence、`ProviderRuntimeFacts` 通过 `project_session_payload()` canonical-first、alias-fallback；旧 `terminal=tmux` session 仍可读。
- `pass`：provider env 暴露 `CCB_MUX_*`；Codex/Gemini/OpenCode loader 优先 `CCB_MUX_PANE_ID`，旧 `*_TMUX_SESSION` 仅 fallback。
- `pass`：provider-runtime/session payload truth 已转到 shared mux payload；direct `TmuxBackend` 仍只作为 tmux adapter/launch 兼容边界。
- `pass`：CMD-001 到 CMD-007 全部通过，无需记录红灯基线。

## Functional Evidence

- CMD-001：checklist YAML validate，`1 passed, 0 failed`。
- CMD-002：roadmap items YAML validate，`1 passed, 0 failed`。
- CMD-003：`python -m pytest -q "test/test_v2_runtime_launch_session_files.py"`，`6 passed`。
- CMD-004：`python -m pytest -q "test/test_v2_runtime_launch.py" -k "session or payload or backend or env or tmux"`，`41 passed, 58 deselected`。
- CMD-005：`python -m pytest -q "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_health_monitor_rebind.py"`，`7 passed`。
- CMD-006：`python -m pytest -q "test/test_cli_runtime_launch_tmux_panes.py" "test/test_v2_runtime_launch.py" -k "tmux or pane or detached"`，`15 passed, 89 deselected`。
- CMD-007：`python -m pytest -q "test/test_provider_runtime_session_payload_guard.py"`，`3 passed`。
- Closure：`python -m pytest -q "test/test_codex_session_fields.py" "test/test_gemini_session_runtime.py" "test/test_opencode_session_runtime.py"`，`24 passed`。

## Verdict

`pass`。Goal acceptance criteria 已满足。

## Residual Risks

- 未做真实 tmux/rmux 端到端启动或长稳态 soak；本轮证据来自 focused tests、fake backend 与只读产物检查。
- 后续新增 provider launcher 时需要同步纳入 guard。
- Rmux production core 仍属于后续 roadmap item。

## Delivery Record

- Final iteration：`iterations/001.md`。
- Feature acceptance：`.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-acceptance.md`。
