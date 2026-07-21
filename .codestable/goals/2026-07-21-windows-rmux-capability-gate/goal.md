---
doc_type: goal
goal: windows-rmux-capability-gate
status: complete
---

# Windows Rmux Capability Gate

## Objective

在当前 Windows 环境执行 rmux/psmux capability gate，生成可审计的 capability report，判断 `windows-rmux-native-backend` 是否具备进入后续 namespace lifecycle 实装的基础。

## Starting Point

上一阶段 `windows-rmux-native-backend` 已完成仓库内首个 runtime backend 实现切片。其 final iteration 明确后续应先运行 `scripts/probe_rmux_capability.py` 并落盘 capability report，再推进 Windows IPC、Job Object 和完整 namespace lifecycle。

## Acceptance Criteria

- 执行 `scripts/probe_rmux_capability.py` 并将 capability report 落盘到本 goal 目录。
- 汇总 `probe_status`、rmux 版本、命令面结果、语义面结果和 blocking gaps。
- 若 required 能力全部 supported 或有可接受 workaround，则记录 gate pass。
- 若 rmux 缺失或 required gap 存在，则记录 blocked/pass 不成立的证据和下一步，不伪造通过。
- Task agent 对 capability gate 产物做功能验收。

## Non-Goals

- 不安装或升级全局 rmux/psmux。
- 不在 capability gate 未通过时接入完整 `ccbd` namespace lifecycle。
- 不实现 named pipe、Job Object 或 provider 进程树治理。

## Decisions And Assumptions

- 本阶段必须使用真实 probe，不用 fake/mock，因为目标是验证当前 Windows 环境下 rmux 的命令面与语义面能力。
- 若 rmux 不存在或 probe 失败，这是有效 gate 结果；除非 owner 明确授权，不执行全局安装。
- 探针使用唯一 `-L` namespace 并由脚本执行清理；结果中的敏感文本由脚本 redaction 处理。

## Current State

已完成真实 Windows capability gate。`rmux 0.9.0` 在 `start-server` 阶段超时，`psmux 3.3.3` 大多数命令可用但仍有 6 个 required blocking gaps。Task agent 已复验通过本 gate 产物和测试覆盖。

## Next Action

本 goal 已完成，但 gate 结论是不通过。后续必须先解决 psmux required gaps 或更换 backend 基座，再进入完整 `ccbd` namespace lifecycle 实装。
