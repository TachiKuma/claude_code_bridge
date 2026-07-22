---
doc_type: goal
goal: rmux-send-capture-logging
status: active
---

# rmux-send-capture-logging

## Objective

在已验收的 `RmuxBackend` core 上补齐 pane IO：`send_text`、`send_key`、`capture_pane`、`ensure_pane_log` / `pane_log_path`，并用 provider completion capture fixtures 证明 capture/log 格式对 completion detector 保真。

## Starting Point

`rmux-backend-core` 已提交并验收通过。当前 roadmap item `rmux-send-capture-logging` 为 `in-progress`，feature design / design-review / checklist 已存在，但 `RmuxBackend` 尚未暴露 IO/logging surface，相关 checklist 均为 `pending`。

## Acceptance Criteria

- `RmuxBackend` 暴露 send/key/capture/logging 方法，并由 fake Rmux client 单测覆盖 capability guard、文本发送、特殊键、capture policy、错误映射和 logging builder bridge。
- provider completion golden fixture 使用 Rmux capture/log 形态输入，证明 detector 对 ANSI、尾部空白、宽字符、多 turn 边界等格式不漂移。
- scope guard 证明未导入 tmux backend、未使用 tmux buffer/paste fallback、未在 Rmux IO 中拼 shell literal、未修改 provider parser 或接入 ccbd lifecycle。
- checklist、feature review、QA、acceptance、roadmap 和 goal iteration / functional acceptance 全部落盘。
- 独立 Task agent code review 与独立 Task agent 功能验收均为 pass。

## Non-Goals

- 不实现 namespace/window/pane core 或 daemon lifecycle。
- 不接 `ccb start` / `ccbd` lifecycle、foreground attach、mobile gateway production path。
- 不修改 provider completion parser 逻辑或 provider session payload/env。
- 不 fallback 到 tmux，不在 Rmux IO 中拼 `tee -a`、`sh -lc`、PowerShell/cmd 字符串。

## Decisions And Assumptions

- Rmux IO 编排放在 `lib/terminal_runtime/rmux_backend_runtime/io.py`，`RmuxBackend` 只做公开 surface 和依赖注入。
- logging 消费 `windows_shell_log_builder` 与既有 pane log path/cleanup/trim helper。
- completion parser 本身视为受保护边界，只新增 fixtures，不调整解析逻辑。
- 若 Task agent review 或功能验收不可启动，按 goal owner-stop 规则处理，不自审或自验收为完成。

## Current State

Goal 已创建，下一步进入实现与测试。

## Next Action

实现 Rmux pane IO module、补齐测试和 scope guard，然后运行 DoD 命令并启动独立 review / acceptance。
