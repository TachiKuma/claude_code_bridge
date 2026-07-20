---
doc_type: feature-design-review
feature: 2026-07-20-accelerator-transport-windows-guard
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7ce4-3d4b-75f2-991b-023484034e1a"
reviewed: 2026-07-20
round: 1
---

# accelerator-transport-windows-guard feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-design.md`
- Checklist: `.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: roadmap item 19；ccbd 控制面 transport track 边界说明；`ccbd-windows-full-chain-smoke` full-chain blocker 清单
- Code facts checked:
  - `lib/runtime_accelerator/client.py`
  - `lib/runtime_accelerator/lifecycle.py`
  - `lib/runtime_accelerator/ownership.py`
  - `lib/provider_backends/codex/execution_runtime/accelerator.py`
  - `test/test_runtime_accelerator_client.py`
  - `test/test_runtime_accelerator_lifecycle.py`
  - `test/test_runtime_accelerator_ownership.py`
  - `test/test_codex_runtime_accelerator_polling.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7ce4-3d4b-75f2-991b-023484034e1a`
- Raw output: 首轮 `changes-requested`，提出 2 个 important、1 个 nit、1 个 suggestion；focused closure 后 verdict `passed`
- Merge policy: 主 agent 已核验 runtime accelerator client/lifecycle/ownership/codex polling 代码事实，修订后由同一 reviewer 做 focused closure
- Gate effect: 独立 reviewer completed + closure verified；允许定稿 `passed`

## 2. Design Summary

- Goal: native Windows / no-AF_UNIX 环境下让 runtime accelerator 干净不可用，保证 codex ask/poll 路径回落普通 Python polling，而不是裸抛 `AttributeError`。
- Key contracts: 单一 availability helper；client unsupported transport 转 `AcceleratorError`；lifecycle 在 binary/reclaim/mkdir/Popen 前返回 fallback handle；ownership direct reclaim/recovery 在 unsupported platform 不杀进程、不删 evidence。
- Steps: 7 个步骤，覆盖 availability helper、client guard、codex polling fallback、lifecycle guard、ownership direct-call guard、Windows baseline/Unix regression、scope guard。
- Checks: 13 项检查，覆盖 unsupported reason、client/call_or_fallback、poll_with_accelerator/poll_submission、lifecycle startup action、ownership connectability/direct reclaim/corrupt recovery、Windows baseline-red、Unix regression、scope guard。
- Baseline / validation: YAML 校验通过；当前 Windows 工作区已复现 `test_runtime_accelerator_client.py::test_default_socket_path_uses_project_ccb_for_short_paths` 的既有 path expectation 红灯，design 已要求实现阶段先平台中立修正或记录为既有红灯再归因。

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

- `RuntimeAcceleratorHandle.error` 已能通过 `ccbd.app_runtime.lifecycle._runtime_accelerator_startup_actions()` 投影为 `runtime_accelerator_fallback:{error}`，因此 startup action 侧不需要新增 seam。
- runtime accelerator socket/protocol 与 ccbd control-plane `RpcTransport` 是两套生命周期；本 design 保持边界清楚，避免把性能 sidecar 与 ccbd 控制面混成一个 adapter。

### praise

- design 明确选择 guard + clean fallback，不借此实现 Windows accelerator transport，符合当前 full-chain smoke 的最小必要目标。
- Acceptance Coverage Matrix 可以从 AC 到 step、evidence、command 追踪，scope guard 清楚禁止扩到 ccbd transport、Rmux、process liveness、provider parser 和 packaging/docs。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只让 accelerator 不可用时 clean fallback，不支持 Windows accelerator sidecar。
- implement 需要重点遵守：unsupported check 必须早于 binary lookup、owner reclaim、socket mkdir、Popen；direct ownership entry 也不能在 no-AF_UNIX 下 kill pid 或删除 owner/socket evidence。
- code review / QA / acceptance 需要重点复核：没有 catch-all 异常吞噬、没有把 `_socket_is_connectable=False` 当作完整 ownership 修复、Windows baseline-red 已归因、Unix AF_UNIX 行为不漂移。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 至 AC-012 | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4；YAML 校验通过 | none |
| Roadmap contract compliance | pass | E | roadmap item 19 要求修复 runtime accelerator Windows AF_UNIX AttributeError；design 明确不做 Windows accelerator transport | none |
| Module interface design | pass | C | client/lifecycle/ownership/codex polling 代码事实已核对；single helper + no new transport seam 的边界合理 | implementation 需保持 helper 单一 owner |
| Validation and artifacts | pass | E | checklist `dod.commands` 覆盖 no-AF_UNIX guard、Windows baseline、Unix regression、scope guard | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- no-AF_UNIX monkeypatch 仍不能完全代表真实 native Windows 文件路径、进程 identity、socket cleanup 行为；最终仍需要 `ccbd-windows-full-chain-smoke` 的真机链路兜底。
- `recover_corrupt_runtime_accelerator_owner(force=True)` 的 unsupported 平台语义实现时必须重点复核，避免 force 模式误删 owner evidence。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop，继续下一个 epic child；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、suggestion
- Attributed delta: `.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-design.md`、`.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-checklist.yaml`
- Verification: reviewer `019f7ce4-3d4b-75f2-991b-023484034e1a` focused closure verdict `passed`；checklist YAML 与 roadmap items YAML 校验通过
- Classification: 修订只关闭 reviewer 提出的 direct reclaim coverage、Windows baseline-red、reason naming 说明和 lifecycle guard 顺序问题；未修改生产代码，也未改变 feature 范围或 roadmap 边界
