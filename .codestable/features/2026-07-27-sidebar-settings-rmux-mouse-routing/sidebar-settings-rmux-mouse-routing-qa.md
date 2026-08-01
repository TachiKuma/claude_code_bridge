---
doc_type: feature-qa
feature: 2026-07-27-sidebar-settings-rmux-mouse-routing
status: passed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-07-30
round: 1
---

# sidebar-settings-rmux-mouse-routing QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-design.md`
- Checklist: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml`
- Review: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-review.md`
- Evidence pack:
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/rmux-mouse-capability.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/wezterm-settings-only-channel.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/capability-summary.json`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/windows-rmux-ux-parity-evidence.json`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/foreground-reverse-validation.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/validation-summary.md`
- Gate results: none
- DoD results: none
- Parent evidence:
  - `.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/manual-foreground-retest.md`
  - `.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/sidebar-mouse-probe.json`
- Diff basis: `git status --short` only reports modified `笔记.md`; no staged diff. Current feature evidence is CodeStable-local/ignored and is attributed by explicit file reads, not by normal git diff output.
- Baseline dirty files: `笔记.md` is unrelated baseline dirty state and not covered by this QA verdict.
- Feature type: mixed. The target is functional sidebar mouse parity, but this child selected the evidence-only `unsupported_capability` route with `runtime_behavior_changed=false`.
- Core evidence gate: QA must prove the feature did not turn blocked parity into a false pass, did not add broad sidebar-left-click fallback, and did persist a reproducible unsupported capability projection.

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | AC-001 / S1 | core-functional | rmux capability audit proves whether settings-only coordinates or equivalent predicate exist | evidence / command transcript | read `evidence/rmux-mouse-capability.md` | rmux version, source refs, live probe, coordinates and `send-keys -M` conclusions recorded | pass |
| QA-002 | AC-002 / S2 | core-functional | WezTerm precise settings-only route is accepted or rejected with evidence | evidence / docs review | read `evidence/wezterm-settings-only-channel.md` | pane-wide mouse binding is not accepted as settings-only | pass |
| QA-003 | AC-003 / DOD-003 | core-functional | selected route must not claim settings click pass without real settings-only foreground click | evidence / JSON | read UX JSON and parent foreground transcript | `evidence_status=blocked`, direct `c` diagnostic is not counted as mouse pass | pass |
| QA-004 | AC-004 / AC-005 | core-functional | x, ordinary sidebar, and ordinary pane behavior must not be widened by this feature | diff / tests / evidence | pytest, cargo tests, foreground scope guard, scoped rg | no runtime route added; no broad fallback | pass |
| QA-005 | AC-006 / DOD-004 | core-functional | unsupported path is projected as blocked with `failure_class=unsupported_capability` | JSON validator | UX JSON validator | required fields and artifact refs exist; route is locked to unsupported capability | pass |
| QA-006 | AC-007 / DOD-001 | supporting | no token leak, default debug, TODO/FIXME/XXX, or broad fallback introduced | rg / diff review | scoped `rg` cleanliness command | only existing tests/fixtures and feature evidence explanations match | pass |
| QA-007 | 必跑命令 | supporting | YAML, Python regression, Rust sidebar helper tests remain healthy | command | validation commands, pytest, cargo test | all commands pass or skips are explained | pass |

## 3. Command Results

- `$env:PYTHONDONTWRITEBYTECODE='1'; python "C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"` -> exit 0: 1 file passed.
- `$env:PYTHONDONTWRITEBYTECODE='1'; python "C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/validate-yaml.py" --file ".codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml" --yaml-only` -> exit 0: 1 file passed.
- `$env:PYTHONPATH='lib'; python -m pytest -q -rs "test/test_v2_tmux_ui.py"` -> exit 0: 13 passed, 2 skipped. Both skips require `bash` for tmux helper scripts and are pre-existing environment skips.
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --quiet` -> exit 0: 63 passed.
- Generic UX JSON validator from the design -> exit 0: required schema, artifact paths, status enum, failure class, and residual risk contract passed.
- Precise UX JSON validator -> exit 0: `evidence_status=blocked`, `failure_class=unsupported_capability`, `selected_route=unsupported_capability`, `runtime_behavior_changed=false`, and `broad_fallback_added=false`.
- `rg -n "send-keys -t = c|send-keys -t %0 c|broad.*fallback|sidebar.*left-click|token=[A-Za-z0-9]|console\.log|console\.error|print\(|fmt\.Print|TODO|FIXME|XXX" ".codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing" "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py" "tools/ccb-agent-sidebar/src"` -> exit 0 with expected matches only:
  - `test/test_v2_tmux_ui.py` matches are existing assertions that forbid `send-keys -t = c` broad fallback.
  - `tools/ccb-agent-sidebar/src` matches are existing test fixtures and token redaction assertions.
  - Current feature matches are evidence/design text documenting rejected broad fallback and direct `c` diagnostic limits.

## 4. Scenario Results

- [x] QA-001 rmux capability audit: pass
  - Evidence: `rmux 0.9.0`; live namespace probe shows sidebar pane/role but empty `mouse_x` and `mouse_y`; source review records internal mouse event support but no ordinary root binding coordinate exposure.
  - Notes: this supports blocked route, not pass parity.
- [x] QA-002 WezTerm precise route audit: pass
  - Evidence: WezTerm `20251201-075747-d3b0fdad`; `mouse_reporting=true` binding is pane-wide and lacks CCB sidebar settings-cell predicate.
  - Notes: rejected as unsafe settings-only channel.
- [x] QA-003 settings click parity is not falsely passed: pass
  - Evidence: `windows-rmux-ux-parity-evidence.json` records `blocked/unsupported_capability`; parent direct `c` transcript is explicitly diagnostic only.
  - Notes: real settings mouse click remains blocked.
- [x] QA-004 reverse behavior scope guard: pass
  - Evidence: no runtime code change in this feature, regression tests still pass, scoped rg found no new broad fallback.
  - Notes: x and ordinary sidebar/pane foreground paths were not newly retested here; they are unchanged by this evidence-only route.
- [x] QA-005 unsupported projection: pass
  - Evidence: precise UX JSON validator passed and all artifact refs resolve.
- [x] QA-006 cleanliness: pass
  - Evidence: scoped rg hits are expected tests/fixtures/evidence text; no new debug output, real token, TODO/FIXME/XXX, or fallback route found.

## 5. Findings

### failed

none

### blocked

none for QA execution.

### residual-risk

- Actual Windows/rmux sidebar settings mouse click remains blocked by unsupported capability. This is the intended product projection for this child, not a QA failure.
- Future rmux or WezTerm versions may add coordinates or a precise route; that requires a new capability probe and likely a new implementation/review/QA loop.
- Feature evidence lives under CodeStable-local paths and is not visible in normal `git status`; final packaging or handoff must keep those artifacts with the roadmap state.

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass
- Out-of-scope files: pass. `笔记.md` is unrelated dirty baseline and not covered.

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段 / epic goal-state 恢复后可把 `sidebar-settings-rmux-mouse-routing` 作为 evidence-complete child 处理。不要把此结论表述为 settings mouse parity passed；正确投影仍是 `blocked/unsupported_capability`。
