---
doc_type: feature-design-review
feature: 2026-07-31-herdr-backend-client
status: passed
review_state: passed
review_reason: ""
reviewer_id: subagent
reviewed: 2026-08-01
round: 4
---

# herdr-backend-client feature design 审查报告（round 4）

## 1. Scope And Inputs

本轮针对 v8.5.2 `source-facts-alignment` 修订，验证 design 的「仓库事实」假设是否与当前分支
`codestable/windows-native-herdr-ccb-v852-source` 真实树一致，以及修订是否仍 implementation-ready。

- Design：`.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-design.md`
- Checklist：`.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-checklist.yaml`
- 上一轮 review：`herdr-backend-client-design-review.md`（round 3 passed，但基于 rmux 存在的旧树）
- 已落地依赖：`lib/terminal_runtime/mux_backend_contract.py`、`backend_resolver.py`、`fake_mux_backend.py`
- 实际 ABC / factory：`backend_types.py`、`api.py`、`api_selection.py`、`backend_selection.py`
- ccbd namespace backend 公共操作：`lib/ccbd/services/project_namespace_runtime/backend.py`

### Independent Review

- 独立执行：本 subagent 独立读全部输入 + 实跑核心 CMD（见下），未沿用 round 3 结论。
- round 3 的「Code facts checked」列含 `rmux_backend.py` / `rmux_backend_runtime/capabilities.py` /
  `test_rmux_backend_core.py`，即 round 3 是在 rmux **存在**的树上审查——这正是本次 handoff 的根因。
  本轮全部基于 rmux **不存在**的当前树复核。

## 2. 修订核验（逐条对 5 个重点给证据）

### 2.1 仓库事实正确性 — 准确（1 处 trivial nit）

- `find lib/terminal_runtime -name '*.py' | grep rmux` → 空。**无** `rmux_backend.py`，
  `rmux_backend_runtime/` 目录仅含 `__pycache__/`（无任何 `.py`）。design §0/§2.1/§2.5 改用
  `tmux_backend.py + tmux_backend_runtime/*` 作结构 analog，正确。
- `test/test_rmux_backend_core.py` 不存在（`ls` 报 No such file）。✓
- V2 contract 已落地于 `mux_backend_contract.py`：`MuxNamespaceRefV2`/`MuxPaneRefV2`/
  `MuxCapabilitiesV2`/`MuxCommandErrorV2`、`herdr-native` family、`herdr_socket` ipc、
  `schema-mismatch` category、`capability_statuses_supported` fail-closed 判定，全部在位。✓
- factory 确仅 tmux：`api_selection.py` 全线程化 `tmux_backend_factory`；`TerminalBackendSelection`
  只在 `selected == 'tmux'` 时构造；`api.py` `get_backend` 传 `tmux_backend_factory=TmuxBackend`。✓
- nit（N1）：§0 line 29「仅遗留 stale `__pycache__/rmux_backend.pyc`」低估了残留 pyc——实际还有
  `rmux_backend_runtime/__pycache__/{client,capabilities,errors,io,namespace,...}.pyc` 及
  `rmux_daemon_contract/rmux_runner/rmux_packaging_support` pyc。核心断言（无 production `.py`）为真，
  仅括注不完整，不影响结论。

### 2.2 CMD-005 可跑 — 通过

- `CMD-005: pytest test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py`
  → **34 passed**。两个引用文件均存在。✓
- 旁证：`CMD-003`（`-k "V2 or herdr"`）→ 8 passed；`CMD-001`/`CMD-002`（YAML）→ passed；
  `CMD-006`（scope guard）→ 当前树 no forbidden paths。
- `test_tmux_backend.py` 预存失败已核实：`1 failed`（`test_tmux_backend_run_strips_outer_tmux_environment`，
  断言 `\dev\null != /dev/null`——纯 Windows 路径分隔符/GBK 平台 artifact，与 Herdr 无关）。design §2.4 S6
  声明它「另有预存 env 失败，不作基线」，且 CMD-005 **不**包含该文件——决定合理，无异议。

