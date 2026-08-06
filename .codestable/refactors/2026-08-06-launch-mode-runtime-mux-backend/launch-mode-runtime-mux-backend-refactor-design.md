---
doc_type: refactor-design
refactor: 2026-08-06-launch-mode-runtime-mux-backend
status: draft
summary: 用 config [runtime.mux] backend=herdr/rmux 扩展 provider launch_mode（当前仅 simple_tmux/codex_tmux），适配原生 Windows 的 herdr/rmux 启动语义
decision_confirm:
  D2: single-source-of-truth（runtime.mux.backend 同时驱动 backend + launch_mode，config 显式 > env）
  D3: send_text 进 pane（交互 CLI 可见，bridge 辅助）
  D5: fail-closed（声明后端不可用时报错，不静默回退）
tech_validation:
  herdr_send_text: supported（herdr_backend.py:557 send_text，capability send_input）
  rmux_backend: not-implemented（rmux_backend_runtime/ 仅 __pycache__ 残留；rmux 仅类型字面量）
tags:
  - launch-mode
  - runtime-mux-backend
  - herdr
  - rmux
  - provider-launch
  - config-schema
---

# 架构设计验证：runtime.mux.backend 驱动 launch_mode（herdr/rmux）

## 1. 现状架构（已验证事实）

### 1.1 terminal backend 选择
- 由 `CCB_BACKEND_ENV` 环境变量 / 终端检测决定（`terminal_runtime/backend_env.py`、`backend_resolver.py`），**不走 config**。
- 可选后端：`tmux` / `herdr` / `rmux`（`rmux_backend_runtime` 存在）。
- herdr UI 环境：`HERDR_ENV=1` → 选择 herdr backend。

### 1.2 provider launch_mode
- `ProviderRuntimeLauncher.launch_mode`（`provider_core/contracts.py:40`）= `Literal['simple_tmux', 'codex_tmux']`，**per-provider 硬编码**（codex→codex_tmux，其余→simple_tmux）。
- **launch_mode 当前无消费点**（全库 grep 无 `\.launch_mode` 读取）——纯元数据。
- 实际行为差异由 provider 的 `build_start_cmd`/`post_launch`（codex 专属）体现。

### 1.3 provider launch（tmux 导向）
- 核心：`lib/cli/services/runtime_launch_runtime/tmux_runtime.py:19 launch_tmux_runtime` —— **硬编码 tmux 语义**：`create_detached_tmux_pane`、`write_session_file`、tmux socket。
- codex `post_launch`（`provider_backends/codex/launcher_runtime/bridge.py`）：
  - `spawn_codex_bridge` 设 `CODEX_TERMINAL='tmux'`、`CODEX_TMUX_SESSION=pane_id`；
  - `write_pane_pid` 用 `backend._tmux_run(['display-message', ...])`（**herdr 后端无 `_tmux_run` → 静默失败**）。
- agent `runtime_ref` 构造为 `tmux:{pane_id}`（`agent_runtime.py:150`）。

### 1.4 herdr 环境的表现（本次采集验证）
- ccbd mounted、agent bound（CCB 内部状态）✓
- **codex 交互 CLI 未进 herdr pane**（herdr pane 前台进程为空 `powershell.exe`）❌
- 用户无法在 herdr UI 看到/交互 agent CLI。

**根因**：provider launch 模型（launch_mode + launch_tmux_runtime + codex bridge）从设计上假设 tmux 后端，herdr 后端无适配。

### 1.5 runtime.mux.backend
- 当前**无任何读取点**（grep 无 `runtime.mux`/`runtime_mux`/`mux.backend`）。
- schema 曾被设计（backend-resolver-opt-in-contract AC-005 验收过）但实现未接线，后在 2026-08-06 issue 中决策"废弃清理"（v2 校验报错带迁移提示）。

## 2. 目标设计

用 config `[runtime.mux] backend` 作为**声明式后端偏好**，扩展 launch_mode 以适配原生 Windows 的 herdr/rmux 启动语义。

