---
doc_type: goal-evidence-summary
goal: windows-native-backend-capability-validation
status: evidence-complete
updated_at: 2026-07-21
---

# Backend Validation Conclusion

## Scope

本结论覆盖当前已获得的证据：

- 本机 `rmux 0.9.0`。
- 本机 PATH 上的 `psmux 3.3.3`。
- 临时下载并用显式路径执行的 `psmux 3.3.7`。
- 参考仓库 `D:\Python\GitHub\claude_code_bridge-rmux-capability-gate` 中 v8.0.16 时代的 rmux 实现与证据。

## Requirement Matrix

| CCB Windows 需求 | rmux 0.9.0 | psmux 3.3.3 | psmux 3.3.7 | 结论 |
|---|---:|---:|---:|---|
| 建立 mux server / session namespace | 部分可解 | 通过 | 通过 | `rmux` 会启动 daemon 的命令不能用 `stdout/stderr=PIPE`；改用 `DEVNULL` / 继承 stdio 后可创建 session。 |
| 多项目 namespace 隔离 | 可验证但未全绿 | 通过 | 通过 | `psmux` full probe 通过；`rmux` 需要 stdio-aware runner 后继续 gate。 |
| pane/window 创建与布局操作 | 可验证但未全绿 | 通过 | 通过 | 两个候选都接近 tmux-family，但 `rmux` gate 仍被多个后续 gap 阻断。 |
| foreground attach/reattach | 未通过 | 未通过 | 未通过 | `rmux 0.9.0` capture attach 报 `open terminal failed: not a terminal`；`psmux 3.3.7` 非交互 attach-survival 不能证明前台 UI 保持。 |
| pane identity marker | 未通过 | 未通过 | 部分通过 | `psmux 3.3.7` window option 可读，pane title 可读；pane user option 仍读不回，当前 tmux pane-level identity 不能原样复用。 |
| provider completion / capture fidelity | 未通过 | 未通过 | 未通过 | `psmux 3.3.7` 仍缺 OSC、wrapping、wide-char 等真实 parser fidelity 证据。 |
| 大文本输入 | 未通过 | 部分可解 | 部分可解 | `psmux 3.3.7` 的 `load-buffer` + `paste-buffer` + 显式 `Enter` 可落屏；provider pane 仍需专项验收。 |
| interrupt / EOF | 未通过 | 部分可解 | 部分可解 | `psmux 3.3.7` 的 `C-c` 可中断；`C-d` 不等价 Windows EOF。参考 rmux 实现用 `C-z Enter` 作为 logical EOF。 |
| kill / cleanup | 部分可解 | 通过 | 通过 | `rmux` 临时 daemon 可按 namespace 或进程命令行清理；但 `kill-server` 在部分 probe 场景仍 partial。 |

## Current Candidate Ranking

1. `psmux 3.3.7` 是当前最优候选：full gate blocking gaps 从 `psmux 3.3.3` 的 6 个降到 4 个，修复了 `set-window-option` 和 `user_options_title` 的 required gap；但仍不能直接声明胜任完整 `ccb` Windows 运行需求。
2. `psmux 3.3.3` 不建议继续作为目标基座：它缺少 `set-window-option` / reliable identity，已经被 `3.3.7` 明确改善。
3. `rmux 0.9.0` 不能直接复用 v8.0.16 参考实现作为完整基座。参考实现的通用 `RmuxRunner` 使用 `capture_output=True`，而本机 `rmux 0.9.0` 对启动 daemon 的命令在该 stdio 形态下会超时；即使改成 stdio-aware runner，当前 full gate 仍有 8 个 gaps。

## Required Workarounds Before Product Integration

