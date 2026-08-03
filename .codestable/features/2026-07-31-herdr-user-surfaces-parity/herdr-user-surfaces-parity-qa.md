---
doc_type: feature-qa
feature: 2026-07-31-herdr-user-surfaces-parity
status: passed
runner_state: completed
runner_reason: ""
runner_id: "019fc5e0-f1d6-7ec2-a4e3-65a30157c6f9"
tested: 2026-08-03
round: 1
---

# herdr-user-surfaces-parity QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-checklist.yaml`
- Review: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-review.md`
- Evidence pack: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/evidence/cmd-008-native-windows-surface-transcript.md`
- Gate results: none
- DoD results: checklist CMD-001..CMD-008 与 implementation report 记录
- Diff basis: 当前工作区 unstaged/untracked diff；staged diff 为空。
- Baseline dirty files: `笔记.md` 是无关 dirty baseline；本 QA 不归因到该 feature。review 与 CMD-008 transcript 是本 feature artifact。
- Feature type: mixed。核心是用户可见 runtime/public surface 行为：ProjectView、ping、foreground attach、Mobile terminal、Config UI、doctor、mounted、diagnostics bundle 以及 Native Windows transcript。
- Core evidence gate: AC-002..AC-012 必须有运行证据或 transcript；Mobile/Config UI partial/degraded 只能作为 blocked evidence，不能投影为 supported。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | AC-001 / CMD-003 | core | upstream provider runtime / recovery boundary 已 accepted | artifact/schema | CMD-003 admission | no missing artifacts | pass |
| QA-002 | AC-002 | core-functional | ProjectView Herdr projection | unit | CMD-004 | projection 含 backend/capability/support tier/source/gaps/next action 且 redacted | pass |
| QA-003 | AC-003 | core-functional | ping projection 与 ProjectView 一致 | unit/CLI | CMD-004 + CMD-008 excerpt | ping payload 含同名 projection/source/next action | pass |
| QA-004 | AC-004 | core-functional | foreground attach supported | unit/manual | CMD-005 + CMD-008 | 调 backend-neutral attach，无 tmux fallback | pass |
| QA-005 | AC-005 | core-functional | foreground attach unsupported | unit | CMD-005 + CMD-008 | fail closed，错误含 beta gap / next action，不要求 tmux | pass |
| QA-006 | AC-006 | core-functional | Mobile terminal supported | unit/integration | CMD-005 + CMD-008 | history/message/websocket 使用 backend-neutral Herdr target | pass |
| QA-007 | AC-007 | core-functional | Mobile terminal blocked/partial | unit | CMD-005 + CMD-008 | HTTP/WS 返回 `status=blocked` 与 `terminal_blocked` | pass |
| QA-008 | AC-008 | core-functional | doctor/mounted/project view/diagnostics projection | unit/CLI | CMD-004 + CMD-008 | 显示 support tier projection/source、blocked reason、next action；bundle 来源 redacted | pass |
| QA-009 | AC-009 | core-functional | Config UI readonly status | unit/browser-light | CMD-005 + CMD-008 | blocked/pass gate 可观察；config edit/apply contract 不变 | pass |
| QA-010 | AC-010 | core | tmux/rmux regression | unit | CMD-006 | existing public surface tests 不退化 | pass |
| QA-011 | AC-011 | core | scope boundary / redaction | static | CMD-007 | 不触碰 provider completion/package/release/update/installer/support final claim/Herdr socket schema-client owner | pass |
| QA-012 | AC-012 / CMD-008 | core | Native Windows x64 surface evidence | manual transcript | 读取 CMD-008 transcript | 覆盖 foreground、Mobile、Config UI、doctor、ping、mounted、project view | pass |

## 3. Command Results

