---
doc_type: feature-design-review
feature: 2026-07-20-windows-shell-log-builder
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7bf6-e2d4-7651-9cb3-81eb6881ffab"
reviewed: 2026-07-20
round: 2
---

# windows-shell-log-builder feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-windows-shell-log-builder/windows-shell-log-builder-design.md`
- Checklist: `.codestable/features/2026-07-20-windows-shell-log-builder/windows-shell-log-builder-checklist.yaml`
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md` §4.4、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related designs: `.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-design.md`、`.codestable/features/2026-07-19-tmux-backend-contract-adapter/tmux-backend-contract-adapter-design.md`、`.codestable/features/2026-07-19-windows-namespace-ipc-schema/windows-namespace-ipc-schema-design.md`
- Code facts checked: `lib/terminal_runtime/env.py`、`lib/terminal_runtime/tmux_respawn.py`、`lib/terminal_runtime/tmux_respawn_service.py`、`lib/terminal_runtime/tmux_logs.py`、`lib/terminal_runtime/tmux_backend_runtime/services.py`、`lib/cli/services/runtime_launch_runtime/tmux_panes.py`、`lib/ccbd/services/project_namespace_runtime/backend.py`
- Test facts checked: `test/test_terminal_runtime_tmux_respawn.py`、`test/test_terminal_runtime_tmux_respawn_service.py`、`test/test_terminal_runtime_tmux_logs.py`、`test/test_v2_project_namespace_backend.py`、`test/test_v2_project_namespace_state.py`、`test/test_v2_runtime_launch.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: subagent `019f7bf6-e2d4-7651-9cb3-81eb6881ffab`
- Raw output: round 1 提出 1 个 blocking 和 3 个 important；round 2 focused closure 判定全部 closed，remaining findings 为 none，verdict 为 `passed`。
- Merge policy: 主 agent 已按 reviewer findings 修订 CMD-005、clipboard scope、shell diagnostic 读取面和 `wrap_provider_command()` 返回语义，并重新运行 YAML / workflow-next 校验。
- Gate effect: independent review completed and merge verified；允许交回 `cs-epic` child design batch。

## 2. Design Summary

- Goal: 建立 Windows Runtime Boundary 内的 shell/log command builder，集中处理 provider command wrapping、pipe-pane log append、stderr redirection 和默认 shell 诊断。
- Key contracts: `wrap_provider_command(cmd, cwd) -> str`、`build_pipe_log_command(log_path) -> str`、`append_stderr_redirection(cmd, stderr_log_path) -> tuple[str, str | None]`；`resolve_shell(...) -> ShellResolution` 作为稳定诊断读取面。
- Derived cleanup: `backend.py` 和 `tmux_panes.py` 的 clipboard copy-pipe command 去重只作为同一 shell 边界的派生 cleanup，不新增 clipboard capability。
- Steps: 6 步，覆盖 builder contract、stderr redirection extraction、provider wrapper wiring、pipe log wiring、clipboard command de-dup、regression/guard。
- Validation: checklist YAML、items YAML、builder tests、tmux respawn/log 回归、真实 clipboard policy 回归和 shell string leakage guard。

## 3. Findings

### blocking

none

### important

none

### nit

none

### learning

- `wrap_provider_command()` 必须与当前 tmux `respawn-pane` 的 `full_command: str` 挂载点对齐；返回 argv 会把 quoting 责任重新推回调用层。
- 默认 shell 可诊断需要稳定读取面，不能只把 `ShellResolution` 作为内部实现细节。
- clipboard copy-pipe 是当前业务层残留的 shell literal，适合作为派生 cleanup 收口，但不应被表述成 roadmap §4.4 之外的新能力。

## 4. User Review Focus

- 实现时优先守住三项主契约：provider command wrapper、pipe log command、stderr redirection。
- `resolve_shell()` 的 diagnostic 应能被后续 doctor/debug payload 直接消费。
- clipboard de-dup 只允许作为 shell literal 收口；不得顺带改变 copy-mode 行为或新增 clipboard feature。
- `CMD-005` 必须继续使用真实 clipboard policy 回归入口：`test_v2_project_namespace_backend.py`、`test_v2_project_namespace_state.py`、`test_v2_runtime_launch.py`。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Roadmap §4.4 alignment | pass | E/C | 三项 builder method 与默认 shell diagnostic 均已明确 | none |
| Scope control | pass | E/C | clipboard copy-pipe 被标注为派生 cleanup，不新增 capability | none |
| Current code mounting | pass | E | design 覆盖 `tmux_respawn_service`、`tmux_logs`、`tmux_backend_runtime/services`、ccbd namespace backend、runtime launch tmux panes | none |
| Validation entry accuracy | pass | E | CMD-005 已切到真实 clipboard policy 测试文件 | none |
| Checklist YAML | pass | E | `validate-yaml.py --yaml-only` 通过 | none |
| Roadmap items YAML | pass | E | `validate-yaml.py` 通过 | none |

Summary: E=6, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- Windows shell quoting 仍需实现阶段通过 matrix tests 覆盖 PowerShell/cmd/POSIX 差异；design 已要求 shell family tests。
- Clipboard copy-pipe 去重可能触发现有测试 fixture 大面积更新；实现时应优先抽共用 expected command helper，避免复制新常量。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child design batch；本 feature design 保持 `draft`，等待所有子 feature design-review passed 后统一 owner 确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004
- Attributed delta: `.codestable/features/2026-07-20-windows-shell-log-builder/windows-shell-log-builder-design.md`、`.codestable/features/2026-07-20-windows-shell-log-builder/windows-shell-log-builder-checklist.yaml`
- Verification: independent reviewer `019f7bf6-e2d4-7651-9cb3-81eb6881ffab` confirmed remaining findings none；YAML 校验通过；workflow-next 可恢复到当前 child 仅缺 design-review 的状态，写入本文件后应继续 batch。
- Classification: 本次 closure 只收紧设计契约、验证命令和派生 cleanup 定位，不改变生产代码。
