---
doc_type: goal
goal: tmux-backend-contract-adapter
status: active
---

# tmux-backend-contract-adapter

## Objective

继续 `windows-rmux-native-backend` epic 中的 `tmux-backend-contract-adapter`，交付现有 `TmuxBackend` 到 `MuxBackend` 契约的生产 adapter、错误映射、代表性调用方迁移和泄漏 inventory，保持当前 tmux 平台行为不漂移。

## Starting Point

`backend-resolver-opt-in-contract` 和 `mux-backend-contract` 已验收通过并提交。`tmux-backend-contract-adapter` 的 feature design 已 approved，checklist 仍为 pending；roadmap item 已是 `in-progress`。admission 初检显示 checklist YAML 合法，roadmap 中 `mux-backend-contract` 为 `done`，带 `PYTHONPATH=lib` 时 contract、fake backend 和 `MuxCommandError` 可导入。

## Acceptance Criteria

- implementation admission 确认 `mux-backend-contract` item done，contract module、fake backend、`MuxCommandError` 与 capability protocols 可导入。
- 新增 tmux adapter 暴露 `backend_impl=tmux`、`MuxNamespaceRef` / `MuxPaneRef`、`MuxCapabilities`，并稳定映射 socket path/name/default ipc evidence。
- `TmuxCommandError`、transient、permission、unsupported、subprocess failure 和 returncode failure 归一为 `MuxCommandError.category`，且保留诊断 evidence。
- 旧 `TmuxBackend` public methods 保持兼容，代表性 namespace/layout/runtime launch/reflow seam 迁移到 mux-facing adapter，不扩大 `_tmux_run` 泄漏面。
- checklist 核心验证命令通过或记录既有环境红灯；feature/epic 状态产物完成回写；可见 Task agent 功能验收通过。

## Non-Goals

- 不实现 `RmuxBackend` 或调用 Rmux CLI/SDK。
- 不迁移 provider session payload、`namespace_tmux_*` 或 `tmux_*` 兼容字段。
- 不修改 ccbd control-plane transport、AF_UNIX/TCP loopback、accelerator guard 或 Windows process liveness。
- 不改 shell/log builder 的 Windows 语义，不新增 `sh -lc`、PowerShell/cmd、tee/log builder 平台分支。
- 不执行 git commit、git push、merge、release、deploy 或生产变更。

## Decisions And Assumptions

- 方案深度：采用真实 `TmuxMuxBackendAdapter` 包装 `TmuxBackend`，不把 `_tmux_run` 塞进 public `MuxBackend` protocol；fake 只用于测试外部 tmux CLI 边界，不替代 adapter 核心逻辑。
- 适配器负责翻译 refs、capabilities、namespace/window/pane 语义和错误 evidence；`TmuxBackend` 保留既有 public methods。
- 代表性迁移以 layout root、ccbd namespace backend、runtime launch detached pane/server policy、agent window reflow 为核心；其他泄漏点做 inventory。

## Current State

Goal 已创建，当前为 `active`，尚未完成实现 iteration。

## Next Action

实现 `TmuxMuxBackendAdapter`、聚焦 adapter tests 与第一批代表性调用 seam。
