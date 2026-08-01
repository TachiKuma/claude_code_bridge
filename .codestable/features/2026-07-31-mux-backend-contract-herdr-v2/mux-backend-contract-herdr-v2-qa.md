---
doc_type: feature-qa
feature: 2026-07-31-mux-backend-contract-herdr-v2
status: passed
runner_state: completed
runner_reason: "契约/resolver 层 feature；QA 以 fresh DoD 命令重跑 + 运行时功能驱动 resolver/contract 关键路径为主，主线程只读验证，未改任何生产/测试代码"
runner_id: ""
tested: 2026-08-01
round: 1
---

# mux-backend-contract-herdr-v2 QA 报告

## Scope

基于当前 diff 对 mux/tmux/rmux/herdr backend contract V2 做只读 QA 验证，覆盖：
`lib/terminal_runtime/{mux_backend_contract,fake_mux_backend,backend_resolver}.py`（新增）、
`test/test_mux_backend_contract.py`、`test/test_terminal_runtime_backend_selection.py`（新增）、
`test/test_herdr_spike_no_production_route.py`。消费输入：design、checklist、code review
（`reviewer: subagent`, passed）、evidence pack、三份 before_review gate 结果
（scope-gate / dod-runner / evidence-pack 均 passed）。QA 不修改代码，仅运行验证与功能驱动。

## QA Matrix

| 维度 | 验证点 | 方法 | 结果 |
|---|---|---|---|
| design 关键场景 | AC-001 tmux/rmux 兼容不退化 | CMD-003 + CMD-004 fresh | passed（34+16） |
| design 关键场景 | AC-006/007 显式/auto Herdr 无 evidence fail-closed | 运行时驱动 resolver | passed（herdr-capability-missing / platform-gate-blocked） |
| design 关键场景 | AC-003/009 windows_beta_gaps / blocking gaps fail-closed | 运行时 + CMD-006 | passed（unsupported-capability；spike guard exit 0） |
| design 关键场景 | AC-008 Native Win x64 直路由 Herdr，非 Windows 保留 tmux/rmux | 运行时驱动 | passed（herdr success；linux→rmux） |
| design 关键场景 | AC-002 Herdr namespace ref 运行时 IPC 约束 | 运行时 make_namespace_ref | passed（ipc_kind=none 被拒 TypeError） |
| DoD commands | CMD-001..006 | fresh 全量重跑 | 全部 exit 0 |
| review QA focus #1 | CMD-003/004 + v2 namespace 无回归 | fresh 重跑 | passed |
| review QA focus #2 | CMD-005 scope + CMD-006 spike fail-closed exit 0 | fresh 重跑 | passed |
| review QA focus #3 | resolver 显式 tmux/rmux/herdr(success) 端到端返回 | 运行时功能驱动 | passed（直接断言 effective_backend） |
| review QA focus #4 | archguard/meta_cc skipped 是否补采 | 评估 | 维持 skipped（见残留风险） |

## Functional Evidence（运行时实际驱动）

以真实模块 `resolve_mux_backend_v2` / `make_namespace_ref` / `capability_statuses_supported`
驱动代表性场景，直接断言返回：

```
[herdr-success]   backend_impl=herdr, effective_backend=herdr, blocked=None, fallback_used=False
[no-evidence]     blocked=True, effective_backend=None, failure_reason=herdr-capability-missing
[beta-gap]        blocked=True, failure_reason=unsupported-capability
[no-platform-gate]blocked=True, failure_reason=platform-gate-blocked
[linux-legacy]    backend_impl=rmux, effective_backend=rmux
[ns-ipc-none]     rejected -> TypeError
[empty-caps]      capability_statuses_supported({}) = False
ALL RUNTIME FAIL-CLOSED / SUCCESS ASSERTIONS PASSED
```

覆盖了 review 指出的 QA focus #3（显式路径端到端返回，此前仅由单测间接覆盖），并对
fix-note 声称修复的三处 fail-open 做了运行时行为核验：空 capability 拒绝、平台 gate 准入分离、
herdr namespace IPC 约束。

## DoD 命令 fresh 结果

- CMD-001 checklist YAML 校验：exit 0
- CMD-002 items.yaml 校验：exit 0
- CMD-003 `pytest test_mux_backend_contract.py test_terminal_runtime_backend_selection.py`：34 passed，exit 0
- CMD-004 `pytest test_v2_project_namespace_backend.py`：16 passed，exit 0
- CMD-005 scope guard：exit 0（无越界路径/内容）
- CMD-006 上游 spike fail-closed guard：exit 0（blocked fixture 与 spike blocking gaps 一致）

## Review QA Focus 关闭

review 交付的 4 条 QA focus 全部验证关闭（见 QA Matrix）。review 的 2 条 info 级观察不阻塞：
①`_has_supported_herdr_capabilities` 在完全缺 ref 时归类为 `unsupported-capability` 而非
`herdr-capability-missing`——QA 运行时确认两条路径均 fail-closed（effective_backend=None），
仅失败分类措辞差异，不影响安全语义，转 acceptance 记为可选后续；②scope-gate.json 快照较当前
工作树略滞后——CMD-005 在当前工作树 fresh 重跑仍 exit 0，属证据快照时序，非缺陷。

## Residual Risks

- `archguard` / `meta_cc` provider 信号维持 `skipped`（配置关闭）。本 feature 为契约/resolver
  层无跨模块架构改动，缺架构漂移/历史模式信号对本 feature 风险低；evidence pack 已如实标注。
  非本 feature 核心验收缺口，不上升为 blocking。
- 本 feature 明确不引入生产 Herdr client / 路由接入 / provider runtime / ccbd 状态迁移；
  scope guard（CMD-005）机器核验无越界。真实 Herdr socket 端到端行为由下游 feature
  `herdr-backend-client` 承接。

## Verdict

**passed** —— design 关键场景、DoD 命令、review QA focus 与运行时 fail-closed/success 行为均有
实际运行证据；无未解决 failed/blocked；残留风险均为非核心且已如实记录。
