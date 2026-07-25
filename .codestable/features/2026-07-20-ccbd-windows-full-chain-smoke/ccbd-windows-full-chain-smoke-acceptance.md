---
doc_type: feature-acceptance
feature: 2026-07-20-ccbd-windows-full-chain-smoke
roadmap: windows-rmux-native-backend
roadmap_item: ccbd-windows-full-chain-smoke
status: passed
updated_at: "2026-07-25"
---

# ccbd-windows-full-chain-smoke 验收

## Acceptance Checks

- native Windows true-host evidence 证明 `ccb -> ccbd -> rmux` start / ping / doctor / ask / kill 走真实 ccbd control plane。
- evidence 明确 `backend_impl=rmux`、`control_plane=ccbd`、`ccbd_transport=tcp_loopback`、`probe_bypass=false`。
- `ccb ask` 通过 `CCB_TEST_ENTRYPOINT=1` 的 fake provider 覆盖系统链路，未声称真实 provider 凭证链路通过。
- cleanup evidence 覆盖 ccbd endpoint、TCP token、rmux namespace/session 与 owned process residue。
- parser / matrix 对缺字段、probe bypass、direct rmux、WSL/fake backend 与缺证据 fail closed。
- feature checklist、review、QA、acceptance、roadmap item 与 goal-state 均完成回写。

## Task Agent Evidence

- goal code review Task agent `019f8db6-cd5d-7fb2-ba4b-1d75eaf960ea`：`passed`，无 unresolved findings。
- goal functional acceptance Task agent `019f8db6-cde0-7440-8f43-6a01c4992b49`：历史验收为 `PASS`。
- 本次 strict closeout 不复用缺失的 PS5 / PS7 transcript 路径作为 pass 依据；它以当前存在且可 fresh 解析的 validation matrix 证据完成报告收口。

## Functional Evidence

- `artifacts/rmux-windows-validation/manual-transcript.json` 存在，记录 native Windows `ccb.py --project ...` start / ping / doctor / ask / kill 命令。
- `artifacts/rmux-windows-validation/rmux_windows_validation_report.json` 生成于 `2026-07-23T12:34:32.799618Z`，`selection_scope=full`、`selected_cases_status=pass`、`full_matrix_status=pass`。
- validation matrix 8 个 windows true-host cases 全部 observed：6 个 `pass`，`restart_replay` 与 `supervision_recovery` 为设计允许的 `valid_non_success`；`missing_evidence=0`、`system_failure=0`、`provider_failure=0`。
- strict closeout fresh command：`python "scripts/rmux_windows_validation_matrix.py" --lane windows_true_host --scope full --transcript "artifacts/rmux-windows-validation/manual-transcript.json" --output-dir "$env:TEMP/rmux-validation-strict-closeout" --json` -> `full_matrix_status=pass`。

## Roadmap Writeback

- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 中本 item 为 `done`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml` 中本 feature 已回写为 `accepted`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-features/ccbd-windows-full-chain-smoke.md` 已回写为 `accepted`。
- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md` 中本 item 已回写为 `accepted`。

## Delivery Record

已交付 full-chain smoke parser、PowerShell runner、scope guard、负例测试、redaction、rmux local pane id / mux runtime ref 修复证据，以及 native Windows true-host validation matrix 证据。本文件补齐 feature acceptance 缺口。

## Residual Risks

- 历史 goal 报告提到的 PS5 / PS7 transcript artifact 在当前 checkout 不存在；本次收口将其降为历史引用，不作为当前 pass 的机械证据。
- 真实 provider 凭证链路、Windows npm supported 发布和 UX parity 属后续边界。

## Verdict

`passed`。本 feature 可视为 accepted。