| runtime.mux.backend | backend 选择 | launch_mode 语义（新增） | 说明 |
|---|---|---|---|
| `"herdr"` | herdr | `herdr_native`（新增） | codex 以 herdr pane 方式启动：把交互 CLI 送进 herdr pane，bridge 用 herdr 语义 |
| `"rmux"` | rmux | `rmux`（新增或复用 tmux 兼容） | provider 启动走 rmux（Windows 原生 tmux 兼容层），复用 launch_tmux_runtime 语义 |
| 未设置 | env 检测（现状） | `simple_tmux`/`codex_tmux`（现状） | 行为不变 |

### 2.1 runtime_ref 前缀规范（review 修订 I-2）
- **约束**：`agent_runtime.py:150` 硬编码 `f'tmux:{pane_id}'`，但 herdr 环境实际运行时 ref 是 `mux:{pane_id}`（`binding_runtime/common.py` 的 `_PANE_RUNTIME_BACKENDS={'tmux','mux','rmux','psmux','herdr'}` 已支持 mux 前缀解析）。
- **设计**：launch 适配 herdr 时，runtime_ref 前缀**按后端选择**：
  - tmux/rmux → `tmux:{pane_id}`
  - herdr → `mux:{pane_id}`（或 `herdr:{pane_id}`，与现有 namespace ref 一致）
- 否则 binding 恢复/匹配（`runtime_ref_backend`）会错位，agent 绑定判定异常。

### 2.2 provider 支持范围（review 修订 I-3）
- **codex**：优先支持 herdr/rmux launch（build_start_cmd + pane run + bridge 适配）。
- **claude/gemini 等 `simple_tmux`**：herdr 模式下其 CLI 同样走 `launch_tmux_runtime`，需评估是否适配 herdr `pane run`。
- **未适配 provider**：在 `runtime.mux.backend=herdr` 下 **fail-closed 报错**（"provider X 不支持 herdr launch"），避免"显示 bound 但无 CLI"的假象。

## 3. 关键决策点（需严格验证后确认）

### D1 — schema 形态
- 重新启用 v2 顶层 `runtime`（仅白名单接受 `runtime.mux.backend`，拒绝其他 `runtime.*` fail-closed）？
- 还是把 `runtime.mux` 收敛进 v3 workflow（`workflow.runtime`）？
- **倾向**：v2 顶层 `runtime` 只接受 `runtime.mux.backend` 一个键（最小面），其余 fail-closed；迁移提示保留。
- 影响：`common.py ALLOWED_TOP_LEVEL_KEYS`、`validation.py _validate_document_shape`、`workflow_v3.py`。

### D2 — 单一事实源边界（已确认，review 修订 M-1）
- `runtime.mux.backend` **同时**驱动 backend 选择（config 显式 > `CCB_BACKEND_ENV`/终端检测）**和** launch_mode。
- 语义：`runtime.mux.backend` 是声明式单一事实源；未设置时保持 env/终端检测现状。
- **耦合边界（review 确认）**：herdr 环境整体用 herdr 语义（backend + launch 同源），**无 per-agent backend 需求**——backend 是项目级声明，所有 agent 在同一后端。若未来出现"某 agent 需不同 launch 语义"，再引入 per-agent 覆盖（不在本次范围）。
- 影响：backend_resolver / api_selection 的输入扩展（config 优先）。

### D3 — herdr 原生 launch 机制（已确认，review 修订 I-1）
- **用 herdr `pane run` 运行 `build_start_cmd` 命令**：review 核实 `herdr_backend_runtime/cli.py:725 _send_text` 实际调用 `["pane", "run", pane_id, text]`——是在 herdr pane 中**运行命令**（非"模拟键盘输入"）。launch 时把 `build_start_cmd` 的命令经 herdr backend 的 `send_text`（=`pane run`）送进 pane，codex 交互 CLI 接管 pane（可见可输入）。
- **交互验证点（review 新增）**：需验证 `pane run` 对交互式 codex 的语义——长/多行命令、codex TUI 全屏接管、Ctrl-C 信号转发、codex 退出后 pane 状态。若 `pane run` 不能保持交互前台，则回退到"pane 内启动 shell + send 命令"的组合方案。
- bridge 作为辅助（`CODEX_TERMINAL` 支持 herdr）。
- 影响：`runtime_launch_runtime/tmux_runtime.py` 抽象出"launch 后端"接口（tmux/herdr 实现）。

