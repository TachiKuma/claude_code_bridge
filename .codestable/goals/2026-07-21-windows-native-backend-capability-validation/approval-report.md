---
doc_type: approval-report
unit: ".codestable/goals/2026-07-21-windows-native-backend-capability-validation"
status: approved
reason: risk
approvals:
  install-psmux-337-for-gate: approved
approval_groups: {}
created_at: 2026-07-21
---

# Approval Report

## Decision History

- 2026-07-21：owner 明确回复“确认，选择 C”。批准临时下载 `psmux 3.3.7` 到 goal evidence 目录、校验 SHA256、用显式路径运行 gate；不授权全局安装或修改 PATH。

## Decision Needed

已批准选项 C：只允许下载临时 `psmux 3.3.7` 到 goal evidence 目录并用显式路径运行，不写入全局 PATH。

## Why Now

当前本机 PATH 上的 `psmux` 是 `3.3.3`，fresh probe 仍有 6 个 required blocking gaps；GitHub API 和 Winget 搜索显示 `psmux` 当前可用版本是 `3.3.7`。如果不在最新版上重跑，就不能证明这些 gap 是否已经被上游修复。

## Context

- `rmux 0.9.0` 已是当前最新版本，但 `start-server` 在被 stdout/stderr pipe 捕获时会超时。
- `psmux 3.3.3` 是当前最佳候选，但 pane user option、interactive attach、capture fidelity、EOF 等语义仍未通过完整 gate。
- `winget search --name psmux` 显示 `marlocarlo.psmux 3.3.7`。

## Options

- A. 批准全局安装/切换 `psmux 3.3.7` 并重跑 gate：可以直接验证最新版是否闭合 required gaps，但会改变本机工具安装状态或 PATH 优先级。
- B. 不批准升级，仅基于当前 `psmux 3.3.3` / `rmux 0.9.0` 下结论：风险最低，但结论只能覆盖当前安装状态，不能排除最新版修复的可能。
- C. 只允许下载临时 `psmux 3.3.7` 到 goal evidence 目录并用显式路径运行，不写入全局 PATH（推荐）：比安装保守，但仍会下载并执行新的外部二进制。

## Recommendation

推荐 C。它满足“最新版重跑”的验证目的，同时不修改全局安装和 PATH；验证完成后是否正式安装再单独决策。Winget 元数据显示 x64 portable zip 的 SHA256 是 `60ff7b236f64184921cef3c1ff2611aa5a36fcc7ed8e2a58e968b8ded57f6028`。

## Risks And Tradeoffs

- A 会改变本机包状态，可能覆盖当前手工安装目录或 PATH 解析顺序。
- C 不改变全局状态，但仍需要信任并执行 GitHub release / Winget 对应的外部可执行文件。
- B 最保守，但无法完成“最新版 psmux capability gate”这条验证。

## Non-Automatic Actions

本审批不授权 `git commit`、`git push`、修改生产配置、接入完整 `ccbd` lifecycle，或接受 capability gate override。

## After You Answer

继续执行选项 C：临时下载 `psmux 3.3.7` x64 portable zip，校验 SHA256，用解压出的显式 `psmux.exe` 跑 capability gate，并把结果写入本 goal evidence。
