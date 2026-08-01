---
doc_type: goal
goal: provider-runtime-backend-session-contract
status: active
---

# provider-runtime-backend-session-contract

## Objective

继续 windows-rmux-native-backend epic 中的 provider-runtime-backend-session-contract，将 provider launch、session payload、runtime health 和 provider env 迁移到 backend-neutral mux 字段，并保留旧 tmux 字段兼容别名，推进到功能验收完成。

## Starting Point

- 依赖 `mux-backend-contract`、`windows-namespace-ipc-schema` 已在 roadmap 中 accepted / done。
- feature design、checklist、design-review 已存在；design-review passed。
- 当前代码仍有共享 session writer 固定写 `terminal="tmux"`，Codex/native CLI payload 重复写 canonical tmux 字段，provider env loader 优先读取 provider-specific `*_TMUX_SESSION`。

## Acceptance Criteria

- 共享 session writer 产生 `terminal="mux"`、`backend_family`、`backend_impl`、`pane_ref`、`namespace_ref`、`compat`，并保留旧 tmux alias。
- provider-specific payload 不能覆盖 shared canonical keys；冲突记录到 `payload_diagnostics.protected_key_conflicts`。
- session readers、session binding evidence 与 `ProviderRuntimeFacts` canonical-first、alias-fallback，旧 tmux session 仍可读。
- provider env 暴露 `CCB_MUX_*` canonical 字段，Codex/Gemini/OpenCode loaders canonical-first，旧 `*_TMUX_*` env 仅 compatibility fallback。
- runtime launch 不再把 direct `TmuxBackend` 作为唯一 production truth，保留 tmux adapter 兼容边界。
- CMD-001 到 CMD-007 验证通过或记录可接受基线，并通过可见 Task agent review 与功能验收。

## Non-Goals

- 不实现 RmuxBackend production core、send/capture/logging 或 daemon lifecycle。
- 不删除旧 `tmux_session`、`tmux_socket_path`、`tmux_socket_name` compatibility alias。
- 不修改 provider completion parser 或 provider JSONL session 内容。

## Decisions And Assumptions

- 方案深度按持久契约处理：新增共享 helper 是本 feature 的核心逻辑，不使用占位实现。
- 兼容字段继续顶层双写，但 canonical authority 固定为 mux-neutral 字段。
- 旧 session/env fallback 只做读取兼容，不作为新 writer / loader 的第一 authority。

## Current State

Goal 已创建，尚未开始实现 iteration。

## Next Action

实现 `provider_runtime/session_payload.py`，迁移 writer/provider payload/readers/env loader，并补齐 focused tests 与 guard。
