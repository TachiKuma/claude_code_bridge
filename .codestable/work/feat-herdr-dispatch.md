---
doc_type: work
work_type: feat
slug: herdr-dispatch
epic: windows-native-herdr-ccb
status: pending
created: 2026-08-10
---

# feat: `ccb herdr dispatch` capability-gated 结构化原语

## 目标

在**不考虑 Herdr 侧改动**的前提下，为 CCB 新增 capability-gated 的 Herdr
terminal agent activation 原语 `ccb herdr dispatch`。能力不存在时必须返回
structured `blocked`，不得静默退回后台子进程（`Start-Process` /
`subprocess.Popen(detached)` / 后台 child process）伪装成功 dispatch。

## 现场

已验证的事实（2026-08-10，来源为代码核实）：

- 运行时 herdr backend = `HerdrBackend`（socket client），底层 request_fn =
  `HerdrCliRequestAdapter`；所有操作先经 `HerdrCapabilityGate.require_supported(operation)`
  再触达 client。来源 `lib/terminal_runtime/api.py:224-236`。
- `require_supported(op)` 对不在 `_OPERATION_REQUIRED_CAPABILITIES` 的操作用 `(op,)`
  作能力键；`command_status[op] != "supported"` 即抛
  `MuxCommandErrorV2(category="unsupported")`。来源
  `lib/terminal_runtime/herdr_backend_runtime/capabilities.py:157-182, 261-262, 233-258`。
- `_KNOWN_CAPABILITIES = core | 所有 operation 依赖值`；`_status_mapping` 只保留
  `_KNOWN_CAPABILITIES` 内的 key。新增 `dispatch_agent` 依赖后自动进
  `_KNOWN_CAPABILITIES`，但 spike evidence 不会声明其 `supported` → gate 保持 blocked。
  来源 `capabilities.py:53-55, 194-198`。
- `HerdrBackend.activate()` 已示范"能力不支持 → 显式抛 unsupported"范式。来源
  `lib/terminal_runtime/herdr_backend.py:658-673`。
- CLI `parse_herdr` 只接受 `open`；`dispatch` 子命令与 handler 均不存在。来源
  `lib/cli/parser_runtime/commands.py:1281-1309`、`lib/cli/phase2_runtime/handlers_start.py`。
- CCB 当前用 `pane run` / `respawn_pane` 注入 provider 命令，pane 非交互 shell
  prompt。`herdr agent start`（要求交互 shell prompt）不能作为 CCB 侧 dispatch 的
  底层调用，只能作为"探测到能力后才接"的可选后端。来源
  `lib/cli/services/runtime_launch_runtime/pane_runtime.py:47-59`。
- `dispatch_agent` / `agent_start` 在 CCB 代码库不存在（codegraph 已核实，无命名冲突）。

可行性结论：**CCB 侧完全可行**。核心机制已存在（gate + structured error + backend
operation 表 + CLI parser/handler 扩展），无需 Herdr 侧改动即可实现 fail-closed 原语。

## 边界

- `ccb herdr dispatch` **只能**表达 Herdr terminal agent activation primitive：
  只负责触发/验证 Herdr pane 内 agent activation，不拥有 CCB job / queue /
  completion / cancel / followup 权威，不写 provider payload 到 Herdr metadata，
  不复活 legacy topology dispatch / communication DSL。
- `dispatch` 在本项目同时可能指：CCB job dispatcher（`ccbd/services/dispatcher.py`）、
  legacy topology dispatch、Herdr agent activation。本原语固定使用
  `ccb herdr dispatch` 前缀 + 内部操作名 `dispatch_agent`，限定在 herdr namespace 内。
- 硬约束：能力不存在时 structured blocked，**绝不**后台子进程伪装成功。
- 不预设 Herdr 侧改动；迭代 4 的底层实现依赖 Herdr 能力探测（capability report 声明
  `dispatch_agent: supported`）与 pane 形态约束（交互 shell prompt）。

## 证据

- `lib/terminal_runtime/herdr_backend_runtime/capabilities.py`
- `lib/terminal_runtime/herdr_backend.py`
- `lib/terminal_runtime/api.py`
- `lib/cli/parser_runtime/commands.py`、`lib/cli/phase2_runtime/handlers_start.py`
- `.codestable/epics/windows-native-herdr-ccb.md` ITEM-8（当前代码状态标记）
- `.codestable/lessons/2026-08-10-herdr-dispatch-interactive-terminal.md`
- `.codestable/compound/2026-08-10-ccb8-bootstrap-shim-analysis.md`

