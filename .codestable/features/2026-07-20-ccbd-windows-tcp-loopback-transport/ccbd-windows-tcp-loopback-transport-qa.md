---
doc_type: feature-qa
feature: 2026-07-20-ccbd-windows-tcp-loopback-transport
status: passed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-07-22
round: 1
---

# ccbd-windows-tcp-loopback-transport QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml`
- Review: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-review.md`
- Evidence pack: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-scope-gate.json`
- DoD results: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-dod-results.json`
- Diff basis: `git diff --name-status` only shows `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml`; current business scope has no dirty code diff.
- Baseline dirty files: `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml` is the parent goal-driver running marker and not part of the transport behavior under QA.
- Feature type: functional.
- Core evidence gate: Windows platform selection, TCP endpoint publish, token ACL fail-fast, pre-handler token handshake, bootstrap self-ping, endpoint canonicalization, token redaction, Unix fallback, and scope guard all need fresh runtime or schema evidence.

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | CMD-001 | supporting | checklist YAML 可解析 | schema | `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml" --yaml-only` | exit 0 | pass |
| QA-002 | CMD-002 | supporting | roadmap items YAML 可解析 | schema | `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` | exit 0 | pass |
| QA-003 | AC-001..AC-005, AC-007 | core-functional | Windows TCP adapter、endpoint、token ACL、handshake、redaction 主路径 | unit/integration | `python -m pytest -q test/test_ccbd_windows_tcp_loopback_transport.py` | exit 0 | pass |
| QA-004 | AC-006 | core-functional | bootstrap self-ping 和 fake seam 回归 | regression | `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_control_plane_transport_fake.py` | exit 0；Windows goal 下 Unix-only skip 不阻塞 | pass |
| QA-005 | CMD-005 | core-functional | start/ping 控制面抽样 | regression | `python -m pytest -q test/test_v2_start_service.py -k "ccbd or endpoint or ping or socket"` | exit 0 | pass |
| QA-006 | AC-008 | core-functional | no token leak、no named pipe production branch、no handler schema drift | guard | `python -m pytest -q test/test_ccbd_windows_tcp_loopback_import_guard.py` | exit 0 | pass |
| QA-007 | review QA focus | supporting | Unix legacy fallback、socket server 行为不漂移 | regression | `python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_socket_server.py` | exit 0 | pass |
| QA-008 | review QA focus | supporting | socket server lifecycle 回归 | regression | `python -m pytest -q test/test_ccbd_socket_server.py test/test_ccbd_socket_lifecycle.py` | exit 0；Windows goal 下 Unix-only skip 不阻塞 | pass |
| QA-009 | cleanliness | supporting | whitespace、调试输出、临时标记、方案外 named pipe | diff/static | `git diff --check`; `rg -n "TODO|FIXME|XXX|print\\(|pdb\\.set_trace|breakpoint\\(|named pipe|NamedPipe|pywin32" ...` | no blocking cleanliness issue | pass |

## 3. Command Results

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml" --yaml-only` -> exit 0: 1 passed, 0 failed.
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` -> exit 0: 1 passed, 0 failed.
- `python -m pytest -q test/test_ccbd_windows_tcp_loopback_transport.py` -> exit 0: 33 passed.
- `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_control_plane_transport_fake.py` -> exit 0: 6 passed, 5 skipped.
- `python -m pytest -q test/test_v2_start_service.py -k "ccbd or endpoint or ping or socket"` -> exit 0: 2 passed, 18 deselected.
- `python -m pytest -q test/test_ccbd_windows_tcp_loopback_import_guard.py` -> exit 0: 2 passed.
- `python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_socket_server.py` -> exit 0: 16 passed.
- `python -m pytest -q test/test_ccbd_socket_server.py test/test_ccbd_socket_lifecycle.py` -> exit 0: 2 passed, 5 skipped.
- `git diff --check` -> exit 0: no whitespace errors.
- `rg -n "TODO|FIXME|XXX|print\\(|pdb\\.set_trace|breakpoint\\(|named pipe|NamedPipe|pywin32" ...` -> exit 0: only expected guard text in `test/test_ccbd_windows_tcp_loopback_import_guard.py` and `fingerprint()` symbol in `token_auth.py`.

## 4. Scenario Results

- [x] QA-001 checklist YAML: pass.
  - Evidence: schema validator accepted the checklist.
- [x] QA-002 roadmap items YAML: pass.
  - Evidence: schema validator accepted roadmap items.
- [x] QA-003 Windows TCP adapter/token/handshake/redaction: pass.
  - Evidence: fresh TCP loopback test run increased the old evidence-pack `CMD-003` snapshot from 7 tests to 33 passing tests.
- [x] QA-004 bootstrap self-ping and fake seam: pass.
  - Evidence: bootstrap/fake suite passed; skipped entries are Unix-only compatibility evidence and not a native Windows core blocker.
- [x] QA-005 start/ping control-plane sample: pass.
  - Evidence: targeted start service selection passed.
- [x] QA-006 import/scope guard: pass.
  - Evidence: guard passed for token redaction and no named-pipe / handler-schema / pid-liveness scope drift.
- [x] QA-007 Unix legacy fallback: pass.
  - Evidence: Unix transport and socket server regressions passed.
- [x] QA-008 socket lifecycle: pass.
  - Evidence: lifecycle regression passed with Unix-only skips.
- [x] QA-009 cleanliness: pass.
  - Evidence: diff check clean; static scan found only expected guard text and a legitimate `fingerprint()` symbol.

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- 真实 Windows 多用户 ACL、域用户 / 本地化 ACL 输出、杀软或防火墙策略仍未由本机 QA 直接证明；当前证据覆盖 adapter 行为、failure mapping、redaction 和 bootstrap 路径。
- Evidence pack 与 DoD results 保留实现前 review 的旧 `CMD-003` 快照；本 QA 已用 fresh command 记录 `33 passed`，acceptance 应以本 QA 结果作为后续判断依据。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass
- Out-of-scope files: pass；当前 dirty 文件只有 goal-state driver marker，未影响业务行为 QA 归因。

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段。
