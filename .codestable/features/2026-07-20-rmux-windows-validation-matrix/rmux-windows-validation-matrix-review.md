---
doc_type: feature-review
feature: 2026-07-20-rmux-windows-validation-matrix
status: passed
reviewer_id: 019f8eba-ce3f-7da1-8f89-d2ede1db7d28
updated_at: 2026-07-23
---

# rmux-windows-validation-matrix 代码审查

## Scope

审查当前 working tree 中 `rmux-windows-validation-matrix` 的实现与验证资产，范围包括矩阵 manifest、report builder、manual transcript parser、PowerShell runbook、Markdown runbook、GitHub Actions subset workflow、scope guard 和新增测试。

## 初次审查结论

只读 Task agent `019f8eb2-3159-72f3-8cb6-eb2f546bf24a` 返回 `review_verdict: fail`，发现两个收口阻塞：

- `scripts/rmux_windows_validation_matrix.py` 的 direct rmux diagnostic guard 对参数执行 lowercase 后比较，导致 `preflight-rmux-version` 误允许 `rmux -v`。
- feature checklist、goal state 和 roadmap item 尚未回写，阻塞 CodeStable 完成判定。

审查同时确认以下实现方向正确：

- Manifest 覆盖 `fake`、`provider_blackbox`、`windows_true_host`、`manual_transcript` 四个 lane，共 13 个 cases。
- fake subset 只让 `selected_cases_status=pass`，`full_matrix_status=incomplete`。
- 无 transcript 的 full scope 返回非零，所有 case 为 `missing_evidence`，`full_matrix_status=incomplete`。
- transcript fail-closed、provider_failure 优先级、`valid_non_success` 恢复类限定均有测试覆盖。

## 修复与复核

本轮修复：

- direct rmux diagnostic guard 保留 argv 参数大小写，只允许命名诊断中的 `rmux -V`、`rmux -version`、`rmux --version` 和 `rmux list-sessions`。
- 新增 `test_named_direct_rmux_diagnostics_do_not_allow_lowercase_short_version`，证明 `rmux -v` 被拒绝。
- 回写 feature checklist、roadmap item、roadmap goal-state 和 goal state。

窄范围只读 Task agent `019f8eba-ce3f-7da1-8f89-d2ede1db7d28` 返回：

- `review_verdict: pass`
- `functional_acceptance_verdict: pass`
- 阻塞问题：none

复核证据：

- `rmux -V`、`rmux -version`、`rmux --version`、`rmux list-sessions` 为允许。
- `rmux -v`、`rmux kill-session`、`psmux list-sessions`、`psmux -V` 为拒绝。
- `python -B -m pytest -q test/test_rmux_windows_validation_matrix.py test/test_rmux_windows_validation_scope_guard.py -p no:cacheprovider`：`25 passed`。
- 后验 native Windows true-host full report `artifacts/rmux-windows-validation/rmux_windows_validation_report.json`：生成于 `2026-07-23T12:34:32.799618Z`，`full_matrix_status=pass`，8/8 cases observed，6 个 `pass`、2 个 `valid_non_success`。

## Residual Risks

- 2026-07-23 已补充 native Windows true-host full matrix evidence；当前审查结论和后验 evidence 一致。
- 当前 full matrix evidence 使用 fake provider 路径覆盖 Rmux/ccbd true-host 系统链路；真实 provider auth/quota 风险仍由 `provider_failure` 分类隔离。

## Verdict

`passed`。无 unresolved blocking findings。