### D4 — rmux 与 tmux 的关系（**待实现，非本次范围**）
- **技术验证结论**：rmux 后端在当前代码库**未实现**（`rmux_backend_runtime/` 仅 `__pycache__` 残留；rmux 仅作为 `RequestedBackendV2`/`BackendImplV2` 类型字面量，无 backend 类/工厂）。
- 因此 `runtime.mux.backend=rmux` **当前无法落地**：需要先实现 rmux backend（Windows 原生 tmux 兼容层，独立 epic）。
- 本次设计：schema 接受 `runtime.mux.backend` ∈ {`herdr`, `rmux`}，但 **rmux 落地依赖独立 rmux backend epic**；schema 校验对 rmux 保留类型预留（fail-closed 提示"rmux backend 未实现"）。

### D5 — 默认与回退（已确认）
- 无 `runtime.mux` → 现状（env/终端检测 + tmux 导向）。
- `runtime.mux.backend=herdr` 但 herdr server 不可用 → **fail-closed 报错**（明确诊断"herdr backend unavailable; check herdr session"），不静默回退 tmux。

## 4. 影响面（blast radius）

| 模块 | 影响 |
|---|---|
| `common.py` / `validation.py` / `workflow_v3.py` | schema：`runtime.mux.backend` 解析与校验 |
| `backend_resolver.py` / `backend_selection.py` | backend 选择输入（config 偏好 vs env） |
| `runtime_launch_runtime/tmux_runtime.py` | launch 从"tmux 硬编码"抽象为多后端（tmux/herdr/rmux） |
| `provider_backends/*/launcher.py` | launch_mode 从硬编码扩展为 config 驱动 |
| `provider_backends/codex/launcher_runtime/bridge.py` | `CODEX_TERMINAL` / `write_pane_pid` 适配 herdr |
| `ccbd/start_runtime/*` | agent runtime_ref（tmux: → herdr:/mux:）规范化 |
| `herdr_backend_runtime/*` | 新增 send_text / pane 启动语义 |
| 测试 | launch_mode / backend / schema 全矩阵 |

## 5. 边界与兼容性

- **存量 config**（无 `runtime` 字段）→ 完全不变。
- **provider 支持度**：见 2.2（I-3）——codex 优先，未适配 provider 在 herdr 下 fail-closed。
- **部分配置**：`runtime.mux.backend` 与 env 冲突时 config 显式声明优先（已确认 D2）。
- **Windows-only**：herdr/rmux 是原生 Windows 需求。**非 Windows 环境 + `runtime.mux.backend` → fail-closed 报错**（"runtime.mux.backend 仅支持 Windows 原生环境"），不静默忽略（review 修订 L-1）。
- **v3 兼容性（review 修订 L-2）**：`runtime.mux.backend` 在 **v2 顶层 `runtime.mux.backend`** 生效；**v3** 走 `workflow.runtime.mux.backend`（与 workflow v3 的 runtime 语义对齐）。两个版本各自校验、各自 fail-closed。
- **长命令（review 修订 L-3）**：`build_start_cmd` 命令可能很长（env+cd+codex），herdr `pane run` 对长文本/换行的支持需在实施时验证；不支持则分段 send 或改用"pane 内 shell + send"方案。

## 6. 验证矩阵（设计验收）

| ID | 输入 | 期望 |
|---|---|---|
| VA-1 | 无 runtime.mux + herdr UI | 现状行为（env 检测）不变 |
| VA-2 | `runtime.mux.backend=herdr` + herdr server 可用 | codex CLI 进 herdr pane，交互可见。**断言方法（review 修订 M-2）**：① herdr `pane process-info` 前台进程含 `codex`；② herdr `pane read`/`capture_pane` 内容含 codex 提示符；③ `ccb8 ps` agent `binding=bound` 且 `runtime_ref` 前缀为 `mux:`（I-2）；④ 交互验证：向 pane send 文本并确认 codex 响应 |
| VA-3 | `runtime.mux.backend=herdr` + herdr server 不可用 | fail-closed 明确报错，不静默 tmux |
| VA-4 | `runtime.mux.backend=rmux` | launch 走 rmux（tmux 兼容），Windows 原生 pane 可见 |
| VA-5 | 未知 `runtime.*` 字段 | fail-closed，报错带路径 + 提示 |
| VA-6 | 非 Windows + runtime.mux.backend | 忽略或报错（明确语义） |
| VA-7 | 各 provider（codex/claude/gemini）在 herdr/rmux 下 | 启动行为符合 launch_mode 语义 |

