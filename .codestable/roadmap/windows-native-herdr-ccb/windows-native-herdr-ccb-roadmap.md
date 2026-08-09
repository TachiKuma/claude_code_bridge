---
doc_type: roadmap
slug: windows-native-herdr-ccb
status: active
created: 2026-07-30
last_reviewed: 2026-07-31
tags: [windows, native-windows, herdr, x64, mux-backend, public-workflow-parity]
related_requirements:
  - .codestable/requirements/native-windows-ccb-via-herdr.md
related_architecture:
  - .codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md
  - .codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md
  - .codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md
---

# Native Windows CCB via Herdr

## 1. 背景

owner 已明确暂停 `windows-rmux-ux-parity-hardening`，转向以 CCB `v8.5.2` 为严格源头基线规划 Native Windows supported 路线。本 roadmap 现在绑定 draft requirement `.codestable/requirements/native-windows-ccb-via-herdr.md`：目标是在 Native Windows x64 上以用户自备 Herdr 的全能力 parity 为基础，让 CCB 的公开工作流达到 Windows x64 CCB supported。这里的“全能力 parity”指 Herdr 需要提供 CCB 所需 terminal primitive 的完整能力证据；CCB 的 authority 边界仍保留在 control plane、provider runtime、completion、queue/cancellation、Mobile、release/update 和 support tier。公开工作流覆盖 `ccb`、所有公开 provider 的 `ask`、`pend`、completion、cancel、`watch`、`ping`、`mounted`、`kill`、`restart`、`reload`、foreground attach、Mobile terminal、Config UI、doctor/update/support projection。

Herdr 的价值在于它已经面向 agentic terminal multiplexer，具备 Windows beta、ConPTY pane、session/pane、socket API、session restore 与 agent state 观察能力。CCB 的价值仍在 control plane、provider runtime authority、completion、queue/cancellation、Mobile、release/update 和 support tier。推荐路线不是把 CCB 重写成 Herdr 插件，而是在 CCB 内新增 Herdr Native Windows backend。

本 roadmap 同时收紧平台口径：npm/Node 中 `os=win32` 表示 Windows 平台名，不表示 32-bit Windows。目标平台是 `os=win32,cpu=x64`，即 64-bit Windows 全链路；32-bit Windows、arm64 Windows 和 WOW64 混合链路均不在本 roadmap 范围内。

## 2. 范围与明确不做

### 本 roadmap 覆盖

- 以严格 CCB `v8.5.2` 源头为实现起点，并在开工前从 CCB 源头拉取后新建分支；当前工作区状态不得作为实现基线。
- 通过 Herdr socket API spike 验证 CCB 所需 session/pane/send/capture/restore 最小语义。
- 将现有 mux backend contract 从 tmux/rmux 语义扩展为可承载 Herdr native backend 的小协议集合。
- 实现 Herdr backend client、capability gate、namespace lifecycle、pane IO、foreground attach 和 terminal snapshot integration。
- 保留 CCB 对 provider state、completion、queue、cancellation、bounded recovery、diagnostics、Mobile、Config UI、update 的权威边界。
- 建立 Native Windows public workflow validation matrix；只有 strict `v8.5.2`、Herdr capability、所有公开 provider、Mobile/Config UI、release dry-run 和 recovery owner 证据全部通过后，才允许 support tier 投影为 `supported`。

### 明确不做

- 不恢复或继续推进 `windows-rmux-ux-parity-hardening`；它已由 owner pause，恢复需 owner 明确授权。
- 不支持 32-bit Windows、arm64 Windows 或混合 32/64 bit runtime；`win32` 仅作为 Node/npm 的 Windows OS 名称。
- 不把 Herdr agent detection 作为 CCB provider completion / health 的唯一权威；它只能进入 evidence/diagnostics。
- 不把 CCB control plane、provider completion、Mobile relay 或 update/support tier 重写成 Herdr 插件。
- 不承诺 Herdr Windows beta 不支持的 remote/live handoff/fd handoff/process group 等能力达到 Unix parity。
- 不在本 roadmap 内发布 npm、push、release 或 promotion；Windows npm 目标只到代码层 `npm install` dry-run / `npm pack --dry-run` 证据，真实发布动作仍需独立授权。

### Granularity Gate

| 判断项 | 结论 |
|---|---|
| 为什么不是 single feature | 该需求横跨平台基线、mux contract、Herdr socket adapter、ccbd namespace、provider runtime、bounded recovery、Mobile/Config UI、packaging/update/support 和真实 Windows x64 验证矩阵。 |
| 为什么不是 brainstorm | 方向已经明确：Herdr 作为 Native Windows backend，CCB 保持 control plane/provider authority；剩余问题是拆解、契约和验证路径。 |
| roadmap 边界 | 只覆盖 CCB public workflow parity 的 Native Windows x64 Herdr backend；不做 32-bit/arm64/remote handoff/Herdr 插件化路线。 |
| 最小闭环 | `herdr-backend-contract-spike` 完成后，用 Python/CCB 侧客户端通过 Herdr socket API 创建 session/pane、发送输入、捕获输出、kill pane 并验证 restore identity，证明 Herdr 能提供 CCB 所需 terminal primitive；它不代表 Windows supported。 |

### 开发环境基准

本 roadmap 所有 feature 的 Native Windows 开发、测试、spike 与 evidence 采集均以
以下环境为基准。除非 feature 文档另有声明，以下路径为固化约定：

