---
doc_type: feature-qa
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
status: passed
runner_state: completed
runner_reason: "独立 QA runner Banach 返回 blocked 的唯一阻塞是 qa-fix 后 review stale；Round 4 code review 已 passed 后，该阻塞解除。功能证据经主线程核验为 passed。"
runner_id: "019fc320-6f29-7d11-81cf-80f5c10f606e"
tested: 2026-08-02
round: 1
---

# ccbd-herdr-namespace-lifecycle QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design.md`
- Checklist: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-checklist.yaml`
- Review: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-review.md`
- Implementation evidence: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-implementation.md`
- CMD-013 evidence: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/evidence/cmd-013-native-windows-herdr-transcript.md`
- Evidence pack / Gate results / DoD results: none。
- Diff basis: 当前工作区 unstaged/untracked diff；存在大量本 feature 外 dirty diff，QA 结论只覆盖本 feature design、review focus 与可归因验证命令。
- Baseline dirty files: `.codestable`、`lib/`、`test/` 多处历史变更；`provider-runtime-on-herdr-admission-blocked.md` 属于后续 admission，不纳入本 QA 通过范围。
- Feature type: functional。
- Core evidence gate: AC-001 到 AC-013 均要求 unit/integration/static guard/manual transcript 证据；功能性核心路径不能降级为 residual-risk。
- Runner: Banach `019fc320-6f29-7d11-81cf-80f5c10f606e`。runner 功能证据基本通过；原 blocked 原因是 qa-fix 后 review stale，已由 Round 4 review passed 解除。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | checklist CMD-001 | supporting | checklist YAML 合法 | schema | `validate-yaml.py --yaml-only` | YAML valid | pass |
| QA-002 | checklist CMD-002 | supporting | roadmap items YAML 合法 | schema | `validate-yaml.py` | YAML valid | pass |
| QA-003 | AC-001 | core-functional | V2/HerdrBackend/attach capability admission | unit | `test_mux_backend_contract.py test_herdr_backend_client.py -k "V2 or HerdrBackend or attach_namespace or presentation or herdr"` | 前置 surface 通过 | pass |
| QA-004 | AC-002..AC-007 | core-functional | state migration、redaction、V2 helper、ensure/layout/reflow | unit | `test_v2_project_namespace_state.py test_v2_project_namespace_backend.py -k "namespace or mux or herdr or restore_token or redacted or presentation or capability"` | focused tests 通过 | pass |
| QA-005 | AC-008..AC-009 | core-functional | foreground attach Herdr/rmux/redaction | unit | `test_v2_start_foreground.py -k "foreground or attach or herdr or rmux or restore_token or redacted"` | focused tests 通过 | pass |
| QA-006 | AC-010 | core-functional | reload/restart/kill boundary | unit | `test_agent_lifecycle_cli.py -k "reload or restart or kill"` | focused tests 通过 | pass |
| QA-007 | AC-013 | core-functional | forbidden path scope guard | static | CMD-007 Python guard | 无越界路径 | pass |
| QA-008 | AC-013 | core-functional | forbidden content scope guard | static | CMD-008 Python guard | 无 provider/recovery/support/release/user-surface 越界内容 | pass |
| QA-009 | AC-004 | core-functional | public payload restore token redaction | static | CMD-009 Python guard | presence 字段存在，无 public raw token key | pass |
| QA-010 | AC-004/AC-012 | core-functional | project view redaction 与 regression | unit | `test_ccbd_project_view.py -k "namespace or herdr or restore_token or redacted or project_view"` | focused tests 通过 | pass |
| QA-011 | AC-010 | core-functional | reload additive patch V2 primitive | unit | `test_ccbd_namespace_additive_patch.py -k "herdr or mux or namespace_ref or reload or move or reflow"` | focused tests 通过 | pass |
| QA-012 | AC-004 | core-functional | event/log redaction | unit | `test_v2_project_namespace_state.py -k "event or summary_fields or log or restore_token or redacted"` | focused tests 通过 | pass |
| QA-013 | AC-011 | core-functional | Native Windows Herdr lifecycle transcript | manual/static | CMD-013 transcript scan | create/attach/reload/restart deferred/kill present；无 raw token 泄露 | pass |
| QA-014 | review focus | core-functional | reload failure diagnostics redaction | unit | `test_ccbd_reload_apply.py -k "namespace_patch_failure or runtime_mount_defers_provider_runtime_for_herdr_namespace"` | focused tests 通过 | pass |
| QA-015 | review focus | core-functional | Herdr deferred readiness 不误报 T4/T6 | unit | `test_v2_ccbd_start_flow.py -k "runtime_supervisor_start_defers_provider_runtime_for_herdr_namespace or runtime_supervisor_start_records_readiness_timeline"` | focused tests 通过 | pass |
| QA-016 | review focus | core-functional | namespace ref alias/cached ref 隔离 | unit | backend alias focused commands | focused tests 通过 | pass |

