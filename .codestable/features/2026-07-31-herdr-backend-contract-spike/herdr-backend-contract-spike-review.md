---
doc_type: feature-review
feature: 2026-07-31-herdr-backend-contract-spike
status: passed
reviewer: subagent+ocr
reviewed: 2026-08-01
round: 4
lane_a_state: completed
lane_a_ref: "019fbb68-cccf-7a91-ab93-b1c25064cda3"
lane_a_reason: "最终窄范围独立复审 passed；blocking/important none"
lane_b_state: completed
lane_b_ref: "ocr workspace review"
lane_b_reason: "OCR 第三轮复扫无 blocking；medium 项已修复并验证"
---

# herdr-backend-contract-spike 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/scope-gate.json`、`.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/evidence-pack-gate.json`
- DoD results: `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/dod-results.json`
- Implementation evidence: checklist steps 全 `done`；DoD runner 记录 CMD-001 至 CMD-006 全部 exit 0。
- Diff basis: 当前工作区新增 spike runner、runbook、machine evidence、gate evidence、evidence pack、validator tests 和 no-production-route tests；未修改 production runtime / ccbd / provider_backends / package metadata。
- Review mode: full-rereview with focused final closure
- Baseline dirty files: none outside this feature scope

### Independent Review

- Detection: independent Task agent 可用；OCR CLI 可用且 `ocr llm test` 通过。
- 环节 A 独立隔离 Task agent: `019fbb68-cccf-7a91-ab93-b1c25064cda3` completed，verdict passed。
- 环节 B OCR CLI: completed。前两轮发现的 fail-closed / traceability / isolation / redaction / test isolation 问题已修复；最终窄范围复扫无 blocking。
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion after verification, Low discarded.
- Merge policy: 所有 reviewer / OCR finding 均经本地事实核验后合并；blocking 和 important 已清零。
- Gate effect: `reviewer: subagent+ocr` 可放行到 Goal QA 阶段。

## 2. Diff Summary

- 新增：
  - `.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-backend-contract-spike/run_spike.py`
  - `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/herdr-contract-spike-evidence.json`
  - `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/manual-native-windows-runbook.md`
  - `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/scope-gate.json`
  - `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/dod-results.json`
  - `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/evidence-pack-gate.json`
  - `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-evidence-pack.md`
  - `test/test_herdr_contract_spike_evidence.py`
  - `test/test_herdr_spike_no_production_route.py`
  - `test/test_mux_backend_contract.py`
- 修改：
  - `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml`
  - `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml`
- 删除：none
- 未跟踪 / staged：均为本 feature 允许范围内新增文件；未 staged。
- 风险热点：外部 Herdr CLI/socket 边界、Windows host gate、restart isolation、evidence truth table、敏感输出脱敏。

## 3. Adversarial Pass

- 假设的生产 bug：fake pass evidence 通过 validator，导致 downstream adapter 误以为 Herdr 已 supported。
- 主动攻击过的反例：pass + non-continue、pass + blocked operation、failure_class none + non-pass、blocking_gaps 不一致、pass operation 缺 command/evidence ref、artifact_refs 缺 schema/status/version、重复 core operation、unknown URI scheme、restart stop command ref 缺失、fallback smoke 冒充 provider dry-run。
- 结果：以上均有负向测试或 validator gate；Restore Capability Matrix v2 后当前 machine evidence 正确停在 `partial/windows-beta-gap/continue-with-gaps`，并保留不支持项为显式 gaps。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- 后续可给 scope guard 增加 synthetic fixture，覆盖 `binxxx/...` 和 `lib/terminal_runtime_extra/...` 这类误匹配反例。

### learning

- DoD runner passed 表示 fail-closed blocked evidence 可生成且可验证，不表示 Herdr backend capability 已通过。
- Post-handoff rerun 后 platform gate artifact 已不再记录 `ccb-version-mismatch`、`python-not-x64`、`herdr-missing` 或 `helper-missing`；v8.5.2 source admission 为 `strict-v8.5.2`，Python 为 64-bit，Herdr 与两个 CCB helper 均为 x64。Restore Capability Matrix v2 显示 schema/status/session_attach/pane_spawn/send_input/read_output/kill_pane/server_restart_layout_restore 已通过；server_restart_process_continuity 与 server_restart_output_history 明确 unsupported，ui_detach_reattach 需要 Herdr UI harness。

### praise

- Spike runner 在 platform gate blocked 时不执行 Herdr operation，避免触碰全局 Herdr server。
- Validator 对 pass truth table、restart isolation、provider/fallback split、artifact traceability 和 secret redaction 都有负向测试覆盖。

## 5. Test And QA Focus

- QA 必须重点复核：machine evidence 的 `verdict=partial`、`failure_class=windows-beta-gap`、`adapter_recommendation=continue-with-gaps` 是否被正确解释为基础 adapter 可继续但不得宣称 process/output continuity 或 Windows supported。
- Evidence pack residual risks / gate warnings：archguard/meta-cc disabled 已记录；residual risk 为 Herdr detach/reattach 与 restart output-history 语义缺口，不是 none。
- 建议新增或加强的测试：none required for this stage。
- 不能靠 review 完全确认的点：真实 Herdr CLI active-host 行为；当前平台 gate blocked，后续需在 supported platform gate + explicit isolated socket/config 下再跑。

## 6. Residual Risk

- Herdr full support 能力本身仍未被证明；当前结果是带缺口继续证据，不是 support pass。

## 7. Verdict

- Status: passed
- Next: 按 Goal lane 进入 `cs-feat` QA 阶段。

## 8. Focused Closure

- Closed findings: OCR timeout handling、schema/status JSON object validation、pass truth table、restart isolation proof、host/platform gate binding、raw command redaction、production no-change guard、artifact refs traceability、duplicate core operation rejection、unknown URI rejection。
- Attributed delta: `run_spike.py` validator / runner guard、`test/test_herdr_contract_spike_evidence.py` negative fixtures、no-production tests、runbook/CMD-005 isolation args。
- Targeted verification: `python -m pytest -q test/test_herdr_contract_spike_evidence.py test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py test/test_herdr_spike_no_production_route.py` -> 35 passed；DoD runner CMD-001 至 CMD-006 -> passed。
- Classification: review-fix 修改了 executable validator，因此每轮实质变化后均重新执行 OCR 和独立 Task reviewer；最终独立复审 passed。