## 迭代方案

### 迭代 0：Parser + 命令模型（薄层，独立可交付）
- `lib/cli/models_start.py`：新增 `ParsedHerdrDispatchCommand`
  （`project`、`session_name`、`pane_id`、`agent_label`、`provider_kind`、`dry_run`）。
- `lib/cli/parser_runtime/commands.py`：`parse_herdr` 增加 `dispatch` 分支。
- `lib/cli/phase2_runtime/handlers_start.py`：新增 `handle_herdr_dispatch`。
- `lib/cli/phase2_runtime/dispatch.py`：注册 `herdr-dispatch` handler。
- 测试：parser 解析、handler 渲染。
- 验收：`ccb herdr dispatch --pane <id> --agent <label>` 解析成功；未知子命令报错
  从 `herdr supports: open` 扩展为 `herdr supports: open, dispatch`。

### 迭代 1：Capability 声明（核心 fail-closed 机制）
- `capabilities.py` `_OPERATION_REQUIRED_CAPABILITIES` 增加：
  ```python
  "dispatch_agent": ("session_attach", "pane_list", "pane_run", "send_input", "pane_metadata"),
  ```
  `_KNOWN_CAPABILITIES` 自动吸收 `dispatch_agent`。
- 不改 spike evidence → `command_status["dispatch_agent"]` 缺省 →
  `require_supported("dispatch_agent")` 抛 unsupported → 能力不存在即 structured blocked。
- 测试：当前 evidence 下 `require_supported("dispatch_agent")` 抛 `category="unsupported"`，
  不 fallback。
- 验收：fail-closed 成立，`_KNOWN_CAPABILITIES` 含 `dispatch_agent`。

### 迭代 2：Backend `dispatch_agent` 方法（structured blocked 落点）
- `herdr_backend.py` 增加 `dispatch_agent(pane, *, agent_label, provider_kind)`：
  先 `_pane_ref` 校验，再 `require_supported("dispatch_agent")`（blocked if missing），
  `server_info()` 后触达底层；当前证据下底层不可达。
- 复用 `activate()` 的 "unsupported" 范式；`_client.dispatch_agent` 在迭代 2 为
  占位/不可达，或直接返回 `{status: blocked}`。
- 测试：真实 evidence 下抛 `MuxCommandErrorV2(category="unsupported")`，且
  monkeypatch `subprocess` / `Popen` 断言未调用（无子进程副作用）。
- 验收：backend 调 `dispatch_agent` 抛 unsupported，无后台进程。

### 迭代 3：CLI handler 接线（structured blocked 渲染）
- `handle_herdr_dispatch`：resolve daemon → 取 herdr backend → 调
  `backend.dispatch_agent(...)`。
- 捕获 `MuxCommandErrorV2(category="unsupported")` → 输出 structured `blocked`
  （含 `failure_reason`、`operation`、`capability_report_ref`），exit 非 0。
- 明确无后台子进程 fallback。
- 测试：端到端 handler 在能力缺失时输出 `blocked` 并返回非 0。
- 验收：CLI 输出 `command_status: blocked` + 结构化原因，exit 非 0，无后台进程。

### 迭代 4（可选，依赖 Herdr 能力探测）：真实 dispatch 后端
- 仅当未来 capability report 声明 `dispatch_agent: supported`（或 spike evidence
  更新）时 gate 放行；此时 `_client.dispatch_agent` 接入真实底层（CLI `herdr agent
  start` 或 socket API）。
- 前提约束：CCB pane 需是"交互 shell prompt"形态才能用 `herdr agent start`；当前
  `pane run` 注入形态不满足，需先改 pane 创建形态（涉及 `pane_runtime.py` respawn
  策略，独立改动）或 Herdr 提供针对已注入 pane 的原生 activation。
- 此迭代不预设实现，保持 gate-gated。

## 状态与未决

- 状态：pending（方案已固化，未开始实施）。
- 未决：
  - 迭代 0 的 `dry_run` 是否纳入首版（建议纳入，便于安全试调）。
  - 迭代 4 的 pane 形态改造是独立前置，是否单独立项（建议独立，不并入 dispatch 原语）。
  - 是否先做迭代 0 薄层（建议先做，风险最低、独立可交付）。
