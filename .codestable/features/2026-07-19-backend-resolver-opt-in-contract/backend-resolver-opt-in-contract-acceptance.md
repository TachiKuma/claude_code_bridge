---
doc_type: feature-acceptance
feature: 2026-07-19-backend-resolver-opt-in-contract
status: passed
audit_state: completed
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: approval-report.md#goal-acceptance
accepted: 2026-07-22
round: 1
---

# backend-resolver-opt-in-contract 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：2026-07-22
> 关联方案 doc：`.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-design.md`

## 1. 接口契约核对

**接口示例逐项核对**

- [x] `RuntimeMuxConfig`：`runtime.mux.backend` 只接受 `tmux` / `rmux` / `auto`，默认 `tmux` 且 `explicit_backend=false`。代码落点：`lib/agents/models_runtime/config_runtime/project.py`、`lib/agents/config_loader_runtime/parsing_runtime/runtime_mux.py`。
- [x] `MuxBackendSelection` / `MuxBackendSelectionFailure`：success schema 包含 `backend_impl`、`requested_backend`、`effective_backend`、`source`、`fallback_used`、`route_approval_ref`、`capability_report_ref`、`diagnostic`；failure 独立为 typed diagnostics。代码落点：`lib/terminal_runtime/backend_resolver.py`。
- [x] `TerminalBackendSelection.select_backend()`：通过 resolver 返回结构化选择结果，`get_backend()` 按 `effective_backend` 实例化 tmux/rmux factory。代码落点：`lib/terminal_runtime/backend_selection.py`。
- [x] diagnostics surface：doctor、ping、foreground attach 能展示 backend selection 摘要。代码落点：`lib/cli/services/backend_selection_diagnostics.py`、`lib/cli/render_runtime/ops_views_doctor.py`、`lib/cli/services/start_foreground.py`、`lib/ccbd/handlers/ping_runtime/payloads.py`。

**名词层“现状 -> 变化”逐项核对**

- [x] `backend_selection.py` 不再只有裸 `selected == "tmux"` 分支；resolver policy 已收敛到 `backend_resolver.py`。
- [x] `ProjectConfig` 新增 `runtime_mux`，`to_record()` 仅在显式配置时输出 `runtime.mux`，避免把默认 tmux 伪装成用户配置。
- [x] 旧 tmux session payload 仍由 `get_backend_for_session()` 兼容 `tmux_socket_name` / `tmux_socket_path` / `tmux_session`。

**流程图核对**

- [x] config/env/platform/route/capability 到 selection result 的路径均有代码落点；route/capability/availability 通过可注入 reader 实现，不在 resolver 内运行 probe。

## 2. 行为与决策核对

**需求摘要逐项验证**

- [x] 无配置、无 env 时默认 tmux：`test_mux_backend_default_selects_tmux_without_fallback` 覆盖。
- [x] 显式 `rmux` 缺 approval 时 fail-fast：`test_mux_backend_explicit_rmux_fails_fast_without_route_approval` 和 namespace backend fail-fast tests 覆盖。
- [x] `auto` fallback 带原因：`test_mux_backend_auto_fallback_records_reason` 覆盖。
- [x] approved route + available rmux 选择 rmux 且不实例化 tmux：`test_mux_backend_approved_rmux_uses_rmux_factory_only` 覆盖。
- [x] doctor/ping/foreground attach 输出 selection diagnostics：`test_backend_selection_diagnostics.py`、`test_v2_ccbd_ping_runtime.py` 覆盖。

**明确不做逐项核对**

- [x] 未在本 feature 内实现 Rmux backend core 语义；本 feature 只消费现有或注入的 rmux factory。
- [x] 未迁移 provider session canonical payload；旧 tmux 字段仍保留，backend-neutral provider session 留给后续 feature。
- [x] resolver 不运行 Rmux probe，也不复制 capability artifact payload；只读 route approval / summary ref。
- [x] 未把 Rmux 宣称为 supported，也未改 packaging/docs 支持级别。

**关键决策落地**

- [x] success/failure schema 分离：`MuxBackendSelectionError.to_diagnostics()` 返回 failure payload，success schema 不 nullable。
- [x] explicit `rmux` 与 `auto` 语义分离：explicit 不 fallback，auto 可 fallback 且必须记录原因。
- [x] 优先级符合设计：CLI > project config > user config > env > platform default；对应 resolver matrix 已跑通。

