---
doc_type: feature-qa
feature: 2026-07-31-herdr-backend-contract-spike
status: passed
runner_state: completed
runner_reason: "本 feature 不修改生产 runtime；QA 以本地验证和独立 review/OCR 已核验的 evidence gate 为主"
runner_id: ""
tested: 2026-08-01
round: 1
---

# herdr-backend-contract-spike QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml`
- Review: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-review.md`
- Evidence pack: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/scope-gate.json`、`.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/evidence-pack-gate.json`
- DoD results: `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/dod-results.json`
- Diff basis: `git status --short --untracked-files=all` 仅显示本 feature 的 checklist、goal-state、evidence、draft runner 和测试文件。
- Baseline dirty files: none outside feature scope.
- Feature type: mixed
- Core evidence gate: 核心不是证明 Herdr supported，而是证明 runner 在当前 platform gate blocked 时产出机器可读 fail-closed evidence，并且 fake pass / fake continue 不能通过 validator。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | design AC-001 | core-functional | platform gate 通过后只在 dedicated session 内运行 Herdr 操作，不碰默认 session | CLI/evidence | CMD-005 | blocked evidence with isolated session refs | pass |
| QA-002 | design AC-002/AC-010 | core-functional | schema/status/pass evidence 不可用自由文本或缺 artifact refs 伪造 | unit | CMD-003/CMD-006 | fake pass rejected | pass |
| QA-003 | design AC-005 | core-functional | provider_cli_dry_run 与 fallback_terminal_smoke 分离 | unit/evidence | CMD-003 | fallback 不支撑 pass | pass |
| QA-004 | design AC-008 | core-functional | restart 必须有隔离和 stop command trace | unit/evidence | CMD-003 | 缺隔离/stop ref 被拒绝 | pass |
| QA-005 | design AC-009 | core-functional | spike 阶段不修改 production runtime / package surface | unit/scope gate | CMD-004 + scope gate | 无生产 diff，Herdr route 不注册 | pass |
| QA-006 | review QA Focus | supporting | machine evidence 被解释为 blocked/stop，不是 support pass | document/evidence | evidence pack + JSON inspection | residual risk 非 none | pass |
| QA-007 | cleanliness | supporting | 无临时 TODO/FIXME/XXX、未脱敏明显样例只在测试 fixture 内出现 | static | rg scan + scope gate | 无未解释清洁度问题 | pass |

## 3. Command Results

- `python -m pytest -q test/test_herdr_contract_spike_evidence.py test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py test/test_herdr_spike_no_production_route.py` -> exit 0：35 passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml" --yaml-only` -> exit 0：validated 1 file。
- DoD runner CMD-001 至 CMD-006 -> passed；CMD-003 记录 26 passed，CMD-004 记录 9 passed，CMD-005 写入 `verdict=blocked failure_class=unsupported-capability`。
- JSON/YAML parse check -> passed：`goal-state.yaml`、checklist、machine evidence、scope gate、DoD results、evidence-pack gate 均可解析。

## 4. Scenario Results

- [x] QA-001 Herdr primitive fail-closed：pass
  - Evidence: `herdr-contract-spike-evidence.json` 为 `verdict=blocked`、`failure_class=unsupported-capability`、`adapter_recommendation=needs-upstream-issue`；schema/status/session_attach/pane_spawn/send_input/read_output/kill_pane 为 pass，server_restart_restore 为 partial，detach_reattach 保持 blocked。
- [x] QA-002 fake pass rejected：pass
  - Evidence: validator tests 覆盖 pass/non-continue、pass/blocked operation、failure_class none/non-pass、artifact_refs 缺失、command/evidence ref 缺失、重复 operation、unknown URI。
- [x] QA-003 provider/fallback split：pass
  - Evidence: fallback smoke alone cannot produce pass verdict；provider dry run 不作为 completion authority。
- [x] QA-004 restart isolation：pass
  - Evidence: authorized restart 缺 socket/config、server identity、preexisting session check、stop_command_ref 均被拒绝。
- [x] QA-005 production no-change：pass
  - Evidence: scope gate changed_files 无 `lib/terminal_runtime/`、`lib/ccbd/`、`lib/provider_backends/`、`bin/` 或 `package.json`；API 层 `get_backend("herdr")` 返回 None。
- [x] QA-006 evidence interpretation：pass
  - Evidence: evidence pack Residual Risks 明确写 `blocked/unsupported-capability/needs-upstream-issue`；v8.5.2 source admission、64-bit Python、Native Windows x64 Herdr 与 x64 helper PE evidence 已满足，剩余风险是 detach/reattach 未在 Herdr UI client 内验证，以及 restart 后输出历史未恢复。
- [x] QA-007 cleanliness：pass
  - Evidence: 清洁度命中仅为测试中的 secret/redaction fixtures 与 `herdr-native` guard 字符串；无未解释生产 debug/TODO。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- Herdr active-host 能力仅部分证明；detach/reattach 未在 Herdr UI client 内验证，server restart restore 只恢复 workspace/pane identity，不恢复 sentinel 输出历史。后续若要继续 Herdr adapter，必须先确认 Herdr 0.7.5 的 detach 与 restore API 语义，或调整 epic 路线。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass
- Out-of-scope files: pass

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段。Acceptance 必须把 `adapter_recommendation=needs-upstream-issue` 回写给 roadmap/后续 goal flow，不得继续把下游 Herdr adapter feature 当作 implementation-ready supported path。