- `attach_reattach`：增加真实交互终端/ConPTY 黑盒验收，证明 `ccb` 前台 attach、关闭终端、重新 attach 的用户路径。
- `pane identity`：对 `psmux 3.3.7`，可用 window option 和 pane title 做一部分 marker；不要依赖 `#{@ccb_*}` pane user option。若需要 pane slot authority，应改成 `pane title + window/session marker + ccbd sidecar registry`。
- `capture fidelity`：provider completion 不得只依赖 `capture-pane` 解析；capture 只能作为诊断证据，或先增强 parser 并用真实 provider fixture 验收。
- `buffer paste`：把大文本输入定义为 `paste-buffer` 后显式 submit，或改成 file/stdin/chunked send，并用 provider pane 验收。
- `EOF`：Windows 下不承诺 Unix `C-d`；若继续 tmux-family 抽象，可参考 v8.0.16 的 `RmuxPaneIO`，把 logical EOF 映射为 `C-z Enter`，但必须对实际 provider 验收。
- `rmux lifecycle`：若保留 `rmux` 候选，`start-server` / `new-session` 这类 daemon 启动命令不能用捕获 stdout/stderr 的通用 runner；需要 lifecycle runner 分层，并重新跑完整 gate。

## Rmux Reference Findings

参考仓库 v8.0.16 提供了有价值的实现经验，但不能直接证明当前 `rmux 0.9.0` 胜任：

- `RmuxMuxBackendAdapter` 已经把 rmux 作为独立 `MuxBackend`，并通过 `RmuxCapabilityGate` fail-fast，不把 unsupported capability 静默吞掉。
- `RmuxPaneIO.send_text()` 使用 `load-buffer` / `paste-buffer -p` / `send-keys Enter` / `delete-buffer`，这与本轮 `psmux` paste workaround 一致。
- `RmuxPaneIO.send_key()` 把 logical EOF 从 `C-d` 映射为 `C-z Enter`，这是 Windows shell 语义下更现实的方向。
- `rmux-foreground-attach-stdio` issue 已确认 foreground attach 不能使用 captured stdio，修复方案是 attach 时继承当前控制台 stdio。
- 但参考 `RmuxRunner` 的普通命令仍是 `capture_output=True`；本轮 fresh evidence 证明 `rmux 0.9.0` 的 `start-server` / `new-session` 在该形态下会超时。

## Evidence

- `evidence/local-backend-inventory.json`
- `evidence/psmux-current/run-20260721T122234Z-14668/capability-report.json`
- `evidence/rmux-current/run-20260721T122234Z-16304/capability-report.json`
- `evidence/rmux-disable-tiny-cli/run-20260721T122234Z-17648/capability-report.json`
- `evidence/rmux-with-libexec-path/run-20260721T122744Z-17132/capability-report.json`
- `evidence/rmux-with-libexec-path-disable-tiny-cli/run-20260721T122744Z-600/capability-report.json`
- `evidence/gap-specific-summary.json`
- `evidence/rmux-diagnostics-summary.json`
- `evidence/psmux-337-release-metadata.json`
- `evidence/winget-psmux-337-show.txt`
- `evidence/winget-rmux-show.txt`
- `evidence/psmux-337-download/download-verification.json`
- `evidence/psmux-337-download/extracted-inventory.json`
- `evidence/psmux-337/run-20260721T124326Z-6984/capability-report.json`
- `evidence/psmux-337-gap-specific.json`
- `evidence/psmux-337-attach-survival.json`
- `evidence/rmux-090-stdio-shape-diagnostics.json`
- `evidence/rmux-090-stdio-aware-probe/run-20260721T124903Z-15696/capability-report.json`
- `evidence/rmux-090-reference-attach-survival/run-20260721T125003976930Z-17352-ns-910d00fe/artifacts/preflight/environment.json`

## Verdict

当前可验证结论是：没有任何候选可以在“无需产品 workaround / 无需补交互验收”的条件下直接胜任完整 `ccb` Windows native backend 基座。

推荐路线是继续以 `psmux 3.3.7` 作为首选候选基座进入后续设计，但必须把剩余 4 个 gap 转成明确 contract：

- attach/reattach 必须补真实前台终端验收。
- provider completion 不以 `capture-pane` 为唯一 authority。
- 大文本输入采用 `paste-buffer + explicit submit` 或 provider-specific 通道。
- EOF 不承诺 Unix `C-d`，使用 provider-specific 退出/提交协议或 Windows logical EOF。

`rmux 0.9.0` 可作为备选研究路线，但不是当前推荐基座；它至少需要 stdio-aware lifecycle runner、foreground attach runner、logical EOF 映射和重新通过完整 gate。