| 组件 | 固化路径 | 覆盖方式 |
|---|---|---|
| **Herdr 可执行文件** | `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe` | `CCB_HERDR_EXE` 环境变量可覆盖 |
| Herdr 配置目录 | `C:\Users\Administrator\AppData\Roaming\herdr\` | `HERDR_CONFIG_PATH` 可覆盖 |
| Herdr session 目录 | `C:\Users\Administrator\AppData\Roaming\herdr\sessions\` | 由 Herdr 管理 |
| WezTerm 可执行文件 | `C:\Program Files\WezTerm\wezterm.exe` | `WEZTERM_EXECUTABLE` / `WEZTERM_EXECUTABLE_DIR` 可覆盖 |
| CCB 源码根 | `E:\GitHub开源项目\TachiKuma\claude_code_bridge` | `CCB_SOURCE_ROOT` 可覆盖 |
| CCB Runtime State | `D:\.c8\rs` | `CCB_RUNTIME_STATE_HOME` 可覆盖 |
| Python | `C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe` | `CCB_PYTHON` / `CCB_PYTHON_BIN` 可覆盖 |
| Git Bash (sh.exe) | `C:\Program Files\Git\bin\sh.exe` | `CCB_SH_EXECUTABLE` 可覆盖 |

所有 wrapper 脚本（`ccb8.ps1`、`run_spike.ps1`、`diagnose_*.ps1`）的默认 fallback
均为上表中的固化路径。环境变量优先于固化默认值。

## 3. 模块拆分（概设）

```text
windows-native-herdr-ccb
├── Platform Baseline Gate：strict v8.5.2 源头/新分支与 Windows x64 全链路准入
├── Herdr Contract Spike：Herdr socket API 与 CCB 最小 mux 语义验证
├── Backend Contract V2：把既有 tmux/rmux MuxBackend 扩展到 Herdr native backend
├── Herdr Backend Client：Herdr socket client、capability gate、error/evidence 归一
├── CCBD Control Plane Transport：Native Windows 下 `ccb` 到 `ccbd` 的控制面 TCP loopback 前置
├── CCBD Namespace Integration：project session、pane topology、foreground attach 与 lifecycle
├── Provider Runtime Integration：provider 私有状态、启动、ask/pend/completion 在 Herdr pane 上运行
├── Recovery Boundary：CCB bounded recovery 与 Herdr restore 的单一 owner 规则
├── User Surfaces：Mobile terminal、Config UI、doctor/ping/project view 的 Herdr evidence 投影
└── Validation & Support：Native Windows public workflow matrix、packaging、docs、support tier
```

### Platform Baseline Gate · strict v8.5.2 与 Windows x64 准入

- **职责**：确认实现基线严格来自 CCB `v8.5.2` 源头并已在新分支上推进，同时在 install/startup/doctor 中建立 Windows x64-only gate。
- **承载的子 feature**：`windows-x64-v852-baseline-gate`
- **触碰的现有代码 / 模块**：`package.json`、`bin/ccb-npm-install.js`、install/update/versioning、managed Python bootstrap、doctor/startup diagnostics。
- **Depth 判断**：deep。它把“win32 是 OS 名称、x64 是位宽”的平台事实集中到一个准入 gate，避免每条 feature 各自判断位宽。
- **边界**：只定义可复用 platform gate contract、版本/位宽探测和 startup/doctor 基础诊断；不写 npm 发布面投影、不改 update/publish gate 的最终承诺。

### Herdr Contract Spike · socket API 能力验证

- **职责**：用最小 Python 客户端验证 Herdr session/pane/send/capture/kill/restore 以及一个 provider CLI dry-run pane 是否满足 CCB backend contract 的最窄路径。
- **承载的子 feature**：`herdr-backend-contract-spike`
- **触碰的现有代码 / 模块**：`.codestable/roadmap/windows-native-herdr-ccb/drafts/` spike 代码与证据；不改生产代码。
- **Depth 判断**：deep。它是事实型路由 gate，不通过则不应投入正式 adapter。

### Backend Contract V2 · Herdr 适配的 mux 契约升级

- **职责**：复用 `mux-backend-contract` 的小协议思想，将 backend identity、namespace/pane ref、capability、error 分类升级到 `tmux` / `rmux` / `herdr` 可共存。
- **承载的子 feature**：`mux-backend-contract-herdr-v2`
- **触碰的现有代码 / 模块**：`lib/terminal_runtime/mux_backend_contract.py`、fake backend、backend resolver、namespace schema tests。
- **Depth 判断**：deep。它阻止 Herdr 被迫伪装成 tmux-family，同时避免 Herdr 特例散落到 callers。

### Herdr Backend Client · socket adapter 与能力门

- **职责**：封装 Herdr socket API、版本/schema 探测、capability gate、structured error、operation evidence。
- **承载的子 feature**：`herdr-backend-client`
- **触碰的现有代码 / 模块**：新增 `lib/terminal_runtime/herdr_*`，backend resolver/factory，unit tests。
- **Depth 判断**：deep。Herdr 是 true external/local service；adapter 必须隔离 API 漂移和 Windows beta 缺口。

### CCBD Control Plane Transport · Windows `ccb -> ccbd` 控制面前置

- **职责**：恢复 ccbd control-plane transport seam，并在 Native Windows 下使用 TCP loopback + same-user token，使 public `ccb` 命令能够启动并连接 `ccbd`。
- **承载的子 feature**：`ccbd-windows-control-plane-transport`
- **触碰的现有代码 / 模块**：`lib/ccbd/socket_client_runtime/*`、`lib/ccbd/socket_server_runtime/*`、新增/恢复 `lib/ccbd/control_plane_transport/*`、control-plane endpoint diagnostics、focused tests。
- **Depth 判断**：deep。控制面 transport 是跨平台 authority 边界；Unix AF_UNIX、Windows TCP/token、bootstrap 和 endpoint store 需要封装在 adapter seam 内，不能散落在 Herdr namespace 或 CLI 调用层。
- **边界**：只恢复 `ccb<->ccbd` 控制面可连接性；不改 Herdr namespace lifecycle、provider runtime、recovery、Mobile/Config UI、package/release/update。

### CCBD Namespace Integration · 项目 session 与 pane 拓扑

- **职责**：把 Herdr backend 接入 ccbd project namespace、layout/reflow、foreground attach、kill/restart/reload。
- **承载的子 feature**：`ccbd-herdr-namespace-lifecycle`
- **触碰的现有代码 / 模块**：`lib/ccbd/services/project_namespace_runtime/*`、`lib/cli/services/start_foreground.py`、project view、shutdown/reload handlers。
- **Depth 判断**：deep。ccbd 继续是 project authority；Herdr session/pane 只是 terminal runtime evidence。

### Provider Runtime Integration · provider 工作流

- **职责**：让所有公开 provider 在 Herdr pane 内按 CCB 既有隔离与 `ask`/`pend`/completion/cancel contract 工作。
- **承载的子 feature**：`provider-runtime-on-herdr`
- **触碰的现有代码 / 模块**：`lib/cli/services/runtime_launch_runtime/*`、`lib/provider_backends/*` launcher/session/comm、pane log support、dispatcher runtime。
- **Depth 判断**：deep。CCB public workflow parity 的核心是 ask/pend/completion 可信，不是单纯 pane 能启动。

### Recovery Boundary · 单一恢复 owner

- **职责**：对齐 CCB v8.5.2 bounded pane recovery 与 Herdr session restore，避免 CCB 和 Herdr 双重 respawn；Herdr auto restore 不能关闭时直接阻塞 recovery/supported 路径。
- **承载的子 feature**：`herdr-bounded-recovery-boundary`
- **触碰的现有代码 / 模块**：`lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/*`、health monitor、runtime records、Herdr backend diagnostics。
- **Depth 判断**：deep。恢复路径是高风险状态机；必须有单一 owner 和 durable circuit evidence。

### User Surfaces · 用户可见面

- **职责**：把 Herdr backend evidence 投影到 foreground attach、Mobile terminal snapshot、Config UI、doctor、ping、mounted、project view；Mobile terminal 与 Config UI 是 supported hard gate。
- **承载的子 feature**：`herdr-user-surfaces-parity`
- **触碰的现有代码 / 模块**：foreground attach、mobile terminal gateway、Config UI launcher、ping/project-view/doctor render。
- **Depth 判断**：deep。public workflow parity 必须用户可见、可诊断，而不是仅 backend API 可用。

### Validation & Support · 验证、发布面、支持等级

- **职责**：建立 Native Windows x64 validation matrix、npm `os=win32,cpu=x64` package gate、install/update/doctor/docs/support projection；Windows npm 只要求代码层 install dry-run，不授权 publish。
- **承载的子 feature**：`windows-x64-release-surface`, `native-windows-public-workflow-validation-matrix`, `herdr-supportability-projection`
- **触碰的现有代码 / 模块**：`package.json`、install/update scripts、CI/release docs、README、doctor/support bundle。
- **Depth 判断**：deep。支持等级必须由证据驱动，不由单机成功或文档声明驱动。
- **边界**：消费 `windows-x64-v852-baseline-gate` 的 platform gate contract，负责 npm metadata、install/update、native helper packaging、release-surface projection 和 support 文档；不重新实现平台/位宽探测。

## 4. 模块间接口契约 / 共享协议（架构层详设）

### 4.1 Windows x64 Platform Gate

**方向**：install/startup/doctor → platform support policy
**形式**：平台检测结果 + fail-closed diagnostics

**契约**：

```python
class WindowsX64PlatformGate(TypedDict):
    os_platform: Literal["win32"]
    cpu_arch: Literal["x64"]
    node_arch: Literal["x64"]
    python_bitness: Literal["64bit"]
    ccb_source_ref: str
    ccb_branch_ref: str
    ccb_source_status: Literal["strict-v8.5.2", "not-v8.5.2", "unknown"]
    herdr_arch: Literal["x64"]
    helper_arch: dict[str, Literal["x64", "missing", "unknown"]]
    supported: bool
    failure_reason: Literal[
        "not-windows",
        "not-x64",
        "python-not-x64",
        "herdr-not-x64",
        "helper-not-x64",
        "unknown",
    ] | None
    diagnostic: str
```

**约束**：

- `os_platform="win32"` 只表示 Node/npm Windows 平台名；不得据此接受 32-bit Windows。
- `supported=true` 必须同时满足 Node x64、Python 64-bit、Herdr x64、CCB native helper x64。
- implementation admission 必须证明 `ccb_source_status="strict-v8.5.2"`，且 `ccb_source_ref` 指向 CCB `v8.5.2` 源头、`ccb_branch_ref` 指向新建实现分支；当前工作区状态只能产生 blocked/default 证据。
- 32-bit / WOW64 / arm64 native 路径必须 fail closed，并在 doctor/startup 显示 actionable diagnostic。
- npm metadata 使用 `os: ["win32"]` 与 `cpu: ["x64"]`；文档必须解释 `win32` 不是 32-bit。

**Interface 设计检查**：

- Module / interface：install/update/startup/doctor 统一消费 platform gate，不各自解释 `win32`。
- Seam placement：位宽准入放在平台 gate；backend adapter 不重复判断。
- Depth / locality：位宽、helper binary、managed Python 检查集中，后续支持 arm64 时只改此 gate。
- Dependency strategy：local-substitutable。测试可注入 platform/process/binary probe。
- Adapter：无生产 adapter；这是 platform policy。

### 4.2 Backend Selection V2

**方向**：config / CLI / env / platform gate → terminal runtime backend resolver
**形式**：配置字段 + resolver result + diagnostics payload

**契约**：

```python
class MuxBackendSelectionV2(TypedDict):
    backend_family: Literal["tmux-family", "herdr-native"]
    backend_impl: Literal["tmux", "rmux", "herdr"]
    requested_backend: Literal["tmux", "rmux", "herdr", "auto"]
    effective_backend: Literal["tmux", "rmux", "herdr"]
    source: Literal["cli", "project_config", "user_config", "env", "platform_default", "auto_probe"]
    platform_gate: WindowsX64PlatformGate | None
    fallback_used: bool
    fallback_reason: str | None
    capability_report_ref: str | None
    diagnostic: str
```

**约束**：

- 既有 `runtime.mux.backend = "tmux" | "rmux" | "auto"` 需要通过 update 扩展为 `"tmux" | "rmux" | "herdr" | "auto"`。
- Native Windows x64 检测通过后，`auto` / platform default 必须直接路由到 Herdr；Herdr 缺失、版本/schema 不匹配、能力不足或用户未安装时 fail closed 并给出 actionable diagnostic，不得 fallback 成 tmux/rmux 成功。
- 显式 `herdr` 缺 capability 时 fail fast；显式 tmux/rmux 在 Native Windows supported 路径外处理，不能作为 Windows supported 的替代证据。
- Linux/macOS/WSL 默认仍保持 tmux；本 roadmap 不改变非 Windows 默认 backend。
- Herdr 不能伪装为 `backend_family="tmux-family"`；需要兼容旧 payload 时只在 adapter boundary 投影 legacy alias。

**Interface 设计检查**：

- Module / interface：terminal runtime backend resolver 是唯一 selection owner。
- Seam placement：resolver 先运行 platform/capability gate，再交付 backend factory。
- Depth / locality：requested/effective/fallback/source 绑定为一个原子结果。
- Dependency strategy：local-substitutable。测试注入 config/env/platform/Herdr capability。
- Adapter：无，policy 层。

### 4.3 Backend Contract V2

**方向**：CLI / ccbd / provider runtime → terminal runtime backend
**形式**：Python capability protocols + refs + errors

**契约**：

```python
class MuxNamespaceRefV2(TypedDict):
    backend_family: Literal["tmux-family", "herdr-native"]
    backend_impl: Literal["tmux", "rmux", "herdr"]
    namespace_id: str
    session_name: str
    ipc_kind: Literal["unix_socket", "named_pipe", "socket_name", "tcp_loopback", "herdr_socket"]
    ipc_ref: str
    restore_token: str | None

class MuxPaneRefV2(TypedDict):
    backend_impl: Literal["tmux", "rmux", "herdr"]
    pane_id: str
    session_name: str
    window_name: str | None
    agent_slug: str | None

class MuxCapabilitiesV2(TypedDict):
    backend_impl: Literal["tmux", "rmux", "herdr"]
    command_status: dict[str, Literal["supported", "partial", "unsupported", "workaround"]]
    semantic_status: dict[str, Literal["supported", "partial", "unsupported", "workaround"]]
    windows_beta_gaps: list[str]
    blocking_gaps: list[str]

class MuxCommandErrorV2(Exception):
    category: Literal["transient-unavailable", "unsupported", "not-found", "permission", "command-failed", "schema-mismatch"]
    backend_impl: Literal["tmux", "rmux", "herdr"]
    operation: str
    detail: str
    ipc_ref: str | None
    evidence: dict[str, object]
```

能力协议仍按小接口拆分：`NamespaceLifecycle`、`WindowLayout`、`PaneIO`、`PanePresentation`、`PaneLogging`、`DiagnosticsCapability`。Herdr 不支持的能力必须由 `capabilities()` 暴露并由调用方 fail closed 或明确 degraded，不得以空实现通过。

**约束**：

- `restore_token` 是 Herdr restore/session identity 的 opaque 值；调用层不得解析。
- pane id 只在同一 backend/namespace 内稳定；不得要求 Herdr pane id 复刻 tmux `%N`。
- `schema-mismatch` 用于 Herdr socket API 版本/schema 不满足 adapter 要求。
- fake backend 要支持 `backend_impl="herdr"` 的状态机测试，不应 mock Herdr JSON 字符串。

**Interface 设计检查**：

- Module / interface：`terminal_runtime` 暴露 backend contract；ccbd/provider/runtime 只依赖小协议。
- Seam placement：Herdr socket JSON、tmux argv、rmux CLI 均藏在各自 adapter 内。
- Depth / locality：contract 封装 pane identity、restore、capability、error evidence；caller 不知道具体 API。
- Dependency strategy：true external for Herdr service；测试用 local fake adapter。
- Adapter：需要 production Herdr adapter + fake/test adapter；不是假 seam，因为 Herdr schema、ConPTY、restore、Windows beta gaps 会长期变化。

### 4.4 Herdr Socket Client Contract

**方向**：Herdr backend adapter → Herdr socket API
**形式**：本地 socket client + schema/version gate

**契约**：

```python
class HerdrServerInfo(TypedDict):
    version: str
    api_schema: str
    platform: Literal["windows"]
    arch: Literal["x64"]
    socket_ref: str

class HerdrOperationEvidence(TypedDict):
    operation: str
    request_id: str
    herdr_session_id: str | None
    herdr_pane_id: str | None
    status: Literal["ok", "failed", "unsupported", "schema-mismatch"]
    elapsed_ms: int
    detail: str | None

class HerdrBackendClient(Protocol):
    def server_info(self) -> HerdrServerInfo: ...
    def create_session(self, *, project_id: str, cwd: str, title: str) -> MuxNamespaceRefV2: ...
    def restore_session(self, *, restore_token: str) -> MuxNamespaceRefV2: ...
    def create_pane(self, namespace: MuxNamespaceRefV2, *, command: list[str], cwd: str, env: dict[str, str], title: str) -> MuxPaneRefV2: ...
    def send_text(self, pane: MuxPaneRefV2, text: str) -> HerdrOperationEvidence: ...
    def capture_pane(self, pane: MuxPaneRefV2, *, lines: int) -> tuple[str, HerdrOperationEvidence]: ...
    def kill_pane(self, pane: MuxPaneRefV2) -> HerdrOperationEvidence: ...
```

**约束**：

- Herdr socket API schema/version 必须先通过 gate；不匹配返回 `schema-mismatch`，不得猜测字段。
- 生产 adapter 不直接暴露 Herdr JSON 给 ccbd/provider runtime；只返回 CCB refs/evidence。
- Herdr agent state 只进入 `HerdrOperationEvidence` 或 diagnostics，不可直接完成 CCB request。

### 4.5 Provider Runtime On Herdr

**方向**：dispatcher / provider runtime → PaneIO + provider native completion
**形式**：provider launch record + CCB completion evidence

**契约**：

```python
class ProviderRuntimeBackendRef(TypedDict):
    provider: str
    agent_slug: str
    backend_impl: Literal["tmux", "rmux", "herdr"]
    namespace_ref: MuxNamespaceRefV2
    pane_ref: MuxPaneRefV2
    managed_home: str
    completion_source: Literal["provider_native_log", "terminal_capture", "provider_event_stream"]

class HerdrProviderCompletionEvidence(TypedDict):
    request_id: str
    provider: str
    pane_ref: MuxPaneRefV2
    terminal_capture_ref: str | None
    provider_native_ref: str | None
    herdr_agent_state_ref: str | None
    verdict: Literal["completed", "working", "failed", "cancelled", "unknown"]
    reason: str
```

**约束**：

- Provider 私有 HOME、auth、session binding、managed memory、completion contract 仍归 CCB。
- `completion_source` 优先使用 provider native log/event；terminal capture 只能作为辅助或 fallback，必须按 provider design 明确。
- Herdr agent state 不得单独产生 `completed` verdict。

### 4.6 Recovery Owner Contract

**方向**：health monitor / dispatcher recovery → Herdr backend
**形式**：恢复策略与 evidence

**契约**：

```python
class HerdrRecoveryPolicy(TypedDict):
    owner: Literal["ccb"]
    herdr_auto_restore_mode: Literal["disabled"]
    probation_seconds: int
    backoff_schedule_seconds: list[int]
    circuit_threshold: int
    restore_token_required: bool

class HerdrRecoveryEvidence(TypedDict):
    agent_slug: str
    pane_ref_before: MuxPaneRefV2 | None
    pane_ref_after: MuxPaneRefV2 | None
    restore_token_present: bool
    herdr_agent_state_ref: str | None
    action: Literal["observe", "respawn", "reattach", "namespace_recover", "circuit_open", "blocked"]
    reason: str
```

**约束**：

- CCB 是唯一 recovery owner；Herdr restore 只能作为 CCB 调用的 backend operation 或 evidence source。
- raw restore token 只允许进入 CCB 发起的 private backend operation；public event、diagnostics、project view、logs 和 support evidence 只能输出 `restore_token_present` / ref，不得输出 token 值。
- v8.5.2 的 90 秒 probation、bounded crash logs、backoff/circuit 语义必须保留。
- Herdr 自身自动恢复必须可关闭并由 evidence 证明 `herdr_auto_restore_mode="disabled"`；`observe-only`、`unsupported` 或 `unknown` 最多进入 diagnostics/blocked evidence，不能进入 recovery-capable 或 Windows supported 路径。

### 4.7 Public Workflow Evidence

**方向**：validation matrix / acceptance / support projection → docs/doctor/support
**形式**：机器可读 evidence JSON

**契约**：

```python
class WindowsHerdrPublicWorkflowEvidence(TypedDict):
    backend_impl: Literal["herdr"]
    os_platform: Literal["win32"]
    cpu_arch: Literal["x64"]
    ccb_version: Literal["8.5.2"]
    herdr_version: str
    ccb_source_status: Literal["strict-v8.5.2", "blocked", "unknown"]
    herdr_auto_restore_mode: Literal["disabled", "observe-only", "unsupported", "unknown"]
    workflows: dict[str, Literal["pass", "partial", "blocked", "failed", "not-run"]]
    required_workflows: list[Literal[
        "ccb",
        "ask",
        "pend",
        "watch",
        "ping",
        "mounted",
        "kill",
        "restart",
        "reload",
        "foreground_attach",
        "mobile_terminal",
        "config_ui",
        "doctor_update",
        "support_projection",
    ]]
    public_providers: list[str]
    provider_workflow_rows: dict[str, dict[Literal["ask", "pend", "completion", "cancel"], Literal["pass", "partial", "blocked", "failed", "not-run"]]]
    mobile_terminal_status: Literal["pass", "partial", "blocked", "failed", "not-run"]
    config_ui_status: Literal["pass", "partial", "blocked", "failed", "not-run"]
    windows_npm_install_dry_run_status: Literal["pass", "partial", "blocked", "failed", "not-run"]
    beta_gaps: list[str]
    residual_risks: list[str]
    artifacts: dict[str, str]
    support_tier: Literal["unsupported", "experimental", "beta", "supported"]
```

**约束**：

- `support_tier="supported"` 需要 core workflows 全部 `pass`、所有公开 provider 的 `ask/pend/completion/cancel` 全部 `pass`、Mobile terminal 与 Config UI 均 `pass`、`windows_npm_install_dry_run_status="pass"`、`ccb_source_status="strict-v8.5.2"`、`herdr_auto_restore_mode="disabled"` 且无 blocking beta gaps。
- `public_providers` 必须来自当前公开 provider catalog，或在 acceptance 中冻结一份可审计 provider 清单；新增公开 provider 后必须进入 provider workflow rows，不能沿用旧 supported evidence。
- `required_workflows` 是最低 key set；feature-design 可扩展，但不得删减上述 public workflow key。
- `partial` / `blocked` 不得被 README、doctor、installer 描述为 full support。
- evidence 必须由专用 Native Windows x64 真机或明确标注的 Windows runner 产出；本项目当前所在机器是目标 Windows x64 验证主机。WSL/Linux 证据不能替代。

## 5. 子 feature 清单

1. **windows-x64-v852-baseline-gate** — 建立 CCB `v8.5.2` + Native Windows x64-only 准入和诊断。
   - 所属模块：Platform Baseline Gate
   - 依赖：无
   - 状态：accepted
   - 对应 feature：`2026-07-31-windows-x64-v852-baseline-gate`
   - 备注：只产出 platform gate contract、版本/位宽探测和 startup/doctor 基础诊断；必须解释 `os=win32,cpu=x64`；implementation admission 必须证明从 CCB `v8.5.2` 源头拉取并在新分支推进，当前工作区状态只能 blocked/default。

2. **herdr-backend-contract-spike** — 用 Herdr socket API 验证 session/pane/send/capture/kill/restore 与 provider dry-run pane 最小语义。
   - 所属模块：Herdr Contract Spike
   - 依赖：`windows-x64-v852-baseline-gate`
   - 状态：accepted
   - 对应 feature：`2026-07-31-herdr-backend-contract-spike`
   - 备注：只写 spike 与 evidence，不改生产代码；Restore Capability Matrix v2 证据为 `verdict=partial`、`failure_class=windows-beta-gap`、`adapter_recommendation=continue-with-gaps`。`platform-gate-summary.json` 已修正为 `ccb_source_status=strict-v8.5.2`、Python 为 64-bit，`C:/Users/Administrator/AppData/Local/Programs/Herdr/herdr.exe` 为 x64，且两个 CCB native helper PE header 为 x64；schema/status/session_attach/pane_spawn/send_input/read_output/kill_pane/server_restart_layout_restore 已通过。server_restart_process_continuity 与 server_restart_output_history 明确 unsupported；ui_detach_reattach 需要 Herdr UI harness，已记录 follow-up `herdr-ui-detach-reattach-harness`。后续 adapter 可按 layout-only restart restore + CCB-side recovery 继续，不得宣称 process/output continuity 或 Windows supported。

3. **mux-backend-contract-herdr-v2** — 将既有 mux 小协议升级到 `tmux` / `rmux` / `herdr` 共存，并保留 legacy compatibility。
   - 所属模块：Backend Contract V2
   - 依赖：`herdr-backend-contract-spike`
   - 状态：accepted
   - 对应 feature：`2026-07-31-mux-backend-contract-herdr-v2`
   - 备注：Herdr 伪装为 tmux-family；交付 backend contract V2（backend-neutral refs/capabilities/structured errors）、fake Herdr fixture、resolver V2 诊断、上游 spike->capability fail-closed 投影。Native Windows x64 + 合规 capability evidence 才路由 herdr，否则 fail-closed（herdr-capability-missing / platform-gate-blocked / unsupported-capability），非 Windows 保留 tmux/rmux。不引入生产 Herdr client；CMD-001..006 全 exit 0，34+16 tests passed，运行时功能断言全过。为下游 `herdr-backend-client` 提供内部 CCB contract。

4. **herdr-backend-client** — 实现 Herdr socket client、schema/version gate、capability/error/evidence 映射。
   - 所属模块：Herdr Backend Client
   - 依赖：`mux-backend-contract-herdr-v2`
   - 状态：accepted
   - 对应 feature：`2026-07-31-herdr-backend-client`
   - 备注：交付 terminal_runtime Herdr backend/client、CLI adapter、schema/capability fail-closed gate、operation evidence 与 resolver/factory gated route；explicit herdr 和 Native Windows auto gate 失败均返回 V2 diagnostics，不 fallback tmux，非 Windows auto/default 不变。真实 Herdr host smoke 未在本机运行，留给后续集成验证。

5. **ccbd-windows-control-plane-transport** — 恢复 ccbd control-plane transport seam 与 Windows TCP loopback adapter，使 Native Windows `ccb->ccbd` 控制面可启动。
   - 所属模块：CCBD Control Plane Transport
   - 依赖：`herdr-backend-client`
   - 状态：accepted
   - 对应 feature：`2026-08-02-ccbd-windows-control-plane-transport`
   - 备注：accepted 2026-08-02；只恢复 `ccb<->ccbd` 控制面 seam、Unix adapter 不漂移、Windows TCP loopback + same-user token、endpoint store/bootstrap/diagnostics redaction。CMD-008 manifest 证明 control-plane transport blocker removed；原始 transcript 中 namespace create、foreground attach、reload apply 仍 blocked，归属后续 `ccbd-herdr-namespace-lifecycle`。

6. **ccbd-herdr-namespace-lifecycle** — 把 Herdr backend 接入 ccbd project namespace、layout、foreground attach、kill/restart/reload。
   - 所属模块：CCBD Namespace Integration
   - 依赖：`ccbd-windows-control-plane-transport`
   - 状态：accepted
   - 对应 feature：`2026-07-31-ccbd-herdr-namespace-lifecycle`
   - 备注：accepted 2026-08-02；ccbd 仍是 authority，Herdr session/pane 是 terminal backend evidence。CMD-013 Native Windows x64 transcript 覆盖 namespace create、foreground attach、reload apply、restart deferred 和 kill；provider runtime/recovery/user-surface/release 留给后续 child。

7. **provider-runtime-on-herdr** — 让所有公开 provider 的启动、`ask`、`pend`、completion、cancel 在 Herdr pane 中按 CCB 语义工作。
   - 所属模块：Provider Runtime Integration
   - 依赖：`ccbd-herdr-namespace-lifecycle`
   - 状态：accepted
   - 对应 feature：`2026-07-31-provider-runtime-on-herdr`
   - 备注：accepted 2026-08-03；S1-S7、review、QA、acceptance 均通过。Herdr assigned pane launch 不要求 tmux binary，不走 detached tmux fallback / size probe，session payload 写入 ProviderRuntimeBackendRef、managed_home、completion_source/completion_source_kind、Herdr namespace_ref/pane_ref 与 restore token redaction，backend_for_session 能构造 Herdr backend且未知 backend 不回退 tmux；pane_log_support/Claude/Codex/Gemini/Opencode ensure_pane 对 Herdr 使用 pane_ref liveness/log/capture，不调用 tmux ownership/rebound；provider execution/dispatcher tracker 继续是 completion authority，terminal decision/snapshot 保留精确 completion_source_kind，terminal capture fallback 带 provider-declared diagnostics，Herdr agent state completed verdict fail closed；cancel 使用结构化 pane_ref / best-effort interrupt，dispatcher 仍只写 cancelled decision；Herdr restart surface 明确 unsupported/deferred 并返回 respawn/session binding not_attempted evidence，不接管 bounded recovery。S7 冻结当前 public provider catalog 20 项（含新增 qoder/qoderclicn），全部 provider 行都有 Native Windows x64 blocked evidence；因缺生产 API 授权/credential readiness 或 CLI 缺失，不得宣称 supported。下游 recovery/user-surface/release/public matrix/supportability 必须继续 fail closed。

8. **herdr-bounded-recovery-boundary** — 对齐 CCB v8.5.2 bounded recovery 与 Herdr restore，避免双重恢复。
   - 所属模块：Recovery Boundary
   - 依赖：`provider-runtime-on-herdr`
   - 状态：accepted
   - 对应 feature：`2026-07-31-herdr-bounded-recovery-boundary`
   - 备注：accepted 2026-08-03；CCB 作为唯一 recovery owner，Herdr auto restore 非 `disabled` 直接 blocked/fail-closed。交付 Herdr recovery policy/evidence ledger redaction、raw restore token presence 投影、90 秒 probation、Herdr 3 次 circuit threshold、lifecycle-start tick durable `recover_blocked` evidence、backend-neutral Herdr pane_ref primitive 和 tmux/rmux recovery regression。真实 Herdr server 当前 `not_running` / `capabilities=null`，只作为 blocked evidence，不能宣称 supported recovery。

9. **herdr-user-surfaces-parity** — 将 Herdr evidence 投影到 foreground attach、Mobile terminal、Config UI、doctor、ping、mounted、project view。
   - 所属模块：User Surfaces
   - 依赖：`provider-runtime-on-herdr`, `herdr-bounded-recovery-boundary`
   - 状态：accepted
   - 对应 feature：`2026-07-31-herdr-user-surfaces-parity`
   - 备注：accepted 2026-08-03；S1-S8、review、QA、acceptance 均通过。Herdr evidence 已投影到 ProjectView、ping、foreground attach、Mobile terminal、Config UI、doctor、mounted 和 diagnostics bundle；Mobile/Config partial 或 degraded 只输出 blocked evidence，不能进入 supported。CMD-008 Native Windows x64 transcript 覆盖 public surface pass/blocked gate；本 child 不声明 Windows x64 CCB final supported，后续 release surface、validation matrix 和 supportability projection 仍需继续 fail closed。

10. **windows-x64-release-surface** — 补齐 npm `os=win32,cpu=x64`、managed Python、native helper、install/update/doctor gate。
   - 所属模块：Validation & Support
   - 依赖：`windows-x64-v852-baseline-gate`, `herdr-user-surfaces-parity`
   - 状态：accepted
   - 对应 feature：`2026-07-31-windows-x64-release-surface`
   - 备注：消费 `windows-x64-v852-baseline-gate` 的 platform gate，不重新实现位宽探测；不发布、不 promotion；只建立 release surface 和 code-level Windows `npm install` dry-run gate。

11. **native-windows-public-workflow-validation-matrix** — 覆盖 CCB public workflow parity 的 Native Windows x64 真机验证矩阵。
    - 所属模块：Validation & Support
    - 依赖：`windows-x64-release-surface`, `herdr-user-surfaces-parity`
    - 状态：accepted
    - 对应 feature：`2026-07-31-native-windows-public-workflow-validation-matrix`
    - 备注：accepted 2026-08-03；建立 evidence schema、required workflow key set、public provider workflow rows、parent admission 与 root-aware artifact validator。当前 matrix 是 blocked candidate：`support_projection_allowed=false`、`support_tier=beta`、`support_tier_is_candidate=true`，不得声明 Native Windows supported；后续 supportability projection 必须重新消费并 fail closed。

12. **herdr-supportability-projection** — 将 validation evidence 汇总到 support tier、README/docs、doctor 和 residual risk。
    - 所属模块：Validation & Support
    - 依赖：`native-windows-public-workflow-validation-matrix`
    - 状态：accepted
    - 对应 feature：`2026-07-31-herdr-supportability-projection`
    - 备注：core workflows、所有公开 provider、Mobile/Config UI、Herdr auto restore disabled、strict `v8.5.2`、Windows npm install dry-run 未全 pass 前只能是 experimental/beta/unsupported，不得宣称 supported。

13. **ccb8-bootstrap-shim-slimming** — 消除 ccb8.ps1 与 Python 侧的职责重叠，将 dispatch 语义从 PowerShell bootstrap shim 渐进迁移到 CCB/Herdr 结构化边界。
    - 所属模块：Validation & Support（一键启动体验优化）
    - 依赖：ITEM-7（`ccb herdr open` 一键启动已交付）
    - 状态：planned（2026-08-10 立项）
    - 对应 epic 子项：ITEM-8
    - 对应 compound：`2026-08-10-ccb8-bootstrap-shim-analysis`
    - 对应 lesson：`2026-08-10-herdr-dispatch-interactive-terminal`
    - 优先级：
      - P0：删 PowerShell 中与 `HerdrCliRequestAdapter._start_server()` 重复的 server 启动 + session 探活逻辑（~80 行）
      - P1：`ccb herdr open --wait-ready`，ccbd 就绪等待从 PowerShell `lifecycle.json` 轮询移入 Python `handle_herdr_open()`
      - P2：Herddr UI attach 从 `wezterm cli send-text --no-paste` 键盘注入迁移为结构化 `herdr agent start` 或 `herdr session attach`
      - P3：对齐 WezTerm `default_prog` 与"形态 2"文档
      - 长期：新增 `ccb herdr dispatch` 结构化原语，PowerShell 退化为 ~50 行 env 引导层
    - 备注：P0/P1 不依赖 Herdr 侧变更，仅消除 CCB 内部重复；P2 依赖 Herdr agent start API 可用性。`send-text` 在当前 Herdr 约束下是已接受的有效 workaround，不是 bug。

**最小闭环**：第 2 条 `herdr-backend-contract-spike` 做完后，能够在 Native Windows x64 上通过 Herdr socket/CLI API 证明 CCB 最小 backend 语义可行；它不代表 public workflow parity 完成，只决定是否继续投入正式 adapter。当前 Restore Capability Matrix v2 证明基础 primitive 与 server restart layout restore 可用，route recommendation 为 `continue-with-gaps`；goal driver 可以继续正式 Herdr adapter，但必须把 restart restore 限定为 layout-only，并把 UI detach/reattach 留给 follow-up harness。

### Goal Coverage Matrix

| Goal / completion signal | Covered by item(s) | Verification entry | Evidence type | Core? |
|---|---|---|---|---|
| CCB 基线严格来自 `v8.5.2` 源头、新分支推进，且平台为 Windows x64-only | `windows-x64-v852-baseline-gate` | source/ref/branch admission + version/package/platform gate tests + doctor output | unit/CLI/source evidence | yes |
| Herdr socket API 能创建 session/pane、发送输入、捕获输出、kill pane、恢复 identity，并启动一个 provider dry-run pane | `herdr-backend-contract-spike` | spike script on Native Windows x64 | spike evidence JSON | yes |
| Herdr backend 不伪装 tmux-family，调用层只依赖小协议 | `mux-backend-contract-herdr-v2` | contract/fake backend tests | unit/diff review | yes |
| Herdr socket schema/version/capability 缺口 fail closed | `herdr-backend-client` | client tests + schema mismatch fixture | unit evidence | yes |
| Native Windows 下 public `ccb` 命令能启动并连接 `ccbd` 控制面 | `ccbd-windows-control-plane-transport` | Windows TCP loopback transport tests + CMD-013 retry | unit/manual transcript | yes |
| `ccb` project namespace 能由 Herdr backend 创建、attach、kill、restart、reload | `ccbd-herdr-namespace-lifecycle` | Windows foreground/manual + focused pytest | command/manual transcript | yes |
| 所有公开 provider 的 `ask` / `pend` / completion / cancel 在 Herdr pane 中保持 CCB provider authority | `provider-runtime-on-herdr`, `native-windows-public-workflow-validation-matrix` | provider-specific focused tests + per-provider Native Windows transcript matrix | pytest/runtime/manual evidence | yes |
| `watch` 能在 Herdr pane 工作流中持续显示 streaming/output/cancellation 状态，且不会把 Herdr agent state 当 completion authority | `provider-runtime-on-herdr`, `herdr-user-surfaces-parity`, `native-windows-public-workflow-validation-matrix` | watch transcript on Native Windows x64 | streaming transcript / runtime evidence | yes |
| pane/provider crash recovery 保留 v8.5.2 bounded semantics，且 Herdr auto restore 可证明 disabled | `herdr-bounded-recovery-boundary` | recovery tests + auto-restore-disabled evidence + crash evidence | pytest/evidence JSON | yes |
| Mobile terminal、Config UI、doctor/ping/mounted/project view 可见且可诊断，Mobile/Config 不 degraded | `herdr-user-surfaces-parity`, `native-windows-public-workflow-validation-matrix` | mobile gateway tests + Config UI tests + CLI render tests + manual UI transcript | test/manual evidence | yes |
| npm/install/update 能表达 `os=win32,cpu=x64` 且不接受 32-bit 链路，Windows npm install dry-run 通过 | `windows-x64-release-surface` | package dry run + npm install dry-run + install/update tests | command/diff evidence | yes |
| public workflow parity matrix 全部核心项与所有公开 provider 行有 pass/partial/blocked 证据 | `native-windows-public-workflow-validation-matrix` | validation matrix runner + provider workflow rows | evidence JSON | yes |
| support tier 不夸大 beta/unsupported gaps，且仅在所有 hard gate 通过时输出 supported | `herdr-supportability-projection` | docs/doctor/support projection tests | diff/CLI render evidence | yes |

## 6. 排期思路

顺序以风险递减和依赖 DAG 为主。先做 strict x64/v8.5.2 源头/新分支基线，避免在旧工作区或混合 bitness 上做无效实现；再做 Herdr spike，用事实决定是否继续。spike 通过后再升级 backend contract 和 adapter；只有 backend 和 namespace lifecycle 稳定后才进入 all-provider runtime。恢复、用户可见面、release surface、validation matrix 与 support projection 放在后半段，避免在核心 backend 还不成立时先写发布面承诺。

Top 3 风险与缓解：

- **Herdr socket API 不足或不稳定**：用 `herdr-backend-contract-spike` 和 `herdr-backend-client` schema gate 先证伪，失败即停止 adapter 投入。
- **CCB 与 Herdr 双 authority**：roadmap 明确 CCB owns provider/control/recovery，Herdr owns terminal primitive；agent state 只作为 evidence。
- **Windows support 夸大**：platform gate、validation matrix、support projection 强制把 x64-only、beta gaps 和 residual risk 体现在 doctor/docs 中。
- **单 provider 或 degraded UI 被误当 supported**：provider runtime 与 validation matrix 必须覆盖所有公开 provider 的 `ask/pend/completion/cancel`，Mobile terminal 与 Config UI 作为 supported hard gate。

关键假设：

- Herdr 由用户自备，并可在 Native Windows x64 上以稳定 socket API 暴露 session/pane/send/capture/restore；CCB 只负责检测、诊断和路由，不负责下载安装 Herdr。
- CCB v8.5.2 的 bounded recovery 和 provider completion contract 可迁移到 Herdr pane，而无需改 provider auth/session 权威模型。
- 当前 tmux/rmux backend contract 产物可以演进为 V2，而不需要推翻重写。

非显然依赖：

- 当前工作区与 `v8.5.2` 源头不一致，实现前必须从 CCB 源头拉取 `v8.5.2` 并新建分支；当前代码状态不能作为实现基线。
- Herdr Windows beta 的不支持项会影响 support tier，但不必阻塞 CCB core public workflow parity，除非它们进入 core workflow。
- Native Windows 真实验证不可由 WSL/Linux 替代；专用验证主机就是当前项目所在 Windows x64 机器。

基线与验证入口：

- YAML/spec：`.codestable/tools/validate-yaml.py`
- Python tests：`python -m pytest -q ...`
- Package/release：`npm pack --dry-run`、Windows `npm install` dry-run、install/update focused tests
- Native Windows evidence：Herdr spike/validation matrix JSON、foreground transcript、doctor/ping/mounted output
- Mobile/Config UI：existing mobile gateway/render tests + manual Windows x64 transcript

知识回写点：

- 若实现确认 Herdr backend adapter 是长期结构性方案，应提示走 `cs-domain` 写 ADR。
- 若 x64-only gate 形成长期发布约束，应提示用 `cs-note` 或 `cs-keep` 沉淀 `os=win32,cpu=x64` 语义。
- 若 Herdr Windows beta gap 形成稳定 unsupported boundary，应在 support projection acceptance 后沉淀到 docs/doctor/support 规则。

## 7. 观察项

- `windows-rmux-native-backend` 已完成并包含大量可复用 mux contract / namespace schema / control plane 经验；Herdr roadmap 应复用这些设计，避免重复抽象。
- `windows-rmux-ux-parity-hardening` 已 owner pause；若后续 Herdr 路线失败，恢复 rmux 线需要 owner 明确选择。
- Herdr 版本与 socket API schema 尚未锁定；正式 design 前不能依赖网页文字猜测具体字段名。
- CCB `v8.5.2` npm metadata 当前未包含 Windows release surface；这不是位宽问题，而是发布支持范围问题。
