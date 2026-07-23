---
doc_type: goal-functional-acceptance
goal: "rmux-windows-validation-matrix"
status: pass
reviewer_id: "019f8eba-ce3f-7da1-8f89-d2ede1db7d28"
final_iteration: "iterations/001.md"
---

# rmux-windows-validation-matrix 功能验收

## Reviewer

- Task agent role：独立 closure reviewer / functional acceptance。
- Task agent id：`019f8eba-ce3f-7da1-8f89-d2ede1db7d28`。
- 上一轮 full-scope reviewer：`019f8eb2-3159-72f3-8cb6-eb2f546bf24a`。
- 关闭结果：消费结果后由主线程关闭；关闭失败只记录 warning。

## Acceptance Checks

- Manifest 覆盖 fake、provider_blackbox、windows_true_host、manual_transcript lane，共 13 cases。
- windows_true_host 防伪字段强制 native Windows、ccbd、rmux、非 probe、backend selection source 可追溯。
- Fake subset 只声明 selected pass，full matrix 在缺真机证据时保持 incomplete。
- Transcript parser 对缺字段、非法 classification、probe bypass、direct rmux 越界 fail closed。
- Provider failure 与 system failure 分离，provider failure 不允许 full pass。
- `valid_non_success` 只允许恢复语义场景。
- PowerShell runbook 与 Markdown runbook 共享 transcript sidecar schema。
- Cleanup evidence 覆盖 endpoint、token、rmux namespace/session、owned process residue。
- Scope guard 禁止 packaging/docs/backend/provider parser 越界。
- Feature checklist、review、QA、acceptance、roadmap item 和 goal iteration 已回写。

## Functional Evidence

- 初次 Task agent `019f8eb2-3159-72f3-8cb6-eb2f546bf24a` 验证了 full scope 行为并发现 `rmux -v` 白名单阻塞。
- 修复后 Task agent `019f8eba-ce3f-7da1-8f89-d2ede1db7d28` 验证：
  - `rmux -V`、`rmux -version`、`rmux --version`、`rmux list-sessions` 允许。
  - `rmux -v`、`rmux kill-session`、`psmux list-sessions`、`psmux -V` 拒绝。
  - 指定测试结果为 `25 passed`。
- 主线程 fresh evidence：
  - manifest validate passed，case count 为 13。
  - fake subset selected pass，full incomplete。
  - scope guard passed，forbidden paths 为空。
  - PowerShell AST parse passed。
  - full scope without transcript 返回 exit `1`，13 个 `missing_evidence`，full incomplete。
- 后验 native Windows true-host full matrix evidence：
  - `artifacts/rmux-windows-validation/rmux_windows_validation_report.json` 生成于 `2026-07-23T12:34:32.799618Z`。
  - `selection_scope=full`，`selected_cases_status=pass`，`full_matrix_status=pass`。
  - 8 个 windows_true_host cases 全部 observed：6 个 `pass`，`restart_replay` 与 `supervision_recovery` 为设计允许的 `valid_non_success`。
  - `missing_evidence=0`，`system_failure=0`，`provider_failure=0`，`failing_case_ids=[]`。

## Verdict

`pass`。

## Delivery Record

本 goal 已交付 Windows Rmux validation matrix、report builder、runbook、manual transcript parser、subset workflow、scope guard、测试和 CodeStable 回写。2026-07-23 已归档 native Windows true-host full runbook/manual transcript report，full matrix 判定为 `pass`。

## Residual Risks

- 当前 full matrix evidence 使用 fake provider 路径覆盖 Rmux/ccbd true-host 系统链路；真实 provider auth/quota 风险仍通过 `provider_failure` 单独分类，不混入 Rmux system failure。

## Final Iteration

本验收对应 final iteration：`iterations/001.md`。
