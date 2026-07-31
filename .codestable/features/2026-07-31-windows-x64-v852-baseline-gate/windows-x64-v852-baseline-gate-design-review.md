---
doc_type: feature-design-review
feature: 2026-07-31-windows-x64-v852-baseline-gate
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb62a-187f-7542-b429-410cca733031
reviewed: 2026-07-31
round: 3
---

# windows-x64-v852-baseline-gate feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`、`.codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md`
- Code facts checked: `package.json`、`bin/ccb-npm-install.js`、`lib/cli/services/doctor.py`、`lib/cli/render_runtime/ops_views_doctor.py`、`lib/terminal_runtime/rmux_packaging_support.py`、`lib/terminal_runtime/backend_resolver.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019fb62a-187f-7542-b429-410cca733031`
- Raw output: 第三轮只读复审返回 `verdict: passed`，未发现 `blocking` 或 `important`。
- Merge policy: 已逐条核验 reviewer finding 与本地 design/checklist/roadmap/code 事实。
- Gate effect: independent review completed，允许本地合并后定稿 `passed`。

## 2. Design Summary

- Goal: 建立 Native Windows x64-only 的 `WindowsX64PlatformGate`，集中表达 CCB `8.5.2` baseline、OS/CPU/Node/Python 位宽、Herdr/helper 位宽、fail-closed reason 和 doctor/startup-baseline projection。
- Key contracts: gate owner 固定在 `lib/terminal_runtime/windows_x64_platform_gate.py`；`failure_reason` 严格兼容 roadmap §4.1，Node/version/source mismatch 进入 `detail_reason`；本 feature 不启用 npm `win32`、不实现 Herdr backend、不扩展 `CcbdStartupReport`。
- Steps: 6 个 step，按 gate owner、probe integration、doctor projection、startup-baseline projection、package no-change guard、evidence handoff 分离。
- Checks: 9 个 check 覆盖 Windows x64 pass、32-bit/arm64/非 Windows、Python bitness、version mismatch、missing/unknown helper、doctor render、package no-change。
- Baseline / validation: CMD-001/CMD-002 是当前 YAML gate；CMD-003 至 CMD-006 是实现阶段必须新增的 core tests；CMD-007 是 package touched 时 conditional-core。

## 3. Findings

### blocking

none

### important

none

### nit

- [ ] FDR-006 `checklist.steps[2].exit_signal` doctor projection step 的退出信号少列 `windows_x64_detail_reason`。
  - Evidence: design §2.4 step 3 要求 doctor render snapshot 包含 `windows_x64_detail_reason`；checklist step 3 当前列出 `windows_x64_supported`、`windows_x64_failure_reason`、`windows_x64_diagnostic`、`ccb_expected_version`、`ccb_detected_version`。后续 checks 已覆盖 detail reason。
  - Impact: 不改变契约，不阻塞实现；实现者只看 step exit signal 时可能漏掉 doctor render 层的 detail reason。
  - Expected fix scope: 后续文案整理或实现前可补入 checklist step 3 exit signal，不需要重启完整 design review。

### suggestion

none

### learning

- Windows/npm 的 `os=win32` 只是 OS 平台名，不能代表 32-bit Windows 支持；本 feature 通过 `cpu_arch`、`node_arch`、`python_bitness`、helper/Herdr arch 分层判断，避免将发布 metadata 与 runtime support 混在一起。
- startup 口径应先通过 doctor payload/render 投影，不应为了早期诊断扩展 `CcbdStartupReport` schema；需要持久化时应另起 feature 设计。

### praise

- `failure_reason` 保持 parent roadmap §4.1 枚举，`detail_reason` 承载更细的 Node/version/source mismatch，兼顾上游 contract 和实现可诊断性。
- gate owner 固定在 `lib/terminal_runtime/windows_x64_platform_gate.py`，doctor/runtime 只消费或提供输入，避免位宽策略散落。
- package metadata no-change guard 明确阻止本 feature 过早发布 Windows npm support，符合 KISS/YAGNI。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只做 platform gate 与 doctor/startup-baseline projection，不启用 Windows npm release surface、不实现 Herdr backend、不自动安装 Herdr。
- implement 需要重点遵守：`failure_reason` 不得扩展 parent 枚举；version/source/Node mismatch 只能进入 `detail_reason`；startup baseline 只来自 `doctor_summary()["windows_x64_platform_gate"]` 与 `render_doctor()` 输出。
- code review / QA / acceptance 需要重点复核：新增测试必须覆盖 CMD-003 至 CMD-006；package metadata 和 postinstall route 不得在本 feature 中宣称 `win32` supported。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 至 AC-009，并映射 S1 至 S5、证据类型和命令 / 动作。 | none |
| DoD Contract | pass | E | design §3.4 定义 Design / Implementation / Review / QA / Acceptance DoD、Validation Commands 和 Required Artifacts。 | 实现阶段补齐新 tests。 |
| Steps and checks traceability | pass | E | checklist 6 steps / 9 checks 均可追溯到 design AC / DOD / 风险段。 | nit FDR-006 可后续补文字。 |
| Roadmap contract compliance | pass | E | roadmap §4.1 的 `failure_reason` 枚举与 design 保持兼容；x64-only / fail-closed / doctor-startup diagnostic 均被继承。 | none |
| Module interface design | pass | C | CodeGraph 与本地文件核验显示 doctor summary/render、rmux support projection、backend resolver 均存在可消费 projection 的模式；新增 owner 放 `terminal_runtime` 合理。 | implementation review 复核依赖方向。 |
| Validation and artifacts | pass | E | checklist `dod.commands` 使用 `{id, command, core, failure_handling}`，Required Artifacts 包含 gate module、doctor tests、package guard 和 evidence JSON。 | 实现阶段运行 CMD-003 至 CMD-006。 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 新测试文件当前尚未存在：`test/test_windows_x64_platform_gate.py`、`test/test_cli_doctor_windows_x64_platform_gate.py`、`test/test_doctor_startup_baseline_windows_x64_platform_gate.py`、`test/test_windows_x64_package_no_change_guard.py`。这是 implementation 阶段的预期工作，不影响 design review passed，但 implementation / QA 必须补齐并运行。
- 当前工作区 `package.json` 为 `8.2.1`，而 epic 目标基线是 `8.5.2`。design 已要求 gate fail closed 并输出 `ccb-version-mismatch`；实现阶段仍必须确保不把当前工作区误判为目标基线。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop，继续处理下一个未完成 child；本 child 的 design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: 第二轮遗留 FDR-002、FDR-004、FDR-005 以及术语 nit 均已由第三轮 independent reviewer 核验关闭。
- Attributed delta: design/checklist 已收敛为 doctor-only startup projection、固定 gate owner、保持 parent-compatible `failure_reason`，并统一使用 `ccb-version-mismatch` / `ccb-version-source-mismatch`。
- Verification: reviewer `019fb62a-187f-7542-b429-410cca733031` 返回 `passed`；本地复核 roadmap §4.1、package metadata、postinstall artifact route、doctor summary/render 与 rmux support projection 模式。
- Classification: 本轮报告仅合并 review 结论，未修改 design/checklist 契约。
