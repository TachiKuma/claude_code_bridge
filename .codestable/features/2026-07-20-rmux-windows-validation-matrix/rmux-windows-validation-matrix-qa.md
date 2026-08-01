---
doc_type: feature-qa
feature: 2026-07-20-rmux-windows-validation-matrix
status: passed
updated_at: 2026-07-23
---

# rmux-windows-validation-matrix QA

## Scope

QA 覆盖 design/checklist 的核心 DoD：matrix schema、manifest coverage、report builder、fake subset lane、manual transcript parser、provider/system failure classification、direct rmux diagnostic guard、PowerShell runbook parse、GitHub Actions scope guard 和 fail-closed full matrix 行为。

## Commands

- `python -B -m pytest -q "test/test_rmux_windows_validation_matrix.py" "test/test_rmux_windows_validation_scope_guard.py" -p no:cacheprovider`：`25 passed`。
- `python -B "scripts/rmux_windows_validation_matrix.py" --validate-manifest --json`：`ok=true`，`verdict=pass`，`case_count=13`。
- `python -B "scripts/rmux_windows_validation_matrix.py" --lane fake --scope subset --json`：`selected_cases_status=pass`，`full_matrix_status=incomplete`。
- `python -B "scripts/rmux_windows_validation_matrix.py" --scope-guard --diff-base HEAD --json`：`ok=true`，`forbidden_paths=[]`。
- PowerShell AST parse for `scripts/rmux-windows-validation-runbook.ps1`：passed。
- `python -B "scripts/rmux_windows_validation_matrix.py" --scope full --json --output-dir "$env:TEMP/rmux-validation-final-full-missing"`：exit `1`，`selected_cases_status=incomplete`，`full_matrix_status=incomplete`，13 个 `missing_evidence`。
- 后验 native Windows true-host full report `artifacts/rmux-windows-validation/rmux_windows_validation_report.json`：生成于 `2026-07-23T12:34:32.799618Z`，`selection_scope=full`，8/8 cases observed，`selected_cases_status=pass`，`full_matrix_status=pass`。

## Coverage

- Manifest 覆盖 start/ping、ask、kill、restart、multi-agent、multi-project、supervision recovery 和 diagnostics。
- `windows_true_host` 强制 `host_kind=native_windows`、`control_plane=ccbd`、`backend_impl=rmux`、`probe_bypass=false`，且 `backend_selection_source` 不得为 `unknown`。
- fake lane、provider_blackbox、windows_true_host、manual_transcript 分层隔离；fake subset 不提升为 full pass。
- transcript row `observed=true` 但缺失或非法 classification 时进入 `test_design_failure`。
- `provider_failure` 优先于 system command failure，且 full scope 不允许 provider failure pass。
- `valid_non_success` 仅允许 `kill`、`restart_replay`、`supervision_recovery` 这类恢复语义场景满足 full core。
- direct rmux guard 只允许命名诊断中的 `rmux -V/-version/--version` 和 `rmux list-sessions`；`rmux -v`、`psmux` 和其他直接 rmux 命令被拒绝。
- PowerShell runbook 使用 shared transcript schema；runbook parser 调用 `--lane windows_true_host --scope full`，不把全 manifest 缺证据混入解析结果。
- cleanup/residue evidence 覆盖 ccbd endpoint、TCP token、rmux session/namespace 与 owned process residue，不硬编码 endpoint success。
- workflow scope guard 覆盖 PR base diff 和删除类变更，禁止 packaging/docs/backend/provider parser 越界。

## Residual Risks

- 2026-07-23 已补充 native Windows true-host full matrix evidence；其中 `restart_replay` 与 `supervision_recovery` 为设计允许的 `valid_non_success`。
- 当前 full matrix evidence 使用 fake provider 路径覆盖 Rmux/ccbd true-host 系统链路；真实 provider auth/quota 风险仍由 `provider_failure` 分类隔离。
- full matrix 在没有真实 transcript 时保持 incomplete，这是设计要求的 fail-closed 行为。

## Verdict

`passed`。