**挂载点反向核对**

- [x] `lib/terminal_runtime/backend_resolver.py`、`backend_selection.py`、`api.py`、`api_selection.py` 是 resolver/API 挂载点。
- [x] `lib/agents/config_loader_runtime/*` 与 `lib/agents/models_runtime/config_runtime/project.py` 是 config schema/model 挂载点。
- [x] `doctor.py`、`ping.py`、`ops_views_doctor.py`、`start_foreground.py`、ccbd ping payload 是 diagnostics 挂载点。
- [x] `rg` 复核命中均落在 design 第 2.3 节清单的 terminal runtime、config、diagnostics、tests 范围内；未发现需要追加的新生产挂载点。
- [x] 拔除沙盘推演：移除 resolver/config/diagnostics/test 清单条目会直接破坏对应 AC-001..AC-008 测试，无隐藏残留入口。

## 3. 验收场景核对

- [x] AC-001：无配置、无 env -> effective backend 为 tmux，fallback_used=false。证据：`test/test_terminal_runtime_backend_selection.py`，本轮 28 passed。
- [x] AC-002：project config `runtime.mux.backend=rmux` 且 route approval 缺失 -> typed selection error，不 fallback。证据：resolver 和 namespace backend fail-fast tests。
- [x] AC-003：env `CCB_MUX_BACKEND=auto` 且 route 未批准或 Rmux unavailable -> fallback 到 tmux 且有 reason。证据：resolver test。
- [x] AC-004：route approved 且 Rmux available，requested=rmux -> rmux factory only。证据：resolver test。
- [x] AC-005：v2/v3 config `runtime.mux.backend` 解析一致；未知 runtime 字段 fail-closed。证据：config loader selected tests，23 passed。
- [x] AC-006：doctor/ping 输出 backend selection diagnostics 且保留旧 tmux socket 字段。证据：diagnostics render / ping tests。
- [x] AC-007：`get_backend_for_session()` 继续兼容旧 tmux session payload。证据：old session compatibility tests。
- [x] AC-008：foreground attach selection failure 或 tmux attach payload 缺失时包含 selection summary。证据：foreground attach diagnostics tests。

**review 报告重点复核**

- [x] Review 第 5 节 QA focus 已由 QA-002..QA-006 覆盖。
- [x] Review 第 6 节 residual risk 中 live rmux smoke 明确为后续 `ccbd-windows-full-chain-smoke` 责任，不是本 resolver-contract feature 的核心缺口。

**QA 报告重点复核**

- [x] 验证证据来源：`.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-qa.md`，frontmatter `status: passed`。
- [x] QA matrix 覆盖 design 关键场景、review QA focus、DoD commands、diagnostics/reload chain 和 QA-fix targeted tests。
- [x] failed / blocked 项为 none；non-core exploratory run 的 Windows host 失败已分类为既有 WSL path / token ACL live-start 行为，不承载本 feature 核心验收。
- [x] Evidence pack、DoD Results、DoD Contract Gate、Scope Gate 均为 `passed` 且无 blocking。

## 4. 术语一致性

- `runtime.mux.backend`：代码和测试命中均用于配置 schema / validation / diagnostics，语义一致。
- `CCB_MUX_BACKEND`：仅作为 env override 输入，且不压过 project/user config。
- `MuxBackendSelection` / `MuxBackendSelectionFailure`：命中集中在 resolver、API diagnostics 和测试。
- `backend_selection` diagnostics：doctor/ping/foreground attach 输出字段一致。
- 防冲突：`ccbd` control-plane transport 未混入本 feature；`socket_path` / TCP endpoint 迁移仍属于 transport track。

## 5. 领域影响盘点（提示而非代写）

- [x] 新术语 `runtime.mux.backend`、`MuxBackendSelection`、`MuxBackendSelectionFailure`：建议后续走 `cs-domain` 写入 CONTEXT，因为它们是后续 mux/backend features 的共享语言。
- [x] 结构性选择“backend resolver policy 与 backend factory 分离”：满足 ADR 候选条件（跨模块接口、错误语义稳定、后续难回退），建议后续走 `cs-domain` 记录 ADR。
- [x] 流程级约束“explicit rmux fail-fast、auto fallback 可诊断”：建议后续走 `cs-domain` 或 roadmap ADR 记录，accept 阶段不代写。

