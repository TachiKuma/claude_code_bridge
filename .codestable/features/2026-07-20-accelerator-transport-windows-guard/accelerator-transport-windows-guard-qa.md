---
doc_type: feature-qa
feature: 2026-07-20-accelerator-transport-windows-guard
status: passed
runner_state: completed
runner_reason: ""
runner_id: ""
tested: 2026-07-21
round: 1
---

# accelerator-transport-windows-guard QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-design.md`
- Checklist: `.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-checklist.yaml`
- Review: `.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-review.md`（round 2，passed）
- Evidence pack: `.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-scope-gate.json`
- DoD results: `.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-dod-results.json`
- Diff basis: working tree diff for runtime accelerator guard implementation and focused tests; `lib/runtime_accelerator/platform.py` is untracked but included in this feature scope.
- Baseline dirty files: none outside current roadmap goal / feature report scope observed for this QA.
- Feature type: mixed。该 feature 改变 codex runtime accelerator 的运行时 fallback / 错误语义，同时保留 Unix AF_UNIX regression。
- Core evidence gate: no-AF_UNIX fallback、codex polling fallback、lifecycle startup guard、ownership fail-closed、Unix regression 和 scope guard 均有 fresh command evidence。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | CMD-001 | supporting | checklist YAML valid | schema | `python ".codestable/tools/validate-yaml.py" --file "...checklist.yaml" --yaml-only` | valid | pass |
| QA-002 | CMD-002 | supporting | roadmap items YAML valid | schema | `python ".codestable/tools/validate-yaml.py" --file "...items.yaml"` | valid | pass |
| QA-003 | AC-001/002 | core-functional | no-AF_UNIX 下 client error/fallback | unit | `python -m pytest -q test/test_runtime_accelerator_client.py ...` | `AcceleratorError` + fallback | pass |
| QA-004 | AC-003/004 | core-functional | codex accelerator fallback 不阻断 Python reader | unit | `python -m pytest -q test/test_codex_runtime_accelerator_polling.py -k "accelerator"` | pass | pass |
| QA-005 | AC-005/006 | core-functional | lifecycle unsupported transport 不启动 sidecar 并投影 startup action | unit | `python -m pytest -q test/test_runtime_accelerator_lifecycle.py ...` | no binary/reclaim/Popen + fallback reason | pass |
| QA-006 | AC-007/008/009 | core-functional | ownership connectability/reclaim/corrupt recovery no-AF_UNIX fail-closed | unit | `python -m pytest -q test/test_runtime_accelerator_ownership.py ...` | no terminate/delete/AttributeError | pass |
| QA-007 | AC-010/011 | regression | Windows path baseline 与 Unix AF_UNIX regression | unit/regression | aggregate pytest | pass with platform skips only | pass |
| QA-008 | AC-012 | guard | 无 ccbd transport/Rmux/process liveness/provider parser 越界 | diff | `git diff --name-only -- lib/runtime_accelerator lib/provider_backends/codex/execution_runtime test` | only allowed files | pass |
| QA-009 | Review focus / CMD-006 | supporting | AF_UNIX 访问集中在 helper guard 后或 Unix-only tests | static | explicit `rg -n "socket\.AF_UNIX" ...` | no unsafe extra hits | pass |

## 3. Command Results

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-checklist.yaml" --yaml-only` → exit 0：Validated 1 file(s), all valid。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` → exit 0：Validated 1 file(s), all valid。
- `python -m pytest -q test/test_runtime_accelerator_client.py test/test_runtime_accelerator_lifecycle.py test/test_runtime_accelerator_ownership.py test/test_codex_runtime_accelerator_polling.py` → exit 0：`46 passed, 3 skipped in 4.21s`。
- `python -m pytest -q test/test_codex_runtime_accelerator_polling.py -k "accelerator"` → exit 0：`6 passed in 0.88s`。
- `git diff --name-only -- lib/runtime_accelerator lib/provider_backends/codex/execution_runtime test` → exit 0：仅列出 `lib/runtime_accelerator/client.py`, `lifecycle.py`, `ownership.py` 与四个 focused test 文件；`platform.py` 是 untracked feature file，需纳入最终变更。
- `rg -n "socket\.AF_UNIX" "lib/runtime_accelerator" "test/test_runtime_accelerator_client.py" "test/test_runtime_accelerator_lifecycle.py" "test/test_runtime_accelerator_ownership.py" "test/test_codex_runtime_accelerator_polling.py"` → exit 0：命中 `client.py`、`ownership.py` 的 guard 后生产访问和 `test_runtime_accelerator_client.py` 的 Unix listener 测试；无额外散落访问。

## 4. Scenario Results

- [x] QA-001 checklist YAML：pass。
  - Evidence: validation exit 0。
- [x] QA-002 roadmap items YAML：pass。
  - Evidence: validation exit 0。
- [x] QA-003 client no-AF_UNIX fallback：pass。
  - Evidence: aggregate pytest 覆盖 `call()` 抛 `AcceleratorError("unsupported_platform:windows_no_af_unix")`，`call_or_fallback()` 返回 fallback 值。
- [x] QA-004 codex polling fallback：pass。
  - Evidence: aggregate pytest + focused accelerator pytest；`poll_with_accelerator()` 返回 `None`，`poll_submission()` 继续 Python reader fallback。
- [x] QA-005 lifecycle guard：pass。
  - Evidence: aggregate pytest 覆盖 unsupported transport 分支早于 binary lookup、reclaim、mkdir、Popen，并投影 `runtime_accelerator_fallback:unsupported_platform:windows_no_af_unix`。
- [x] QA-006 ownership fail-closed：pass。
  - Evidence: aggregate pytest 覆盖 socket connectability false、direct reclaim no-op、corrupt owner recovery blocked/warning，且保留 owner/socket evidence。
- [x] QA-007 regression：pass。
  - Evidence: aggregate pytest `46 passed, 3 skipped`；skip 为平台条件，不是 feature failure。
- [x] QA-008 scope guard：pass。
  - Evidence: diff scope 仅限 runtime accelerator / focused tests；无 ccbd transport、Rmux、process liveness、provider parser、packaging/docs 越界。
- [x] QA-009 AF_UNIX grep：pass。
  - Evidence: 修正 PowerShell glob 后的显式文件列表命令 exit 0，原 CMD-006 warning 已关闭。

## 5. Findings

### failed

- none

### blocked

- none

### residual-risk

- 本 QA 未执行真实 native Windows full-chain `ccb ask` smoke；该目标属于后续 `ccbd-windows-full-chain-smoke`，不是本 guard feature 的 completion gate。
- Windows accelerator transport 仍未实现；这是 design 明确不做项。本 feature 只保证无 AF_UNIX 时 clean fallback。
- `lib/runtime_accelerator/platform.py` 当前仍是 untracked 文件；后续 scoped commit 前必须显式纳入，否则 clean checkout 会因 import 缺失失败。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass（目标 pytest 通过）
- Out-of-scope files: pass（diff scope 与 design 挂载点一致；untracked `platform.py` 属本 feature）

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段（以 `acceptance_authorization_ref: approval-report.md#goal-acceptance` 显式进入）。
