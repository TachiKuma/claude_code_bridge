---
doc_type: feature-review
feature: 2026-07-31-herdr-backend-client
status: passed
reviewer: subagent+ocr
reviewed: 2026-08-02
round: 9
lane_a_state: completed
lane_a_ref: "019fbe88-00f9-7f63-bafe-502106c380b2"
lane_a_reason: "独立 reviewer 初始 verdict 为 changes-requested；唯一 blocking 已按本轮 closure evidence 修复并验证。"
lane_b_state: completed
lane_b_ref: ""
lane_b_reason: "ocr review 已完成；剩余 send_text/pane run 评论与已确认 feature 决策冲突，未采纳为 blocking。"
---

# herdr-backend-client 代码审查报告

## 0. Reopen Review 2026-08-02

Scope: owner approved `ReopenBackendClient` to fix real Herdr server lifecycle and split direction defects found by CMD-013 probing.

Independent reviewer: Task agent `019fbf9d-af8d-7ae3-b1f9-24ff45881bd0`.

### Findings Closure

blocking:

- [x] REV-REAL-001 `cli.py` `_start_server()` originally reused a session marker without checking whether the saved `Popen` was still alive. Fixed by checking `poll() is None`; exited or missing process records are cleared and respawned on the next NotFound retry.
- [x] REV-REAL-002 process state contradiction: `approval-report.md` now records owner approval as resolved, and `goal-state.yaml` no longer stays at the old owner-stop handoff. It records an active reopened backend-client repair state.

important:

- [x] REV-REAL-003 unsupported split direction is now validated before parent pane lookup or any Herdr command, so invalid directions fail closed without external side effects.

nit:

- [x] Error text kept behavior-focused; accepted aliases are test-covered.

### Fresh Verification

- `python -m py_compile "lib/terminal_runtime/herdr_backend_runtime/cli.py" "test/test_herdr_backend_client.py"` -> exit 0
- `python -m pytest -q "test/test_herdr_backend_client.py" -k "server or split_direction or bottom or unrepresentable or cli_request_adapter"` -> 39 passed, 105 deselected
- `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` -> 159 passed
- `python -m pytest -q "test/test_mux_backend_contract.py" -k "V2 or herdr"` -> 8 passed, 12 deselected
- `python -m pytest -q "test/test_mux_backend_contract.py" "test/test_terminal_runtime_backend_selection.py" "test/test_herdr_backend_client.py"` -> 179 passed
- Real Herdr smoke with `C:/Users/Administrator/AppData/Local/Programs/Herdr/herdr.exe` -> passed; returned version `0.7.5-preview.2026-07-29-44b3adb12552`, schema `Herdr API`, namespace `w1`, pane `w1:p2`, kill `ok`.