## 3. Command Results

- CMD-001 checklist YAML validate → exit 0：1 passed。
- CMD-002 roadmap items YAML validate → exit 0：1 passed。
- CMD-003 V2/HerdrBackend admission → exit 0：174 passed, 12 deselected。
- CMD-004 首跑 → exit 1：1 failed, 59 passed；`test_project_namespace_controller_preserves_herdr_server_session_name` 暴露 qa-fix 缺口。
- CMD-004 最新工作区复跑 → exit 0：60 passed；后续聚合复核为 64 passed。
- CMD-005 foreground attach → exit 0：16 passed。
- CMD-006 reload/restart/kill → exit 0：6 passed, 25 deselected。
- CMD-007 path scope guard → exit 0：未命中 forbidden path。
- CMD-008 content scope guard → exit 0：未命中 forbidden content。
- CMD-009 public payload restore token guard → exit 0：presence 字段存在，public payload 附近未发现 raw `restore_token` 输出。
- CMD-010 project view → exit 0：90 passed。
- CMD-011 reload additive patch → exit 0：26 passed, 11 deselected；Round 4 后聚焦复核为 26 passed。
- CMD-012 event/log redaction → exit 0：8 passed, 32 deselected。
- Review focus reload sanitizer → exit 0：3 passed。
- Review focus Herdr deferred readiness → exit 0：1 passed。
- Backend alias/cached ref 聚焦 → exit 0：5 passed。
- Herdr backend session scope 聚焦 → exit 0：4 passed。
- `git diff --check` → exit 0：仅 line-ending warning，无 whitespace error。
- CMD-013 transcript scan → exit 0：只出现 `namespace_restore_token_present`，未命中 `expected_restore_token` / `actual_restore_token` / raw restore token pattern。

未运行：未重新 live 执行 Native Windows CMD-013。原因是已有同日 transcript 覆盖核心场景；重新运行会创建/启动/停止外部 Herdr session，不符合本轮 QA runner 只读边界。该项不阻塞，因为 transcript 已作为 core manual evidence 被扫描复核。

## 4. Scenario Results

- [x] AC-001 implementation admission：pass。CMD-003 证明 V2 contract、HerdrBackend、attach/presentation surface 有测试证据。
- [x] AC-002..AC-003 state compatibility / Herdr state round-trip：pass。CMD-004 覆盖旧 tmux/rmux 兼容与 Herdr namespace state。
- [x] AC-004 public redaction：pass。CMD-009、CMD-010、CMD-012 和 CMD-013 scan 共同证明 public payload/event/project view/log/transcript 不输出 raw restore token。
- [x] AC-005..AC-007 V2 helper / ensure / layout / reflow：pass。CMD-004 与 backend alias 聚焦测试覆盖 per-operation capability、Herdr ensure/reflow 与 requested/actual session alias。
- [x] AC-008..AC-009 foreground attach：pass。CMD-005 覆盖 Herdr foreground attach path、blocked error 与 rmux regression。
- [x] AC-010 kill/restart/reload boundary：pass。CMD-006、CMD-011 与 CMD-013 覆盖 reload patch、restart deferred、kill。
- [x] AC-011 Native Windows manual transcript：pass。CMD-013 记录 Windows x64、Herdr version、namespace create、foreground attach、reload apply、restart deferred 和 kill。
- [x] AC-012 tmux/rmux regression：pass。CMD-005、CMD-010 与相关 focused regression 未退化。
- [x] AC-013 scope boundary：pass。CMD-007/CMD-008 未命中 forbidden path/content。
- [x] Review QA focus 1：pass。reload namespace patch failure 的 API/stage/CLI redaction 链路经 review focus tests 与 static scan 覆盖。
- [x] Review QA focus 2：pass。Herdr deferred provider runtime 不把 T4/T6 或 `timeline_complete` 误报成功。
- [x] Review QA focus 3：pass。旧 cached namespace ref 不污染新 session V2 helper call 或 state fields。

## 5. Findings

### failed

none。

### blocked

none。runner 原 blocked 项为 review-stale；Round 4 review passed 后已解除。

### residual-risk

- 工作区 dirty diff 很大，QA 结论不代表全工作区通过，只覆盖本 feature 可归因范围。
- OCR-001 `endpoint_store.py::unlink_token` stale token 风险属于前置 Windows transport dirty diff，不归因本 feature。
- Native Windows CMD-013 本轮未 live 重跑；同日已通过 artifact 被扫描复核。

## 6. Cleanliness

- Debug output: pass。
- Temporary TODO/FIXME/XXX: pass。
- Commented-out code: pass。
- Unused imports / dead code from this feature: pass。
- Out-of-scope files: pass；仅对 CMD-007/CMD-008 scope guard 可检测范围负责。

## 7. Verdict

- Status: passed
- Next: 进入 `cs-feat --stage accept`。
