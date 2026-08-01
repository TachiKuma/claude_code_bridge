---
doc_type: feature-acceptance
feature: 2026-07-20-ccbd-control-plane-transport-seam
status: passed
audit_state: completed
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: approval-report.md#goal-acceptance
accepted: 2026-07-20
round: 1
---

# ccbd 控制面 transport seam 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：2026-07-20
> 关联方案 doc：`.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-design.md`

验证证据来源：`{slug}-qa.md` round 2（status: passed）+ 本次 final audit 抽样复核。Goal 授权：`goal-state.yaml` `acceptance_authorization_ref: approval-report.md#goal-acceptance`，且同 unit `approval-report.md` `approvals.goal-acceptance: approved`。feature 代码已提交于 `83897b79`；越界 Windows-compat 改动已拆出（见 approval-report Decision History 2026-07-20 与 `pending-split/`）。

## 1. 接口契约核对

对照方案第 2.1 节名词层：

**接口示例逐项核对**：
- [x] `CcbdEndpoint`/`EndpointRef`（`lib/ccbd/control_plane_transport/endpoint.py`）：`kind`/`address`/`legacy_socket_path` 投影 → 代码实际：canonical endpoint record + legacy `socket_path` fallback，QA-003 覆盖，一致。
- [x] `ControlPlaneConnection` protocol（`interface.py`）：`settimeout`/`sendall`/`recv`/`close`/context-manager → fake connection 覆盖 `settimeout` 与 `__enter__/__exit__` close，QA-003/checklist check #2 覆盖，一致。
- [x] `ControlPlaneListener` protocol（`interface.py`）：`endpoint`/`accept`/`close` + `fileno()`（Unix bootstrap `select.select()` 需要）→ unix adapter listener 实现 `fileno()`，review learning 已锁定，一致。

**名词层"现状 → 变化"核对**：
- [x] client `connect_socket(path)` → `connect_endpoint(endpoint)`：旧 path 自动投影为 Unix endpoint，`socket_client_runtime/transport.py` 委托 seam，AC-001 regression 通过。
- [x] server `listen_server()` → `transport_factory.listen(endpoint)`：`socket_server_runtime/lifecycle.py` 委托 listener adapter，AC-002 通过。
- [x] bootstrap self-ping → adapter probe/evidence：`bootstrap_probe.py` 委托 seam，AC-003 通过。

**流程图核对**（第 2.2 节 mermaid）：
- [x] 图中节点/调用关系均有代码落点（grep 确认）：`control_plane_transport` 被 `socket_client_runtime/transport.py`、`socket_server_runtime/{lifecycle,bootstrap_probe,server}.py` 引用；endpoint projection → factory → connect/listen → accept/bootstrap/loop → `handle_connection` 链路完整。

无偏差。

## 2. 行为与决策核对

**需求摘要逐项验证**：
- [x] transport seam 建立、Unix adapter 行为不漂移：CMD-003/004（`37 passed, 5 skipped`）、CMD-005 AF_UNIX lifecycle set（`42 passed, 15 skipped`）实测，Unix 用例在支持平台运行、Windows 平台 skip。
- [x] fake transport 驱动 lifecycle/bootstrap/client 不需真实 socket：`test_ccbd_control_plane_transport_fake.py` 通过。
- [x] JSON-line frame/handler dispatch 不变：review §4 praise 确认 `RpcRequest`/`RpcResponse` frame 与 handler dispatch 未漂移。

**明确不做逐项核对**（第 3.2 节反向核对项）：
- [x] 未实现 Windows TCP loopback / token handshake / ACL / named pipe：grep 无 `tcp_loopback` adapter 实现；import guard `no_windows_tcp_adapter` 通过。
- [x] 未改 RPC op/handler dispatch/frame schema：import guard `no_rpc_handler_change` 通过；review praise 确认。
- [x] 未修 `process_exists()` / keeper pid liveness：`system.py` 的 AF_UNIX 出现为既有 Unix-only helper（design §0 声明不改），diff 未触碰 pid liveness。
- [x] 未改 mux backend / provider runtime：checklist check #8 覆盖，diff 未触碰。

**关键决策落地**：
- [x] D1 端口式接口（不暴露 socket object）：`interface.py` 用 Protocol 表达，caller 不需知 AF_UNIX/inode。
- [x] D4 bootstrap transport-neutral primitive：adapter 提供 probe/readiness pump，fake 无需真实 socket。
- [x] D5 stale cleanup 属 adapter：unix adapter 保留 `stat.S_ISSOCK`/connectable proof/inode identity，AC-002 通过。
- [x] D6 endpoint discovery/store 归 transport boundary：`endpoint.py`/`factory.py` 承担，CLI 无平台判断散落。

