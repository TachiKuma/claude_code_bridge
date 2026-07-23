# Rmux Windows Validation Runbook

本 runbook 用于收集 `rmux-windows-validation-matrix` 的 native Windows 证据。它不替代 CI subset；CI subset 通过只能说明 `selected_cases_status=pass`，不能提升为 `full_matrix_status=pass`。

## 前置条件

- 在 native Windows 执行，不在 WSL、MSYS 或 Linux/macOS 中执行。
- `python`、`ccb.py` 和 `rmux` 可用。
- 使用一次性项目目录；本 runbook 会执行 ask、restart 和 `ccb kill -f`。
- 真实 provider case 使用 operator 自己的凭证；fake provider case 使用 `CCB_TEST_ENTRYPOINT=1`。

## 命令

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\rmux-windows-validation-runbook.ps1" -ProjectRoot "$env:TEMP\ccb-rmux-validation" -AskCaseKind fake_provider -Json
```

可选场景开关：

- `-IncludeRestartReplay`：执行 `ccb restart <agent>` 后检查 `ccb ps`。
- `-IncludeMultiAgent`：在同一项目配置第二个 fake agent，并执行第二个 agent 的 ask。
- `-IncludeMultiProject`：创建第二个项目目录，执行 start / ping / ask / kill，验证项目隔离证据。
- `-IncludeRecovery`：执行 restart 后用 `ccb ping ccbd` 记录恢复证据。

## Transcript Contract

PowerShell runner 写入 `artifacts/rmux-windows-validation/manual-transcript.json`，并把命令 stdout / stderr 写入 `artifacts/rmux-windows-validation/commands/`。

sidecar 必须包含：

- `host_kind=native_windows`
- `control_plane=ccbd`
- `backend_impl=rmux`
- `probe_bypass=false`
- `backend_selection_source` 为 `cli`、`project_config`、`user_config`、`env` 或 `manual_transcript`
- `ccbd_transport=tcp_loopback`
- ccb start、ping、doctor、ask、kill 的命令记录
- endpoint、TCP token ref、Rmux namespace/session、owned process/job residue 的 cleanup evidence
- 已移除 secret 和 user home 的 redaction summary

## 验证

解析 transcript 并生成矩阵报告：

```powershell
python ".\scripts\rmux_windows_validation_matrix.py" --lane windows_true_host --scope full --transcript ".\artifacts\rmux-windows-validation\manual-transcript.json" --json
```

期望输出：

- `artifacts/rmux-windows-validation/rmux_windows_validation_report.json`
- `artifacts/rmux-windows-validation/rmux_windows_validation_rows.jsonl`
- `artifacts/rmux-windows-validation/rmux_windows_validation_summary.md`

## Failure Classes

- `missing_evidence`：缺少必需 transcript row 或 artifact。
- `provider_failure`：provider auth、quota 或 provider CLI 失败；它不能证明 Rmux system failure，也不能作为 full matrix pass。
- `system_failure`：ccb、ccbd、Rmux backend、transport、cleanup 或 runtime 失败。
- `test_design_failure`：transcript schema、probe bypass、防伪字段或 redaction 错误。
- `valid_non_success`：有明确 bounded reason 的 residue 或 degraded recovery。
