---
doc_type: feature-qa
feature: 2026-07-31-herdr-backend-client
status: passed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-08-02
round: 1
---

# herdr-backend-client QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-checklist.yaml`
- Review: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-review.md`
- Evidence pack: none
- Gate results: none
- DoD results: none
- Diff basis: `git status --short` 显示 Herdr backend/client、resolver/factory、focused tests 与 checklist 变更；staged diff 为空；新增 Herdr runtime/test/review 文件未跟踪。
- Baseline dirty files: `笔记.md`，既有/无关工作区脏文件，未纳入本 QA verdict。
- Feature type: mixed。该 feature 改变 terminal runtime backend selection、Herdr adapter、schema/capability gate 与错误语义，按功能性核心路径验证；scope guard/清洁度按非功能性验证。
- Core evidence gate: AC-001 至 AC-009 需要 unit/contract 运行证据；AC-010 需要 diff/scope guard。真实 Herdr host 未配置，design 已明确本 feature 核心证据使用 fake socket/CLI 与 contract tests，真实 host shape 留作 residual risk。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | design AC-001/CMD-004 | core-functional | 缺 upstream spike evidence / blocked fixture | unit | `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` | Herdr capability gate blocked，不构造 backend | pass |
| QA-002 | design AC-002/CMD-004 | core-functional | stop/needs-upstream-issue、blocked/failed、failure_class、unknown/gaps | unit | `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` | fail closed，diagnostics 可观测 | pass |
| QA-003 | design AC-003/CMD-004 | core-functional | server_info/schema 匹配 | unit | `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` | schema gate 通过并记录 socket/server info | pass |
| QA-004 | design AC-004/CMD-004 | core-functional | schema/version/platform/arch 不匹配 | unit | `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` | 抛 `schema-mismatch` structured error | pass |
| QA-005 | design AC-005/CMD-004 | core-functional | create/restore session | unit | `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` | 返回 `herdr-native`/`herdr_socket` refs 与 restore token | pass |
| QA-006 | design AC-006/CMD-004 | core-functional | create pane / send / capture / kill | unit | `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` | 返回 pane refs 与 operation evidence | pass |
| QA-007 | design AC-007/AC-008/CMD-004 | core-functional | explicit `herdr` route gate pass/fail | unit | `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` | pass 时创建 HerdrBackend；fail 时 V2 failure 且不 fallback | pass |
| QA-008 | design AC-009/CMD-005 | core-functional | Native Windows auto 与非 Windows default | unit/regression | `python -m pytest -q "test/test_mux_backend_contract.py" "test/test_terminal_runtime_backend_selection.py"` | Windows x64 auto 走 Herdr gate；非 Windows default 不变 | pass |
| QA-009 | design DOD-IMPL-000/CMD-003 | core-functional | V2 contract admission | unit/contract | `python -m pytest -q "test/test_mux_backend_contract.py" -k "V2 or herdr"` | V2 refs/capabilities/errors 单一来源可用 | pass |
| QA-010 | design AC-010/CMD-006/CMD-007 | core-functional | ccbd/provider/doctor/package/recovery 越界 | diff | CMD-006、CMD-007 | 禁止路径和禁止内容未出现 | pass |
| QA-011 | design Validation Commands | supporting | checklist 与 roadmap YAML 合法 | schema | CMD-001、CMD-002 | YAML 校验通过 | pass |
| QA-012 | review Test And QA Focus | supporting | 真实 Herdr CLI/host 输出形态 | environment/manual | `Get-Command "herdr" -ErrorAction SilentlyContinue` | 如本机有 Herdr，则可做实机 smoke；当前无 Herdr | pass with residual-risk |
| QA-013 | QA cleanliness | non-functional | debug/TODO/FIXME/print、diff whitespace | static | `rg -n "TODO|FIXME|debug|print\(" ...`；`git diff --check` | 无 feature 临时调试输出；diff check exit 0 | pass |

## 3. Command Results

- `python -m py_compile "lib/terminal_runtime/api.py" "lib/terminal_runtime/backend_selection.py" "lib/terminal_runtime/herdr_backend.py" "lib/terminal_runtime/herdr_backend_runtime/client.py" "lib/terminal_runtime/herdr_backend_runtime/cli.py" "test/test_herdr_backend_client.py"` -> exit 0：Python 编译通过。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-checklist.yaml" --yaml-only` -> exit 0：1 passed, 0 failed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` -> exit 0：1 passed, 0 failed。
- `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` -> exit 0：150 passed。
- `python -m pytest -q "test/test_mux_backend_contract.py" -k "V2 or herdr"` -> exit 0：8 passed, 12 deselected。
- `python -m pytest -q "test/test_mux_backend_contract.py" "test/test_terminal_runtime_backend_selection.py"` -> exit 0：35 passed。
- `python -m pytest -q "test/test_mux_backend_contract.py" "test/test_terminal_runtime_backend_selection.py" "test/test_herdr_spike_no_production_route.py"` -> exit 0：38 passed。
- CMD-006 scope guard -> exit 0：未命中 forbidden path。
- CMD-007 content guard -> exit 0：未命中 provider completion/support/release forbidden terms。
- `git diff --check` -> exit 0：仅输出已知 `.codestable/features/.../herdr-backend-client-checklist.yaml` CRLF warning。
- `rg -n "TODO|FIXME|debug|print\(" "lib/terminal_runtime" ...` -> exit 0：只命中测试中的有意 `python -c "print(...)"` 命令字符串。
- `Get-Command "herdr" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source` -> exit 1：当前 PATH 未发现 Herdr executable；真实 host smoke 未运行，非本 feature 核心阻塞。

## 4. Scenario Results

- [x] QA-001 缺 evidence blocked：pass
  - Evidence: 150-test focused suite 通过，覆盖 missing/malformed capability report 与 blocked fixture。
  - Notes: 归因本 feature。
- [x] QA-002 capability fail-closed：pass
  - Evidence: focused suite 覆盖 recommendation/verdict/failure_class/blocking gaps/unknown status。
  - Notes: `continue-with-gaps` 仍不被当作成功。
- [x] QA-003 schema pass：pass
  - Evidence: fake socket `server_info` schema pass tests。
  - Notes: 不依赖真实 host。
- [x] QA-004 schema mismatch：pass
  - Evidence: fake socket mismatch/platform/arch tests 抛 `schema-mismatch`。
  - Notes: failure category 可诊断。
- [x] QA-005 session/restore refs：pass
  - Evidence: lifecycle tests 验证 namespace/session/restore_token exact matching。
  - Notes: `restore_token` 必须为 exactly one `session::workspace`。
- [x] QA-006 pane operations evidence：pass
  - Evidence: create_pane/send/capture/kill/is_alive tests 通过。
  - Notes: `send_text` via Herdr `pane run` 是本 feature 已接受决策。
- [x] QA-007 explicit route：pass
  - Evidence: selection/factory tests 覆盖 pass、blocked、prepare/factory failure。
  - Notes: explicit `herdr` failure 抛 `MuxCommandErrorV2`。
- [x] QA-008 auto/default route：pass
  - Evidence: contract/selection regression 35 passed 与组合 38 passed。
  - Notes: 非 Windows auto/default 保持 tmux 路径。
- [x] QA-009 V2 contract admission：pass
  - Evidence: focused V2/herdr contract 8 passed。
  - Notes: 未在 Herdr adapter 内重复定义 V2 类型。
- [x] QA-010 scope guard：pass
  - Evidence: CMD-006/CMD-007 exit 0。
  - Notes: 未改 ccbd durable state、provider runtime、doctor、package/release/recovery。
- [x] QA-011 YAML/schema：pass
  - Evidence: checklist 与 roadmap items 校验通过。
  - Notes: `.codestable` CRLF warning 不影响 YAML/schema。
- [x] QA-012 真实 Herdr host shape：pass with residual-risk
  - Evidence: `Get-Command herdr` exit 1，当前环境无 Herdr executable。
  - Notes: design 明确本 feature 用 fake Herdr socket/client 单元和 contract tests 作为核心证据；真实 host 输出形态继续作为后续集成 residual risk。
- [x] QA-013 cleanliness：pass
  - Evidence: diff check exit 0；`rg` 仅命中测试命令字符串。
  - Notes: 未发现 feature 临时 TODO/FIXME/debug 输出。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- 当前机器未安装或未暴露 `herdr` executable，未执行真实 Herdr host smoke；真实 `workspace create/list`、`pane split/run/read/close` JSON shape 与 host lifecycle 仍需后续 Windows/Herdr 集成验证。
- `send_text` 通过 Herdr `pane run` 实现是本 feature 已接受适配决策；若后续要求 stdin-style input，需要另开协议/adapter 能力修正。
- Legacy string pane IDs 只在创建它们的 backend 实例内可靠；跨进程/重建后的 durable 操作应使用 `MuxPaneRefV2`。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass
- Out-of-scope files: pass
- Baseline dirty handling: pass，`笔记.md` 排除在本 feature verdict 外。

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段