**挂载点反向核对（可卸载性）**——对照第 2.3 节：
- [x] 10 个挂载点清单条目均有代码落点：5 个 `control_plane_transport/*` 文件存在；`socket_client_runtime/transport.py`、`socket_server_runtime/{lifecycle,bootstrap_probe,loop,server}.py`、mounted lease/diagnostics payload 均委托 seam。
- [x] **反向 grep**：`AF_UNIX` 在 `lib/ccbd/` 源码仅出现于 `control_plane_transport/unix.py` 与既有 `system.py`（清单外引用 = `system.py`，属 design §0 声明的既有 Unix-only helper，非本 feature 新增，不构成漏记）。
- [x] **拔除沙盘推演**：移除 `control_plane_transport/` 后，client/server/bootstrap 的 seam 委托会失去实现 → 说明 seam 是真实边界而非空壳；无残留裸 socket 调用层依赖。

## 3. 验收场景核对

对照第 3 节关键场景清单（证据来源：QA round 2 Verification Matrix + final audit 抽样）：

- [x] **AC-001** 旧 socket_path client connect 投影为 Unix endpoint：regression 通过（QA-003）。
- [x] **AC-002** Unix server listen + stale cleanup：unit/regression 通过（QA-003/005，live socket 不被替换、stale 安全删除）。
- [x] **AC-003** bootstrap readiness probe：self-ping nonce/bootstrap-gate/deferred connection/overflow close 保持（QA-004）。
- [x] **AC-004** fake transport lifecycle：不创建真实 AF_UNIX 也跑通 listen/connect/accept/handler（QA-003）。
- [x] **AC-005** frame protocol 不变：unit/regression 通过（QA-003/004，review praise 确认）。
- [x] **AC-006** endpoint discovery/diagnostics：endpoint store/factory 从 descriptor 或 legacy socket_path 构造，lease/ping/doctor payload 含 endpoint kind/address 且保留 socket_path（QA-003 直接 projection 证据）。
- [x] **AC-007** control-plane 调用层无新增裸 AF_UNIX：grep guard + import guard 通过（QA-007）。
- [x] **AC-008** scope guard：diff guard，未改 pid liveness/Windows token/mux backend/provider runtime/handlers（QA-007）。

**功能性前端**：本 feature 无 UI，用运行验证替代，无需浏览器核对。

**review 报告重点复核**：
- [x] `{slug}-review.md` §5 Test And QA Focus 逐条覆盖（endpoint canonical-first、legacy fallback、Unix listener `fileno()`/bootstrap path、fake nonce/closed/connectability、lease/ping/doctor projection）→ 均由 QA round 2 覆盖。
- [x] `{slug}-review.md` §6 residual risk 逐条处理：Windows CMD-005 fcntl → owner document-baseline 接受；真实 Unix AF_UNIX → compatibility residual，两者在 QA residual-risk 明确留档。
- [x] review §4 suggestion（fake one-shot listener restart）：非阻塞，留作后续 fake restart lifecycle 测试增强，记入第 9 节遗留。

**QA 报告重点复核**：
- [x] 验证证据来源：`{slug}-qa.md` round 2（passed）。
- [x] QA Verification Matrix 覆盖 design 关键场景与 review QA focus。
- [x] feature 性质（mixed）与核心证据说明合理：核心功能路径有运行证据；CMD-005 supporting 抽样为 owner-accepted document-baseline，AF_UNIX 为 compatibility residual。
- [x] failed / blocked 项为 none。
- [x] residual-risk 逐条处理，未承载核心验收缺口。
- [x] Evidence pack、DoD Results、Gate Results 已复核；blocking DoD 均有 pass evidence（CMD-005 document-baseline 经 owner 接受）。

## 4. 术语一致性

对照第 0/2.1 节命名 grep：
- `control_plane_transport` / `EndpointRef` / `PeerEvidence` / `StaleCleanupResult` / `BootstrapProbe`：代码命中一致 ✓
- 防冲突：control-plane transport 只承载 JSON-line RPC，未与 tmux/Rmux mux transport 混用；`AF_UNIX` 未泄漏到调用层 ✓

无不一致。

## 5. 领域影响盘点（提示而非代写）

- **结构性选择**（满足 ADR 3 判据：难回退 + 不显然 + 真权衡）→ `requirements/adrs/` 候选：新增 `ccbd/control_plane_transport` 作为 ccbd 控制面唯一 transport 边界，端口式 Protocol 接口 + Unix adapter + fake 替身，是跨模块接口模式选型；后续 Windows TCP loopback 必须消费本 seam。**建议走 `cs-domain` 记 ADR**（roadmap §4.9 已有方向记录，可据此补正式 ADR）。
- **流程级约束** → ADR 候选：包装 socket 后若继续 `select.select()`，listener protocol 必须含 `fileno()`（review learning）。建议在 ADR 或 compound 中沉淀。
- **新名词** → `requirements/CONTEXT.md` 候选：`EndpointRef` / control-plane transport seam 术语；建议 `cs-domain` 评估是否登记。

本节仅登记 + 建议，不在 accept 内改 CONTEXT.md 或写 ADR。

## 6. requirement delta / clarification 回写

