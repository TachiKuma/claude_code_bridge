---
doc_type: issue-report
issue: 2026-07-24-rmux-pane-id-exact-target
status: confirmed
issue_path: fast-track
severity: P1
summary: 源码版 ccb 使用 rmux 启动后 agent pane 没有按 2x 布局稳定绑定
tags: [rmux, layout, pane-binding]
---

# rmux pane id exact target Issue Report

## 1. 问题现象

源码版 `ccb` 启动后，`.ccb/ccb.config` 中 `codex, agent1; claude, agent2` 语义上应形成 2x agent 区域，但运行态只给部分 pane 写入了正确身份，多个 agent runtime 指向同一个 pane，界面表现为不是预期 2x 布局。

## 2. 复现步骤

1. 在源码工作区使用 `ccb-src.ps1` / `ccb-src.cmd` 启动项目。
2. 配置包含 `main = "codex:codex, agent1:codex; claude:claude, agent2:codex"`。
3. 观察 `.ccb/ccbd/startup-report.json` 和 `rmux list-panes`。
4. 看到多个 agent runtime 绑定到同一 pane，部分 pane 缺少 `@ccb_role` / `@ccb_slot`。

复现频率：当前运行态稳定观察到。

## 3. 期望 vs 实际

**期望行为**：4 个 agent 按配置落到主窗口的 2x agent 区域，且每个 agent runtime 绑定唯一 pane。

**实际行为**：`agent1`、`claude`、`agent2` 的 runtime 曾共同指向 `%2`，现场 pane 中只有 `codex` 和 `agent2` 有正确身份，另外存在空 pane。

## 4. 环境信息

- 涉及模块 / 功能：rmux backend、project namespace topology materialization、pane target canonicalization
- 相关文件 / 函数：`lib/terminal_runtime/rmux_backend_runtime/targets.py`, `lib/ccbd/services/project_namespace_runtime/backend.py`
- 运行环境：Windows 源码版 ccb，rmux 后端
- 其他上下文：`ccb-src.ps1` 仅设置源码根和默认 rmux 后端，不直接创建布局。

## 5. 严重程度

**P1** - 启动后 resident agent pane 绑定错误，会破坏多 agent 可视布局和后续 pane 定向操作。

## 备注

快速通道根因：rmux `%N` 在 `split-window` 返回值和后续 pane target 中都有 stable pane id / pane index alias 双重语义。此前两条路径都可能在 exact id 和 index alias 冲突时选错 pane，导致 `agent1` 的 Codex bridge 启动到 Claude pane。