- QA runner `019fc5e0-f1d6-7ec2-a4e3-65a30157c6f9` -> verdict `pass`：AC-001..AC-012 全部 pass；无 failed/blocked finding。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-checklist.yaml" --yaml-only` -> exit 0：1 passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` -> exit 0：1 passed。
- CMD-003 upstream admission -> exit 0：`provider-runtime-on-herdr` 与 `herdr-bounded-recovery-boundary` roadmap item done，acceptance artifacts 含 evidence refs。
- CMD-004 `python -m pytest -q test/test_ccbd_project_view.py test/test_v2_ccbd_ping_runtime.py test/test_doctor_runtime_identity.py test/test_doctor_active_inbound_diagnostics.py test/test_v2_cli_render.py test/test_v2_diagnostics_bundle.py -k "herdr or backend or evidence or diagnostics or project_view or ping or doctor or mounted or ps or layout"` -> exit 0：130 passed, 29 deselected。
- CMD-005 `python -m pytest -q test/test_v2_start_foreground.py test/test_mobile_gateway_terminal.py test/test_mobile_gateway_service.py test/test_config_ui.py -k "herdr or backend or terminal or attach or blocked or config or readonly"` -> exit 0：106 passed, 1 skipped, 74 deselected。
- CMD-006 `python -m pytest -q test/test_terminal_runtime_tmux_attach.py test/test_mobile_gateway_terminal.py test/test_mobile_gateway_service.py test/test_ccbd_project_view.py test/test_doctor_runtime_identity.py test/test_doctor_active_inbound_diagnostics.py` -> exit 0：231 passed。
- CMD-007 scope/redaction guard -> exit 0：passed。
- CMD-008 focused transcript tests in evidence report -> exit 0：10 passed。
- `python -m py_compile` touched core files -> exit 0。
- `git diff --check` -> exit 0：无 whitespace error；仅 `.codestable` design/implementation 文档 LF->CRLF warning。
- `python -c "import platform, struct, sys; ..."; python -m pytest --version` -> exit 0：Python `64` bit，pytest `9.1.1` 可用。

## 4. Scenario Results

- [x] QA-001 upstream admission：pass
  - Evidence: CMD-003 原样 here-string 执行通过；两个 upstream acceptance artifact 可验证。
- [x] QA-002 ProjectView projection：pass
  - Evidence: CMD-004 通过，覆盖 namespace/runtime Herdr projection 与 redaction。
- [x] QA-003 ping projection：pass
  - Evidence: CMD-004 与 CMD-008 ping excerpt 均显示 `backend_impl=herdr`、support tier projection/source、gaps、next action。
- [x] QA-004 foreground attach supported：pass
  - Evidence: CMD-005 与 CMD-008 pass 样例显示 Herdr namespace/session refs，`tmux_fallback=not_called`。
- [x] QA-005 foreground attach blocked：pass
  - Evidence: CMD-008 blocked error 包含 `capability_status=blocked`、beta gaps、blocking gaps、next action。
- [x] QA-006 Mobile terminal supported：pass
  - Evidence: CMD-005 与 CMD-008 supported samples 覆盖 history/message/attach target，target `backend_impl=herdr` 且 `socket_path=""`。
- [x] QA-007 Mobile terminal blocked：pass
  - Evidence: CMD-008 blocked samples 均返回 `status=blocked` 或 409，并含 `terminal_blocked`。
- [x] QA-008 doctor/mounted/diagnostics：pass
  - Evidence: CMD-004 通过；CMD-008 doctor/mounted excerpt 显示 projection/source/gaps/next action。
- [x] QA-009 Config UI readonly status：pass
  - Evidence: CMD-005 通过；CMD-008 blocked/pass gate 显示 partial -> blocked，supported projection -> pass。
- [x] QA-010 tmux/rmux regression：pass
  - Evidence: CMD-006 `231 passed`。
- [x] QA-011 scope/redaction：pass
  - Evidence: CMD-007 通过，未发现 forbidden release/package/support final claim、Herdr socket schema-client owner 或 raw token public logging。
- [x] QA-012 Native Windows transcript：pass
  - Evidence: CMD-008 transcript 覆盖 foreground attach、Mobile terminal、Config UI、ping/project view、doctor/mounted；声明不代表最终 supported claim。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- `REV-006` 保留：Config UI blocked reason 当前主要显示 `capability_status=...`；当 hard gate 因 support tier/source/beta gaps/blocking gaps/degraded action 失败时文案不够精确。完整 projection 已暴露失败字段，不阻塞 QA。
- CMD-008 是本 feature harness + 同 roadmap true-host upstream evidence 的组合；它证明 surface projection 与 pass/blocked gate，不是 Windows x64 CCB 最终 supported claim。
- `笔记.md` 是无关 dirty baseline；acceptance 与提交归因时必须继续排除。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass，`py_compile` 与 focused tests 已覆盖 touched core files。
- Out-of-scope files: pass，CMD-007 未发现 provider completion、package/release/update/installer/support final claim、Herdr socket schema-client owner 越界。

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段。acceptance 必须继续确认 Mobile/Config UI partial/degraded 只作为 blocked evidence，不得宣称 Windows x64 CCB 最终 supported。
