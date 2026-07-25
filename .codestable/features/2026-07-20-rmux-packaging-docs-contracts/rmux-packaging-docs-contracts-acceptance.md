---
doc_type: feature-acceptance
feature: 2026-07-20-rmux-packaging-docs-contracts
status: passed
updated_at: 2026-07-25
---

# rmux-packaging-docs-contracts 验收

## Acceptance Checks

- Support projection 已由 `lib/terminal_runtime/rmux_packaging_support.py` 单一 owner 产出，并消费 route approval、capability、validation matrix、local install smoke、package gate 和 docs consistency evidence。
- `support_tier` 枚举为 `blocked`、`experimental`、`beta`、`supported`；当前 packaged projection 与 evidence pack 均为 `beta`。
- `supported` 只在 full validation、true-host rows、docs consistency 和 local install smoke 同时满足时可达；当前缺 local install smoke 与 package gate，因此保持 `beta`。
- `install.ps1` 暴露 `-RmuxCheck detect_only|warn|fail_fast`，默认 `warn`，只探测/提示 rmux，不自动下载或安装 rmux。
- Windows npm 未启用；`package.json.os` 不含 `win32`，README、runbook 和 support contract 均说明 native Windows Rmux 走 `install.ps1` / source beta opt-in。
- doctor / diagnostics bundle 输出 rmux support、version、capability、validation、install entry、npm enabled、installer check 和 fallback 字段。
- troubleshooting 覆盖 route approval、capability gap、rmux missing、provider auth failure、validation incomplete。
- release guard 与 evidence pack 记录未执行 `git push`、`git tag`、`npm publish`、release upload。

## Task Agent Evidence

- 独立 code review 初轮发现 doctor root 与 installer hardcoded projection 两个问题；均已修复。
- 聚焦 closure reviewer `019f9768-b255-7292-895d-0245bb7d3daf` 返回 `verdict: passed`，无新增 findings。
- Goal 功能验收 agent `019f976d-5559-7523-8177-5a9dc3c2a205` 对实现主体返回 pass/partial pass，但指出 feature acceptance、roadmap writeback 和 goal final acceptance 缺失；本报告和后续 goal final iteration 用于关闭这些流程缺口。

## Functional Evidence

- `python -m pytest -q "test/test_rmux_packaging_docs_contracts.py" "test/test_doctor_rmux_packaging_summary.py" "test/test_install_windows_rmux_contract.py" "test/test_windows_bootstrap_script.py" "test/test_ccbd_diagnostics_bundle_rmux.py" "test/test_cli_doctor_rmux_packaging.py" "test/test_rmux_packaging_release_guard.py" "test/test_rmux_docs_consistency_gate.py"`：`21 passed`。
- `python -m pytest -q "test/test_rmux_packaging_docs_contracts.py"`：`7 passed`，包含 packaged projection 与 repo evidence 稳定字段一致性检查。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-checklist.yaml" --yaml-only`：passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`：passed。
- PowerShell AST parse for `install.ps1`：passed。
- `npm run pack:check`：passed，dry-run only。

## Roadmap Writeback

- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 中 `rmux-packaging-docs-contracts` 已回写为 `done`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml` 中 `rmux-packaging-docs-contracts` 已回写为 `accepted`。
- `.codestable/roadmap/windows-rmux-native-backend/goal-features/rmux-packaging-docs-contracts.md` 已回写为 `accepted`。
- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md` 中对应子 feature 状态已更新。

## Delivery Record

已交付 Windows Rmux packaging/docs support contract、install runbook、diagnostics contract、README 同步、support projection owner、installer rmux check、doctor/diagnostics projection、docs consistency guard、release guard 和 evidence pack。当前对外支持档为 `beta`，不是 `supported`。

## Residual Risks

- Windows npm 后续启用仍需要独立 package gate、artifact/checksum/postinstall 策略和 owner 授权。
- release guard 是本地静态和测试证据，不替代远端发布系统审计。

## Verdict

`passed`。本 feature 可视为 accepted。
