---
doc_type: goal-functional-acceptance
goal: "ccbd-windows-full-chain-smoke"
status: pass
reviewer_id: "codex-task-agent-ccbd-windows-full-chain-smoke-20260723"
task_agent_id: "019f8db6-cde0-7440-8f43-6a01c4992b49"
final_iteration: "iterations/004.md"
---

# 功能验收

## Reviewer

- Task agent id: `019f8db6-cde0-7440-8f43-6a01c4992b49`
- Reviewer id: `codex-task-agent-ccbd-windows-full-chain-smoke-20260723`
- Role: 独立功能验收，只读检查 goal acceptance、transcript、parser 和 scope guard。
- 生命周期：验收结果已消费，agent 已关闭。

## Acceptance Checks

- 2026-07-25 strict closeout：原 PS5 / PS7 transcript 路径在当前 checkout 不存在，不再作为当前机械 pass 依据。
- 当前 canonical native Windows evidence 使用 `artifacts/rmux-windows-validation/manual-transcript.json` 与 `artifacts/rmux-windows-validation/rmux_windows_validation_report.json`。
- validation matrix fresh parser 对该 transcript 生成 `selected_cases_status=pass`、`full_matrix_status=pass`。
- 该 evidence 满足 `host_kind=native_windows`、`control_plane=ccbd`、`backend_impl=rmux`、`ccbd_transport=tcp_loopback`、`probe_bypass=false`。
- 核心命令记录齐全：`ccb-start`、`ccb-ping-ccbd`、`ccb-doctor`、`ccb-ask`、`ccb-kill-force`；核心命令通过 `python .../ccb.py --project ...` 进入，不是 direct rmux。
- `fake_provider` 只在 `CCB_TEST_ENTRYPOINT=1` 下放行，runtime/backend evidence 仍显示 `runtime=rmux:%1`、`terminal=rmux`、`namespace_backend_impl=rmux`。
- parser fail-closed 覆盖缺字段、WSL、probe bypass、fake backend、direct rmux、错误 subcommand、unknown scope path 负例。
- cleanup evidence 显示 `endpoint_removed=true`、`token_removed=true`、`rmux_namespace_removed=true`、`session_removed=true`、`owned_process_residue=[]`。

## Functional Evidence

Task agent 独立只读抽查：

- 历史 Task agent 曾记录 PS5 / PS7 transcript parser pass；这些 artifact 在当前 checkout 不存在，不能作为 strict closeout 的 fresh evidence。
- `python scripts/ccbd_windows_full_chain_smoke.py --scope-guard --diff-base HEAD --json` -> `ok:true`，`forbidden_paths: []`。
- `python -m pytest -q -p no:cacheprovider test/test_ccbd_windows_full_chain_smoke.py` -> `31 passed`。

Strict closeout fresh evidence：

- `python scripts/rmux_windows_validation_matrix.py --lane windows_true_host --scope full --transcript "artifacts/rmux-windows-validation/manual-transcript.json" --json` -> `selected_cases_status=pass`，`full_matrix_status=pass`。
- `artifacts/rmux-windows-validation/rmux_windows_validation_report.json` -> 8/8 windows true-host cases observed，6 个 `pass`，2 个设计允许的 `valid_non_success`，0 个 `missing_evidence/system_failure/provider_failure/test_design_failure`。

主线程补充 fresh evidence：

- `python -m pytest -q test/test_ccbd_start_agent_runtime.py test/test_ccbd_start_binding.py test/test_ccbd_start_preparation.py test/test_ccbd_windows_full_chain_smoke.py` -> `71 passed`。
- `python -m pytest -q test/test_rmux_backend_core.py test/test_terminal_runtime_rmux.py test/test_provider_helper_cleanup.py test/test_cli_kill_runtime_processes.py test/test_ccbd_stop_flow_runtime.py test/test_ccbd_windows_full_chain_smoke.py test/test_ccbd_start_agent_runtime.py test/test_ccbd_start_binding.py test/test_ccbd_start_preparation.py test/test_ccbd_sidebar_helper.py test/test_ccbd_namespace_additive_patch.py test/test_v2_project_namespace_state.py` -> `196 passed`。
- PowerShell 5 真机脚本：`powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/ccbd-windows-full-chain-smoke.ps1 -ProjectRoot $env:TEMP/ccb-rmux-full-chain-ps5-v15 -Backend rmux -AskCaseKind fake_provider -Json` -> parser `ok:true`。
- PowerShell 7 真机脚本：`pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/ccbd-windows-full-chain-smoke.ps1 -ProjectRoot $env:TEMP/ccb-rmux-full-chain-pwsh7-v3 -Backend rmux -AskCaseKind fake_provider -Json` -> parser `ok:true`。

## Code Review Gate

- Task agent id: `019f8db6-cd5d-7fb2-ba4b-1d75eaf960ea`
- Verdict: `passed`
- Findings: `none`
- 已复核历史 blocking/important 项：rmux 本地 pane id、mux runtime_ref warm reuse、scope guard fail-closed、`access_token` / `refresh_token` 脱敏。
- 生命周期：审查结果已消费，agent 已关闭。

## Verdict

`PASS`。当前 checkout 的可解析证据满足 owner acceptance：native Windows true-host validation matrix 证明真实 `ccb -> ccbd -> rmux` start/ping/ask/kill 链路，parser fail-closed，scope guard 通过，独立代码审查通过。

## Residual Risks

- `fake_provider` 只证明 ccbd ask 链路和 runtime/backend evidence，不证明真实外部 provider 凭证链路；这是本 goal 明确允许的测试入口约束。
- 本次验收不是完整 rmux backend 架构审计，仍有 packaging/docs、多项目和 validation matrix 后续 item。

## Delivery Record

本验收报告反向引用 final iteration `iterations/004.md`；final iteration 也引用本报告。`state.yaml.current_iteration` 应更新为 `4` 后才能标记 complete。
