---
doc_type: issue-fix
issue: 2026-07-23-windows-rmux-smoke-runtime-fixes
status: confirmed
path: fast-track
fix_date: 2026-07-23
tags:
  - windows
  - rmux
  - ccbd
  - smoke
---

# Windows rmux smoke runtime fixes 修复记录

## 1. 问题描述

`ccbd-windows-full-chain-smoke` 在 native Windows 上要求真实 `ccb -> ccbd -> rmux` 全链路通过，但实测暴露多处 runtime 与证据采集问题：

- project namespace 对 rmux pane 仍按 tmux 字符串调用 pane mutation API，导致 split / respawn / identity 操作不能稳定工作。
- rmux 0.9.0 不支持 `respawn-pane -P`，当前适配层仍发送该 flag。
- Windows sidebar respawn 使用 POSIX env 前缀，rmux pane 中会断开 daemon 连接。
- agent authority 在 rmux namespace pane 复用时仍记录 `runtime_ref=tmux:%pane` / `terminal=tmux`，strict parser 正确拒绝。
- smoke 脚本把保留的 `.ccb/ccbd` 状态目录误判为 endpoint residue，且未从 ping artifact 采集 TCP loopback transport evidence。

## 2. 根因

根因是 Windows rmux native backend 的若干边界仍沿用 tmux / POSIX 假设：

- project namespace backend 暴露的是统一 backend，但部分调用点直接把 pane id 字符串传给 mux backend，缺少 `MuxPaneRef` 包装。
- rmux 0.9.0 CLI 参数面与 tmux 不完全一致，`respawn-pane -P` 属于不兼容参数。
- Windows shell 中不能使用 `NAME=value command` 形式设置 sidebar 环境变量。
- `start_agent_runtime` 没有把 namespace backend impl 传到 agent runtime authority，因此 assigned rmux pane 的 evidence 被旧 provider binding 覆盖成 tmux。
- smoke parser / runner 的 residue 与 artifact label 判定未对齐当前 `ccb ping` / `ccb ps` 的真实输出格式。

## 3. 修复方案

- 在 project namespace runtime backend 增加 pane mutation wrapper，统一把 mux pane id 转成 backend-specific pane ref。
- 对 rmux 0.9.0 去掉 `respawn-pane -P`，保留 cwd respawn 行为。
- 为 Windows sidebar respawn 生成 PowerShell env assignment command；POSIX 路径保持原行为。
- 将 `namespace_backend_impl` 贯穿 start flow、supervisor lifecycle 和 reload mount start，并在 namespace assigned pane 场景写入 `runtime_ref=rmux:%pane`、`terminal_backend=rmux`、`backend_impl=rmux`、`pane_ref={backend_impl,pane_id}`。
- 对 warm reuse restored runtime 保留既有 `workspace_path` authority，避免 Windows `Path('/tmp/ws')` 字符串格式导致无意义 store write。
- 更新 smoke parser / runner：接受 `ccb ps` 的 `binding: runtime=... pane=...` 作为带标签 runtime identity，transport 从 ping/doctor artifact 合并识别，cleanup endpoint 检查真实 endpoint/token 文件而不是要求删除状态目录。

## 4. 改动文件清单

- `lib/ccbd/services/project_namespace_runtime/backend.py`
- `lib/ccbd/services/project_namespace_runtime/ensure_identity.py`
- `lib/ccbd/services/project_namespace_runtime/materialize_topology.py`
- `lib/ccbd/services/project_namespace_runtime/additive_patch_windows.py`
- `lib/ccbd/services/project_namespace_runtime/additive_patch_agents.py`
- `lib/ccbd/services/project_namespace_runtime/move_patch_agents.py`
- `lib/ccbd/services/project_namespace_runtime/sidebar_helper.py`
- `lib/terminal_runtime/rmux_backend.py`
- `lib/terminal_runtime/rmux_backend_runtime/panes.py`
- `lib/ccbd/start_runtime/agent_runtime.py`
- `lib/ccbd/start_flow_runtime/service.py`
- `lib/ccbd/start_flow.py`
- `lib/ccbd/supervisor_runtime/lifecycle.py`
- `lib/ccbd/reload_runtime_mount_start.py`
- `lib/provider_runtime/helper_cleanup.py`
- `scripts/ccbd-windows-full-chain-smoke.ps1`
- `scripts/ccbd_windows_full_chain_smoke.py`
- 相关单测文件。

## 5. 验证结果

