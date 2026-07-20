---
doc_type: feature-design-review
feature: 2026-07-20-ccbd-windows-full-chain-smoke
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7cfd-14a9-7e53-ac34-97cb93d22be6"
reviewed: 2026-07-20
round: 1
---

# ccbd-windows-full-chain-smoke feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: `rmux-windows-validation-matrix` design；前置 child `ccbd-windows-tcp-loopback-transport`、`ccbd-rmux-namespace-lifecycle`、`accelerator-transport-windows-guard`、`ccbd-windows-process-liveness` 的 design/review
- Code facts checked:
  - `lib/cli/parser_runtime/commands.py`
  - `lib/agents/config_loader_runtime/parsing_runtime/workflow_v3.py`
  - `lib/cli/services/role_command_policy.py`
  - 相关 ccbd / rmux / accelerator / process-liveness 前置设计中的代码事实摘要

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7cfd-14a9-7e53-ac34-97cb93d22be6`
- Raw output: 首轮 `changes-requested`，提出 4 个 important、1 个 nit、1 个 suggestion；focused closure 后 verdict `passed`
- Merge policy: 主 agent 已核验 reviewer findings 与 design/checklist 证据，修订后由同一 reviewer 做 focused closure
- Gate effect: 独立 reviewer completed + closure verified；允许定稿 `passed`

## 2. Design Summary

- Goal: 在 native Windows 真机上以 command transcript 证明 `ccb -> ccbd -> rmux` 的 start/ping/ask/kill 最小全链路跑通，且不经 probe 旁路。
- Key contracts: transcript sidecar 强制 `host_kind=native_windows`、`control_plane=ccbd`、`backend_impl=rmux`、`probe_bypass=false`、`ccbd_transport=tcp_loopback`；机器判定使用 `verdict` / `failure_class`；ask case 用 `ask_case_kind` 区分 fake/local/real provider。
- Steps: 7 个步骤，覆盖 schema/parser、runner skeleton、dependency preflight、start/ping、ask、kill cleanup、true-host/scope guard。
- Checks: 9 项检查，覆盖防伪字段、dependency_status、command capture、`ccb ping ccbd` / doctor、provider failure 分类、cleanup residue、negative fixtures、deterministic scope guard。
- Baseline / validation: checklist YAML 与 roadmap items YAML 已通过校验；实现阶段新增 parser/unit/runner/true-host/manual command。

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

- 最小 full-chain smoke 与完整 validation matrix 必须分层：本 feature 只证明 milestone 的 start/ping/ask/kill 真链路，不承诺 supervision recovery、多项目矩阵或 packaging/docs supported 收口。
- `fake_provider` 可以作为无 secret 的 ask case，但只能在仓库认可测试入口下使用；它不是 fake backend，也不能绕过 `ccb -> ccbd -> rmux` 控制链路。
- scope guard 若只是 `git diff --name-only` 人工检查，无法支撑 blocking DoD；本 design 已改为 deterministic guard fail closed。

### praise

- design 对 probe bypass、WSL、direct rmux CLI 的排除条件明确，并复用 validation matrix 的 true-host 防伪字段。
- 修订后 failure classification、dependency pending、provider failure、scope guard 都进入机器可判定契约，acceptance 不需要靠人工解释 stdout。

## 4. User Review Focus

- 用户需要重点拍板：本 child 是本轮 milestone smoke，不代表完整 Windows Rmux 支持矩阵或正式发布支持。
- implement 需要重点遵守：核心证据必须从 `ccb` CLI 入口进入 ccbd/Rmux；`provider_failure`、`system_failure`、`test_design_failure` 和 `dependency_pending` 不能混淆；fake provider 只能在测试入口下使用。
- code review / QA / acceptance 需要重点复核：native Windows transcript 是否真机、`ccb ping ccbd` / doctor 是否证明 tcp_loopback control plane、ask case 是否可接受、`ccb kill -f` cleanup residue 是否完整、deterministic scope guard 是否 fail closed。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.1 / §3.3 覆盖 AC-001 至 AC-009，含 `verdict` / `failure_class` / `ask_case_kind` | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4；YAML 校验通过 | none |
| Roadmap contract compliance | pass | E | roadmap item `ccbd-windows-full-chain-smoke` 要求 native Windows 真链路 start/ask/kill 且非 probe；design 边界对齐 | none |
| Module interface design | pass | C | 前置 design/review 已定义 ccbd TCP transport、Rmux namespace lifecycle、accelerator fallback、process liveness；本 design 只消费 observable evidence | implementation 需等待前置实现 ready |
| Validation and artifacts | pass | E | checklist `dod.commands` 覆盖 parser、runner、true-host transcript、parser verdict、deterministic scope guard | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 真正的 native Windows / Rmux 运行证据只能在 implementation、QA 或 acceptance 阶段由 true-host transcript 补齐；design review 不能替代真机验收。
- 前置四个 child 仍必须实现并验收 ready；本 smoke 只能把前置未 ready 稳定归类为 `blocked/dependency_pending`，不能自行补实现。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004、nit、suggestion
- Attributed delta: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-design.md`、`.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-checklist.yaml`
- Verification: reviewer `019f7cfd-14a9-7e53-ac34-97cb93d22be6` focused closure verdict `passed`；checklist YAML 与 roadmap items YAML 校验通过
- Classification: 修订只关闭 reviewer 提出的机器契约、provider case、命令契约、scope guard、transport 文案和 dependency_status 问题；未修改生产代码，也未改变 feature 范围或 roadmap 边界
