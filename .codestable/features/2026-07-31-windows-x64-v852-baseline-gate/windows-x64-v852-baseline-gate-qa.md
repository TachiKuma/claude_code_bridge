---
doc_type: feature-qa
feature: 2026-07-31-windows-x64-v852-baseline-gate
status: passed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-08-01
round: 1
---

# windows-x64-v852-baseline-gate QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-checklist.yaml`
- Review: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-review.md`
- Evidence pack: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/scope-gate.json`
- DoD results: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/dod-results.json`
- Platform evidence: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/platform-gate-summary.json`
- Feature type: mixed，核心路径是 Native Windows x64 platform/source gate 与 doctor/startup diagnostics。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | CMD-001 | core | checklist YAML 可解析 | schema | `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-checklist.yaml" --yaml-only` | exit 0 | pass |
| QA-002 | CMD-002 | core | roadmap items YAML 可解析 | schema | `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` | exit 0 | pass |
| QA-003 | AC-001..AC-006, AC-010 | core | gate classifier、版本/source/branch admission、OS/CPU/Node/Python/helper/Herdr fail-closed | unit | `python -m pytest -q test/test_windows_x64_platform_gate.py` | exit 0 | pass |
| QA-004 | AC-003, AC-004, AC-007 | core | doctor payload/render 字段和版本 mismatch diagnostic | render/unit | `python -m pytest -q test/test_cli_doctor_windows_x64_platform_gate.py` | exit 0 | pass |
| QA-005 | AC-008 | core | startup baseline 从 top-level gate 派生，不写 ccbd/readiness_timeline/backend config | unit | `python -m pytest -q test/test_doctor_startup_baseline_windows_x64_platform_gate.py` | exit 0 | pass |
| QA-006 | AC-009 | core | 本 feature 不启用 package Windows artifact route | guard | `python -m pytest -q test/test_windows_x64_package_no_change_guard.py` | exit 0 | pass |
| QA-007 | AC-004, AC-006, AC-010 | core | installation summary、PE arch evidence、git source/branch refs | unit | `python -m pytest -q test/test_doctor_runtime_system_windows_x64_platform_gate.py test/test_cli_versioning_local.py` | exit 0 | pass |
| QA-008 | CMD-007 | conditional-core | package dry-run 在 touched install/versioning 范围内可运行 | dry-run | `npm run pack:check` | exit 0 | pass |
| QA-009 | review QA focus | supporting | 当前本机 blocked/default platform evidence 不误报 supported | evidence review | 读取 `platform-gate-summary.json` | `supported=false`，version mismatch 可见 | pass |

## 3. Command Results

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-checklist.yaml" --yaml-only` -> exit 0: 1 passed, 0 failed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` -> exit 0: 1 passed, 0 failed。
- `python -m pytest -q test/test_windows_x64_platform_gate.py` -> exit 0: 17 passed。
- `python -m pytest -q test/test_cli_doctor_windows_x64_platform_gate.py` -> exit 0: 3 passed。
- `python -m pytest -q test/test_doctor_startup_baseline_windows_x64_platform_gate.py` -> exit 0: 2 passed。
- `python -m pytest -q test/test_windows_x64_package_no_change_guard.py` -> exit 0: 2 passed。
- `python -m pytest -q test/test_doctor_runtime_system_windows_x64_platform_gate.py test/test_cli_versioning_local.py` -> exit 0: 7 passed。
- `npm run pack:check` -> exit 0: dry-run produced `seemseam-ccb-8.2.1.tgz`。

## 4. Scenario Results

- [x] QA-001 checklist YAML: pass。
- [x] QA-002 roadmap items YAML: pass。
- [x] QA-003 platform gate classifier: pass，覆盖 Windows x64 pass、非 Windows、非 x64、Node/Python 非 x64、版本 mismatch、source/branch blocked、Herdr/helper missing 和 helper conflict。
- [x] QA-004 doctor payload/render: pass，输出 `windows_x64_supported`、failure/detail reason、diagnostic、expected/detected CCB version。
- [x] QA-005 startup baseline projection: pass，startup baseline reason 从 top-level gate 派生，未扩展 ccbd payload。
- [x] QA-006 package no-change guard: pass，未声明 Windows npm artifact support。
- [x] QA-007 runtime/versioning admission: pass，覆盖 installation refs、helper PE arch evidence 与 `v8.5.2` tag ancestor source ref。
- [x] QA-008 npm pack dry-run: pass。
- [x] QA-009 current host evidence: pass，当前 Windows x64 主机因 CCB `8.2.1`、Herdr/helper missing 保持 `supported=false`。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- 真实 Herdr executable 和 helper x64 artifact 尚未在本机证明；本 feature 的 contract 要求 missing/unknown fail closed，后续 feature 负责提供真实 Herdr evidence。
- 当前仓库不是 strict CCB `v8.5.2` source branch，blocked/default evidence 是预期输出。
- 相邻完整 doctor runtime identity 测试有既有 Windows path baseline 失败，不纳入本 feature QA core。

## 6. Cleanliness

- Debug output: pass。
- Temporary TODO/FIXME/XXX: pass。
- Commented-out code: pass。
- Out-of-scope files: `.codestable/reference/agent-conventions.md` 与 `笔记.md` 保持排除，不作为本 feature 证据或提交范围。

## 7. Verdict

- Status: passed
- Next: 进入 acceptance 阶段。
