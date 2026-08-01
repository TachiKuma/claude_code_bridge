---
doc_type: feature-acceptance
feature: 2026-07-20-rmux-windows-validation-matrix
status: passed
updated_at: 2026-07-23
---

# rmux-windows-validation-matrix 验收

## Acceptance Checks

- Matrix manifest 已覆盖 `fake`、`provider_blackbox`、`windows_true_host`、`manual_transcript` 四个 lane 和 13 个核心 cases。
- `windows_true_host` case 强制 native Windows、ccbd control plane、rmux backend、非 probe 旁路，并要求 backend selection source 可追溯。
- Report builder 输出 JSON、JSONL 和 Markdown summary；row classification 覆盖 pass、missing_evidence、provider_failure、system_failure、test_design_failure、valid_non_success。
- fake subset report 只声明 selected cases pass，不冒充 full matrix pass。
- manual transcript parser 可解析、脱敏、回填 rows；缺字段和非法 classification fail closed。
- Provider failure 与 system failure 分离；真实 provider ask 失败不会误算为 Rmux system failure。
- PowerShell runbook 与 Markdown runbook 共享 transcript sidecar schema。
- Cleanup/residue evidence 覆盖 ccbd endpoint、TCP token ref、rmux namespace/session、owned process/job residue。
- Scope guard 禁止 packaging/docs contract、backend implementation、provider parser 越界。
- Feature checklist、review、QA、acceptance、roadmap item 与 goal iteration 均已回写。

## Task Agent Evidence

- 初次独立 review / functional pass 前检查：Task agent `019f8eb2-3159-72f3-8cb6-eb2f546bf24a` 返回 `review_verdict: fail`、`functional_acceptance_verdict: inconclusive`，指出 `rmux -v` 误放行和状态回写未完成。
- 窄范围 closure review / functional acceptance：Task agent `019f8eba-ce3f-7da1-8f89-d2ede1db7d28` 返回 `review_verdict: pass`、`functional_acceptance_verdict: pass`，阻塞问题 `none`。

## Functional Evidence

- `25 passed` for the dedicated matrix and scope guard tests。
- Manifest validate `ok=true`，case count 为 13。
- Fake subset report `selected_cases_status=pass` 且 `full_matrix_status=incomplete`。
- Full scope without transcript returns exit `1` and 13 个 `missing_evidence` rows。
- PowerShell runbook AST parse passed。
- Scope guard report `ok=true`，`forbidden_paths=[]`。
- Native Windows true-host full matrix report：`artifacts/rmux-windows-validation/rmux_windows_validation_report.json` 生成于 `2026-07-23T12:34:32.799618Z`，`selection_scope=full`，`selected_cases_status=pass`，`full_matrix_status=pass`，8/8 cases observed，分类计数为 6 个 `pass`、2 个 `valid_non_success`、0 个 `missing_evidence/system_failure/provider_failure`。

## Roadmap Writeback

- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 中 `rmux-windows-validation-matrix` 已从 `in-progress` 更新为 `done`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml` 中 `rmux-windows-validation-matrix` 已更新为 `accepted`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-features/rmux-windows-validation-matrix.md` 已更新为 `accepted`。

## Delivery Record

已交付 Windows Rmux validation matrix、report builder、fake subset runner、manual transcript parser、PowerShell runbook、Markdown runbook、GitHub Actions subset workflow、scope guard、测试与 CodeStable 回写。2026-07-23 已归档 native Windows true-host full report；矩阵在缺少该证据时仍 fail closed，而不会将 fake subset 伪装为 full pass。

## Residual Risks

- 当前 full matrix evidence 使用 fake provider 路径覆盖 Rmux/ccbd true-host 系统链路；真实 provider blackbox auth/quota 类风险由 `provider_failure` 分类隔离。

## Verdict

`passed`。本 feature 可视为 accepted。
