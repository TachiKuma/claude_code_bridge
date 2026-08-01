---
doc_type: issue-fix-note
issue: mux-backend-contract-herdr-v2
status: fixed
root_cause_type: contract-fail-open
tags:
  - terminal-runtime
  - herdr
  - resolver
  - contract
---

# mux backend contract Herdr V2 修复记录

## 根因

review 指出的三个核心问题都属于 contract / resolver 层的 fail-open：

1. `capability_statuses_supported()` 只看值是否全为 `supported`，没有拒绝空 `command_status` / `semantic_status`，导致空证据也能走成功路径。
2. `resolve_mux_backend_v2()` 把平台身份和 gate 准入混在一起，`win32/x64` 身份命中后会提前进入 Herdr 分支，但又没有把 `python_bitness` 和 `is_wsl` 纳入准入判断。
3. `make_namespace_ref()` 对 `backend_impl="herdr"` 没有做运行时 IPC 约束，`ipc_kind="none"` 也能构造成功 ref。

## 改动

- `lib/terminal_runtime/mux_backend_contract.py`
  - 给 Herdr namespace ref 增加最小运行时校验，拒绝 `ipc_kind="none"` 和空 `ipc_ref`。
  - 让 capability 判定显式拒绝空 mapping，并继续保持 tmux/rmux 兼容。
- `lib/terminal_runtime/backend_resolver.py`
  - 将 Native Windows x64 身份判断和 gate 准入拆开。
  - Herdr auto 路径现在要求 `supported=True`、`python_bitness="64bit"`、`is_wsl=False`，否则返回 `platform-gate-blocked`。
  - Herdr 成功路由要求完整基础 capability 集合、`backend_impl="herdr"`、可追溯 evidence ref。
  - 畸形 blocked report 统一收敛为结构化失败，不再抛裸异常。
- `test/test_mux_backend_contract.py`
  - 补了 Herdr IPC 约束和空 capability fail-closed 回归。
- `test/test_terminal_runtime_backend_selection.py`
  - 补了缺失 capability、错误 backend_impl、缺失 required key、Windows gate 不满足、畸形 blocked report 的回归。
- `.codestable/features/2026-07-31-mux-backend-contract-herdr-v2/evidence/herdr-capability-blocked-fixture.json`
  - 补齐 `is_wsl` / `platform_gate_ref`，和 spike 证据保持一致。
- `.codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-evidence-pack.md`
  - 将 residual risks 从 `none` 改成真实状态，说明 archguard/meta_cc 仍是跳过采集。

## 验证

- `python -m pytest -q test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py test/test_herdr_spike_no_production_route.py test/test_v2_project_namespace_backend.py`
- 结果：`39 passed`
- `git diff --check`：通过

## 遗留风险

- 这次只修 contract / resolver / test / feature evidence，不引入生产 Herdr client 或路由接入。
- archguard / meta_cc provider signals 仍然是 skipped，evidence pack 只能反映本地 gate 和聚焦测试。
