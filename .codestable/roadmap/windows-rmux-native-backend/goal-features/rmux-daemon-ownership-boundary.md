---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: rmux-daemon-ownership-boundary
feature: 2026-07-20-rmux-daemon-ownership-boundary
status: accepted
---

# rmux-daemon-ownership-boundary Goal Feature Spec

## 1. Identity

- Roadmap item: `rmux-daemon-ownership-boundary`
- Feature dir: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary`
- Design: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-design.md`
- Checklist: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-checklist.yaml`
- Design review: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-design-review.md`
- Review output: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-review.md`
- QA output: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-qa.md`
- Acceptance output: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-acceptance.md`
- Goal acceptance: `.codestable/goals/2026-07-23-rmux-daemon-ownership-boundary/functional-acceptance.md`
- Depends on: `mux-backend-contract`, `windows-namespace-ipc-schema`

## 2. Deliverable

Rmux daemon discovery/start/health/crash/cleanup ownership boundary 已交付。

## 3. Accepted Behavior

- Rmux daemon evidence contract 覆盖 discovery、start、health、crash、cleanup 字段。
- start_result success/failure evidence 不改变 ccbd owner / lease generation。
- cleanup plan 默认 namespace/project scope，shared daemon 默认 `leave_running`。
- daemon-wide cleanup 只有 explicit force 和 force reason 才允许。
- `backend_daemon_*` diagnostics 不覆盖 ccbd `daemon_*`、namespace `namespace_*` 或裸 `tmux_socket_path`。
- 默认 tmux namespace 不输出 Rmux daemon diagnostics。

## 4. Mandatory Commands

- CMD-001：checklist YAML validate passed。
- CMD-002：roadmap items YAML validate passed。
- CMD-003：`test/test_rmux_daemon_ownership_boundary.py`，`9 passed`。
- CMD-004：tmux cleanup / startup fence / service graph，`7 passed, 13 deselected`。
- CMD-005：health / socket，`5 passed, 46 deselected`。

## 5. Gates

- Implementation：complete。
- Independent review：Task agent `019f8b7c-a2c1-7271-b380-aefaa01b9424` closure `pass`。
- QA：pass。
- Functional acceptance：Task agent `019f8b83-b68c-7bf0-b02c-741e7353b5b8` verdict `pass`。
- Roadmap writeback：complete。

## 6. Residual Risks

- 未运行全量测试套件；真实 Windows full-chain smoke 仍由后续 roadmap item 覆盖。
- `backend_daemon_action` 当前是 diagnostics 动态投影字段；后续如需静态类型强约束需单独提升。
