---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: provider-runtime-backend-session-contract
feature: 2026-07-20-provider-runtime-backend-session-contract
status: accepted
---

# provider-runtime-backend-session-contract Goal Feature Spec

## 1. Identity

- Roadmap item: `provider-runtime-backend-session-contract`
- Feature dir: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract`
- Design: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-design.md`
- Checklist: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-checklist.yaml`
- Design review: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-design-review.md`
- Review output: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-review.md`
- QA output: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-qa.md`
- Acceptance output: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-acceptance.md`
- Goal acceptance: `.codestable/goals/2026-07-22-provider-runtime-backend-session-contract/functional-acceptance.md`
- Depends on: `mux-backend-contract`, `windows-namespace-ipc-schema`

## 2. Deliverable

backend-neutral provider session payload 和 health/recovery contract 已交付。

## 3. Accepted Behavior

- Shared session writer 生成 mux-neutral canonical payload，并保留旧 tmux compatibility alias。
- Provider-specific payload 不能覆盖 shared canonical keys，冲突进入 `payload_diagnostics.protected_key_conflicts`。
- Session reader、binding evidence、runtime facts 和 runtime attach/refresh canonical-first、alias-fallback。
- Provider env 暴露 `CCB_MUX_*`，Codex/Gemini/OpenCode loader canonical-first，旧 `*_TMUX_SESSION` fallback。
- `terminal=mux` 且 `backend_family=tmux-family` 的 provider session 保持 tmux-compatible pane recovery。

## 4. Mandatory Commands

- CMD-001：checklist YAML validate passed。
- CMD-002：roadmap items YAML validate passed。
- CMD-003：`test/test_v2_runtime_launch_session_files.py`，`6 passed`。
- CMD-004：`test/test_v2_runtime_launch.py -k "session or payload or backend or env or tmux"`，`41 passed, 58 deselected`。
- CMD-005：`test/test_ccbd_runtime_refresh.py test/test_ccbd_health_monitor_rebind.py`，`7 passed`。
- CMD-006：`test/test_cli_runtime_launch_tmux_panes.py test/test_v2_runtime_launch.py -k "tmux or pane or detached"`，`15 passed, 89 deselected`。
- CMD-007：`test/test_provider_runtime_session_payload_guard.py`，`3 passed`。

## 5. Gates

- Implementation：complete。
- Independent review：Task agent `019f8aab-1fd1-75a1-a37f-0b3eca51b33e` closure `pass`。
- QA：pass。
- Functional acceptance：Task agent `019f8ace-ea96-7620-86fb-b9ff44cfa5dc` verdict `pass`。
- Roadmap writeback：complete。

## 6. Residual Risks

- 未做真实 tmux/rmux 端到端启动或长稳态 soak；真实 Windows full-chain smoke 仍由后续 roadmap item 覆盖。
- 后续新增 provider launcher 需要同步纳入 guard。
