---
doc_type: feature-qa
feature: 2026-07-20-rmux-packaging-docs-contracts
status: passed
updated_at: 2026-07-25
---

# rmux-packaging-docs-contracts QA

## Scope

QA 覆盖 design/checklist 的核心 DoD：support projection classifier、validation fail-closed、doctor/diagnostics rmux 字段、`install.ps1` rmux check 行为、Windows npm gate no-change rationale、README/docs consistency、troubleshooting、release guard、YAML 合法性和 npm pack dry run。

## Commands

- `python -m pytest -q "test/test_rmux_packaging_docs_contracts.py" "test/test_doctor_rmux_packaging_summary.py" "test/test_install_windows_rmux_contract.py" "test/test_windows_bootstrap_script.py" "test/test_ccbd_diagnostics_bundle_rmux.py" "test/test_cli_doctor_rmux_packaging.py" "test/test_rmux_packaging_release_guard.py" "test/test_rmux_docs_consistency_gate.py"`：`21 passed`。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-checklist.yaml" --yaml-only`：passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`：passed。
- PowerShell AST parse for `install.ps1`：passed。
- `npm run pack:check`：passed，dry-run tarball `seemseam-ccb-8.2.1.tgz`，未发布。
- `git diff --check`：只有换行符转换 warning，无 whitespace error。

## Coverage

- Support projection owner/classifier 覆盖 `blocked`、`experimental`、`beta`、`supported`，缺证据 fail closed。
- 当前 packaged projection 输出 `beta`，因为 full matrix pass 之外仍缺 local install smoke 与 package gate。
- `install.ps1` 暴露 `-RmuxCheck detect_only|warn|fail_fast`，默认不自动下载 rmux。
- Windows npm 未启用；`package.json.os` 保持 Linux/macOS，README/docs 说明 native Windows Rmux 使用 `install.ps1` / source beta opt-in。
- doctor/diagnostics bundle 输出 rmux support/version/capability/validation/install entry/fallback 字段。
- docs consistency gate 覆盖 support tier wording、install entry mapping、release note future promise 和 troubleshooting。
- release guard 覆盖 no push/tag/npm publish/release upload。

## Residual Risks

- 本 feature 不执行真实发布、不上传 artifact、不启用 Windows npm；Windows npm 后续启用仍需要独立 package gate 和 owner 授权。
- 当前 `supported` gate 未满足 local install smoke 和 package gate，因此交付状态保持 `beta` 是预期行为。

## Verdict

`passed`。