## 7. 技术可行性验证（2026-08-06 已核验）

| 前提 | 状态 | 证据 |
|---|---|---|
| herdr backend 支持 send_text（D3 核心） | ✅ | `herdr_backend.py:557 send_text(pane_id, text)`；capabilities `"send_text": ("send_input",)` |
| herdr 会话可达时可 send 到 pane | ✅ | herdr `pane send` / `send_input` 语义存在 |
| rmux backend 已实现（D4 前提） | ❌ | `rmux_backend_runtime/` 仅 `__pycache__` 残留；rmux 仅 `RequestedBackendV2`/`BackendImplV2` 类型字面量，无 backend 类/工厂 |
| `launch_mode` 有消费点（扩展基础） | ❌ | 全库无 `\.launch_mode` 读取，纯元数据——需先把 launch_mode 接入 launch 流程 |

**结论**：herdr 模式可落地（send_text 已存在）；rmux 模式依赖未实现的 rmux backend（独立 epic）。`launch_mode` 当前无消费点，需先建立"launch 后端抽象"再扩展。

## 8. 风险

1. **决策变更（review 修订 M-3）**：重新启用 `runtime.mux.backend` 是对 2026-08-06 issue（`herdr-windows-keeper-mutex-config-runtime`）"废弃清理"决策的**正式修订**。变更链记录：AC-005 验收（曾支持）→ 2026-08-06 废弃（未接线）→ 本次按用户方向补实现（作为 launch_mode 后端驱动）。修订理由：原生 Windows herdr/rmux 环境需要声明式后端偏好。
2. `launch_mode` 从元数据变实际控制，且当前无消费点 → 需先补 launch 后端抽象，改动面大。
3. herdr `pane run` 对交互式 codex（长命令、TUI、信号、退出行为）的语义需验证（D3/I-1）。
4. 各 provider launcher 差异（simple_tmux vs codex_tmux）在 herdr 下的行为需逐 provider 验证；未适配 provider 须 fail-closed（I-3）。
5. rmux 是独立未实现 epic——本次只做 schema 类型预留，不实现 rmux backend。

## 9. 建议实施顺序

1. **schema**：重新启用 `runtime.mux.backend`（v2 顶层 `runtime` 白名单最小面：仅 `runtime.mux.backend`，其余 fail-closed）；`backend=rmux` 时校验提示"rmux backend 未实现"。
2. **launch 后端抽象**：`launch_tmux_runtime` 抽离"launch 后端"接口（tmux 现有 + herdr 新增），先接入 herdr。
3. **herdr launch**：launch 时用 herdr `send_text` 把 `build_start_cmd` 命令送进 herdr pane（交互 CLI 可见）；bridge 的 `CODEX_TERMINAL` 支持 herdr。
4. **backend 选择**：config `runtime.mux.backend` 优先于 env（D2）。
5. **验证矩阵**：VA-1..VA-7 全量（VA-4 rmux 待 rmux epic）。
6. **rmux**：独立 epic 实现 rmux backend 后，`runtime.mux.backend=rmux` 落地。

## 10. Review 修订记录

| 日期 | Review 发现 | 修订 |
|---|---|---|
| 2026-08-06 | I-1：send_text 实为 `pane run`（运行命令） | D3 明确为"`pane run` 运行 `build_start_cmd`"，加交互 CLI 验证点 |
| 2026-08-06 | I-2：runtime_ref 前缀 `tmux:` vs `mux:` 不一致 | 新增 2.1：runtime_ref 按后端选前缀 |
| 2026-08-06 | I-3：非 codex provider 的 herdr 支持范围未定 | 新增 2.2：codex 优先，未适配 provider fail-closed |
| 2026-08-06 | M-1：D2 耦合边界 | D2 确认"无 per-agent backend"，backend 为项目级声明 |
| 2026-08-06 | M-2：VA-2 无自动验证方法 | VA-2 补 4 项断言方法（process-info / pane read / runtime_ref / 交互） |
| 2026-08-06 | M-3：决策变更未记录 | 风险 #1 记录"废弃 → 补实现"变更链 |
| 2026-08-06 | L-1/L-2/L-3：非 Windows / v3 / 长命令 | 第 5 节补三处边界 |
