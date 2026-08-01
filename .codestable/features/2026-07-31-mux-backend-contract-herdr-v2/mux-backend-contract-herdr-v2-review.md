---
doc_type: feature-review
feature: 2026-07-31-mux-backend-contract-herdr-v2
status: passed
reviewer: subagent
reviewed: 2026-08-01
round: 1
lane_a_state: completed
lane_a_ref: "a1d91368c8b9b285d"
lane_a_reason: "独立 Task agent reviewer 首轮完整独立复审 passed；blocking findings 0，仅 2 条 info 级观察 + archguard/meta_cc provider skipped，均非阻塞并交 QA"
---

# mux-backend-contract-herdr-v2 code review

## Scope

首次独立只读 code review，基于当前工作树 diff（`git status --short` + `git diff`）。审查文件：

- 生产（新增）：`lib/terminal_runtime/mux_backend_contract.py`、`lib/terminal_runtime/backend_resolver.py`、`lib/terminal_runtime/fake_mux_backend.py`
- 测试：`test/test_mux_backend_contract.py`（改）、`test/test_terminal_runtime_backend_selection.py`（新增）、`test/test_herdr_spike_no_production_route.py`（改）
- 证据/契约：design、checklist、evidence pack、`evidence/{scope-gate,dod-results,evidence-pack-results,herdr-capability-blocked-fixture}.json`、fix-note、上游 `herdr-contract-spike-evidence.json`

只读审查，未修改任何生产或测试代码。

## Evidence Pack 与 Gate Results 消费

- **scope-gate.json**：`status=passed`，`changed_files` 仅限 `lib/terminal_runtime/*` 三文件与本 feature 目录；无 provider/ccbd/package 越界。核对通过。
- **dod-results.json**：CMD-001..006 全部 `exit_code=0`；CMD-003 `20 passed`、CMD-004 `16 passed`。CMD-005（scope 越界正则守卫）、CMD-006（上游 spike fail-closed 守卫）均 exit 0。
- **evidence-pack-results.json**：`status=passed`，但 `archguard`/`meta_cc` 两个 provider `skipped`（见下节）。
- **上游 spike 证据交叉核验**：我实际读取 `herdr-contract-spike-evidence.json`，确认 `verdict=partial`、`failure_class=windows-beta-gap`、`blocking_gaps` 非空、command/semantic status 含 `needs_harness`/`unsupported`。据此 CMD-006 `must_block=True`，而 `herdr-capability-blocked-fixture.json`（`blocked=true`、`backend_impl=herdr`、`effective_backend=null`、`fallback_used=false`、`failure_reason=unsupported-capability`）满足 `blocked_ok`。**fail-closed 结论是真实上游证据驱动的，非伪造 supported。**

## fix-note 三处 fail-open 修复核验

fix-note 声称修了 3 个 contract/resolver 层 fail-open，逐一核验为真实且完整：

1. **空 capability 走成功路径** —— `capability_statuses_supported()`（`mux_backend_contract.py:227-245`）现要求 `_REQUIRED_CAPABILITIES_V2.issubset(command_status/semantic_status)`，空 mapping 无法满足 issubset，且额外要求 `not blocking_gaps and not windows_beta_gaps` 与全部值 `== "supported"`。空证据/含 gap/含非 supported 值均 fail-closed。回归 `test_empty_capability_statuses_fail_closed`、`test_capability_statuses_require_herdr_required_keys` 覆盖。✔

2. **平台身份与 gate 准入混淆** —— `resolve_mux_backend_v2()`（`backend_resolver.py:55-94`）已把「是否 win32/x64 身份」（`_is_native_windows_x64`，:222）与「gate 是否准入」（`_has_supported_native_windows_x64_gate`，:237-244，额外要求 `supported is True`、`python_bitness=="64bit"`、`is_wsl is False`）拆开。非 Windows auto 走 legacy tmux/rmux（:65-73），不产生 herdr。回归 `test_mux_backend_resolver_blocks_windows_x64_when_gate_is_not_admitted`（supported=False / 32bit / WSL 三变体）覆盖。✔

3. **herdr namespace ref 无 IPC 约束** —— `make_namespace_ref()`（`mux_backend_contract.py:154-158`）对 `backend_impl=="herdr"` 强制 `ipc_kind in {herdr_socket, tcp_loopback}` 且 `ipc_ref` 非空，拒绝 `ipc_kind="none"`。回归 `test_herdr_namespace_ref_requires_addressable_ipc`（none/socket_path/空 ref 三参数化）覆盖。✔

## 与 Design 一致性

