---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: rmux-backend-core
feature: 2026-07-20-rmux-backend-core
status: accepted
---

# rmux-backend-core Goal Feature Spec

## 1. Identity

- Roadmap item: `rmux-backend-core`
- Feature dir: `.codestable/features/2026-07-20-rmux-backend-core`
- Design: `.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-design.md`
- Checklist: `.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-checklist.yaml`
- Design review: `.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-design-review.md`
- Review output: `.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-review.md`
- QA output: `.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-qa.md`
- Acceptance output: `.codestable/features/2026-07-20-rmux-backend-core/rmux-backend-core-acceptance.md`
- Goal acceptance: `.codestable/goals/2026-07-23-rmux-backend-core/functional-acceptance.md`
- Depends on: `tmux-backend-contract-adapter`, `windows-namespace-ipc-schema`, `windows-shell-log-builder`, `provider-runtime-backend-session-contract`, `rmux-daemon-ownership-boundary`

## 2. Deliverable

Rmux namespace/session/window/pane/list/split/respawn/kill/title/user-option/style backend core 已交付。

## 3. Accepted Behavior

- `RmuxBackend` 是独立 production core adapter，不继承或导入 tmux/psmux implementation。
- capability guard 在 construction 和 operation 前 fail-fast，unsupported required command 不 fallback。
- command client seam 隔离 Rmux subprocess execution，测试使用 fake client。
- namespace/window/pane/presentation 返回 backend-neutral refs / records。
- error mapping 统一为 `MuxCommandError`，保留 operation、capability、daemon、ipc 和 command evidence。
- core 边界不包含 send/capture/logging/provider parser/foreground attach/ccbd lifecycle。

## 4. Mandatory Commands

- CMD-001：checklist YAML validate passed。
- CMD-002：roadmap items YAML validate passed。
- CMD-003：`test/test_rmux_backend_core.py`，`9 passed`。
- CMD-004：tmux/backend/pane/namespace compatibility 抽样，`52 passed`。
- CMD-005：`test/test_rmux_backend_core_import_guard.py`，`3 passed`。

## 5. Gates

- Implementation：complete。
- Independent review：Task agent `019f8b97-402d-75a2-91ca-c465fb93aa63` closure `pass`。
- QA：pass。
- Functional acceptance：Task agent `019f8ba0-0945-78e1-bee2-efb75f5ef6ae` verdict `pass`。
- Roadmap writeback：complete。

## 6. Residual Risks

- 未运行全量测试套件；真实 Windows full-chain smoke 仍由后续 roadmap item 覆盖。
- `RmuxSubprocessCommandClient` 复用 tmux-family argv helper；若后续要求更严格 helper ownership，可单独拆分。