- `python -m pytest -q test/test_ccbd_start_agent_runtime.py::test_real_runtime_service_warm_reuse_preserves_restored_without_store_write`：通过。
- `python -m pytest -q test/test_ccbd_start_agent_runtime.py::test_start_agent_runtime_records_rmux_namespace_pane_binding`：通过。
- `python -m pytest -q test/test_ccbd_windows_full_chain_smoke.py`：`30 passed`。
- `python scripts/ccbd_windows_full_chain_smoke.py --scope-guard --diff-base HEAD --json`：`ok: true`，`forbidden_paths=[]`。
- `python -m pytest -q test/test_rmux_backend_core.py test/test_terminal_runtime_rmux.py test/test_provider_helper_cleanup.py test/test_cli_kill_runtime_processes.py test/test_ccbd_stop_flow_runtime.py test/test_ccbd_windows_full_chain_smoke.py test/test_ccbd_start_agent_runtime.py test/test_ccbd_sidebar_helper.py test/test_ccbd_namespace_additive_patch.py test/test_v2_project_namespace_state.py`：`172 passed`。
- Windows PowerShell 5 真机：`powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/ccbd-windows-full-chain-smoke.ps1 -ProjectRoot $env:TEMP/ccb-rmux-full-chain-ps5-v14 -Backend rmux -AskCaseKind fake_provider -Json`：parser `ok: true`，`runner_host.edition=Desktop`，`runner_host.version=5.1.19041.6157`。
- PowerShell 5 pass artifact：`artifacts/ccbd-windows-full-chain-smoke-ps5-pass-20260723-142213/transcript.json`。
- Windows PowerShell 5 独立 parser：`python scripts/ccbd_windows_full_chain_smoke.py --transcript artifacts/ccbd-windows-full-chain-smoke-ps5-pass-20260723-142213/transcript.json --json`：parser `ok: true`。
- PowerShell 7 真机：`pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/ccbd-windows-full-chain-smoke.ps1 -ProjectRoot $env:TEMP/ccb-rmux-full-chain-pwsh7-v2 -Backend rmux -AskCaseKind fake_provider -Json`：parser `ok: true`，`runner_host.edition=Core`，`runner_host.version=7.5.4`。
- PowerShell 7 独立 parser：`python scripts/ccbd_windows_full_chain_smoke.py --transcript artifacts/ccbd-windows-full-chain-smoke/transcript.json --json`：parser `ok: true`。
- 审查补丁后 focused tests：`python -m pytest -q test/test_ccbd_start_agent_runtime.py test/test_ccbd_start_binding.py test/test_ccbd_start_preparation.py test/test_ccbd_windows_full_chain_smoke.py`：`71 passed`。
- 审查补丁后 broader regression：`python -m pytest -q test/test_rmux_backend_core.py test/test_terminal_runtime_rmux.py test/test_provider_helper_cleanup.py test/test_cli_kill_runtime_processes.py test/test_ccbd_stop_flow_runtime.py test/test_ccbd_windows_full_chain_smoke.py test/test_ccbd_start_agent_runtime.py test/test_ccbd_start_binding.py test/test_ccbd_start_preparation.py test/test_ccbd_sidebar_helper.py test/test_ccbd_namespace_additive_patch.py test/test_v2_project_namespace_state.py`：`196 passed`。
- 审查补丁后 scope guard：`python scripts/ccbd_windows_full_chain_smoke.py --scope-guard --diff-base HEAD --json`：parser `ok: true`，`forbidden_paths=[]`。
- 审查补丁后 PowerShell 5 真机：`powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/ccbd-windows-full-chain-smoke.ps1 -ProjectRoot $env:TEMP/ccb-rmux-full-chain-ps5-v15 -Backend rmux -AskCaseKind fake_provider -Json`：parser `ok: true`，artifact `artifacts/ccbd-windows-full-chain-smoke-ps5-pass-20260723-144145/transcript.json`，`runner_host.edition=Desktop`，`runner_host.version=5.1.19041.6157`。
- 审查补丁后 PowerShell 7 真机：`pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/ccbd-windows-full-chain-smoke.ps1 -ProjectRoot $env:TEMP/ccb-rmux-full-chain-pwsh7-v3 -Backend rmux -AskCaseKind fake_provider -Json`：parser `ok: true`，artifact `artifacts/ccbd-windows-full-chain-smoke/transcript.json`，`runner_host.edition=Core`，`runner_host.version=7.5.4`。
- 独立 code review Task agent `019f8db6-cd5d-7fb2-ba4b-1d75eaf960ea`：`verdict=passed`，`findings=none`。
- 独立 functional acceptance Task agent `019f8db6-cde0-7440-8f43-6a01c4992b49`：`verdict=PASS`。

## 6. 遗留事项

本 fix-note 不把 goal 标记为 complete；`cs-goal` 仍需按终端功能验收 gate 启动独立 Task agent，写入 `functional-acceptance.md`，并在 final iteration 中双向引用后才能完成。
