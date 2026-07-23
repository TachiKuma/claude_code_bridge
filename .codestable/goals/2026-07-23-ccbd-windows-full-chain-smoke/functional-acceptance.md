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

- PS5 transcript `artifacts/ccbd-windows-full-chain-smoke-ps5-pass-20260723-144145/transcript.json` 解析通过，`ok:true`。
- PS7 transcript `artifacts/ccbd-windows-full-chain-smoke/transcript.json` 解析通过，`ok:true`。
- PS5 `runner_host` 为 `PowerShell Desktop 5.1.19041.6157`。
- PS7 `runner_host` 为 `PowerShell Core 7.5.4`。
- 两份 transcript 均满足 `host_kind=native_windows`、`control_plane=ccbd`、`backend_impl=rmux`、`ccbd_transport=tcp_loopback`、`probe_bypass=false`。
- 核心命令记录齐全：`ccb-start`、`ccb-ping-ccbd`、`ccb-doctor`、`ccb-ask`、`ccb-kill-force`；核心命令通过 `python .../ccb.py --project ...` 进入，不是 direct rmux。
- `fake_provider` 只在 `CCB_TEST_ENTRYPOINT=1` 下放行，runtime/backend evidence 仍显示 `runtime=rmux:%1`、`terminal=rmux`、`namespace_backend_impl=rmux`。
- parser fail-closed 覆盖缺字段、WSL、probe bypass、fake backend、direct rmux、错误 subcommand、unknown scope path 负例。
- cleanup evidence 显示 `endpoint_removed=true`、`token_removed=true`、`rmux_namespace_removed=true`、`session_removed=true`、`owned_process_residue=[]`。

## Functional Evidence

Task agent 独立只读抽查：

- `python scripts/ccbd_windows_full_chain_smoke.py --transcript "artifacts/ccbd-windows-full-chain-smoke-ps5-pass-20260723-144145/transcript.json" --json` -> `ok:true`，`verdict: pass`，`failure_class: none`。
- `python scripts/ccbd_windows_full_chain_smoke.py --transcript "artifacts/ccbd-windows-full-chain-smoke/transcript.json" --json` -> `ok:true`，`verdict: pass`，`failure_class: none`。
- `python scripts/ccbd_windows_full_chain_smoke.py --scope-guard --diff-base HEAD --json` -> `ok:true`，`forbidden_paths: []`。
- `python -m pytest -q -p no:cacheprovider test/test_ccbd_windows_full_chain_smoke.py` -> `31 passed`。

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

`PASS`。当前证据满足 owner acceptance：native Windows PS5/PS7 均有真实 `ccb -> ccbd -> rmux` start/ping/ask/kill transcript，parser fail-closed，scope guard 通过，独立代码审查通过。

## Residual Risks

- `fake_provider` 只证明 ccbd ask 链路和 runtime/backend evidence，不证明真实外部 provider 凭证链路；这是本 goal 明确允许的测试入口约束。
- 本次验收不是完整 rmux backend 架构审计，仍有 packaging/docs、多项目和 validation matrix 后续 item。

## Delivery Record

本验收报告反向引用 final iteration `iterations/004.md`；final iteration 也引用本报告。`state.yaml.current_iteration` 应更新为 `4` 后才能标记 complete。
