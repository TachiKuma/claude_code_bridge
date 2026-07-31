---
doc_type: feature-design-review
feature: 2026-07-31-mux-backend-contract-herdr-v2
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb90f-0ee4-7322-b44e-033197f143df
reviewed: 2026-08-01
round: 9
---

# mux-backend-contract-herdr-v2 feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-design.md`
- Checklist: `.codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design.md`、`.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design-review.md`
- Code facts checked: `lib/terminal_runtime/mux_backend_contract.py`、`lib/terminal_runtime/backend_resolver.py`、`lib/terminal_runtime/backend_selection.py`、`lib/terminal_runtime/fake_mux_backend.py`、`lib/ccbd/services/project_namespace_state_runtime/models.py`、`test/test_mux_backend_contract.py`、`test/test_terminal_runtime_backend_selection.py`、`test/test_v2_project_namespace_backend.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fb669-6cc8-72d0-912a-548c5a3ef72f` changes-requested；round 2 `019fb66e-855b-7a11-97a3-1a4bdb7f7649` changes-requested；round 3 `019fb674-e302-7591-87f0-60909cb22f3c` changes-requested；round 4 `019fb682-09bd-7b81-87c0-dd626d5f3062` changes-requested；round 5 `019fb687-e868-7293-988e-920ea28142e2` passed；round 6 `019fb8fa-aa16-72c3-8d02-02b7ae03120e` changes-requested；round 7 `019fb900-5bee-7471-837e-7f3939d65acf` changes-requested；round 8 `019fb909-a44f-7163-ba93-33c56068e263` changes-requested；round 9 `019fb90f-0ee4-7322-b44e-033197f143df` passed。
- Raw output: round 9 未发现 blocking / important；确认 CMD-005 覆盖 installer/support/provider/ccbd/package/doctor 越界、staged/untracked/content/path，CMD-006 能阻止 tmux/rmux fallback success，Native Windows x64 `auto` / platform default 直路由 Herdr blocked/success selection，Herdr 保持 `herdr-native` 且本 feature 不越界实现 production Herdr client。
- Merge policy: 已逐条核验 reviewer finding 与 design/checklist/roadmap/code 事实；只合并有仓库事实支撑的结论。
- Gate effect: independent review completed and merged; final verdict passed.

## 2. Design Summary

- Goal: 将 CCB terminal runtime 的 mux backend 小协议升级为能表达 `tmux`、`rmux` 与未来 `herdr` 共存的 V2 contract、capability、structured error 和 resolver diagnostics。
- Key contracts: Herdr 使用 `herdr-native` family，不伪装 `tmux-family`；V2 refs/capabilities/errors 支持 `herdr_socket`、`restore_token`、`schema-mismatch`、Windows beta gaps 和 fail-closed blocking gaps。
- Steps: 6 个 step，覆盖 V2 contract types、fake backend fixture、resolver diagnostics、spike capability projection、scope/evidence guard、tmux/rmux regression。
- Checks: 10 个 check 覆盖 compatibility、Herdr refs、capability gaps、schema mismatch、fake backend、resolver blocked/failure、Native Windows auto Herdr blocked/success selection、upstream evidence fail-closed 和 production scope guard。
- Baseline / validation: CMD-001/CMD-002 YAML gate；CMD-003/CMD-004 focused pytest；CMD-005 scope guard；CMD-006 upstream evidence / blocked fixture guard。

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

- Contract V2 先落在 terminal runtime / fake / resolver diagnostics，能把 Herdr schema drift 和 production socket client 风险推迟到后续 `herdr-backend-client`，符合 KISS/YAGNI。
- Guard 类命令需要同时覆盖 modified、staged、rename/copy target 与 untracked；只看 `git diff --name-only` 或只看 unstaged content 不足以保护实现范围。

### praise

- `MuxBackendSelectionV2` / `MuxBackendSelectionFailureV2` 把 requested/effective/source/platform gate/capability ref/failure reason 放进同一结果，足以支撑 roadmap §4.2 的 resolver contract。
- `CMD-006` 明确缺 upstream evidence、stop/needs-upstream-issue、blocked/failed verdict、failure_class 非 none、blocking gaps、未归类 status 或 `unknown` 时必须出现 Herdr native blocked fixture/result，且不得以 tmux/rmux fallback success 通过。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只建立 V2 contract/fake/resolver diagnostics，不实现 production Herdr socket client，不迁移 ccbd durable state，不改变 provider runtime 或 doctor/support tier。
- implement 需要重点遵守：CMD-005/CMD-006 是 core guard；实现阶段必须补 `herdr-capability-blocked-fixture.json` 或等价 blocked result，否则缺上游 spike evidence 时不能绿灯。
- code review / QA / acceptance 需要重点复核：合法 Herdr V2 字面量不应被误禁；production Herdr client/adapter/schema parser、provider runtime、ccbd state、package/doctor/support 越界必须 fail closed。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 至 AC-010，并映射 step、证据类型和命令 / 动作。 | none |
| DoD Contract | pass | E | design §3.4 覆盖 design、implementation、review、QA、acceptance DoD、validation commands 和 required artifacts。 | implementation 补齐 V2 tests 与 blocked fixture。 |
| Steps and checks traceability | pass | E | checklist steps/checks 均可追溯到 AC / DOD / 明确不做；YAML 校验通过。 | none |
| Roadmap contract compliance | pass | E | roadmap §4.2/§4.3 要求 Herdr 不伪装 tmux-family；design 明确 `herdr-native`、`herdr` selection/failure 与 fake contract fixture。 | none |
| Module interface design | pass | C | 现有 `mux_backend_contract.py` 小协议、`fake_mux_backend.py`、`backend_resolver.py` 和 tests 支撑 V2 扩展边界。 | 后续 `herdr-backend-client` 设计 production adapter。 |
| Validation and artifacts | pass | E | CMD-005 覆盖 modified/staged rename-copy/staged content/untracked scope guard；CMD-006 覆盖 upstream evidence fail-closed。 | implementation 必须创建 blocked fixture/result。 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 上游 `.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/herdr-contract-spike-evidence.json` 当前不存在；这是实现阶段事实产物。CMD-006 已设计为缺 evidence 时必须要求 Herdr blocked fixture/result。
- 当前 feature 还没有实现代码、V2 tests 或 blocked fixture；这些是 implementation 阶段必交付物，不阻塞 design review。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop；本 child design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: first-round FDR-001、FDR-002、FDR-003、FDR-004；second-round FDR-001、FDR-003；third-round FDR-001 与 doctor/support guard finding；fourth-round staged content guard finding。
- Attributed delta: 增加 `HerdrFailureReasonV2`、`MuxBackendSelectionV2`、`MuxBackendSelectionFailureV2`；明确 `socket_path` / `none` legacy 来源；收紧 CMD-005 到 path + content 双 guard；收紧 CMD-006 到 blocked fixture/result fail-closed。
- Verification: design/checklist/review YAML 均通过；roadmap items YAML 通过；CMD-005 当前执行通过；round 9 independent reviewer 返回 `passed`。
- Classification: 多轮修订均为 design/checklist 契约和 validation guard 补强，没有进入 implementation，没有改变本 feature 不实现 production Herdr client、provider runtime、ccbd durable state、package/doctor/support 的范围边界。
