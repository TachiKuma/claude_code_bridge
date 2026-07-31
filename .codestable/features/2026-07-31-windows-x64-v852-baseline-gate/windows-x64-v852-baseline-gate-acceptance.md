---
doc_type: feature-acceptance
feature: 2026-07-31-windows-x64-v852-baseline-gate
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: approval-report.md#goal-acceptance
accepted: 2026-08-01
round: 1
---

# windows-x64-v852-baseline-gate 验收报告

> 阶段：Goal feature acceptance
> 验收日期：2026-08-01
> 关联方案 doc：`.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-design.md`

## 1. 接口契约核对

- [x] `WindowsX64PlatformGate` owner 落在 `lib/terminal_runtime/windows_x64_platform_gate.py`，doctor/versioning 只做输入收集和渲染 wiring。
- [x] gate stable output 覆盖 `platform_ready`、`native_helpers_ready`、`herdr_executable_ready`、`supported`、parent-compatible `failure_reason`、`detail_reason`、`diagnostic`、`ccb_source_status`、`ccb_source_ref`、`ccb_branch_ref`。
- [x] `supported=true` 只在 Windows x64、Node x64、Python 64-bit、strict CCB `v8.5.2` source/branch、Herdr x64 和两个 helper x64 同时满足时成立。
- [x] `win32` 被当作 Windows OS 名称处理，不被解释为 32-bit support。

## 2. 行为与决策核对

- [x] fail-closed 顺序覆盖非 Windows、非 x64、Node 非 x64、Python 非 64-bit、版本源不一致、CCB 非 `v8.5.2`、source/branch evidence 缺失、Herdr/helper missing/unknown/conflict。
- [x] doctor payload/render 输出 raw fields、supported、failure reason、detail reason、diagnostic、expected/detected CCB version。
- [x] startup baseline reason 从 top-level `windows_x64_platform_gate` 派生；未新增 `CcbdStartupReport` 字段，未写 `readiness_timeline`，未自动修改 backend/config。
- [x] `install.sh` 写入 `source_ref` / `branch_ref` admission metadata；versioning 支持从 `v8.5.2` tag ancestor 推出 source ref。
- [x] `package.json` 未启用 `win32`，postinstall artifact route 未新增 Windows artifact support。

## 3. 验收场景核对

- [x] AC-001 Windows x64 full pass：`test/test_windows_x64_platform_gate.py` 覆盖。
- [x] AC-002 Windows 32-bit / Node 32-bit blocked：`test/test_windows_x64_platform_gate.py` 覆盖。
- [x] AC-003 Python 32-bit / unknown fail closed：platform gate 与 doctor tests 覆盖。
- [x] AC-004 CCB version/source/branch mismatch fail closed：platform gate、doctor、versioning tests 覆盖。
- [x] AC-005 非 Windows / arm64 Windows blocked：platform gate tests 覆盖。
- [x] AC-006 Herdr/helper missing/unknown/conflicting evidence blocked：platform gate 与 runtime system tests 覆盖。
- [x] AC-007 doctor payload/render：doctor tests 覆盖。
- [x] AC-008 startup baseline projection：startup baseline tests 覆盖。
- [x] AC-009 package metadata no-change：package no-change guard 覆盖。
- [x] AC-010 当前工作区 blocked/default evidence：`platform-gate-summary.json` 记录 `supported=false`、`detail_reason=ccb-version-mismatch`。

## 4. Review / QA 复核

- [x] Review report status passed，独立 subagent reviewer ref `019fba54-73cc-7e02-8160-abb15b46079b`，无 unresolved blocking / important。
- [x] QA report status passed，覆盖 DoD commands、review QA focus、evidence pack residual risks。
- [x] OCR unavailable 已记录，不作为 gate pass anchor。
- [x] Evidence pack、scope gate、DoD results 均为 passed。

## 5. DoD Contract 核对

- [x] DOD-IMPL-001：platform gate owner 是单一 module。
- [x] DOD-IMPL-002：fail-closed unit tests 覆盖指定反例。
- [x] DOD-IMPL-003：doctor payload/render 展示 required fields。
- [x] DOD-IMPL-004：startup-baseline projection 不扩展 ccbd payload。
- [x] DOD-IMPL-005：package metadata 与 npm artifact route 未启用 win32。
- [x] DOD-IMPL-006：strict `v8.5.2` source/branch admission fail closed。
- [x] DOD-REVIEW-001：code review passed。
- [x] DOD-QA-001：QA passed。
- [x] DOD-ACCEPT-001：roadmap item 已回写，gate evidence refs 已记录。

## 6. Roadmap / Requirement 回写

- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml` 中 `windows-x64-v852-baseline-gate` 已回写为 `done`。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md` 子 feature 清单状态已回写为 `accepted`。
- [x] 当前 requirement `native-windows-ccb-via-herdr` 不需要新增 delta；本 feature 只实现平台准入 contract，不声明 Windows supported。
- [x] 后续 `herdr-backend-contract-spike` 可消费 `platform-gate-summary.json` 的 blocked/default evidence 和 strict admission fields。

## 7. 遗留

- 后续 feature 必须提供真实 Herdr executable/helper x64 evidence，并验证 Herdr socket API。
- 若未来 admission evidence 使用 commit SHA + annotated tag ref，需要单独扩展 source ref policy。
- 完整 doctor runtime identity Windows path baseline 问题不属于本 feature，实现不依赖该邻域全绿。

## 8. 最终审计

- Acceptance authorization: `approval-report.md#goal-acceptance` 已 approved。
- Commit authorization: `approval-report.md#goal-commits` 已 approved；提交仍只允许本 feature scoped commit，不包含 push。
- Checklist steps: done。
- Checklist checks: passed。
- Roadmap item: done。
- Goal state: feature accepted，`current_feature_index` 前进到 1。
- 结论：通过。
