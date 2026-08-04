# Herdr UI integration ccbd bootstrap 根因分析

## 根因判断

当前失败链路优先级如下：

1. `ccbd` 启动阶段未能稳定进入 mounted。
2. keeper 重试启动 ccbd，ccbd 在 ready 前退出，最终达到最大失败次数后被抑制。
3. lifecycle/startup 证据中出现 JSON 解析异常：`Expecting property name enclosed in double quotes`。
4. `layout-status` 能从配置读到两个 agent，但 runtime state 没有 pane id，说明问题发生在 control-plane/runtime materialization 之前。

## 追加判断：run-20260804-205310

最新 UI spike 把状态推进为 `mounted-but-layout-materialization-missing`：`ping ccbd` / `ping all` 均成功，`layout_configured_count=2`，但 `layout_materialized_count=0`。同时 doctor bundle 的 `startup-report.json` 记录 `start_flow_failed`，`failure_reason=unknown option: --json`。

本机 Herdr 0.7.5 的帮助输出显示 `workspace list` 和 `pane list` 不支持 `--json`；机器可读 workspace/pane 状态应从 `api snapshot` 读取。因此上一轮“给 Herdr list 命令显式追加 `--json`”是兼容性回归，会打断 startup flow，并让 layout materialization 停在旧的 mounted/unattachable 状态。

## 设计结论

- CCB provider authority 继续以 CCB `ping` / `ps` / `layout status --json` 为准。
- Herdr agents 面板文本只作为辅助 UI 观察。
- Herdr CLI 自动采集必须优先使用机器可读命令；Herdr 0.7.5 的 workspace/pane 状态使用 `api snapshot`，不要对 `workspace list` / `pane list` 追加 `--json`。
- 启动期 JSON 状态文件读取需要短重试和路径化错误信息，避免瞬时半写入/损坏状态把根因隐藏成无路径的 JSONDecodeError。