### 2.3 factory 接线意图 vs 实际 ABC / resolver — 意图可实现，但接线描述需澄清（见 F-1）

- 关键更正：本仓库存在**两套 backend surface**：
  1. 薄 `TerminalBackend` ABC（`backend_types.py`：`send_text(pane_id,text)`/`is_alive`/`kill_pane`/
     `activate`/`create_pane`）——`api.py get_backend()→TerminalBackend`、`TmuxBackend` 实现的 legacy 面。
  2. V2/MuxBackend 面——`FakeMuxBackend`（`fake_mux_backend.py`）已实现的
     `create_session/restore_session/create_pane/split_pane/send_text/capture_pane/kill_pane`（over
     `MuxNamespaceRefV2`/`MuxPaneRefV2`/`MuxOperationEvidenceV2`），以及 ccbd
     `project_namespace_runtime/backend.py` 的 `prepare_server/create_session/session_root_pane/split_pane`。
- design §2.1 的 `HerdrBackendClient` Protocol 与 public↔internal mapping 表**精确对应**已落地的
  `FakeMuxBackend` 形状与 ccbd namespace 操作——grounding 扎实，implementation-ready。
- `resolve_mux_backend_v2`（`backend_resolver.py`）返回 **selection dict**（非 backend 实例），且与
  `api_selection.py` 的 `TerminalBackendSelection`（基于 `detect_terminal_fn`）**互相独立**。design 的
  gated-route/blocked 语义在 resolver 层已由 green tests
  （`test_terminal_runtime_backend_selection.py` 的 `test_mux_backend_resolver_*`）覆盖。
- 因此 design 说「HerdrBackend 实现 MuxBackend V2 surface」比 parent 转述的「实现 TerminalBackend ABC」
  更贴合真实代码——HerdrBackend **不应**去实现薄 ABC。

### 2.4 design 完整性 — 自洽，无新矛盾

- AC-001~010、Acceptance Coverage Matrix、DoD（DOD-IMPL-000~005）、CMD-001~007、scope guard
  （CMD-006 路径 + CMD-007 内容）相互可追溯；修订未引入互斥项。
- checklist 7 steps / 11 checks / dod.commands 与 design 对齐；YAML 校验通过。

### 2.5 残留 rmux 提及 — 基本正确（1 处 stale co-reference，N2）

- analog 已完全切换到 tmux（§2.1「无 rmux capability gate 可复用」、§2.5「tmux backend 是主要结构类比」），
  无任何把 rmux production 模块当可复用 analog 的残留。✓
- rmux 仅出现在正确语境：§0 声明不存在；§3.2 forbidden-fallback；CMD-006 forbidden
  `rmux_packaging_support.py/.json`；contract 层 `RequestedBackendV2`/`BackendImplV2` 仍合法枚举 `rmux`。
- nit（N2）：AC-009 与 checklist step 7 / AC-009 check 写「保持现有 **tmux/rmux** behavior」「现有
  **tmux/rmux** selection/contract tests」。本分支既无 rmux backend 也无 rmux 测试，「rmux tests」是 stale
  co-reference（「rmux behavior」在 resolver 枚举层尚可辩护，但测试层不成立）。与 design 自身已更正的事实轻微
  不一致，非阻塞。

## 3. Findings（按严重度）

### blocking

- 无。

### important

