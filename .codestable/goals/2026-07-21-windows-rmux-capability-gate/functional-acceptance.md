---
doc_type: goal-functional-acceptance
goal: "windows-rmux-capability-gate"
status: pass
reviewer_id: "019f8478-5244-7b12-8913-635d7d3e3dd8"
final_iteration: "iterations/002.md"
---

# 功能验收

## Reviewer

可见 Task agent：`019f8478-5244-7b12-8913-635d7d3e3dd8`（nickname: Noether）。

Task agent 首轮验收指出测试覆盖缺口：未直接覆盖 Windows timeout 子进程树清理和 early-stop orphan daemon cleanup artifact。补测后复验 verdict 为 pass。

## Scope

验收范围是 `windows-rmux-capability-gate`：

- Windows 下执行真实 `rmux` capability probe 并落盘 report。
- 使用同一 probe 运行本机 `psmux`，比较更接近可用的 tmux-family backend。
- 修复 probe 工具在 Windows timeout / early-stop 场景下的报告和清理能力。
- 根据 report 判断 capability gate 是否通过。

## Acceptance Checks

- `rmux` report 已落盘：`evidence/rmux-capability/run-20260721T113521Z-1428/capability-report.json`。
- `psmux` report 已落盘：`evidence/psmux-capability/run-20260721T113657Z-13484/capability-report.json`。
- `rmux 0.9.0` report 显示 `start-server` returncode 124、unsupported、early_stop、blocking gaps = 1。
- `psmux 3.3.3` report 显示多数命令和语义 supported，但 required blocking gaps = 6。
- probe 脚本支持 timeout 后 Windows process tree cleanup、core command early-stop report、orphan daemon cleanup artifact 和 backend_impl 二进制名派生。
- 测试覆盖 timeout cleanup、early-stop cleanup evidence、core command early-stop report 和 backend_impl 派生。
- 当前没有把 capability gate 未通过伪造成可进入完整 lifecycle 实装。

## Functional Evidence

- `python -m pytest -q "test/test_rmux_capability_probe.py"`：17 passed。
- `python -m py_compile "scripts/probe_rmux_capability.py"`：通过。
- `git diff --check`：通过。
- `rmux` probe：completed，blocking gaps = 1，core lifecycle 的 `start-server` unsupported。
- `psmux` probe：completed，blocking gaps = 6。
- Task agent 复验 verdict：pass。
- 本地主线程最终进程检查未发现 `rmux` / `psmux` 残留进程。

## Verdict

pass。

本 goal 的完成含义是 capability gate 已执行、已落盘、已分析、已验收；结果是不通过。后续不能进入完整 `ccbd` namespace lifecycle 实装，除非先解决 `psmux` required gaps 或更换 backend 基座。

## Residual Risks

- `psmux` 尚未满足 `set-window-option`、attach/reattach、user option/title identity、capture fidelity、buffer paste、Ctrl-C/Ctrl-D 等 required gate。
- `rmux 0.9.0` 默认入口在 `start-server` 阶段超时，不适合作为当前 backend lifecycle 基座。
- 真实 provider、named pipe、Job Object 和完整 namespace lifecycle 仍未实现也未验收。

## Delivery Record

- Final iteration：`iterations/002.md`。
- Task agent 结果已消费；agent 已成功关闭。
