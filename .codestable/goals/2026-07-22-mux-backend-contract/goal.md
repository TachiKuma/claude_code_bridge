---
doc_type: goal
goal: mux-backend-contract
status: active
---

# mux-backend-contract Goal

## Objective

继续 `windows-rmux-native-backend` epic 中的 `mux-backend-contract`，交付 backend-neutral MuxBackend 契约、能力拆分、fake backend 测试替身、泄漏点 inventory，并通过 feature checklist 的核心验证。

## Starting Point

`backend-resolver-opt-in-contract` 已验收通过。`mux-backend-contract` 的 feature design 已 approved，checklist 仍为 pending。epic `goal-state.yaml` 当前处于 `handoff`，原因是 `GoalDriverUnavailable`，要求从 `mux-backend-contract` 继续。

## Acceptance Criteria

- 新增 contract module 定义 `MuxNamespaceRef`、`MuxPaneRef`、`MuxCapabilities`、`MuxCommandError`，且不依赖 tmux implementation module。
- `MuxBackend` 使用 namespace/window/pane io/presentation/logging/diagnostics 小协议组合，不把 `_tmux_run(args)` 暴露为 public protocol。
- fake backend 以 namespace/window/pane 状态机和 event log 支持 lifecycle、layout、io、presentation、logging、capabilities 与 failure injection。
- 记录当前 `_tmux_run` / tmux argv 泄漏点，作为 `tmux-backend-contract-adapter` 输入。
- 运行 checklist 核心验证命令，并同步 CodeStable feature/epic 状态产物。

## Non-Goals

- 不实现 `RmuxBackend` 或调用 Rmux CLI/SDK。
- 不迁移 provider session payload。
- 不修改 ccbd control-plane transport endpoint schema。
- 不删除 `TerminalBackend` / `TmuxBackend` 现有 public methods。
- 不执行 git commit、git push、merge、release、deploy 或生产变更。

## Decisions And Assumptions

- 方案深度按已 approved design：新增 capability-specific protocols 和组合 facade，不扩大现有 `TerminalBackend` 成胖接口。
- fake backend 是长期测试资产，用真实状态机表达 mux 语义；它不是 tmux argv recorder。
- 当前 goal 可直接使用 feature design/checklist 作为验收来源，不再追加 owner grill。

## Current State

Goal 已创建，尚未完成任何 implementation iteration。

## Next Action

实现 contract/fake backend/inventory/tests，并运行 checklist 核心验证。