- **F-1（factory 接线描述需澄清，非阻塞）**：§2.1 line 93 / §2.5 line 219 称在
  `api.py`/`api_selection.py` 新增 `herdr_backend_factory`「与 `tmux_backend_factory` 并列，由
  `resolve_mux_backend_v2` selection 决定构造哪个」。但 `api.py get_backend()` 类型为
  `Optional[TerminalBackend]` 且 `TerminalBackendSelection` 走 `detect_terminal_fn`（无 platform_gate/
  capability_report 输入），与 `resolve_mux_backend_v2` 完全脱钩；HerdrBackend 又是 V2/MuxBackend 面而非
  薄 `TerminalBackend`。「并列」措辞可能误导实现者把 HerdrBackend 塞进 `TerminalBackendSelection.get_backend`
  造成类型面不匹配。
  - 不阻塞理由：正确路径（V2-aware selection 消费 `resolve_mux_backend_v2` → 构造 `FakeMuxBackend` 形状的
    HerdrBackend）已被已落地的 resolver + fake backend + green tests 充分支撑；真实 consumer（ccbd
    namespace lifecycle）显式 out-of-scope，本 child 无任何运行路径要求 HerdrBackend 满足薄 ABC；ACs 均可在
    现有 green 的 resolver + fake-socket unit seam 上证伪。
  - 实现期建议（非 design gate）：新增的是**独立 V2 选择/构造入口**，明确 HerdrBackend 实现 V2/MuxBackend 面
    （analog：`FakeMuxBackend` + `project_namespace_runtime/backend.py`），legacy `get_backend()→TmuxBackend`
    路径不改；并在实现中明确 `platform_gate`/`capability_report` 的来源与到构造分支的桥接。

### nit

- **N1**：§0「仅遗留 stale `__pycache__/rmux_backend.pyc`」低估残留 pyc 集合（见 §2.1）。
- **N2**：AC-009 / checklist step 7 与 AC-009 check 的「tmux/rmux behavior/tests」stale co-reference（见 §2.5）；
  建议改为「tmux behavior / tmux selection/contract tests」，rmux 仅保留在 resolver 枚举语境。

### suggestion / learning

- learning：production adapter child 的「仓库事实」必须绑定实现分支复核——round 3 在 rmux 存在的树 passed，
  切到 no-rmux 分支即失效；design-review 的 code-facts 快照应记录所依据的分支。

### praise

- `HerdrBackendClient` Protocol 与 public↔internal mapping 表与已落地 `FakeMuxBackend` 形状逐字对齐，
  raw Herdr JSON 不外露、缺 evidence/stop/blocking/unknown fail-closed、Herdr agent state 不作 completion
  authority——adapter 隔离与 fail-closed 语义扎实。

## 4. Evidence Confidence Ledger

| Check | Verdict | Class | Basis |
|---|---|---|---|
| rmux/test 非存在 | pass | E | `find`/`ls` 直接核实无 production `.py`、无 `test_rmux_backend_core.py` |
| V2 contract 落地 | pass | E | `mux_backend_contract.py` 全类型 + herdr-native/herdr_socket/schema-mismatch |
| factory 仅 tmux | pass | E | `api_selection.py`/`backend_selection.py`/`api.py` 只线程化 tmux |
| CMD-005/003/001/002/006 | pass | E | 实跑 green（34/8 passed；YAML pass；scope guard clean） |
| tmux_backend 预存失败排除 | pass | E | 实跑 `1 failed`（\dev\null 路径 artifact），未纳入 CMD-005 基线 |
| HerdrBackend 目标面 | pass | C | `FakeMuxBackend` + ccbd `backend.py` 支撑 V2 面；mapping 表对齐 |
| factory 接线描述 | concern | C | resolver 与 `TerminalBackendSelection` 脱钩；「并列」措辞含糊（F-1，非阻塞） |

## 5. Verdict

- Status: **passed**
- 结论：v8.5.2 修订已把 design 的仓库事实与当前 no-rmux 分支对齐——rmux backend/test 非存在、V2 contract
  已落地、factory 仅 tmux，全部核实准确；CMD-001/002/003/005/006 实跑 green；`test_tmux_backend.py` 预存失败
  排除决定合理。design 的 HerdrBackend 目标面（V2/MuxBackend）由已落地 `FakeMuxBackend` grounding，
  implementation-ready。无 blocking。
- 携带项（不阻塞进入实现）：F-1 factory 接线澄清、N1/N2 两处 stale co-reference，建议实现期一并处理。
- Next：回到 `cs-epic` child design batch loop；本 child design 保持 `draft`。
