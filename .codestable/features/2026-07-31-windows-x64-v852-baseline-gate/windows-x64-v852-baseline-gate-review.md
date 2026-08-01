---
doc_type: feature-review
feature: 2026-07-31-windows-x64-v852-baseline-gate
status: passed
reviewer: subagent
reviewed: 2026-08-01
round: 4
lane_a_state: completed
lane_a_ref: "019fba54-73cc-7e02-8160-abb15b46079b"
lane_a_reason: "independent Task agent reviewer Descartes completed final rereview; no blocking or important findings"
lane_b_state: unavailable
lane_b_ref: ""
lane_b_reason: "OCR CLI exists but ocr llm test returned HTTP 400 in this environment; recorded as unavailable, not used as a pass anchor"
---

# windows-x64-v852-baseline-gate 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/scope-gate.json`
- DoD results: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/dod-results.json`
- Platform evidence: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/platform-gate-summary.json`
- Diff scope: `install.sh`、`lib/terminal_runtime/windows_x64_platform_gate.py`、doctor/versioning wiring、目标测试、当前 feature evidence 与 roadmap/goal 状态文件。
- Baseline dirty files excluded from this review scope: `.codestable/reference/agent-conventions.md`、`笔记.md`。

## 2. Independent Review

- 环节 A 独立 Task agent: completed，ref `019fba54-73cc-7e02-8160-abb15b46079b`。
- Verdict: passed；blocking none，important none。
- OCR lane: unavailable；本机 `ocr llm test` 返回 400，未作为放行锚点。
- Merge policy: 独立 reviewer 的 residual risk 与 QA focus 已纳入本报告和 QA。

## 3. Diff Summary

- 新增：`lib/terminal_runtime/windows_x64_platform_gate.py`，以及 6 个 Windows x64 gate/doctor/versioning/package guard 测试文件。
- 修改：doctor payload/render、installation/versioning runtime、`install.sh` build metadata、feature checklist、goal/roadmap 状态。
- 未修改：`package.json` 未启用 `win32`；postinstall artifact route 未声明 Windows artifact support；backend resolver 未切 Herdr。
- 风险热点：版本源不一致时 fail-closed、`v8.5.2` source/branch admission、helper/Herdr arch 可信证据、doctor startup baseline 不写入 ccbd payload。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- 后续若 admission evidence 需要支持 commit SHA + annotated tag ref，可另起设计扩展 `_is_v852_source_ref()`；本轮严格接受 `v8.5.2` / `refs/tags/v8.5.2`，符合当前 design。

### learning

- `version_sources` 不一致已经 fail closed：`failure_reason="unknown"`、`detail_reason="ccb-version-source-mismatch"`，且 `platform_ready` 同时要求版本源一致。
- `source_ref` 不依赖 HEAD exact tag：feature branch ahead of `v8.5.2` tag ancestor 时，versioning 能投影 `refs/tags/v8.5.2`，`install.sh` 同步持久化 `source_ref` / `branch_ref`。
- Post-handoff 重新生成的当前本机 evidence 已通过：Windows x64、Node x64、Python 64-bit、CCB `8.5.2` source admission、x64 Herdr 与两个 CCB native helper x64 PE header evidence 均满足，`supported=true`。

## 5. Test And QA Focus

- QA 必须覆盖 DoD commands：YAML 校验、platform gate unit、doctor payload/render、startup baseline projection、package no-change guard、runtime/versioning admission、`npm run pack:check`。
- 复核真实 Windows x64 source install 路径：从 `v8.5.2` tag 新建 `feature/*` 分支时，`BUILD_INFO.json` 应写入 `source_ref=refs/tags/v8.5.2` 与 `branch_ref=refs/heads/feature/...`。
- 复核 residual risk：相邻 `test/test_doctor_runtime_identity.py` 在 Windows 上仍有 3 个既有临时路径识别失败；该失败不属于本 feature diff，不能作为本 feature core blocker。

## 6. Residual Risk

- 未执行真实 Herdr socket/API 能力验证；这属于后续 `herdr-backend-contract-spike`。
- 当前工作区已是基于 CCB `v8.5.2` tag ancestor 的实现分支；platform evidence 仍因 helper evidence 缺失保持 blocked/default，这是环境准入要求，不是版本失败。
- 完整 doctor 邻域测试存在既有 Windows path baseline 问题，本 feature 仅以目标测试和 gate evidence 作为验收证据。

## 7. Verdict

- Status: passed
- Next: 进入 QA 阶段。