- V2 类型（family/impl/ipc/error/capability/selection）与 design §2.1 契约字段完全对齐；`herdr-native` family、`herdr_socket` IPC、`schema-mismatch` error、`restore_token`、非 tmux pane id 均可表达（AC-001~005）。
- resolver 满足 design §2.2 流程约束：缺 capability → `herdr-capability-missing`（AC-006）；platform gate 不准入 → `platform-gate-blocked`；结构化 blocked report 透传其 `failure_reason`（`backend_resolver.py:116-133`），畸形/非 mapping report 收敛为 `invalid-request`，均不 fallback tmux/rmux success（AC-007）。
- Native Windows x64 auto 直路由 herdr、缺证据即 blocked；非 Windows/WSL 默认不变（AC-008），`test_...preserves_non_windows_auto_legacy_selection` 证实。
- checklist 6 个 step 状态 `done` 与代码/测试一一对应。

## 范围与清洁度

- diff 仅新增 3 个 terminal_runtime 契约文件，**无生产 Herdr client / socket adapter / schema parser / 路由接入**，符合 design「明确不做」。CMD-005 正则守卫在 CI 通过。
- 无 dead import、调试输出、注释代码、TODO（逐文件核对 `__all__` 与 import 使用，全部被引用）。
- 生产代码中 `herdr-native` 字面量仅出现在 `mux_backend_contract.py` 与 `backend_resolver.py`，由 `test_..._surface_is_limited_to_contract_modules` 锁定。

## 测试质量

fail-closed 路径覆盖扎实，非仅 happy path：空 capability、缺平台 gate、错 backend_impl、缺必需 key、`unknown` 状态值、windows_beta_gaps、WSL、32bit、畸形 blocked report、非 mapping report 均有断言。断言强度足够（校验 `blocked/failure_reason/effective_backend/fallback_used`）。fake backend 覆盖 create/split/send/capture/kill + kill 后 fail-closed。

轻微覆盖缺口（非阻塞，交 QA）：resolver 对显式 `requested_backend="tmux"/"rmux"`（`backend_resolver.py:45-53`）与显式 `herdr` 成功路径无直接单测（成功路径仅经 `auto` 覆盖，代码共享）。

## Gate / Provider Warnings 解释

- `archguard` 与 `meta_cc` 两个 provider 均 `skipped`（配置关闭），evidence pack §5 已如实标注。**影响**：本 pack 仅反映本地 gate 与聚焦测试，缺架构漂移/历史模式的 provider 信号；对本 feature（纯内部契约、无跨模块拓扑改动）风险低，但架构层无独立第三方背书，QA 应知悉。
- 其余 gate（scope-gate、dod-runner、evidence-pack）无 blocking、无 warning。

## Findings

无 blocking finding。以下为非阻塞观察（info 级）：

- **[info] 缺 evidence ref 的失败归类偏泛** —— `_has_supported_herdr_capabilities`（`backend_resolver.py:247-269`）在能力齐全但无 `capability_report_ref`/`source_ref` 时返回 `unsupported-capability` 而非语义更贴切的 `herdr-capability-missing`。仍是 fail-closed，仅诊断措辞不精确。
- **[info] scope-gate.json 快照略滞后于当前工作树** —— 该 JSON 的 `changed_files` 未含现存 `goal-state.yaml`、`笔记.md`、`.codestable/issues/...`、reviewer.md 等改动；但这些均为文档/roadmap 回写，且 CMD-005 对 lib/package 的实时守卫通过，故非代码缺陷，仅证据快照时点问题。

## Test And QA Focus

交 QA 实际运行验证的点：

1. 复跑 CMD-003/004：`python -m pytest -q test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py test/test_v2_project_namespace_backend.py`，确认无回归。
2. 复跑 CMD-005 scope 守卫与 CMD-006 上游 spike fail-closed 守卫，确认当前工作树（含新增 issues/ 与 docs 改动）仍 exit 0。
3. 补验 resolver 显式 `tmux`/`rmux`/`herdr`(success) 路径的端到端返回（当前单测覆盖间接）。
4. 确认 archguard/meta_cc skipped 是既定策略而非误关；如需架构背书，QA/accept 阶段决定是否补采。

## Verdict

**passed** —— 三处 fail-open 修复真实、完整、有针对性回归；契约/resolver fail-closed 语义与 design 一致，范围干净无生产 Herdr client 越界，上游 spike 证据交叉核验为真实 blocked 驱动。无 blocking finding；两条 info 级观察与 provider skipped 说明留档，交 QA 跟进。
