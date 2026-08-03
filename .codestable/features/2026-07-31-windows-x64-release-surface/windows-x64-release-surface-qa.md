---
doc_type: feature-qa
feature: 2026-07-31-windows-x64-release-surface
status: passed
runner_state: completed
runner_reason: "QA runner reported blocked on incomplete CMD-008/live doctor evidence; main QA added isolated doctor/doctor --output transcript and kept destructive install/cleanup as blocked evidence. Runner result consumed and closed."
runner_id: "019fc65b-e0a5-7641-9385-520f3758b6e5"
tested: 2026-08-03
round: 1
---

# windows-x64-release-surface QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml`
- Review: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-review.md`
- Evidence pack: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-gate-results.json`
- DoD results: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-dod-results.json`
- Diff basis: 当前工作区 feature diff；staged diff 为空。
- Baseline dirty files: `.codestable/gates/roadmap-goal-gates.yaml`、`.codestable/reference/agent-conventions.md`、`笔记.md` 为本轮外 baseline，不纳入 QA verdict。
- Feature type: mixed。
- Core evidence gate: npm/install/update/doctor/docs projection 与 fail-closed route 必须有运行证据；真实 install/uninstall/PATH/skills cleanup 因高风险只接受 design 允许的 blocked evidence，不得宣称 release route 或 final supported。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | CMD-003 / AC-001..003 | core-functional | projection schema、host gate、npm route、all bin mapping | unit | `python -m pytest -q test/test_windows_x64_release_surface.py` | 通过 | pass |
| QA-002 | CMD-004 / AC-004..006 | core-functional | doctor/install/update wiring | unit/integration | `python -m pytest -q test/test_cli_doctor_windows_x64_release_surface.py test/test_windows_bootstrap_script.py test/test_cli_management_update.py -k "windows or release_surface or install or update or doctor"` | 通过 | pass |
| QA-003 | CMD-005 / AC-007 | supporting | Rmux / non-Windows regression | regression | `python -m pytest -q test/test_cli_doctor_rmux_packaging.py test/test_install_windows_rmux_contract.py test/test_rmux_packaging_docs_contracts.py` | 通过 | pass |
| QA-004 | CMD-009/010/012 | core-functional | dependency/baseline admission 与 Windows rollback | unit | `python -m pytest -q test/test_windows_x64_release_surface_dependency_admission.py test/test_windows_x64_release_surface_baseline_version.py test/test_windows_x64_release_surface_update_rollback.py` | 通过 | pass |
| QA-005 | CMD-006 | core evidence | projection JSON 进入 npm payload | package dry-run | npm pack wrapper | projection JSON present | pass |
| QA-006 | CMD-007 / AC-008 | core evidence | 无 publish/push/tag/support/completion 越界 | static guard | scope guard | 无命中 | pass |
| QA-007 | CMD-013 / AC-006 | supporting | `doctor --bundle` 只在 deprecated/unsupported 语境 | static guard | docs guard | 通过 | pass |
| QA-008 | review QA focus / CMD-008 | core-functional | Native Windows diagnostic transcript | CLI/manual | `cmd-008-native-windows-release-surface-diagnostic-transcript.md` | 同一 projection；release route blocked | pass as blocked evidence |
| QA-009 | review residual / CMD-011 | core evidence | cleanup / rollback | unit/manual | `cmd-011-windows-cleanup-rollback-blocked-evidence.md` + CMD-012 | blocked evidence + fake rollback | pass as blocked evidence |
| QA-010 | cleanliness | supporting | whitespace / out-of-scope | static | `git diff --check ...` | 无 whitespace error | pass |

## 3. Command Results

- `python -m pytest -q test/test_windows_x64_release_surface.py` -> exit 0：21 passed。
- `python -m pytest -q test/test_cli_doctor_windows_x64_release_surface.py test/test_windows_bootstrap_script.py test/test_cli_management_update.py -k "windows or release_surface or install or update or doctor"` -> exit 0：64 passed。
- `python -m pytest -q test/test_cli_doctor_rmux_packaging.py test/test_install_windows_rmux_contract.py test/test_rmux_packaging_docs_contracts.py` -> exit 0：5 passed。
- `python -m pytest -q test/test_windows_x64_release_surface_dependency_admission.py test/test_windows_x64_release_surface_baseline_version.py test/test_windows_x64_release_surface_update_rollback.py` -> exit 0：7 passed。
- npm pack payload wrapper -> exit 0：`projection JSON present`。
- scope guard CMD-007 -> exit 0：`scope guard pass`。
- docs guard CMD-013 -> exit 0：`doctor docs guard pass`。
- Node code-level npm route smoke -> exit 0：blocked diagnostic，`release_install_entry=diagnostic_only`。
- PowerShell `Show-WindowsX64ReleaseSurfaceProjection` non-destructive smoke -> exit 0：blocked diagnostic，`source_install_allowed=True`。
- Windows update diagnostic-only smoke -> exit 0，业务返回码预期为 1：`failure_reason=release-artifact-missing`。
- `ccb.py doctor` in isolated temp project -> exit 0：输出 `windows_x64_release_surface` rows。
- `ccb.py doctor --output` in isolated temp project -> exit 0：gzip bundle 内含 `windows_x64_release_surface` payload。
- `git diff --check` scoped feature files -> exit 0：无 whitespace error；仅 CRLF warning。

## 4. Scenario Results

- [x] QA-001 projection / host gate / schema / npm route：pass。
  - Evidence: 21 focused tests cover strict schema, available invariants, host gate fail-closed, package metadata, npm route, all bin mapping.
- [x] QA-002 doctor/install/update wiring：pass。
  - Evidence: 64 tests cover doctor payload/render, Windows bootstrap script and update diagnostics.
- [x] QA-003 Rmux / non-Windows regression：pass。
  - Evidence: 5 regression tests passed.
- [x] QA-004 dependency/baseline/update rollback：pass。
  - Evidence: 7 tests passed, including checksum mismatch and no Unix installer on Windows branch.
- [x] QA-008 Native Windows diagnostic transcript：pass as blocked evidence.
  - Evidence: CMD-008 transcript shows npm/update/doctor/install.ps1 projection consume the same blocked projection.
- [x] QA-009 cleanup / rollback evidence：pass as blocked evidence.
  - Evidence: CMD-011 blocked evidence plus fake rollback tests; no real uninstall/PATH/skills cleanup.

## 5. Findings

### failed

- none

### blocked

- none for this QA gate. CMD-008/CMD-011 are blocked evidence by design and remain non-support claims, not implementation failure.

### residual-risk

- CMD-008 did not execute real `install.ps1 install`; it records non-destructive projection diagnostics and source/dev preservation tests. Acceptance must not treat it as a real source install transcript.
- CMD-011 did not execute real `install.ps1 uninstall`、PATH cleanup 或 skills cleanup；acceptance must keep it as blocked evidence.
- OCR scoped rerun did not complete; review already records this as residual risk.
- Current projection remains blocked/default with `failure_reason=release-artifact-missing`; no release route or final supported claim is allowed.

## 6. Cleanliness

- Debug output: pass.
- Temporary TODO/FIXME/XXX: pass by scope guard and focused review.
- Commented-out code: pass by review/QA spot checks.
- Unused imports / dead code from this feature: pass by tests and review closure.
- Out-of-scope files: pass for feature verdict; unrelated dirty baseline files are documented and excluded.

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段。Acceptance 必须消费 `approval-report.md#goal-acceptance`，并确认 CMD-008/CMD-011 仍是 blocked/diagnostic evidence，不能升级为 real install/uninstall transcript 或 Windows x64 final support。
