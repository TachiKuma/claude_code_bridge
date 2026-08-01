---
doc_type: feature-qa
feature: 2026-07-20-ccbd-windows-full-chain-smoke
roadmap: windows-rmux-native-backend
roadmap_item: ccbd-windows-full-chain-smoke
status: passed
updated_at: "2026-07-25"
---

# ccbd-windows-full-chain-smoke QA

## Scope

QA 覆盖 full-chain smoke checklist 的核心 DoD：transcript schema/parser、PowerShell runner、dependency preflight、start/ping/doctor evidence、ask evidence、kill cleanup evidence、probe/direct-rmux/WSL/fake-backend 负例、scope guard 与 native Windows true-host evidence。

## Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-checklist.yaml" --yaml-only`：passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`：passed。
- `python -m pytest -q test/test_ccbd_windows_full_chain_smoke.py`：历史 goal evidence 为 `31 passed`；本次 strict closeout fresh run 继续覆盖该测试。
- `python "scripts/rmux_windows_validation_matrix.py" --lane windows_true_host --scope full --transcript "artifacts/rmux-windows-validation/manual-transcript.json" --output-dir "$env:TEMP/rmux-validation-strict-closeout" --json`：fresh 输出 `selected_cases_status=pass`、`full_matrix_status=pass`。
- `python "scripts/rmux_windows_validation_matrix.py" --validate-manifest --json`：manifest validate pass。

## Coverage

- true-host evidence 强制 `host_kind=native_windows`、`control_plane=ccbd`、`backend_impl=rmux`、`probe_bypass=false`、`ccbd_transport=tcp_loopback`。
- 核心命令记录齐全：`ccb-start`、`ccb-ping-ccbd`、`ccb-doctor`、`ccb-ask`、`ccb-kill-force`，核心路径通过 `ccb.py --project ...` 进入，不是 direct rmux probe。
- cleanup evidence 显示 endpoint、TCP token、rmux namespace/session 和 owned process residue 清理。
- validation matrix 覆盖 start/ping、ask、kill、restart、multi-agent、multi-project、supervision recovery 和 diagnostics；其中 restart / recovery 的 `valid_non_success` 属设计允许的恢复语义分类。
- full-chain 原 parser 对历史 PS5 / PS7 transcript path 的 pass 只作为历史记录；当前 checkout 不再引用这些缺失路径作为 QA pass 依据。

## Residual Risks

- 当前 true-host evidence 使用 `fake_provider` 证明 backend/control-plane/ask 系统链路；真实 provider auth/quota 风险不归类为 Rmux system failure。
- `rmux-packaging-docs-contracts` 后续已将 Windows npm 支持档明确为 `beta`，不是本 feature QA 的阻塞项。

## Verdict

`passed`。
