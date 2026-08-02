---
doc_type: approval-report
unit: .codestable/roadmap/windows-native-herdr-ccb
status: approved
reason: ScopeBoundaryChange
approvals:
  roadmap-review: approved
  roadmap-plan: approved
  all-feature-designs: approved
  ccbd-windows-control-plane-transport-design: approved
  goal-acceptance: approved
  goal-commits: approved
  ReopenBackendClientForLifecycleFacade: approved
approval_groups:
  child-designs:
    status: approved
    confirmation_id: child-designs-2026-08-02-windows-native-herdr-ccb
    decisions:
      all-feature-designs: approved
      ccbd-windows-control-plane-transport-design: approved
  goal-execution:
    status: approved
    confirmation_id: goal-execution-2026-08-01-windows-native-herdr-ccb
    decisions:
      - goal-acceptance
      - goal-commits
created_at: 2026-07-31
updated_at: 2026-08-02
---

# Approval Report

## Decision History

- 2026-07-31：owner 批准 roadmap review、plan 与 child design batch，并通过 `/goal` 授权执行、acceptance 和 scoped local commit；不含 push、merge、deploy 或发布。
- 2026-08-02：真实 Herdr 定位为 `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`。真实 CLI 契约验证确认五项核心 capability 可用，但暴露 server lifecycle 与 split direction 缺陷。owner 选择 **ReopenBackendClient**；该 child 已修复 server 启动 seam 与 `bottom -> down` 归一并 accepted。
- 2026-08-02：Native Windows `ccb -> ccbd` 因 AF_UNIX-only control-plane 被阻断。owner 选择 **CreateRoadmapItem**；`ccbd-windows-control-plane-transport` 已完成并 accepted。
- 2026-08-02：重新运行 CMD-013 后，`ccbd ping` 已在 Windows TCP loopback control-plane 上返回 healthy，证明前一 blocker 已解除；但 namespace create 在 Herdr lifecycle materialization 阶段失败，进入本 checkpoint。
- 2026-08-02：owner 选择 **ReopenBackendClientForLifecycleFacade**，批准 `approval-report.md#ReopenBackendClientForLifecycleFacade`；重开 `herdr-backend-client`，仅在 `HerdrBackend` facade 中定义并实现 workspace/pane 到 ccbd logical window/root pane 的 V2 映射，补审查与真实 Native Windows evidence 后恢复 CMD-013。

## Decision Needed（已解决）

当前 `ccbd-herdr-namespace-lifecycle` 的 CMD-013 需要 owner 决定如何承接 Herdr 的**逻辑 window / root pane lifecycle facade**缺口。

真实 transcript：
`.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/evidence/cmd-013-native-windows-herdr-transcript.md`

当前可观察事实：

- `ccb -n` 已越过交互确认，启动 ccbd，且 `ping ccbd` 返回 `mount_state: mounted`、`health: healthy`、`control_plane_endpoint.kind: tcp_loopback`。
- namespace materialization 失败为：`mux backend lacks required method for ensure_window`。
- 当前 `HerdrBackend` 只有 session/pane/I/O facade；缺少 `ensure_window`、`window_root_pane`、logical window-to-pane 映射及相应的 reflow/destroy 语义。
- 真实 Herdr CLI 有 `workspace` 与 `pane`，但没有 tmux-compatible window object；不能在 ccbd 调用点或 transcript 中假装 window 已实现。
- 现有 `ccbd-herdr-namespace-lifecycle` design 要求通过 V2 backend primitive 实现 layout/reflow/reload；当前 feature checklist 同时禁止 `herdr_socket_client_changes`。
- 已 accepted 的 `herdr-backend-client` 仅被授权重开以修 server lifecycle 与 split direction；它的已验收 facade 并未定义 window/root-pane 语义。

## Why Now

这是 CMD-013 从 control-plane blocker 前进后的第一个真实 Herdr lifecycle blocker。继续只改 ccbd helper 会把不存在的 Herdr window primitive 伪造成成功，违反本 feature 的 fail-closed 与 project-authority contract；直接扩张 accepted backend-client 则会绕过该 child 的 design/review/QA/acceptance gate。

## Options

- **ReopenBackendClientForLifecycleFacade（推荐）**：重开 `herdr-backend-client`，仅为 ccbd lifecycle 设计并实现真实 Herdr `workspace/pane` 到 V2 logical window/root-pane 的明确 facade，补 Native Windows contract tests；然后恢复当前 child 重跑 CMD-013。
- **CreateLifecycleAdapterChild**：在当前 namespace child 前新增一个独立 roadmap item，专门实现和验收 Herdr logical-window lifecycle adapter；边界更清晰，但增加一个 feature loop。
- **KeepBlocked**：保持当前 roadmap handoff，不引入该 facade，停止 CMD-013 后续推进。

## Recommendation

选择 **ReopenBackendClientForLifecycleFacade**。该缺口的实现落点是 `terminal_runtime.HerdrBackend` facade，而不是 ccbd durable state 或 provider runtime；与此前已授权的 backend-client 语义最内聚。重开 design 必须明确：一个 Herdr workspace 如何承载 ccbd logical windows、root pane 如何稳定识别、哪些 tmux-only UI/reflow 操作保持 unsupported/fail-closed，以及 kill 只能销毁当前 namespace。

## Risks And Tradeoffs

- 直接把所有 ccbd windows 映射到一个 Herdr workspace 的同一 root pane，会损坏 topology/reload identity，不能接受。
- 新建 child 增加流程开销，但能避免已 accepted backend-client 的语义漂移。
- 重开 backend-client 需要重新 review、QA、acceptance 与真实 Herdr evidence；此前 acceptance 不自动覆盖新 facade。

## Non-Automatic Actions

不会自动执行 git commit、push、merge、发布、部署或修改 provider runtime/recovery/Mobile/Config UI/release surface。未获得本决策前，不会在 ccbd 层伪造 Herdr window 成功路径，也不会修改已 accepted backend-client 的 contract。

## After You Answer

- 选择 `ReopenBackendClientForLifecycleFacade`：重开该 child，补 design/checklist/review 后实现 facade 和真实 Herdr evidence，再恢复 `ccbd-herdr-namespace-lifecycle` 的 CMD-013。
- 选择 `CreateLifecycleAdapterChild`：插入新 roadmap item 并完成其独立 feature loop。
- 选择 `KeepBlocked`：将 roadmap 保持 blocked，并记录终态原因。