Verdict: passed. No unresolved blocking for the reopened backend-client fix.

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-checklist.yaml`
- Evidence pack: none
- Gate results: none
- DoD results: 本报告第 5 节命令矩阵
- Implementation evidence: 当前工作区 diff
- Diff basis: `git status --short`；baseline dirty `笔记.md` 排除
- Review mode: full-rereview + closure verification
- Baseline dirty files: `笔记.md`，非本 feature 归因，未纳入 verdict

### Independent Review

- Detection: subagent 可用；OCR CLI 可用并通过 `ocr llm test`
- 环节 A 独立隔离 Task agent: independent-agent completed (`019fbe88-00f9-7f63-bafe-502106c380b2`)
- 环节 B OCR CLI: completed
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion/residual-risk, Low->discarded
- Merge policy: 外部 finding 逐条用仓库事实核验；与已确认 feature 决策冲突的项不升级为 blocking
- Gate effect: 独立 reviewer 唯一 blocking 已关闭；无未关闭 blocking

## 2. Diff Summary

- 新增：`lib/terminal_runtime/herdr_backend.py`、`lib/terminal_runtime/herdr_backend_runtime/*`、`test/test_herdr_backend_client.py`
- 修改：`lib/terminal_runtime/api.py`、`lib/terminal_runtime/api_selection.py`、`lib/terminal_runtime/backend_resolver.py`、`lib/terminal_runtime/backend_selection.py`、`test/test_mux_backend_contract.py`、`test/test_terminal_runtime_backend_selection.py`、`test/test_herdr_spike_no_production_route.py`
- 删除：none
- 未跟踪 / staged：Herdr backend/runtime/test 新增文件未跟踪；staged none
- 风险热点：backend selection、IPC/ref validation、CLI JSON envelope、fail-closed capability gate

## 3. Adversarial Pass

- 假设的生产 bug：Herdr CLI/socket 返回部分成功或跨 session/ref 数据，导致 CCB 缓存或 ref 透传错误。
- 主动攻击过的反例：missing/malformed capability report、unknown capability、Windows gap、schema mismatch、restore token mismatch、foreign IPC ref、同 session 多 namespace、pane_id 缺失、JSON nested failed status、pane close 空 stdout、factory/prepare 异常。
- 结果：已关闭所有确认 bug；真实 Herdr host 形态和 legacy pane 生命周期留给 QA 复核。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- `lib/terminal_runtime/backend_selection.py`：若未来长期复用 `TerminalBackendSelection` 实例，可考虑排除 explicit `auto` cache，避免复用旧 gate 结果。当前生产 `api.get_backend()` 每次新建 selection，未作为阻塞。

### learning

- Herdr namespace IPC ref 必须只保留 exact current socket ref 或 exact `herdr://{session_name}`；foreign raw ref 要归一化，不能进入 V2 ref。
- `send_text` 使用 Herdr `pane run` 是本 feature 已接受适配决策；review 不再以该语义差异阻塞本阶段。

### praise

- Capability gate 对 missing/malformed/unknown/gaps/recommendation/verdict/failure_class 覆盖完整。
- CLI adapter 对 top-level/nested failed JSON status、missing pane_id、empty pane close output 都有回归测试。
- explicit Herdr 与 auto/default selection 的错误语义拆分清晰。

## 5. Test And QA Focus

- QA 必须重点复核：真实 Herdr CLI `workspace create/list`、`pane split/run/read/close` 输出形态；session-scoped IPC ref 与 explicit socket override；真实 host 下 pane close 后 legacy namespace 是否仍可用。
- Evidence pack residual risks / gate warnings：`git diff --check` 仅报告已知 `.codestable` checklist CRLF warning；baseline `笔记.md` 排除。
- 建议新增或加强的测试：真实 Herdr host integration/QA；当前 unit/contract 覆盖已满足 code review gate。
- 不能靠 review 完全确认的点：真实 Herdr binary/host 的最终 CLI schema、pane input 语义、workspace 生命周期。

验证命令：

- `python -m py_compile "lib/terminal_runtime/api.py" "lib/terminal_runtime/backend_selection.py" "lib/terminal_runtime/herdr_backend.py" "lib/terminal_runtime/herdr_backend_runtime/client.py" "lib/terminal_runtime/herdr_backend_runtime/cli.py" "test/test_herdr_backend_client.py"` -> passed
- `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` -> 150 passed
- `python -m pytest -q "test/test_mux_backend_contract.py" -k "V2 or herdr"` -> 8 passed, 12 deselected
- `python -m pytest -q "test/test_mux_backend_contract.py" "test/test_terminal_runtime_backend_selection.py"` -> 35 passed
- `python -m pytest -q "test/test_mux_backend_contract.py" "test/test_terminal_runtime_backend_selection.py" "test/test_herdr_spike_no_production_route.py"` -> 38 passed
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-checklist.yaml" --yaml-only` -> passed
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` -> passed
- CMD-006 scope guard -> passed
- CMD-007 content guard -> passed
- `git diff --check` -> exit 0；仅已知 CRLF warning
- `rg -n "TODO|FIXME|debug|print\(" ...` -> only intentional test command strings
- `ocr review --audience agent --exclude "笔记.md,.codestable/**" ...` -> completed; no unclosed accepted blocking

## 6. Residual Risk

- 未连接真实 Herdr host；CLI/host 最终 JSON shape 与 pane lifecycle 需要 QA 实机确认。
- `send_text` 通过 `pane run` 实现是当前 feature 决策；若后续要求 stdin-style input，需要另开协议/adapter 能力修正。
- Legacy string pane IDs 只在创建它们的 backend 实例内可靠；跨进程/重建后的 durable 操作应使用 `MuxPaneRefV2`。

## 7. Verdict

- Status: passed
- Next: Goal feature 进入 QA 阶段。

## 8. Focused Closure

- Closed findings: REV-001 independent reviewer IPC ref finding；OCR create_pane envelope/session/path/pane close/factory failure findings
- Attributed delta: `lib/terminal_runtime/herdr_backend_runtime/client.py`、`lib/terminal_runtime/herdr_backend_runtime/cli.py`、`lib/terminal_runtime/backend_selection.py`、`test/test_herdr_backend_client.py`
- Targeted verification: 见第 5 节命令矩阵，全部通过
- Classification: closure 修复均限制在 Herdr backend selection/ref/CLI adapter fail-closed 语义内，未扩展 provider runtime、ccbd lifecycle、doctor、package/release 或 installer 范围
