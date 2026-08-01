---
doc_type: feature-review
feature: provider-runtime-backend-session-contract
status: pass
reviewer_id: "019f8aab-1fd1-75a1-a37f-0b3eca51b33e"
updated_at: "2026-07-22"
---

# provider-runtime-backend-session-contract Review

## Reviewer

- Task agent：Cicero
- Agent id：`019f8aab-1fd1-75a1-a37f-0b3eca51b33e`
- 模式：可见独立 Task agent，只读审查。
- 生命周期：review 结论已消费，agent 已关闭。

## Initial Review

初次 review verdict 为 `changes_requested`，发现三个 blocking：

- provider env loader 在 env 分支没有从 canonical session 文件补齐 `terminal`、`backend_family`、`backend_impl`、`pane_ref`、`namespace_ref`。
- `terminal=mux` 的 provider session 会绕过 `ensure_pane()` 中现有 tmux-compatible recovery。
- rebind writer 只更新 legacy alias，未同步更新 canonical `pane_ref.pane_id`。

## Closure Fixes

- 新增 `merge_missing_mux_session_fields()`，让 Codex、Gemini、OpenCode env loader 在 env 明确值缺失时从 session 文件补齐 canonical mux fields。
- 新增 `session_uses_tmux_compatible_pane()`，让 `terminal=mux` 且 `backend_family=tmux-family` 的 session 继续走 tmux-compatible recovery。
- 新增 `update_mux_session_pane_binding()`，让 pane rebind 同步写回 `pane_id`、`tmux_session`、`pane_ref` 与 `compat.tmux_session`。
- 补充 canonical mux env merge、canonical mux recovery 和 replacement pane writeback 测试。

## Closure Review

Focused closure verdict 为 `pass`。

Reviewer 结论：未发现阻塞问题。

已核验：

- env loader closure 已覆盖 Codex/Gemini/OpenCode env 分支从 session 文件补齐 canonical mux fields。
- `terminal=mux` + `backend_family=tmux-family` 已进入 tmux-compatible recovery。
- rebind 写回已同步 canonical 与 compatibility 字段。

## Verification Referenced

- `python -m pytest -q "test/test_gemini_session_runtime.py" "test/test_opencode_session_runtime.py" "test/test_codex_session_fields.py"`：`24 passed`。
- `python -m pytest -q "test/test_codex_session_ensure_pane.py" -k "canonical_mux or replacement_created"`：`2 passed`。
- `python -m pytest -q "test/test_provider_runtime_session_payload_guard.py" "test/test_v2_runtime_launch_session_files.py" "test/test_ccbd_runtime_refresh.py" "test/test_codex_session_fields.py" "test/test_gemini_session_runtime.py" "test/test_opencode_session_runtime.py"`：`36 passed`。
- `python -m pytest -q "test/test_codex_session_ensure_pane.py" "test/test_gemini_session_ensure_pane.py" "test/test_opencode_session_ensure_pane.py"`：`21 passed`。
- `python -m compileall -q "lib"`：通过。

## Residual Risks

- Closure review 重点核验三个 blocking 修复闭环，没有重新完整审查整个 diff。
- 当前 production launch 仍是 tmux path；未来接入 rmux production launch 时，需要继续把 backend impl 从实际 backend/context 投射到启动 env。
