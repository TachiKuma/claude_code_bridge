---
doc_type: feature-design-review
feature: 2026-07-31-windows-x64-v852-baseline-gate
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb8d6-368d-7031-a6a9-197806284f1a
reviewed: 2026-07-31
round: 5
---

# windows-x64-v852-baseline-gate feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/requirements/native-windows-ccb-via-herdr.md`、`.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`、`.codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md`
- Code facts checked: `package.json`、`VERSION`、`bin/ccb-npm-install.js`、`lib/cli/services/doctor.py`、`lib/cli/render_runtime/ops_views_doctor.py`、`lib/cli/services/doctor_runtime/system.py`、`lib/terminal_runtime/rmux_packaging_support.py`、`lib/terminal_runtime/backend_resolver.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019fb8d6-368d-7031-a6a9-197806284f1a`
- Raw output: 第 5 轮只读复审确认 FDR-R4-001 已关闭，未发现 `blocking` / `important` / `nit`。
- Merge policy: 已逐条核验 reviewer finding 与本地 design/checklist/roadmap/code 事实。
- Gate effect: independent review completed and merged; final verdict may pass.

## 2. Design Summary

- Goal: 建立 Native Windows x64-only 的 `WindowsX64PlatformGate`，集中表达 CCB strict `v8.5.2` 源头/新分支 admission、OS/CPU/Node/Python 位宽、Herdr/helper 位宽、fail-closed reason 和 doctor startup-baseline projection。
- Key contracts: gate owner 固定在 `lib/terminal_runtime/windows_x64_platform_gate.py`；`failure_reason` 保持 roadmap §4.1 parent-compatible 枚举，`detail_reason` 承载 Node/version/source/helper 细分原因；本 feature 不启用 npm `win32`、不实现 Herdr backend、不扩展 `CcbdStartupReport`。
- Steps: 6 个 step，按 gate owner、probe integration、doctor projection、startup-baseline projection、package no-change guard、evidence handoff 分离。
- Checks: 10 个 check 覆盖 Windows x64 pass、32-bit/arm64/非 Windows、Python bitness、version/source/branch mismatch、missing/unknown/conflicting helper、doctor render、startup-baseline projection、package no-change。
- Baseline / validation: CMD-001/CMD-002 是当前 YAML gate；CMD-003 至 CMD-006 是实现阶段必须新增的 core tests；CMD-007 是 package touched 时 conditional-core。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- Windows/npm 的 `os=win32` 只是 OS 平台名，不能代表 32-bit Windows 支持；本 feature 通过 `cpu_arch`、`node_arch`、`python_bitness`、helper/Herdr arch 分层判断。
- startup baseline 诊断保留在 doctor top-level projection，不早期扩展 `CcbdStartupReport` schema，符合 KISS/YAGNI。

### praise

- `source-branch-blocked` 已进入 `detail_reason` enum，并明确不扩展 parent `failure_reason`。
- AC-010 已进入 Acceptance Coverage Matrix，strict source/branch admission 不再只停留在正文。
- `startup_baseline_failure_reason/detail_reason` 已明确从 top-level `windows_x64_platform_gate` 派生，且不进入 `ccbd` payload、不扩展 startup report。
- raw state 扩展已声明为 parent-compatible projection，后续 consumer 的稳定依赖面被收紧。
- helper arch 可信来源冲突规则已收敛到 fail-closed：release metadata、PE header probe、explicit artifact ref 全部一致为 x64 才可接受；任一非 x64、冲突、unknown/missing 都不得 `native_helpers_ready=true` 或 `supported=true`。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只做 platform gate 与 doctor/startup-baseline projection，不启用 Windows npm release surface、不实现 Herdr backend、不自动安装 Herdr。
- implement 需要重点遵守：`failure_reason` 不得扩展 parent 枚举；version/source/Node/helper mismatch 只能进入 `detail_reason`；startup baseline 只来自 top-level `doctor_summary()["windows_x64_platform_gate"]` 与 `render_doctor()` 输出。
- code review / QA / acceptance 需要重点复核：新增测试必须覆盖 CMD-003 至 CMD-006；package metadata 和 postinstall route 不得在本 feature 中宣称 `win32` supported；helper arch 冲突 fixture 不得被单一 x64 来源覆盖。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 至 AC-010，并映射 step、证据类型和命令 / 动作。 | none |
| DoD Contract | pass | E | design §3.4 定义 Design / Implementation / Review / QA / Acceptance DoD、Validation Commands 和 Required Artifacts，DOD-IMPL-006 覆盖 strict source/branch admission。 | 实现阶段补齐新 tests。 |
| Steps and checks traceability | pass | E | checklist 6 steps / 10 checks 均可追溯到 design AC / DOD / 风险段，并包含 helper trusted-source conflict fixture。 | none |
| Roadmap contract compliance | pass | E | roadmap §4.1 的 `failure_reason` 枚举保持 parent-compatible；x64-only、strict `v8.5.2`、fail-closed、doctor startup diagnostic 均被继承。 | none |
| Module interface design | pass | C | 本地文件核验显示 doctor summary/render、rmux support projection、backend resolver 均存在可消费 projection 的模式；新增 owner 放 `terminal_runtime` 合理。 | implementation review 复核依赖方向。 |
| Validation and artifacts | pass | E | checklist `dod.commands` 使用 `{id, command, core, failure_handling}`，Required Artifacts 包含 gate module、doctor tests、package guard 和 evidence JSON。 | 实现阶段运行 CMD-003 至 CMD-006。 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 新测试文件当前尚未存在：`test/test_windows_x64_platform_gate.py`、`test/test_cli_doctor_windows_x64_platform_gate.py`、`test/test_doctor_startup_baseline_windows_x64_platform_gate.py`、`test/test_windows_x64_package_no_change_guard.py`。这是 implementation 阶段的预期工作，不影响 design review passed，但 implementation / QA 必须补齐并运行。
- 当前工作区 `package.json` 和 `VERSION` 均为 `8.2.1`，而 epic 目标基线是 strict CCB `v8.5.2` 源头新分支。design 已要求当前工作区只能产出 blocked/default admission evidence；实现阶段仍必须确保不把当前工作区误判为目标基线。
- Herdr 可执行文件位宽和 helper 位宽最终依赖真实 Windows x64 artifact/probe；实现阶段必须证明 `supported=true` 不会由 heuristic-only 证据触发。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop，继续处理下一个未完成 child；本 child 的 design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001 `detail_reason` 契约漂移、FDR-002 AC-010 matrix 缺口、FDR-003 startup baseline 挂载口径、FDR-004 parent-compatible raw/gate projection、FDR-005 helper arch evidence 来源、FDR-R4-001 helper trusted-source conflict rule。
- Attributed delta: design/checklist 增加 `source-branch-blocked`、AC-010 matrix、top-level startup baseline 派生口径、parent-compatible projection、helper trusted-source conflict fail-closed rule 和对应 checklist/test coverage。
- Verification: reviewer `019fb8d6-368d-7031-a6a9-197806284f1a` 返回无 blocking/important/nit；本地复核 roadmap §4.1、requirement hard gates、package/version/postinstall、doctor summary/render、rmux support projection 与 backend resolver 现状。
- Classification: 第 5 轮为实质契约修订后的完整独立复审，不是 focused-only closure。
