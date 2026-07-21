---
doc_type: goal
goal: windows-rmux-full-backend
status: active
---

# Windows Rmux Full Backend

## Objective

重做 rmux stdio-aware lifecycle runner、foreground attach runner、logical EOF 映射，并重跑完整 capability gate，使 rmux 能作为 `ccb` Windows native backend 完整基座进入可验收状态。

## Starting Point

前置验证已经完成：

- `rmux 0.9.0` 在普通 `capture_output=True` runner 下执行 `start-server` / `new-session` 会超时。
- 同类命令在 `DEVNULL` 或继承 console stdio 时可快速返回。
- stdio-aware probe 绕过 daemon 启动问题后，full gate 仍有 8 个 gaps。
- `D:\Python\GitHub\claude_code_bridge-rmux-capability-gate` v8.0.16 有 rmux runner/backend/IO 分层经验，可作为实现参考。

## Acceptance Criteria

- 仓库内 rmux lifecycle runner 对 daemon/session 管理采用 stdio-aware 策略，避免 Windows capture 模式挂起。
- 仓库内 rmux foreground attach runner 对交互 attach 继承终端 stdio，且不污染普通命令 runner。
- 仓库内 logical EOF 在 Windows rmux 路径映射为可工作的 EOF 发送方式，并有测试或 probe 证据覆盖。
- 完整 rmux capability gate 使用更新后的 runner/adapter 重跑并落盘 fresh report，报告明确 pass/fail 和剩余 gaps。
- 聚焦测试通过；Task agent 对实现和 gate 结果做功能验收并给出 pass/fail/inconclusive。

## Non-Goals

- 不修改全局 PATH、不全局升级或安装 rmux。
- 不执行 `git commit` / `git push`。
- 不在 capability gate 未通过时宣称 rmux 已完整胜任。
- 不引入 psmux 作为本 goal 的主实现路径。

## Decisions And Assumptions

- 本 goal 选择真实实现，不用 fake / stub：runner 和 EOF 映射是 Windows native backend 的核心正确性路径，属于长期维护资产。
- 优先复用当前仓库既有 terminal runtime 接口和 v8.0.16 参考实现经验，避免新建平行抽象。
- capability gate 的结果可以是 pass、fail 或带剩余 gap 的 blocked 结论；完成 goal 的条件是实现与验证闭环完成，不是伪造 gate 通过。

## Current State

状态为 active，等待代码结构恢复和首轮实现。

## Next Action

读取现有 rmux/terminal runtime 代码与 v8.0.16 参考实现，确定需要迁移或重写的最小实现切面。
