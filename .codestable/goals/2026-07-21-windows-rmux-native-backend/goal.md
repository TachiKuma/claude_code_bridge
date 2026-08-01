---
doc_type: goal
goal: windows-rmux-native-backend
status: complete
---

# Windows Rmux Native Backend

## Objective

完成仓库内 Windows rmux/psmux native backend 的首个可验收实现切片：在不破坏现有 tmux 默认路径的前提下，让 runtime 层能显式选择 psmux/rmux 后端，并为后续 Windows 真机 namespace lifecycle 接入留下清晰边界。

## Starting Point

仓库没有既有 CodeStable goal。已有 `docs/ccbd-windows-psmux-plan.md`、`scripts/probe_rmux_capability.py` 和 `test/test_rmux_capability_probe.py`，但 `terminal_runtime` 只暴露 `TmuxBackend`，后端选择也默认只识别 `tmux`。

## Acceptance Criteria

- `terminal_runtime` 暴露 `PsmuxBackend`，并能用 `backend_family` / `backend_impl` 区分 tmux family 与 psmux 实现。
- 显式 `terminal_backend`、`backend_impl`、`mux_backend` 或会话字段能选择 `psmux` / `rmux`；现有 tmux 默认路径保持兼容。
- rmux 后端使用 `rmux` 命令与 `-L namespace`，不泄漏 `CCB_TMUX_CONFIG`。
- 聚焦测试通过，并记录当前环境无法完成 Windows 真机 psmux capability gate。
- Task agent 完成功能验收并给出 verdict。

## Non-Goals

- 不在缺少 Windows 真机 capability report 的情况下接入完整 `ccbd` namespace lifecycle。
- 不实现 Windows named pipe、Job Object 和 provider 进程树治理。
- 不把 WezTerm 作为本 goal 的主路径。

## Decisions And Assumptions

- 采用 tmux-family 复用方案，而不是复制一套独立 backend 行为，原因是 psmux/rmux 目标是尽量贴近 tmux 命令语义。
- 本轮选择真实后端类和选择逻辑，不做占位实现；但不越过 Windows 真机 capability gate。
- 当前环境只能做代码级、单测级和产物级验收，不能证明 Windows GUI/ConPTY/provider 进程树行为。

## Current State

已完成仓库内 rmux/psmux backend 实现切片、修复 Task agent 首轮验收发现的 `CCB_TMUX_CONFIG` 环境泄漏问题，并通过 Task agent 复验。最终 Windows 真机 capability gate、named pipe、Job Object 和完整 `ccbd` namespace lifecycle 明确不属于本切片完成条件。

## Next Action

Goal 已完成。后续阶段应先在 Windows 真机运行 psmux capability gate，再推进 IPC、Job Object 和 namespace lifecycle 接入。
