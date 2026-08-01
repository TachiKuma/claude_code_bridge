---
doc_type: feature-qa
feature: 2026-07-20-rmux-supervision-recovery
status: passed
updated_at: 2026-07-23
---

# rmux-supervision-recovery QA

## Scope

QA 覆盖 design / checklist 的 DoD 命令、独立 review 修复点、diagnostics projection 和 scope guard。真实 destructive Windows/Rmux kill smoke 未在当前项目运行；本 feature 的恢复语义由 fake evidence 单元/集成 smoke 覆盖，真机 destructive smoke 作为 `rmux-windows-validation-matrix` 后续证据。

## Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-rmux-supervision-recovery/rmux-supervision-recovery-checklist.yaml" --yaml-only`：passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`：passed。
- `python -m pytest -q "test/test_ccbd_supervision.py" "test/test_ccbd_supervision_recovery.py" "test/test_ccbd_rmux_supervision_evidence.py" "test/test_ccbd_rmux_supervision_recovery.py" "test/test_ccbd_rmux_daemon_supervision.py" "test/test_ccbd_supervision_diagnostics.py" "test/test_ccbd_project_view.py" "test/test_cli_doctor_supervision.py" "test/test_cli_ping_supervision.py" "test/test_ccbd_diagnostics_bundle_supervision.py" "test/test_ccbd_rmux_supervision_guard.py"`：`137 passed`。
- `python -m pytest -q "test/test_v2_ccbd_supervision_loop.py" "test/test_v2_ccbd_ping_runtime.py" "test/test_v2_diagnostics_bundle.py" "test/test_v2_tmux_cleanup_history.py"`：`63 passed`。
- `python -m pytest -q "test/test_v2_diagnostics_bundle.py" "test/test_ccbd_diagnostics_bundle_supervision.py"`：`10 passed` after diagnostics ledger summary action projection.

## Coverage

- Evidence ledger 分离 pane、process/job、namespace、daemon health。
- Rmux backend-local pane id 不要求 `%N`。
- Process/job death 与 pane death 分开建模；pane alive + process dead 不判 healthy。
- Namespace missing/crashed/foreign 使用 backend-neutral namespace evidence 进入 reflow 或 hard diagnostics。
- Shared / unowned daemon crash 只写 `daemon_degraded` + `degraded_only` evidence，不 refresh、不 restart、不误杀。
- Project / owned daemon generation mismatch 走 recover path 并记录 `daemon_recover`。
- `SupervisionEvent`、project view、ping、doctor 和 diagnostics bundle 展示 ledger；bundle generated summary 直接包含 action/reason/ownership。
- Scope guard 覆盖 provider parser、backend resolver、namespace lifecycle、process liveness implementation 和 validation matrix scope。

## Residual Risks

- `rmux.exe` 在本机可发现，但当前 QA 未执行真实 kill pane/provider/daemon。该动作会影响运行时资源，应由后续 validation matrix 在 disposable true-host 场景中执行。

## Verdict

`passed`。
