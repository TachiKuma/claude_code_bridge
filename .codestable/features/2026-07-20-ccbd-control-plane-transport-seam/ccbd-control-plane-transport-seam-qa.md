---
doc_type: feature-qa
feature: 2026-07-20-ccbd-control-plane-transport-seam
status: passed
runner_state: completed
runner_reason: ""
runner_id: ""
tested: 2026-07-20
round: 2
---

# ccbd-control-plane-transport-seam QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml`
- Review: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-review.md`（round 5，passed）
- Evidence pack: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-scope-gate.json`
- DoD results: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-dod-results.json`
- Owner decision: `.codestable/roadmap/windows-rmux-native-backend/approval-report.md` Decision History（2026-07-20 拆分 + CMD-005 document-baseline 接受）
- Diff basis: feature 代码已提交于 `83897b79`；当前工作树 diff 仅含本 feature/roadmap 文档改动，无新增 feature 代码。
- Baseline dirty files:
  - `.codestable/reference/agent-conventions.md` — feature 外的全局约定文档改动（放宽 goal driver 可见性/`canSpawnReviewer` 规则），owner 决定保留；与本 feature 代码行为无关，不计入本 feature 归因。
  - `.codestable/roadmap/windows-rmux-native-backend/pending-split/…` — 从本 feature 拆出的越界 Windows-compat 改动的保存物（patch + tests + NOTE），非本 feature 交付面。
- Feature type: mixed。改 ccbd control-plane runtime seam 与 endpoint diagnostics，刻意不改 RPC schema / handler dispatch。
- Core evidence gate: fake transport、endpoint projection、frame/client/server regression、import guard 均有运行证据（round 2 复跑）。本轮相对 round 1 的变化是：越界 Windows import/locking/atomic 改动已拆出为独立 feature（见 approval-report 与 pending-split），CMD-005 的 `mobile_gateway.terminal -> import fcntl` collection gap 经 owner 依 checklist `failure_handling: document-baseline` **单独记录接受**（满足 goal-protocol §3.1 escape hatch）；真实 Unix `AF_UNIX` 主机证据为 compatibility residual。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | DoD CMD-001 | supporting | checklist YAML valid | schema | `python ".codestable/tools/validate-yaml.py" --file "...checklist.yaml" --yaml-only` | valid | pass |
| QA-002 | DoD CMD-002 | supporting | roadmap items YAML valid | schema | `python ".codestable/tools/validate-yaml.py" --file "...items.yaml"` | valid | pass |
| QA-003 | AC-001/004/006 | core-functional | endpoint descriptor, fake transport, lease/lifecycle/inspection/ping projection | unit | `python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_control_plane_transport_fake.py` | pass | pass |
| QA-004 | AC-003/005 | core-functional | bootstrap, server, client regression | unit/regression | `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_server.py test/test_ccbd_socket_client.py` | pass or platform skip only | pass with Windows skips |
| QA-005 | AC-002/003 | compatibility | real AF_UNIX lifecycle/bootstrap/stale cleanup | unit/regression | `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_lifecycle.py test/test_ccbd_socket_server_loop.py test/test_ccbd_socket_client.py` | Unix behavior exercised where platform supports it | residual on Windows skips |
| QA-006 | AC-006 | supporting | start/ping/doctor endpoint projection sample | regression | `python -m pytest -q test/test_v2_start_service.py test/test_v2_phase2_entrypoint.py -k "ccbd or socket or endpoint or ping"` | pass or documented baseline | document-baseline（fcntl collection，owner 已接受） |
| QA-007 | AC-007/008 | core-functional | AF_UNIX boundary, no Windows TCP adapter, no RPC handler scope drift | guard | `python -m pytest -q test/test_ccbd_control_plane_transport_import_guard.py` | pass | pass |
| QA-008 | Cleanliness | supporting | compile, whitespace, debug marker hygiene | static | `python -m compileall lib/ccbd`; `git diff --check`; scope gate | pass | pass |

## 3. Command Results

- `python ".codestable/tools/validate-yaml.py" --file "...checklist.yaml" --yaml-only` → exit 0：valid。
- `python ".codestable/tools/validate-yaml.py" --file "...windows-rmux-native-backend-items.yaml"` → exit 0：valid。
- `python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_control_plane_transport_fake.py test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_server.py test/test_ccbd_socket_client.py test/test_ccbd_control_plane_transport_import_guard.py` → exit 0：`37 passed, 5 skipped`（QA-003/004/007）。
- `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_lifecycle.py test/test_ccbd_socket_server_loop.py test/test_ccbd_socket_client.py` → exit 0：`42 passed, 15 skipped`（QA-005，Windows 上 AF_UNIX 用例 skip）。
- `python -m compileall lib/ccbd` → exit 0。
- `git diff --check` → exit 0（仅 LF/CRLF 警告，无 whitespace 错误）。
- `python -m pytest -q test/test_v2_start_service.py test/test_v2_phase2_entrypoint.py -k "ccbd or socket or endpoint or ping"` → 2 errors during collection：`ModuleNotFoundError: No module named 'fcntl'` @ `lib/mobile_gateway/terminal.py:4`。这是本 feature 之外的既有 Windows collection 基线，owner 已按 checklist `CMD-005: failure_handling: document-baseline` 单独记录接受；Windows-safe import 修复拆至独立 feature `windows-runtime-import-lock-compat`。

## 4. Scenario Results

- [x] QA-001 checklist YAML：pass。
  - Evidence: validation exit 0。
- [x] QA-002 roadmap items YAML：pass。
  - Evidence: validation exit 0。
- [x] QA-003 endpoint/fake/projection behavior：pass。
  - Evidence: canonical endpoint record、legacy `socket_path` fallback、lifecycle/lease/ping projection、fake bootstrap nonce、fake closed/connectability、recv EOF 均由目标测试覆盖。
- [x] QA-004 bootstrap/server/client regression：pass。
  - Evidence: 目标测试 exit 0；Windows 跳过纯 AF_UNIX 用例。
- [x] QA-005 real AF_UNIX behavior：compatibility residual。
  - Evidence: 本机无 AF_UNIX，相关用例 skip（42 passed, 15 skipped）。按 owner 记录的 native Windows evidence decision，这是 compatibility residual，不是 native Windows milestone core gate。
- [x] QA-006 v2 start/ping/doctor sample：document-baseline。
  - Evidence: collection 在到达 feature 代码路径前因既有 `mobile_gateway.terminal -> import fcntl` 失败。该 gap 经 owner 依 `failure_handling: document-baseline` 单独接受（approval-report.md Decision History 2026-07-20），修复由独立 feature 承接；本 feature 的直接 projection 证据已由 QA-003 覆盖。
- [x] QA-007 guard/scope：pass。
  - Evidence: import guard 通过；scope gate passed；无 Windows TCP adapter、无 RPC schema/handler dispatch 改动。
- [x] QA-008 cleanliness：pass。
  - Evidence: compileall、`git diff --check`、scope gate 通过。

## 5. Findings

### failed

- none

### blocked

- none（round 1 的 CMD-005 阻塞项经 owner document-baseline 接受后不再作为阻塞；见 residual-risk）

### residual-risk

- `mobile_gateway.terminal -> import fcntl` Windows collection baseline 仍存在于本 feature 提交基线中；已由 owner 依 CMD-005 `document-baseline` 接受，Windows-safe import 修复拆至独立 feature `windows-runtime-import-lock-compat`（`.codestable/roadmap/windows-rmux-native-backend/pending-split/`）。CMD-005 完整 start/ping/doctor 抽样证据待该修复 feature 落地后可补齐。
- 真实 Unix `AF_UNIX` bootstrap / lifecycle / stale-cleanup / deferred-connection 证据在本机为 skip；按 native Windows milestone 口径是 compatibility residual，应由 Unix CI/真机在需要声明 Unix 兼容时复跑，不阻塞 `windows-rmux-native-working`。
- native Windows 下 ccbd 真实控制面运行（AF_UNIX 不可用）需要下一 roadmap feature `ccbd-windows-tcp-loopback-transport` 提供原生传输；本 feature 刻意不实现 Windows TCP adapter。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass（compileall + 目标测试）
- Out-of-scope files: pass（feature 代码在 scope-gate `allowed_prefixes` 内；`agent-conventions.md` 与 pending-split 记为 feature 外改动并已归因）

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段（以 `acceptance_authorization_ref: approval-report.md#goal-acceptance` 显式进入）。acceptance 复核时应确认本 QA verdict 显式引用 owner 的 CMD-005 document-baseline 接受与 AF_UNIX residual decision。