design frontmatter `requirement:` 为空；本 feature 是 ccbd 内部控制面 transport seam 抽取，不新增用户可感能力、不改边界/用户故事/pitch。→ **无 requirement 影响**，跳过。

## 7. roadmap 回写

design frontmatter `roadmap: windows-rmux-native-backend` / `roadmap_item: ccbd-control-plane-transport-seam`，两字段成对存在：
- [x] `items.yaml` 找到 `slug: ccbd-control-plane-transport-seam`，当前 `status: in-progress` + `feature: 2026-07-20-ccbd-control-plane-transport-seam` 核对无误。
- [x] 改 `status: done`，`validate-yaml.py` 校验通过（见 §10 final audit）。
- [x] 同步 `windows-rmux-native-backend-roadmap.md` 子 feature 清单对应条目状态。

## 8. attention.md 候选盘点

- 候选 1：本机原生 Windows 缺 `AF_UNIX`，且 `mobile_gateway.terminal -> import fcntl` 会阻断 v2 测试 collection —— 已在 memory/windows-native-env 记录，且属独立 split feature 修复范围，**不重复入 attention.md**。
- 其余无"每个 feature 都会撞一次"的新环境/工具/工作流候选：写"本 feature 未暴露需要新增到 attention.md 的内容"。

知识出口分流：结构性 seam 决策 → §5 已建议 `cs-domain`；`fileno()` 约束 → 建议 compound/ADR。

## 9. 遗留

- 后续优化点：fake transport 当前为 one-shot listener；若后续需要 `shutdown()->listen()` 重启同一 fake，可增加 fake one-shot / restart contract 测试（review §4 suggestion，非阻塞）。
- 已知限制：
  - CMD-005 完整 start/ping/doctor 抽样在本机仍因 `mobile_gateway.terminal -> import fcntl` collection baseline 无法执行；owner 已按 document-baseline 接受，修复在独立 feature `windows-runtime-import-lock-compat`。
  - 真实 Unix AF_UNIX bootstrap/lifecycle/stale-cleanup 在本机为 skip，属 compatibility residual，待 Unix CI/真机复跑。
  - native Windows ccbd 真实控制面运行待下一 roadmap item `ccbd-windows-tcp-loopback-transport`（本 feature 刻意不实现 Windows TCP adapter）。
- 实现阶段顺手发现：拆出的 Windows import/locking/atomic 兼容改动越出本 feature scope，已保存至 `pending-split/windows-runtime-import-lock-compat/` 待建独立 feature。

## 10. 最终审计

用最终工作区反查原始设计：

**聚合命令复验**：
- CMD-001 checklist YAML valid → exit 0（re-verified）。
- CMD-002 items YAML valid → exit 0（re-verified，含本次 status 回写）。
- CMD-003 `test_ccbd_control_plane_transport_unix.py test_ccbd_control_plane_transport_fake.py` → 含于 `37 passed, 5 skipped`（re-verified）。
- CMD-004 `test_ccbd_bootstrap_probe.py test_ccbd_socket_server.py test_ccbd_socket_client.py` → 含于 `37 passed, 5 skipped`（re-verified）。
- CMD-005 v2 start/ping/doctor → fcntl collection baseline，owner document-baseline 接受（re-verified 为既有基线）。
- CMD-006 import guard → 含于 `37 passed, 5 skipped`（re-verified）。

**场景抽样复核**：AC-002 stale cleanup、AC-007 AF_UNIX guard 已现场 grep + 测试复核（re-verified）；AC-001/003/004/005/006 依 QA round 2 命令结果（trust-prior-verify）。

**交付物 / 工作区 / diff 清洁度**：
- 交付物齐全：transport package 5 文件、interface、unix adapter、fake、bootstrap seam tests、client/server regression、diagnostics projection tests、import guard、items.yaml 回写。
- `compileall lib/ccbd` exit 0；`git diff --check` exit 0（仅 LF/CRLF 警告）。
- 清洁度：debug/TODO/注释代码/死 import 均 forbidden 且未命中。
- 工作区 feature 外改动（`agent-conventions.md`、`pending-split/`）已归因，**排除在本 feature scoped commit 之外**（见 goal-state resume_note 与 approval-report Decision History）。

**覆盖率诚实标记**：re-verified = 8（CMD-001/002/003/004/006 + AC-002/AC-007 grep + compileall/diff-check）；trust-prior-verify = AC-001/003/004/005/006（依 review round 5 独立 agent+OCR 与 QA round 2）；document-baseline = CMD-005（owner accepted）；compatibility-residual = 真实 Unix AF_UNIX。

**结论**：无未处理缺口。所有 checklist checks → passed。

## Verdict

- Status: passed
- Goal 授权：`ResumeGoalAcceptance approval-report.md#goal-acceptance`，与 goal-state 匹配、approval-report `goal-acceptance: approved`。
- Next：feature status → accepted，`current_feature_index` 1→2，scoped commit（排除 conventions/pending-split），继续 roadmap 下一 item `accelerator-transport-windows-guard`（index 2）。
