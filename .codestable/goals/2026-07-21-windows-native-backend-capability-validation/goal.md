---
doc_type: goal
goal: windows-native-backend-capability-validation
status: active
---

# Windows Native Backend Capability Validation

## Objective

验证三条 Windows native backend 基座建议：升级/重跑 `psmux` capability gate、逐项验证 `psmux` required gaps 的可解性或可接受 workaround、诊断 `rmux` 入口超时原因，并给出候选 backend 是否足以支撑 `ccb` Windows 运行需求的证据化结论。

## Starting Point

前置 goal `windows-rmux-capability-gate` 已完成，但 capability gate 的业务结论未通过：

- `rmux 0.9.0` 在 `start-server` 阶段超时，无法证明可建立 mux server。
- `psmux 3.3.3` 支持多数 tmux-family 命令，但仍有 6 个 required blocking gaps。
- 仓库内首个 `PsmuxBackend` 实现切片已验收通过，但完整 Windows native 运行仍依赖 capability gate、IPC、Job Object 与 namespace lifecycle。

## Acceptance Criteria

- 记录本机 `rmux` / `psmux` 安装来源、版本、可升级状态，并在可行时对最新版 `psmux` 重跑 capability probe。
- 对 `psmux` 6 个 required gaps 逐项给出 fresh evidence、可解性判断、workaround 接受条件和对 `ccb` Windows 运行需求的影响。
- 诊断 `rmux start-server` 超时的安装布局、daemon 可执行文件、环境开关和直接启动行为。
- 形成候选 Windows native backend 基座是否胜任 `ccb` 完整运行需求的明确结论，且不把未证明能力伪装为通过。
- Task agent 对本轮证据和结论做功能验收并给出 verdict。

## Non-Goals

- 不在 capability gap 未闭合时接入完整 `ccbd` namespace lifecycle。
- 不修改生产环境配置，不执行 `git commit` / `git push`。
- 不把 `psmux` 或 `rmux` 的外部项目事实写成未经验证的内部契约。

## Decisions And Assumptions

- 本 goal 的完成条件是“证据充分、结论明确”，不是强行让某个 backend 通过。
- 若升级 `psmux` 需要包管理写系统级状态，需先遵守危险操作确认；未获确认时以现有版本与可升级证据继续。
- 对 `psmux` gap 的 workaround 必须能维持 `ccb` 的核心语义：项目 namespace、attach/reattach、pane identity、输入控制、状态判断和可诊断性。

## Current State

已完成本轮证据验证：

- 已按 owner 批准的选项 C 临时下载 `psmux 3.3.7` 到 goal evidence 目录，SHA256 与 Winget 元数据一致，并使用显式路径运行 capability gate。
- `psmux 3.3.7` full gate 从 `psmux 3.3.3` 的 6 个 blocking gaps 降到 4 个，修复了 `set-window-option` 和 `user_options_title`；剩余 gap 是 `attach_reattach`、`capture_format_fidelity_for_provider_completion`、`buffer_paste`、`ctrl_c_ctrl_d`。
- 已参考 `D:\Python\GitHub\claude_code_bridge-rmux-capability-gate` 的 v8.0.16 rmux 实现与证据，并验证当前 `rmux 0.9.0` 对 daemon 启动类命令存在 stdout/stderr capture 超时问题。
- 当前证据结论是：没有候选能在无 workaround 条件下直接胜任完整 `ccb` Windows native backend 基座；`psmux 3.3.7` 是后续设计的首选候选，`rmux 0.9.0` 是需要 runner/lifecycle 重做后才能继续评估的备选。

## Next Action

进行终端功能验收；若 Task agent 复验通过，写入 `functional-acceptance.md` 并完成 goal。
