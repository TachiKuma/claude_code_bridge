---
doc_type: goal
goal: rmux-windows-validation-matrix
status: complete
---

# rmux-windows-validation-matrix

## Objective

继续 `windows-rmux-native-backend` epic 中的 `rmux-windows-validation-matrix`，建立 Windows Rmux 自动化与真机验证矩阵、证据 schema、报告聚合和可重复 runbook，覆盖多 agent、ask、kill、restart、多项目，并推进到功能验收完成。

## Starting Point

- `rmux-supervision-recovery` 已完成并验收通过。
- `.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-design.md` 为 `approved`。
- `.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-design-review.md` 为 `passed`。
- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 中该 item 为 `in-progress`。
- checklist 的 implementation steps/checks 仍为 `pending`。

## Acceptance Criteria

- matrix manifest 覆盖 start/ping/ask/kill/restart/multi-agent/multi-project/recovery/diagnostics 核心 cases，且 `windows_true_host` 强制 true-host 防伪字段。
- report builder 输出 JSON、JSONL、markdown summary，fake/provider/windows/manual evidence 分类不混淆，缺证据 fail closed。
- PowerShell runbook 与 markdown runbook 共享 transcript sidecar schema，manual transcript 可解析、可脱敏并回填 report。
- subset CI / fake lane 只能断言 `selected_cases_status`，不得冒充 `full_matrix_status`；`provider_failure` 与 `system_failure` 分离。
- Windows cleanup/residue evidence 覆盖 ccbd endpoint、TCP token ref、Rmux namespace/session、owned process/job。
- scope guard 禁止 packaging/docs contract、backend implementation、provider parser 越界；feature checklist、QA、acceptance、roadmap item 与 goal iteration 回写完成。
- 独立 Task agent code review passed，独立 Task agent 功能验收 passed。

## Non-Goals

- 不实现或修改 Rmux backend、supervision/recovery、Windows TCP transport 或 provider completion parser。
- 不把 WSL、probe、fake lane 或 capability report 作为 native Windows true-host pass。
- 不要求默认 CI 拥有真实 provider secrets。
- 不更新 installer、npm os、README、用户手册、release contract 或 packaging/docs supported 收口。
- 不执行 git commit、git push、merge、release、deploy 或生产变更。

## Decisions And Assumptions

- 复用已批准 feature design/checklist/design-review 作为 implementation contract。
- 缺少真机 Windows transcript 时实现必须 fail closed，并把 full matrix status 与 selected subset status 分离。
- 默认 CI 只覆盖 deterministic subset；true-host full evidence 通过 PowerShell runbook/manual transcript lane 记录，真实 provider auth/quota 风险单独归入 `provider_failure`。

## Current State

Goal 已完成。最终 iteration 见 `iterations/001.md`，功能验收见 `functional-acceptance.md`。2026-07-23 native Windows true-host full matrix report 已归档：`full_matrix_status=pass`，8/8 cases observed，6 个 `pass`、2 个允许的 `valid_non_success`。

## Next Action

full pass 证据已归档；后续仅在刷新 Windows full-matrix evidence 时重跑 PowerShell runbook，并通过 manual transcript lane 回填报告。