## 6. requirement delta / clarification 回写

Design frontmatter `requirement` 为空。本 feature 是 roadmap 内部技术契约和后续实现前置，不直接新增用户可感 capability；无 owner-approved requirement delta 需求。本阶段不写 requirement。

## 7. roadmap 回写

- [x] Design frontmatter 同时包含 `roadmap: windows-rmux-native-backend` 与 `roadmap_item: backend-resolver-opt-in-contract`。
- [x] `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 对应条目已为 `status: done` 且 `feature: 2026-07-19-backend-resolver-opt-in-contract`。
- [x] 本轮同步 roadmap 主文档第 5 节子 feature 清单，将该条从 planned / 未启动改为 accepted / 对应 feature。
- [x] 本轮重新运行 items YAML 校验通过。

## 8. attention.md 候选盘点

本 feature 未暴露需要每次 CodeStable 启动都知道的新环境 / 命令 / 工作流硬约束；无需写入 attention.md。

其他知识出口：

- 可复用技术约束：resolver policy 与 diagnostics 字段建议 `cs-domain` / `cs-keep` 归档。
- 用户指南/API 文档：当前不更新，后续 packaging/docs feature 负责支持级别和用户文档。

## 9. 遗留

- 后续优化点：`backend_selection.py` selection cache key 未包含 route/capability reader 的内容 freshness；review 已标为 future risk，等 route approval 变为运行期可变时再设计 invalidation。
- 已知限制：live Windows rmux foreground smoke 不属于本 feature 核心，后续由 `ccbd-windows-full-chain-smoke` 证明。
- 顺手发现：无需要另开 issue 的 acceptance 缺口。

## 10. 最终审计

- 验证证据来源：`backend-resolver-opt-in-contract-qa.md`。
- Evidence sources：`backend-resolver-opt-in-contract-evidence-pack.md`、`backend-resolver-opt-in-contract-dod-results.json`、`backend-resolver-opt-in-contract-dod-contract-results.json`、`backend-resolver-opt-in-contract-scope-gate-results.json`。
- 聚合命令：
  - `validate-yaml.py --file backend-resolver-opt-in-contract-checklist.yaml --yaml-only` -> exit 0，1 passed。
  - `validate-yaml.py --file windows-rmux-native-backend-items.yaml` -> exit 0，1 passed。
  - `python -m pytest -q test/test_terminal_runtime_backend_selection.py` -> exit 0，28 passed。
  - `python -m pytest -q test/test_v2_config_loader.py test/test_v3_config_loader.py test/test_v2_start_foreground.py test/test_backend_selection_diagnostics.py -k "runtime_mux or foreground or backend_selection"` -> exit 0，23 passed / 168 deselected。
  - `python -m pytest -q test/test_ccbd_reload_apply.py test/test_ccbd_reload_dry_run.py test/test_ccbd_service_graph.py test/test_v2_ccbd_ping_runtime.py` -> exit 0，78 passed。
  - `python -m pytest -q test/test_v2_storage_paths.py::test_socket_placement_payload_uses_posix_path_text` -> exit 0，1 passed。
  - `python -m pytest -q test/test_v2_ccbd_start_flow.py::test_runtime_supervisor_start_persists_startup_report` -> exit 0，1 passed。
  - `git diff --check` -> exit 0。
- 场景复核：re-verified 8 / trust-prior-verify 0。
- 交付物复核：代码 / 配置 / schema / 路由 / diagnostics / roadmap 均通过；requirement 跳过有明确理由。
- 完整工作区复核：写入 acceptance 前 `git status --short` 仅有 CodeStable runtime reference 变更；实现代码已在当前基线，acceptance 写回将新增报告并更新状态文件。
- diff 清洁度：通过；未发现新增 debug 输出、临时 TODO、注释掉代码或死 import。
- 知识沉淀出口：attention 无候选；CONTEXT/ADR/compound 候选已在第 5/8 节分流。
- 结论：通过。
