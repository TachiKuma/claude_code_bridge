---
doc_type: roadmap
slug: windows-rmux-native-backend
status: active
created: 2026-07-06
last_reviewed: 2026-07-19
tags: [windows, rmux, mux-backend, terminal-runtime, ccbd-control-plane, af-unix]
related_requirements: []
related_architecture:
  - docs/ccbd-windows-psmux-plan.md
  - docs/plantree/plans/windows-wezterm-native/README.md
  - docs/ccbd-startup-supervision-contract.md
  - docs/ccbd-diagnostics-contract.md
  - docs/ccb-config-layout-contract.md
---

# Windows Rmux Native Backend

## 1. 背景

CCB 当前最新版以 tmux 作为项目 UI 和 runtime pane 的核心多路复用后端。Linux、macOS、WSL 路线已经围绕 tmux socket、session、pane、capture、send-keys、pipe-pane 和 project namespace 建立了完整闭环；原生 Windows 长期缺少足够接近 tmux 的稳定 mux 基座。

Rmux 提供原生 Windows ConPTY、same-user named pipe、本地 daemon、tmux-compatible CLI、Python/TypeScript/Rust SDK，并在 v0.8.0 强化了 Windows attach、PowerShell/cmd、ConPTY、tmux command compatibility。它比 Windows Terminal / WezTerm 更贴近 CCB 现有 tmux-family 控制模型，但不能假设“把 rmux 当 tmux 放到 PATH”即可获得全功能。本 roadmap 目标是在不破坏现有 tmux 用户的前提下，为原生 Windows 提供可验证、可回退的 Rmux 后端路线。

`docs/ccbd-windows-psmux-plan.md` 是本路线的前置 Windows tmux-family 方案材料，其中的 `psmux` 表示“原生 Windows 下接近 tmux 的 mux 基座”这一类方案，而不是本 roadmap 要继续实现的具体后端名。本 roadmap 将该类方案的候选实现收敛到 Rmux：版本下限以 capability gate 实测的 Rmux release 为准，初始假设为 v0.8.0 或更新；安装与发现方式必须在后续 packaging/docs item 中明确区分 Windows npm 分发和 `install.ps1` 本地安装。若 capability gate 证明 Rmux 不满足 required set，旧 psmux/其他 mux 方向需要重新开选型，而不是在本 roadmap 内静默替换。

### v8.2.1 再基线（2026-07-19）

本 roadmap 初稿基于 ccb v8.0.16。2026-07-19 owner 要求以 **ccb v8.2.1**（当前 checkout VERSION=8.2.1）及之后提交为基线，落地终点为「`ccb→ccbd→rmux` 全链路在 native Windows 真跑通」（WezTerm 仅作宿主 GUI 终端，不动 mux 选型）。再基线核实：§4 全部代码锚点文件在 v8.2.1 仍存在，`backend_selection.py` 仍 tmux-only，接口契约与模块拆分依然成立，故本轮为 **update 补缺 + 重排关键路径**，非重写。

再基线纳入一个原 roadmap 完全缺失、却是上述终点必经的独立 blocker：**ccbd 控制面自身的 RPC transport 硬编码 AF_UNIX**。原 roadmap 隐含假设 ccbd 在 Windows 已能起，只规划了 mux 后端；但 native Windows 无 AF_UNIX，`ccb→ccbd` 控制面 RPC 根本起不来——历史所有「Windows 能跑」证据都是 probe 直驱 rmux **绕过 ccbd**，从未证明全链路。该 transport 与 rmux mux 后端**正交**，两条 track 可并行，但都是终点的前置。详见新增模块 “CCBD Control Plane Transport” 与接口契约 §4.9；实测硬编码点见 §8 观察项。

## 2. 范围与明确不做

### 本 roadmap 覆盖

- 在 Windows 真机上验证 Rmux 是否满足 CCB 所需 tmux-family 命令与语义。
- 收束 CCB 现有 `TmuxBackend` 上层依赖，形成可承载 tmux 与 Rmux 的 `MuxBackend` 契约。
- 引入 Windows 原生 IPC、shell、日志与进程树治理边界，避免平台差异散落到业务层。
- 实现 opt-in `RmuxBackend`，接入 project namespace、layout、send/capture、provider runtime、supervision、diagnostics。
- 建立 Windows 原生全链路测试矩阵，证明 `ccb` / `ccb ask` / `ccb kill` / pane 恢复 / 多项目隔离可运行。

### 明确不做

- 不把 Rmux 作为 Linux/macOS 默认后端；现有 tmux 路线保持稳定。
- 不要求第一版复制 tmux 每个 UI option 或 control-mode 细节；只承诺 CCB 依赖的命令与语义。
- 不在本 roadmap 内重写 provider-native completion 解析；provider 层只通过统一 runtime 接口接入。
- 不恢复旧 WezTerm backend，不把 Windows Terminal 作为后台 mux authority。
- 不把 `rmux` 零改动伪装成 `tmux` 作为最终架构；可作为 capability probe 的临时手段。

### 本轮里程碑范围（v8.2.1 再基线终点）

owner 本轮选定的终点是「全链路跑通」，不是整条 roadmap 的可交付收口。里程碑 `windows-rmux-native-working` 的验收边界：

- **里程碑内**：ccbd 控制面 transport（seam + Windows TCP loopback）、accelerator AF_UNIX guard、rmux 后端从 capability-gate 到 `ccbd-rmux-namespace-lifecycle` 的实现链、以及终点验收 item `ccbd-windows-full-chain-smoke`（`ccb` 启动 / `ccb ask` / `ccb kill` 真链路跑通）。
- **里程碑外（留在 roadmap，post-milestone）**：`rmux-supervision-recovery`（pane/provider/daemon crash 恢复）、`rmux-windows-validation-matrix` 的多 agent / 多项目并行矩阵、`rmux-packaging-docs-contracts`（安装 / 打包 / 文档收口）。这些不删、不 drop，只是不阻塞本轮终点。

「跑通」与「可日常使用 / 可交付」是两个验收档；本轮只承诺前者。

### Granularity Gate

| 判断项 | 结论 |
|---|---|
| 为什么不是 single feature | 该需求横跨 terminal runtime、ccbd namespace、CLI foreground attach、diagnostics、installer/package、Windows IPC/process lifecycle 和真实平台测试，必须拆成多条可独立验证的 feature。 |
| 为什么不是 brainstorm | 真问题、候选基座和成功标准已经清楚：验证并落地 Rmux 作为原生 Windows mux backend。未知点是事实型 capability 与实现分期，适合 roadmap 规划。 |
| roadmap 边界 | 本次只覆盖 Rmux 后端路线，不扩大到 WezTerm/Windows Terminal，也不改变现有 Linux/macOS tmux 默认行为。 |
| 最小闭环 | `rmux-capability-gate` 完成后，能基于 Windows 真机证据判断是否继续实现，避免在不满足命令语义时提前重构。 |

## 3. 模块拆分（概设）

```
windows-rmux-native-backend
├── CCBD Control Plane Transport：ccbd 控制面 RPC 的平台 transport seam（Unix socket / Windows TCP loopback）与 same-user 鉴权【v8.2.1 再基线新增】
├── Accelerator Transport Guard：runtime_accelerator 控制面的 Windows AF_UNIX 兜底【v8.2.1 再基线新增】
├── Capability Gate：Windows 真机能力探针和差距分类
├── Backend Resolver & Opt-in：后端选择、优先级、fail-safe 和诊断
├── MuxBackend Contract：tmux-family 后端契约与现有 TmuxBackend 收口
├── Windows Runtime Boundary：named pipe、shell、日志、job object 与路径语义
├── Rmux Daemon Ownership：Rmux daemon 发现、启动、健康检查与归属
├── RmuxBackend：Rmux CLI/SDK 驱动的 mux backend 实现
├── CCBD Integration：project namespace、layout、supervision、foreground attach 接入
├── Provider Runtime Contract：provider session payload、env、runtime health 的 backend-neutral 迁移
└── Validation & Packaging：真实平台测试、诊断、安装与文档收口
```

### Capability Gate · Windows 真机能力探针

- **职责**：在原生 Windows 上以黑盒方式验证 Rmux 对 CCB 必需命令和语义的支持，产出 capability table 与 gap list；不改主链路。
- **承载的子 feature**：`rmux-capability-gate`
- **触碰的现有代码 / 模块**：新增 probe 脚本和报告；可参考 `scripts/probe_codex_pane_status.py` 的证据记录方式。
- **Depth 判断**：deep。它把后续所有实现路线的事实前提集中到一份可重复探针和报告里，避免每条 feature 重复摸索。

### Backend Resolver & Opt-in · 后端选择入口

- **职责**：定义用户如何 opt-in Rmux、平台默认如何选择、自动探测何时允许、显式选择失败时如何 fail-safe、诊断如何展示选择原因。
- **承载的子 feature**：`backend-resolver-opt-in-contract`
- **触碰的现有代码 / 模块**：`lib/terminal_runtime/backend_selection.py`、config loading、CLI startup、diagnostics / doctor。
- **Depth 判断**：deep。它是对外开关和 fallback seam；如果不先定义，`RmuxBackend` 即使实现也没有可审计的启用路径。

### MuxBackend Contract · 后端契约收口

- **职责**：定义上层依赖的最小 mux 能力，隔离 `tmux` 可执行名、socket path、pane id、shell quoting、pipe/log 等实现差异。
- **承载的子 feature**：`mux-backend-contract`, `tmux-backend-contract-adapter`
- **触碰的现有代码 / 模块**：`lib/terminal_runtime/*`、`lib/cli/services/start_foreground.py`、`lib/cli/services/tmux_ui_runtime/*`、`lib/ccbd/services/project_namespace_runtime/*`
- **Depth 判断**：deep。上层只知道 namespace/session/window/pane/capture/send/attach/policy 语义，复杂度留在 backend implementation。

### Windows Runtime Boundary · Windows 运行时边界

- **职责**：承接 Rmux Windows named pipe、PowerShell/cmd/pwsh shell 命令包装、日志管道、进程树 Job Object、路径与环境变量差异。
- **承载的子 feature**：`windows-namespace-ipc-schema`, `windows-shell-log-builder`, `windows-job-object-runtime-evidence`
- **触碰的现有代码 / 模块**：`lib/terminal_runtime/env.py`、runtime authority schema、diagnostics、Windows install/runtime helpers。
- **Depth 判断**：deep。Windows 平台差异必须集中在此边界内，不能扩散为业务层 `if windows`。

### Rmux Daemon Ownership · Rmux daemon 归属边界

- **职责**：定义 Rmux daemon 的发现、启动、健康检查、crash evidence、shutdown 参与顺序，以及它与 `ccbd` authority 的关系。
- **承载的子 feature**：`rmux-daemon-ownership-boundary`
- **触碰的现有代码 / 模块**：backend resolver、`RmuxBackend` daemon client、runtime authority、ccbd startup/shutdown/supervision diagnostics。
- **Depth 判断**：deep。Rmux daemon 是外部本地服务；它不能变成第二个项目 authority，也不能在 crash/restart 时绕过 ccbd lifecycle。

### RmuxBackend · Rmux 后端实现

- **职责**：在 `MuxBackend` 契约下调用 Rmux CLI 或 SDK，实现 namespace、pane、send/capture、pipe/log、respawn、UI metadata、capability degrade。
- **承载的子 feature**：`rmux-backend-core`, `rmux-send-capture-logging`
- **触碰的现有代码 / 模块**：新增 `lib/terminal_runtime/rmux_*`，少量接入 backend resolver。
- **Depth 判断**：deep。它应隐藏 Rmux tiny/full CLI、named pipe、format output 与 Windows PTY 差异。

### CCBD Integration · daemon 与项目生命周期接入

- **职责**：把 RmuxBackend 接入 `ccbd` project namespace、layout projection、supervision、foreground attach、kill/recover 和 diagnostics。
- **承载的子 feature**：`ccbd-rmux-namespace-lifecycle`, `rmux-supervision-recovery`
- **触碰的现有代码 / 模块**：`lib/ccbd/*`、`lib/cli/services/start.py`、`lib/cli/services/start_foreground.py`、project view/doctor/bundle。
- **Depth 判断**：deep。ccbd 仍是 authority，Rmux 只提供 mux evidence 和操作表面。

### Provider Runtime Contract · provider session 与健康检查契约

- **职责**：把 provider launch、session payload、runtime health、provider env 中的 `terminal=tmux` / `tmux_session` / `TmuxBackend` 假设迁移为 backend-neutral 字段，并保留兼容别名。
- **承载的子 feature**：`provider-runtime-backend-session-contract`
- **触碰的现有代码 / 模块**：`lib/cli/services/runtime_launch.py`、`lib/cli/services/runtime_launch_runtime/*`、`lib/provider_backends/native_cli_support/launcher.py`、provider health/session readers。
- **必须纳入的 provider 触点**：`lib/cli/services/runtime_launch_runtime/session_files.py`、`lib/provider_backends/*/launcher*.py`、`lib/provider_backends/*/launcher_runtime/*`、`lib/provider_backends/pane_log_support/session.py`、各 provider session reader / health checker、provider env 中读取 `*_TMUX_SESSION` 的路径。
- **Depth 判断**：deep。`ccb ask` 和 provider recovery 依赖 session authority；如果这里仍写死 tmux，Rmux namespace 接入后仍会在 submit/health/recovery 路径漂移。

### Validation & Packaging · 验证、安装、文档

- **职责**：补齐 Windows CI/手工 runbook、installer/package gating、用户文档和最终 contract 更新。
- **承载的子 feature**：`rmux-windows-validation-matrix`, `rmux-packaging-docs-contracts`
- **触碰的现有代码 / 模块**：`.github/workflows/*`、`install.ps1`、README/docs、diagnostics docs、package metadata。
- **Depth 判断**：deep。交付可信度来自重复验证和文档契约，而不是一次本机成功。

### CCBD Control Plane Transport · ccbd 控制面 transport 边界【v8.2.1 再基线新增】

- **职责**：把 ccbd 控制面 RPC（`ccb`↔`ccbd`，非 mux）的 connect / listen / accept / same-user 鉴权 / liveness / stale 清理 / 端点发现从 AF_UNIX 硬编码中抽出为 transport seam，Unix 保持现行为，Windows 提供 TCP loopback adapter。
- **承载的子 feature**：`ccbd-control-plane-transport-seam`, `ccbd-windows-tcp-loopback-transport`
- **触碰的现有代码 / 模块**：`lib/ccbd/socket_client_runtime/transport.py`、`lib/ccbd/socket_server_runtime/lifecycle.py`、`lib/ccbd/socket_server_runtime/bootstrap_probe.py`、`lib/ccbd/system.py`、`.ccb/` ccbd 端点存储。
- **Depth 判断**：deep。JSON-line 帧与 handler dispatch 与 transport 无关可复用；真正复杂度在连接建立、Unix inode 身份 vs TCP token 握手、same-user 鉴权、stale 清理——必须集中在两个 adapter，不能让 ccbd loop / CLI 分叉 `if windows`。

### Accelerator Transport Guard · accelerator 控制面 Windows 兜底【v8.2.1 再基线新增】

- **职责**：修复 `lib/runtime_accelerator` 控制面在 native Windows 无 guard 的 AF_UNIX 访问（`client.py:53`、`ownership.py:534` 抛 `AttributeError` 且不被 `except OSError` 接住），使 `ccb ask` 的 codex accelerator caller 不崩。
- **承载的子 feature**：`accelerator-transport-windows-guard`
- **触碰的现有代码 / 模块**：`lib/runtime_accelerator/client.py`、`lib/runtime_accelerator/ownership.py`。
- **Depth 判断**：medium。范围小且与 ccbd 控制面独立（accelerator 有自己的 socket 与协议）；depth 由 design 决定——给 Windows transport 还是 guard+clean fallback，取决于 accelerator 是否在 Windows ask 必经路径。

## 4. 模块间接口契约 / 共享协议（架构层详设）

### 4.0 Backend resolver / opt-in 契约

**方向**：config / CLI / env / platform detection → terminal runtime backend resolver
**形式**：配置字段 + resolver result + diagnostics payload

**契约**：

```python
class MuxBackendSelection(TypedDict):
    backend_family: Literal["tmux-family"]
    backend_impl: Literal["tmux", "rmux"]
    source: Literal["cli", "project_config", "user_config", "env", "platform_default", "auto_probe"]
    requested_backend: Literal["tmux", "rmux", "auto"]
    effective_backend: Literal["tmux", "rmux"]
    fallback_used: bool
    fallback_reason: str | None
    diagnostic: str
```

**约束**：

- 持久配置字段使用 `runtime.mux.backend = "tmux" | "rmux" | "auto"`；feature-design 若改名，必须保持同等语义、优先级和 diagnostics。
- 优先级：显式 CLI override（若本 feature 引入）> project config > user config > env `CCB_MUX_BACKEND` > platform default。env 是临时 override，必须在 diagnostics 中标明 source。
- 平台默认在本 roadmap 落地前仍是 `tmux`。Windows 上只有用户显式选择 `rmux` 或 route approval 后允许的 `auto` 才能走 Rmux。
- 显式选择 `rmux` 但 Rmux 缺失、未通过 `rmux-route-approval`、或 required capability gap 未满足时，必须 fail fast 并给出 actionable diagnostics；不得静默 fallback 到 tmux。
- `auto` 可以 fallback，但必须记录 `fallback_used=true` 与原因；fallback 不得掩盖 route approval 失败。
- `backend_selection.py` 当前只有 `selected == "tmux"` 分支；`backend-resolver-opt-in-contract` 必须把该入口改成 backend-neutral resolver，再允许后续 backend implementation 接入。

**Interface 设计检查**：

- Module / interface：terminal runtime 暴露 backend resolver；CLI、ccbd startup、diagnostics 读取 selection result。
- Seam placement：选择逻辑在 backend resolver，不散落到 provider launcher 或 ccbd controller。
- Depth / locality：把 opt-in、平台默认、auto、fallback 和诊断绑定成一个原子决策，避免“能运行但不知道为什么选了某后端”。
- Dependency strategy：local-substitutable。测试可构造 config/env/platform matrix。
- Adapter：无生产 adapter；这是 selection policy。

### 4.1 `MuxBackend` 组合能力契约

**方向**：CLI / ccbd / provider execution → terminal runtime backend
**形式**：Python protocol / abstract base class / capability-specific protocols

`MuxBackend` 是 roadmap 级的组合能力集合，不要求 feature-design 把下面所有方法落成一个胖 `Protocol`。实现时应按职责拆成较小协议，例如：

- `NamespaceLifecycle`：namespace/session create、attach、destroy、exists、server policy。
- `WindowLayout`：window list/create/select/kill、split/reflow/move/swap/layout。
- `PaneIO`：send text/key、capture、respawn、kill。
- `PanePresentation`：title、user option、style、log binding。
- `DiagnosticsCapability`：capabilities、describe pane、error/evidence detail。

`MuxBackend` facade 可以组合这些能力；fake adapter 只需要实现测试场景声明依赖的协议，不应被迫实现无关方法。

**契约**：

```python
class MuxNamespaceRef(TypedDict):
    backend_family: Literal["tmux-family"]
    backend_impl: Literal["tmux", "rmux"]
    namespace_id: str
    session_name: str
    ipc_kind: Literal["unix_socket", "named_pipe", "socket_name"]
    ipc_ref: str

class MuxPaneRef(TypedDict):
    backend_impl: Literal["tmux", "rmux"]
    pane_id: str
    session_name: str
    window_name: str | None

class MuxCapabilities(TypedDict):
    backend_impl: Literal["tmux", "rmux"]
    command_status: dict[str, Literal["supported", "partial", "unsupported", "workaround"]]
    semantic_status: dict[str, Literal["supported", "partial", "unsupported", "workaround"]]
    blocking_gaps: list[str]

class MuxCommandError(Exception):
    category: Literal["transient-unavailable", "unsupported", "not-found", "permission", "command-failed"]
    backend_impl: str
    command: list[str] | None
    detail: str
    ipc_ref: str | None

class MuxBackend(Protocol):
    def capabilities(self) -> MuxCapabilities: ...
    def ensure_namespace(self, *, session_name: str, cwd: str, config_ref: str | None) -> MuxNamespaceRef: ...
    def destroy_namespace(self, namespace: MuxNamespaceRef) -> None: ...
    def attach_namespace(self, namespace: MuxNamespaceRef, *, window_name: str | None = None) -> int: ...
    def namespace_exists(self, namespace: MuxNamespaceRef) -> bool: ...
    def ensure_server_policy(self, namespace: MuxNamespaceRef) -> None: ...
    def list_windows(self, namespace: MuxNamespaceRef) -> list[dict[str, str]]: ...
    def ensure_window(self, namespace: MuxNamespaceRef, *, window_name: str, cwd: str, select: bool = False) -> dict[str, str]: ...
    def select_window(self, namespace: MuxNamespaceRef, *, window_name: str) -> None: ...
    def kill_window(self, namespace: MuxNamespaceRef, *, window_name: str) -> None: ...
    def session_root_pane(self, namespace: MuxNamespaceRef, *, window_name: str | None = None) -> MuxPaneRef: ...
    def list_panes(self, namespace: MuxNamespaceRef) -> list[MuxPaneRef]: ...
    def describe_pane(self, pane: MuxPaneRef, *, user_options: tuple[str, ...] = ()) -> dict[str, str] | None: ...
    def split_pane(self, parent: MuxPaneRef, *, direction: Literal["right", "bottom"], percent: int, cwd: str | None = None) -> MuxPaneRef: ...
    def respawn_pane(self, pane: MuxPaneRef, *, cmd: str, cwd: str | None, stderr_log_path: str | None = None) -> None: ...
    def kill_pane(self, pane: MuxPaneRef) -> None: ...
    def send_text(self, pane: MuxPaneRef, text: str) -> None: ...
    def send_key(self, pane: MuxPaneRef, key: str) -> bool: ...
    def capture_pane(self, pane: MuxPaneRef, *, lines: int) -> str | None: ...
    def set_pane_title(self, pane: MuxPaneRef, title: str) -> None: ...
    def set_pane_user_option(self, pane: MuxPaneRef, name: str, value: str) -> None: ...
    def set_pane_style(self, pane: MuxPaneRef, *, border_style: str | None, active_border_style: str | None) -> None: ...
    def ensure_pane_log(self, pane: MuxPaneRef) -> Path | None: ...
```

**约束**：

- 调用方不得拼接 `tmux` / `rmux` CLI 命令。
- 调用方不得从 `ipc_ref` 推断 OS 路径语义；Windows named pipe 与 Unix socket 只由 backend 解释。
- `pane_id` 只在同一 `backend_impl` 与 `namespace_id` 内有意义，不能跨后端比较。
- `backend_impl=rmux` 的 capability gap 必须通过 `capabilities()` 和 diagnostics 显式暴露。
- `TmuxTransientServerUnavailable`、`TmuxCommandError` 等现有 tmux 错误必须映射到 backend-neutral `MuxCommandError.category`；startup / diagnostics 仍要保留原始 command、ipc_ref、detail，不能丢失排障证据。
- ccbd project namespace runtime 不允许继续直接拼 `_tmux_run`、`_tmux_run_ready` 或等价 tmux helper wrapper / `rmux` 命令；server/window/session policy 必须通过 `MuxBackend` 或专门的 `TmuxFamilyBackend` higher-level operations 完成。
- `ProjectNamespaceBackend` 只能拥有 project namespace higher-level policy，不重复暴露 primitive pane/window 操作；primitive 能力由上述 capability-specific protocols 提供。

**Interface 设计检查**：

- Module / interface：`terminal_runtime` 暴露 `MuxBackend`；caller 只需要 namespace/pane 引用和错误语义。
- Seam placement：seam 放在 terminal runtime 边界。CLI、ccbd、provider runtime、tests 都穿过此接口。
- Depth / locality：后端差异集中在 backend 实现；未来替换 Rmux SDK/CLI 不影响 ccbd。
- Dependency strategy：local-substitutable。测试可使用 fake backend；真实 Rmux/tmux 是本地进程依赖。
- Adapter：需要 production adapters（TmuxBackend、RmuxBackend）和 fake/test adapter；不是假 seam，因为至少两个生产实现和多类测试替身都会使用。

### 4.2 `MuxCapabilityReport` 能力表

**方向**：Capability Gate / backend implementation → roadmap review / diagnostics / feature design
**形式**：YAML / JSON 报告

**契约**：

> 以下 YAML 是 schema 与证据形态示例，不是 Rmux v0.8.0 的实测结论。`status: supported` 仅表示示例值；真实状态必须由 `rmux-capability-gate` 在 Windows 真机上生成。

```yaml
backend_impl: rmux
version: "0.8.0"
platform: windows
generated_at: "2026-07-06T00:00:00Z"
commands:
  start-server:
    required: true
    status: supported
    evidence: artifacts/rmux-start-server.txt
  new-session:
    required: true
    status: supported
    evidence: artifacts/rmux-new-session.txt
  attach-session:
    required: true
    status: supported
    evidence: artifacts/rmux-attach-session.txt
  has-session:
    required: true
    status: supported
    evidence: artifacts/rmux-has-session.txt
  kill-session:
    required: true
    status: supported
    evidence: artifacts/rmux-kill-session.txt
  kill-server:
    required: true
    status: supported
    evidence: artifacts/rmux-kill-server.txt
  list-windows:
    required: true
    status: supported
    evidence: artifacts/rmux-list-windows.txt
  new-window:
    required: true
    status: supported
    evidence: artifacts/rmux-new-window.txt
  rename-window:
    required: true
    status: supported
    evidence: artifacts/rmux-rename-window.txt
  select-window:
    required: true
    status: supported
    evidence: artifacts/rmux-select-window.txt
  kill-window:
    required: true
    status: supported
    evidence: artifacts/rmux-kill-window.txt
  move-pane:
    required: true
    status: supported
    evidence: artifacts/rmux-move-pane.txt
  resize-pane:
    required: true
    status: supported
    evidence: artifacts/rmux-resize-pane.txt
  select-layout:
    required: true
    status: supported
    evidence: artifacts/rmux-select-layout.txt
  swap-pane:
    required: true
    status: supported
    evidence: artifacts/rmux-swap-pane.txt
  split-window:
    required: true
    status: supported        # supported | partial | unsupported | workaround
    evidence: artifacts/rmux-split-window.txt
    notes: "supports -P -F #{pane_id}"
  list-panes:
    required: true
    status: supported
    evidence: artifacts/rmux-list-panes.txt
  display-message:
    required: true
    status: supported
    evidence: artifacts/rmux-display-message.txt
  set-option:
    required: true
    status: supported
    evidence: artifacts/rmux-set-option.txt
  set-window-option:
    required: true
    status: supported
    evidence: artifacts/rmux-set-window-option.txt
  set-hook:
    required: true
    status: supported
    evidence: artifacts/rmux-set-hook.txt
  bind-key:
    required: false
    status: supported
    evidence: artifacts/rmux-bind-key.txt
  send-keys:
    required: true
    status: supported
    evidence: artifacts/rmux-send-keys.txt
  load-buffer:
    required: true
    status: supported
    evidence: artifacts/rmux-load-buffer.txt
  paste-buffer:
    required: true
    status: supported
    evidence: artifacts/rmux-paste-buffer.txt
  delete-buffer:
    required: true
    status: supported
    evidence: artifacts/rmux-delete-buffer.txt
  capture-pane:
    required: true
    status: supported
    evidence: artifacts/rmux-capture-pane.txt
  pipe-pane:
    required: true
    status: partial
    evidence: artifacts/rmux-pipe-pane.txt
    notes: "requires Windows-specific log command"
  respawn-pane:
    required: true
    status: supported
    evidence: artifacts/rmux-respawn-pane.txt
  list-clients:
    required: true
    status: supported
    evidence: artifacts/rmux-list-clients.txt
  refresh-client:
    required: true
    status: supported
    evidence: artifacts/rmux-refresh-client.txt
semantics:
  terminal_close_keeps_session:
    required: true
    status: supported
  project_namespace_isolation:
    required: true
    status: supported
  attach_reattach_after_terminal_close:
    required: true
    status: supported
  session_window_policy_roundtrip:
    required: true
    status: supported
  layout_projection_roundtrip:
    required: true
    status: supported
  reload_reflow_patch_roundtrip:
    required: true
    status: supported
  pane_id_stability_within_namespace:
    required: true
    status: supported
  pane_user_options_roundtrip:
    required: true
    status: supported
  pane_title_roundtrip:
    required: true
    status: supported
  capture_last_n_lines:
    required: true
    status: supported
  capture_format_fidelity_for_provider_completion:
    required: true
    status: supported
    notes: "byte/format golden fixtures must compare newline, trailing whitespace, ANSI stripping policy, wrapping and wide-char behavior against current tmux parser expectations"
  bracketed_or_buffer_paste_large_text:
    required: true
    status: supported
  ctrl_c_ctrl_d_delivery:
    required: true
    status: supported
  copy_mode_cancel_before_send:
    required: false
    status: partial
  pane_death_detectable:
    required: true
    status: supported
  provider_process_death_distinguishable_from_pane_death:
    required: true
    status: workaround
    notes: "requires Windows Job Object evidence"
  kill_session_removes_namespace:
    required: true
    status: supported
  kill_server_or_equivalent_cleanup:
    required: true
    status: supported
blocking_gaps:
  []
```

**约束**：

- `required=true` 且 `status=unsupported` 阻止进入 `rmux-backend-core`。
- `partial` 必须写明 workaround；没有 workaround 的 partial 视为 blocking。
- 所有 evidence 必须能从仓库报告或 CI artifact 找到。
- capability gate 退出需要两层信号：`probe completed` 只表示事实采集完成；`route approved` 必须由独立 `rmux-route-approval` item 根据 `blocking_gaps`、required partial workaround 和后续 item 影响明确拍板。后续实现 item 只能依赖 `rmux-route-approval`。
- `rmux-capability-gate` 的 acceptance checklist 必须直接映射当前代码路径：`materialize_topology.py` 的 `resize-pane`、`agent_window_reflow.py` 的 `select-layout` / `swap-pane`、`move_patch_agents.py` 的 `move-pane`、`remove_patch_agents.py` 的 `select-layout`，以及 send/capture/logging 的 `load-buffer` / `paste-buffer` / `pipe-pane`。
- capture capability 不能只证明 `capture-pane` 能返回最后 N 行；必须用 provider completion parser 的 golden fixtures 证明 Rmux/ConPTY 输出在尾部空白、ANSI、换行 wrapping、宽字符和截断语义上不会让 `ccb ask` 静默漂移。该项不要求重写 provider completion parser，但要求记录格式兼容证据。

**Interface 设计检查**：

- Module / interface：Capability Gate 产出，后续 feature 只读。
- Seam placement：在实现前的事实闸门，避免实现阶段猜测。
- Depth / locality：把 Rmux 兼容性判断集中成一份权威输入。
- Dependency strategy：true external。Rmux 是第三方 release；probe 通过黑盒验证。
- Adapter：无 adapter；这是证据报告，不是运行时接口。

### 4.3 Runtime authority 扩展字段

**方向**：ccbd runtime authority ↔ terminal runtime / diagnostics
**形式**：JSON runtime state / diagnostics payload

**契约**：

```json
{
  "backend_family": "tmux-family",
  "backend_impl": "rmux",
  "namespace_id": "<project-id>",
  "namespace_ref": {
    "session_name": "<project-id>",
    "ipc_kind": "named_pipe",
    "ipc_ref": "\\\\.\\pipe\\rmux-<project-id>"
  },
  "pane_ref": {
    "pane_id": "%1",
    "window_name": "main"
  },
  "process_ref": {
    "job_id": "ccb-<project-id>-agent-codex",
    "owner_pid": 1234
  },
  "layout_version": 3
}
```

**约束**：

- `ccbd` 仍然是 authority；Rmux session/pane 事实只能作为 evidence，不反向定义 `.ccb/ccb.config`。
- `process_ref` 在 Windows 下用于 kill/recovery 的第二生命信号；pane alive 不等于 provider runtime healthy。
- diagnostics 必须同时展示 namespace、pane、process/job、capability 状态。
- `namespace_tmux_socket_path` / `namespace_tmux_session_name` 等现有 ping payload 字段在迁移期保留为兼容别名；新增 canonical 字段使用 `namespace_backend_impl`、`namespace_ipc_kind`、`namespace_ipc_ref`、`namespace_session_name`。原生 Windows/Rmux 路径的 foreground attach 必须走 `MuxBackend.attach_namespace()`，不得继续由 `lib/cli/services/start_foreground.py` 直接调用 `tmux attach-session`。

**Interface 设计检查**：

- Module / interface：ccbd runtime store 与 diagnostics 消费。
- Seam placement：runtime authority schema 是 ccbd 与 terminal runtime 的持久契约。
- Depth / locality：生命周期判断集中到 ccbd，不让 provider adapter 自己解释 Rmux。
- Dependency strategy：local-substitutable。测试可构造 fake runtime authority 和 fake backend evidence。
- Adapter：无独立 adapter；通过 store serializer/deserializer 和 backend fake 测试。

### 4.4 Windows shell/log command builder

**方向**：RmuxBackend → Windows shell / logging
**形式**：函数接口

**契约**：

```python
class WindowsCommandBuilder(Protocol):
    def wrap_provider_command(self, cmd: str, *, cwd: str | None) -> list[str]: ...
    def build_pipe_log_command(self, log_path: Path) -> str: ...
    def append_stderr_redirection(self, cmd: str, stderr_log_path: str | None) -> tuple[str, str | None]: ...
```

**约束**：

- 不允许业务层拼 PowerShell/cmd 字符串。
- `pipe-pane` 日志命令不能使用 Unix-only `tee -a`。
- 默认 shell 选择必须可诊断：`powershell.exe` / `pwsh` / `cmd` / user override。

**Interface 设计检查**：

- Module / interface：Windows Runtime Boundary 暴露命令构造接口。
- Seam placement：位于 RmuxBackend 内部依赖边界，测试应直接覆盖。
- Depth / locality：shell quoting 复杂度集中在一个模块，避免每个 caller 处理。
- Dependency strategy：in-process。
- Adapter：不需要 adapter；纯函数式本地策略即可。

### 4.5 Rmux daemon ownership 契约

**方向**：backend resolver / RmuxBackend / ccbd lifecycle ↔ local Rmux daemon
**形式**：daemon health record + backend startup policy

**契约**：

```json
{
  "backend_impl": "rmux",
  "daemon_ref": {
    "discovery": "path-or-sdk",
    "version": "0.8.0",
    "pid": 1234,
    "ipc_kind": "named_pipe",
    "ipc_ref": "\\\\.\\pipe\\rmux-<project-id>"
  },
  "daemon_health": "healthy",
  "owner": "rmux-backend",
  "authority": "ccbd"
}
```

**约束**：

- `ccbd` 仍是 project authority；Rmux daemon 只能提供 mux evidence 和 command surface，不能反向定义 desired agents、runtime state 或 shutdown intent。
- `RmuxBackend` 负责 Rmux daemon discovery、version/capability check、best-effort start、health probe 和 command error mapping；ccbd 只消费 backend-neutral health/evidence。
- 显式 `ccb kill` 的顺序必须能覆盖 Rmux daemon 资源：先停止 provider/job evidence，再销毁 namespace/session，再执行 Rmux daemon cleanup 或 leave-running policy，并把结果写入 diagnostics。
- Rmux daemon crash 必须被区分为 backend evidence failure，不得被误判为 provider completion failure；supervision/recovery 需要同时记录 namespace、pane、process/job、daemon health。
- 如果 Rmux daemon 是 per-user shared service 而不是 per-project process，roadmap 后续 feature 必须明确 cleanup degrade：`kill namespace` 不等于 `kill daemon`，diagnostics 要展示共享模式。

**Interface 设计检查**：

- Module / interface：RmuxBackend 与 ccbd diagnostics 共享 daemon health record。
- Seam placement：daemon ownership 在 backend implementation 边界，不让 provider launcher 或 project controller 直接管 Rmux daemon。
- Depth / locality：把 daemon-of-daemon 的启动、崩溃、清理语义集中，避免 ccbd 和 Rmux daemon 竞争 authority。
- Dependency strategy：true external + local-substitutable。测试可用 fake daemon probe，真实验证走 Windows integration。
- Adapter：需要 Rmux production daemon client 和 fake daemon client。

### 4.6 Project namespace policy 接口

**方向**：ccbd project namespace runtime → mux backend
**形式**：higher-level backend operations

**契约**：

```python
class ProjectNamespaceBackend(Protocol):
    def prepare_server(self, namespace: MuxNamespaceRef, *, timeout_s: float | None = None) -> None: ...
    def ensure_server_policy(self, namespace: MuxNamespaceRef, *, timeout_s: float | None = None) -> None: ...
    def create_session(self, *, session_name: str, project_root: Path, window_name: str | None, terminal_size: tuple[int, int] | None) -> MuxNamespaceRef: ...
    def ensure_window(self, namespace: MuxNamespaceRef, *, window_name: str, project_root: Path, select: bool) -> dict[str, str]: ...
    def session_alive(self, namespace: MuxNamespaceRef, *, timeout_s: float | None = None) -> bool: ...
    def kill_namespace(self, namespace: MuxNamespaceRef) -> bool: ...
```

**约束**：

- 当前 `lib/ccbd/services/project_namespace_runtime/backend.py` 覆盖 server policy、window create/list/rename/kill、session alive、root pane、copy-mode key binding、environment policy、kill-server；这些不能长期留在 tmux-only helper 内。
- `TmuxBackend` 可以先通过 adapter 包装现有 helper；`RmuxBackend` 必须提供等价 higher-level operation 或明确 capability degrade。
- project namespace runtime 的 patch/reflow/add/remove 路径只能依赖该接口返回的 namespace/window/pane evidence。
- 该接口不得成为 primitive pane/window pass-through；它只表达 project namespace policy、readiness、session/window ownership、kill/recover 这类 higher-level operation。需要 pane IO、presentation、layout primitive 时必须委托 4.1 的 capability-specific protocols。

**Interface 设计检查**：

- Module / interface：`ccbd.services.project_namespace_runtime` 消费 `ProjectNamespaceBackend`。
- Seam placement：seam 放在 namespace lifecycle 边界，比单个 pane operation 更高，能覆盖 reflow 和 reload patch。
- Depth / locality：server/window/session policy 的复杂度留在 backend，不扩散到 controller。
- Dependency strategy：local-substitutable。fake project namespace backend 可模拟 transient unavailable、missing session、policy partial。
- Adapter：需要 Tmux production adapter、Rmux production adapter 和 fake adapter；不是 pass-through，因为它隐藏 policy、readiness、error mapping 和 platform IPC。

### 4.7 Provider runtime session payload 契约

**方向**：runtime launch / provider session readers ↔ provider backends / diagnostics
**形式**：JSON session payload + provider env

**契约**：

```json
{
  "terminal": "mux",
  "backend_family": "tmux-family",
  "backend_impl": "rmux",
  "pane_ref": {
    "pane_id": "%1",
    "session_name": "ccb-<project-id>",
    "window_name": "main"
  },
  "namespace_ref": {
    "ipc_kind": "named_pipe",
    "ipc_ref": "\\\\.\\pipe\\rmux-<project-id>"
  },
  "compat": {
    "tmux_session": "%1",
    "tmux_socket_path": null
  }
}
```

**约束**：

- `terminal="tmux"`、`tmux_session`、`tmux_socket_path` 在迁移期只能作为兼容别名，canonical 字段必须是 `terminal="mux"`、`backend_family`、`backend_impl`、`pane_ref`、`namespace_ref`。
- `lib/cli/services/runtime_launch.py` 不允许长期直接导入 `TmuxBackend` 作为唯一 production backend；provider runtime launch 必须通过 backend resolver 或 runtime launch context 获得 backend。
- provider health/session readers 不得把 `pane_id` 当成 tmux-only session identity；需要按 `backend_impl` 解释，或通过 `MuxBackend.describe_pane()` / runtime authority 获取 evidence。
- provider env 中若继续暴露旧 `CCB_TMUX_*` 字段，必须同时暴露 mux-neutral 字段，并在 diagnostics 中标明旧字段为 compatibility。
- acceptance checklist 必须覆盖共享 writer 和 provider-specific payload builder：`runtime_launch_runtime/session_files.py`、Codex/Claude/Gemini/native CLI/Kimi/MiMo/DeepSeek 等 launcher、`pane_log_support/session.py` 和 provider session readers。旧字段只可作为 compatibility alias，新字段必须是 canonical authority。

**Interface 设计检查**：

- Module / interface：provider runtime session payload 是 launch、health、recovery、diagnostics 的共享协议。
- Seam placement：放在 runtime launch 与 provider backends 之间，避免每个 provider 自己迁移 tmux 字段。
- Depth / locality：provider 只读 backend-neutral pane/namespace evidence，不直接解释 Rmux IPC。
- Dependency strategy：local-substitutable。测试可用 fake session payload 覆盖 tmux/rmux 两种 backend。
- Adapter：需要兼容 reader/writer adapter，确保旧 session 文件可读，新 session 文件不再写死 tmux。

### 4.8 Design It Twice 记录

本 roadmap 比较过两种接口路线：

- **最小 tmux shim 路线**：仅让 `_tmux_base()` 选择 `rmux`，尽量保持现有 TmuxBackend。优点是短期改动少；缺点是 Windows named pipe、shell/log、process job、capability gap 会散落在调用点，无法支撑全功能。
- **MuxBackend contract 路线**：先定义 backend contract，再让 TmuxBackend/RmuxBackend 分别实现。优点是边界清晰、测试替身明确、长期可维护；代价是前期重构量更大。

选定 **MuxBackend contract 路线**。原因：本需求的失败模式不是某条命令缺失，而是生命周期和平台差异泄漏；只做 shim 会快速退化成 scattered `if windows`。

### 4.9 ccbd 控制面 RPC transport seam 契约【v8.2.1 再基线新增】

**方向**：`ccb` CLI client ↔ `ccbd` daemon（控制面 RPC，非 mux）
**形式**：transport 抽象接口 + 平台 adapter（Unix domain socket / Windows TCP loopback）

**背景**：ccbd 控制面把 AF_UNIX 直接写死在 client connect、server listen、bootstrap self-ping、liveness 探针里（实测点见 §8）。native Windows 无 AF_UNIX，`ccb→ccbd` RPC 起不来，这是「全链路跑通」终点在 mux 之外的独立 blocker。JSON-line 帧协议（`send_request`/`recv_response_line`/`decode_response`）与 30+ handler dispatch 与 transport 无关，可原样复用；需要 seam 化的是「连接建立 + 端点身份 + same-user 鉴权 + liveness/stale 清理 + 端点发现存储」。

**方案决策（owner 2026-07-19 确认）**：Windows adapter 用 **TCP loopback + same-user token**，named pipe 为 documented fallback。决定性理由：现有 server 运行时是 `select()`-based（`bootstrap_probe._pump_until_probe_response` 用 `select.select` + 非阻塞 accept + deferred 队列），而 Windows `select` 不支持 pipe handle——TCP 保持 socket 语义可让 select 循环 / 帧 / worker / 超时原样复用（"业务零改动"），named pipe 则需把 server I/O 改写为 overlapped + `WaitForMultipleObjects` 并引入 `pywin32`/ctypes 依赖、且 Windows-only 不可跨平台测。**fallback 触发条件**：仅当"本机任意本地用户可 pre-auth connect 到 loopback 端口"在目标部署环境被判定为不可接受威胁（硬化多用户主机），才切 named pipe 换取 OS 级 DACL 拒绝。此决策符合 ADR 三判据，`ccbd-windows-tcp-loopback-transport` 落地后走 `cs-domain` 记 ADR。

**契约**：

```python
class RpcEndpointRef(TypedDict):
    transport: Literal["unix_socket", "tcp_loopback"]
    # unix_socket: socket_path 有值，host/port/token_ref 为 None
    # tcp_loopback: host="127.0.0.1"、port=OS 分配、token_ref 指向 same-user token 文件；socket_path 为 None
    socket_path: str | None
    host: str | None
    port: int | None
    token_ref: str | None

class RpcTransport(Protocol):
    def endpoint(self) -> RpcEndpointRef: ...
    # server 侧
    def listen(self) -> None: ...                    # bind+listen；写端点发现信息与（TCP）token 文件
    def accept(self, *, timeout_s: float): ...        # 返回已通过 same-user 鉴权的连接
    def close(self) -> None: ...                      # 释放端点；stale 清理（Unix: socket 文件 / TCP: token 文件）
    def is_stale(self) -> bool: ...                   # 端点是否为死残留
    # client 侧
    def connect(self, *, timeout_s: float): ...       # 建连并完成 same-user 鉴权握手
    def liveness_connectable(self, *, timeout_s: float) -> bool: ...

class RpcTransportAuthError(Exception):
    category: Literal["not-same-user", "token-missing", "token-unprotectable", "handshake-failed"]
    transport: str
    detail: str
```

**约束**：

- 帧层与 handler dispatch 保持 transport-neutral，不得因平台分叉；业务 handler 零改动。
- **端点身份不得跨 transport 混用**：Unix 用 socket 文件 inode（`st_dev,st_ino`，现 `lifecycle._bound_socket_stat`）判 own/stale，TCP 用 host:port + token；调用方不得从 `RpcEndpointRef` 推断另一 transport 的语义。
- **same-user 鉴权是硬要求**：Unix 靠文件系统权限 + peer-path 匹配（现 `bootstrap_probe._same_peer_path`）；TCP loopback 换成 same-user token 握手——token 文件用 `icacls` 收敛为仅当前用户可读，**无法收敛则 `RpcTransportAuthError(category="token-unprotectable")` fail-fast，不得降级为无鉴权监听**。
- TCP 端口由 OS 分配（bind port 0 读回），不得硬编码；端点发现信息（host/port/token_ref）写入现有 `.ccb/` ccbd 端点存储，旧 `socket_path` 字段迁移期保留为兼容别名。
- bootstrap self-ping 的 probe 鉴权必须走 seam 的鉴权路径，不得保留 Unix peer-path 专用逻辑作为 TCP 路径旁路。
- platform 默认：Unix→`unix_socket`，Windows→`tcp_loopback`；这是平台强制，不引入用户 opt-in（与 §4.0 mux backend 的 opt-in 语义不同）。
- **client 侧端点发现读取**必须归属 transport factory 或 store adapter：从 `.ccb/` 读回 `RpcEndpointRef`（Unix 读 socket_path / TCP 读 host+port+token_ref 并加载 token）并构造对应 transport，不得让 CLI 侧散落 `if windows` 读端点。feature-design 明确 factory/store 归属。

**Interface 设计检查**：

- Module / interface：ccbd socket client/server runtime 暴露 `RpcTransport`；帧层与 handler 只见已连接 stream 与 endpoint ref。
- Seam placement：seam 在 connect/listen/accept/auth 边界，帧与 dispatch 在其上。
- Depth / locality：Unix inode-identity、TCP token-handshake、stale 清理、端点发现集中在两个 adapter；ccbd loop 与 CLI 只见 neutral 接口。
- Dependency strategy：true external（OS socket）+ local-substitutable（fake transport 可测握手 / 鉴权失败 / stale）。
- Adapter：需要 Unix production adapter（包住现有行为）、Windows TCP production adapter、fake adapter；两个真实实现 + 测试替身，非假 seam。

> 注：`lib/runtime_accelerator` 控制面是**另一条独立 socket / 协议**（`{"method","params"}`↔`{"ok","result"}`），不共用本 seam。它的 Windows 兜底由 `accelerator-transport-windows-guard` 单独处理，depth 由该 feature-design 决定。

## 5. 子 feature 清单

1. **rmux-capability-gate** — 在原生 Windows 上建立 Rmux capability probe、报告格式和 blocking gap 判定。
   - 所属模块：Capability Gate
   - 依赖：无
   - 状态：accepted
   - 对应 feature：`2026-07-06-rmux-capability-gate`
   - 备注：最小闭环；不修改主链路；完成状态只表示 probe completed，不批准后续实现。最新验收 report 为 `.codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T094438Z-4728/capability-report.json`，`blocking_gaps=7`，后续 `rmux-route-approval` 必须消费。

2. **rmux-route-approval** — 基于 capability report、blocking gaps、partial workaround 和用户/owner 判断，明确 Rmux 路线继续、暂停或重新选型。
   - 所属模块：Capability Gate
   - 依赖：`rmux-capability-gate`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：必须落盘 approval evidence；后续实现 item 只能依赖此 item，不直接依赖 probe completed。

3. **backend-resolver-opt-in-contract** — 定义 Rmux opt-in 配置、平台默认、auto 探测、fallback/fail-fast 和 diagnostics selection result。
   - 所属模块：Backend Resolver & Opt-in
   - 依赖：`rmux-route-approval`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：覆盖 `backend_selection.py` 当前 tmux-only 分支；显式 rmux 缺失或未批准时必须 fail fast，不能静默 fallback。

4. **mux-backend-contract** — 定义 `MuxBackend` 组合能力 / `ProjectNamespaceBackend` higher-level policy / namespace 与 pane 引用 / capability / error 契约和 fake backend 测试替身。
   - 所属模块：MuxBackend Contract
   - 依赖：`backend-resolver-opt-in-contract`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：先建 seam 和测试替身，避免实现直接耦合 Rmux。

5. **tmux-backend-contract-adapter** — 将现有 TmuxBackend 适配到 `MuxBackend`，保持 Linux/macOS/WSL 行为不变。
   - 所属模块：MuxBackend Contract
   - 依赖：`mux-backend-contract`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：回归重点是当前 tmux lifecycle 与 provider path 不漂移。

6. **windows-namespace-ipc-schema** — 增加 mux-agnostic namespace state、named pipe IPC 字段、ping/doctor payload 和旧 `namespace_tmux_*` 兼容别名策略。
   - 所属模块：Windows Runtime Boundary
   - 依赖：`mux-backend-contract`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：不直接启动 Rmux；先让 namespace schema、foreground attach 输入和 diagnostics 字段可测。

7. **windows-shell-log-builder** — 增加 Windows shell command builder、pipe/log command builder、stderr redirection 和默认 shell 诊断。
   - 所属模块：Windows Runtime Boundary
   - 依赖：`mux-backend-contract`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：替代 `sh -lc`、`tee -a` 等 Unix-only 命令构造。

8. **windows-job-object-runtime-evidence** — 增加 Windows Job Object 进程树 evidence、runtime authority 字段和 kill/recovery 判定输入。
   - 所属模块：Windows Runtime Boundary
   - 依赖：`windows-namespace-ipc-schema`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：pane alive 不等于 provider healthy；job evidence 是第二生命信号。

9. **provider-runtime-backend-session-contract** — 将 provider launch、session payload、runtime health 和 provider env 迁移到 backend-neutral mux 字段，并保留旧 tmux 字段兼容别名。
   - 所属模块：Provider Runtime Contract
   - 依赖：`mux-backend-contract`, `windows-namespace-ipc-schema`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：覆盖共享 session writer、provider-specific launcher、pane_log_support session reader、provider env 和 `TmuxBackend` 直接导入；不改变 provider completion 解析。

10. **rmux-daemon-ownership-boundary** — 定义 Rmux daemon discovery/start/health/crash/cleanup 的 ownership 和 diagnostics evidence。
   - 所属模块：Rmux Daemon Ownership
   - 依赖：`mux-backend-contract`, `windows-namespace-ipc-schema`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：Rmux daemon 只能是 backend evidence，不能成为 project authority；共享 daemon 与 per-project cleanup 必须可诊断。

11. **rmux-backend-core** — 实现 Rmux namespace/session/window/pane/list/split/respawn/kill/title/user-option/style 的 backend core。
   - 所属模块：RmuxBackend
   - 依赖：`tmux-backend-contract-adapter`, `windows-namespace-ipc-schema`, `windows-shell-log-builder`, `provider-runtime-backend-session-contract`, `rmux-daemon-ownership-boundary`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：必须消费 capability report，unsupported required command 不能静默降级。

12. **rmux-send-capture-logging** — 实现 Rmux send-text/send-key/capture-pane/pipe-pane/logging，并覆盖 Ctrl-C/Ctrl-D 与大文本输入。
   - 所属模块：RmuxBackend
   - 依赖：`rmux-backend-core`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：重点替换 `load-buffer/paste-buffer/tee -a` 的 Windows 语义；必须用 provider completion parser golden fixtures 验证 capture 格式保真。

13. **ccbd-rmux-namespace-lifecycle** — 将 RmuxBackend 接入 `ccb` / `ccbd` project namespace ensure、foreground attach、layout projection 和 `ccb kill`。
   - 所属模块：CCBD Integration
   - 依赖：`rmux-send-capture-logging`, `windows-job-object-runtime-evidence`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：第一条真正用户可见闭环；必须通过 mux-agnostic foreground attach，仍建议 opt-in。

14. **rmux-supervision-recovery** — 接入 pane death、provider process death、namespace crash、Rmux daemon crash 的 supervision/recovery 与 diagnostics。
   - 所属模块：CCBD Integration
   - 依赖：`ccbd-rmux-namespace-lifecycle`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：必须证明 pane evidence 与 process/job evidence 的边界。

15. **rmux-windows-validation-matrix** — 建立 Windows 原生真实平台验证矩阵和可重复 runbook，覆盖多 agent、ask、kill、restart、多项目。
   - 所属模块：Validation & Packaging
   - 依赖：`rmux-supervision-recovery`
   - 状态：planned
   - 对应 feature：未启动
   - 备注：包含 CI 可跑部分与手工真机证据部分。

16. **rmux-packaging-docs-contracts** — 更新 installer/package/docs/contracts，将 Rmux 后端从实验能力收口为受支持入口或明确 beta。
    - 所属模块：Validation & Packaging
    - 依赖：`rmux-windows-validation-matrix`
    - 状态：planned
    - 对应 feature：未启动
    - 备注：包含用户安装说明、diagnostics bundle 字段、README/contract 同步；区分 Windows npm 分发与 `install.ps1` 本地安装两个入口。

### 新增：CCBD 控制面 transport track（v8.2.1 再基线，与上面 rmux track 正交并行）

17. **ccbd-control-plane-transport-seam** — 为 ccbd 控制面 RPC 抽 transport seam，Unix 保持 AF_UNIX 行为不变。
   - 所属模块：CCBD Control Plane Transport
   - 依赖：无（可与 `rmux-capability-gate` 并行起步）
   - 状态：planned
   - 备注：先建 seam + Unix adapter + fake transport 替身；帧与 handler dispatch 零改动。

18. **ccbd-windows-tcp-loopback-transport** — 实现 Windows TCP loopback adapter（127.0.0.1 + OS 端口 + same-user token 握手，token 文件 icacls 收敛、无法收敛 fail-fast），替换 Unix peer-path 鉴权与 inode stale 判定。
   - 所属模块：CCBD Control Plane Transport
   - 依赖：`ccbd-control-plane-transport-seam`
   - 状态：planned
   - 备注：v8.0.16 另一 checkout 的 TCP 方案仅作蓝本，v8.2.1 重验；备选 named pipe。

19. **accelerator-transport-windows-guard** — 修复 runtime_accelerator 控制面 Windows AF_UNIX AttributeError，使 `ccb ask` 的 codex accelerator caller 不崩。
   - 所属模块：Accelerator Transport Guard
   - 依赖：无
   - 状态：planned
   - 备注：`codex_accelerator_enabled()` 默认 True，`poll_with_accelerator` 在默认 codex ask/poll 路径调用，故默认路径下即 ask 必经（列 milestone-内）；depth 由 design 定（Windows transport vs guard+fallback）。

20. **ccbd-windows-process-liveness** — 抽出跨平台进程存活判定，替换 `system.py:43 process_exists` 的 `os.kill(pid,0)`（Windows signal 0 == `CTRL_C_EVENT`，误判 + 副作用）。
   - 所属模块：CCBD Control Plane Transport（控制面 liveness）
   - 依赖：无（可与 transport seam 并行）
   - 状态：planned
   - 备注：独立审查发现的第四个控制面 blocker；被 keeper/health/ownership 约 10 文件消费；与 `windows-job-object-runtime-evidence`（job 树 evidence）区分，本项是基本 pid 存活。

21. **ccbd-windows-full-chain-smoke** — native Windows 真机证明 `ccb→ccbd→rmux` 全链路跑通（`ccb` 启动 namespace / `ccb ask` / `ccb kill`），不经 probe 旁路。
   - 所属模块：Validation & Packaging（终点验收）
   - 依赖：`ccbd-windows-tcp-loopback-transport`, `ccbd-rmux-namespace-lifecycle`, `accelerator-transport-windows-guard`, `ccbd-windows-process-liveness`
   - 状态：planned
   - 备注：本轮 owner 终点 `windows-rmux-native-working` 的验收 item；证据须为真链路 command transcript。

**最小闭环**：第 1 条 `rmux-capability-gate` 做完后，能在 Windows 真机上以证据判断 Rmux 是否满足继续投入条件；第 2 条 `rmux-route-approval` 明确继续、暂停或重新选型。若 blocking gap 存在或 owner 未批准，后续实现不启动。transport track（17/18/20）不依赖 route approval，可并行起步——它解的是 ccbd 控制面而非 mux 选型，不受 Rmux 路线是否继续影响。

**本轮终点关键路径**：`ccbd-control-plane-transport-seam → ccbd-windows-tcp-loopback-transport`、`ccbd-windows-process-liveness`、rmux track `... → ccbd-rmux-namespace-lifecycle`、`accelerator-transport-windows-guard` 四股汇入 `ccbd-windows-full-chain-smoke`。

### Goal Coverage Matrix

| Goal / completion signal | Covered by item(s) | Verification entry | Evidence type | Core? |
|---|---|---|---|---|
| 知道 Rmux 是否满足 CCB required command/semantic set | `rmux-capability-gate` | Windows 真机 probe 脚本 + capability report | probe output / report | yes |
| Rmux 路线被明确批准继续、暂停或重新选型 | `rmux-route-approval` | capability report review + owner approval evidence | approval note / decision record | yes |
| 用户可通过明确、可诊断的 opt-in 机制选择 Rmux，缺失或未批准时 fail-safe | `backend-resolver-opt-in-contract` | config/env/platform resolver matrix tests + doctor output | pytest / diagnostics snapshot | yes |
| 现有 tmux 路径不因抽象收口发生行为漂移 | `mux-backend-contract`, `tmux-backend-contract-adapter` | `python -m pytest test/ -v --tb=short -m "not provider_blackbox"`；重点 terminal/runtime suites | pytest / CI | yes |
| Windows 平台差异集中在 runtime boundary，不散落到业务层 | `windows-namespace-ipc-schema`, `windows-shell-log-builder`, `windows-job-object-runtime-evidence` | 单元测试 + diff review 检查调用层不拼 PowerShell/Rmux 命令 | pytest / review | yes |
| provider runtime session payload 和 health/recovery 不再写死 tmux | `provider-runtime-backend-session-contract` | provider session fixture tests + runtime launch tests | pytest / session payload fixtures | yes |
| Rmux daemon 发现、启动、健康、崩溃、清理归属明确，不成为第二 project authority | `rmux-daemon-ownership-boundary`, `rmux-supervision-recovery` | fake daemon unit tests + Windows daemon crash/restart smoke | pytest / diagnostics bundle | yes |
| Rmux 可完成 namespace/window/pane/send/capture/logging 核心操作，且 capture 格式不破坏 provider completion 解析 | `rmux-backend-core`, `rmux-send-capture-logging` | Windows Rmux integration tests + provider completion golden fixtures | pytest / probe artifacts | yes |
| `ccb` 在原生 Windows 上能启动、附着、kill 项目 namespace | `ccbd-rmux-namespace-lifecycle` | Windows 手工/CI lifecycle smoke；ping payload 包含 mux-agnostic namespace fields | command transcript / acceptance report | yes |
| `ccb ask` 在 Rmux 后端下按 backend-neutral session authority 定位 provider runtime | `provider-runtime-backend-session-contract`, `ccbd-rmux-namespace-lifecycle`, `rmux-windows-validation-matrix` | fake-provider ask smoke + 至少一个真实 provider Windows runbook | pytest / command transcript | yes |
| pane/provider/namespace 异常能恢复或诊断清楚 | `rmux-supervision-recovery` | Windows recovery smoke：kill pane、kill provider、restart daemon | smoke report / diagnostics bundle | yes |
| 多 agent / ask / 多项目并行在 Windows Rmux 下可运行 | `rmux-windows-validation-matrix` | provider blackbox 或 fake-provider matrix | pytest / runbook evidence | yes |
| 用户安装、启用、诊断路径清楚 | `rmux-packaging-docs-contracts` | README/docs diff review + install.ps1 dry/real smoke | docs review / command output | no |
| ccbd 控制面 RPC 在 native Windows 可建连（去 AF_UNIX 硬编码，帧/handler 零改动） | `ccbd-control-plane-transport-seam`, `ccbd-windows-tcp-loopback-transport` | fake transport 握手/鉴权/stale 单测 + Windows 真机 ccb→ccbd ping | pytest / command transcript | yes |
| TCP loopback 端点仅 same-user 可用，无法收敛 ACL 时 fail-fast | `ccbd-windows-tcp-loopback-transport` | token ACL / icacls 单测 + 跨用户拒绝 smoke | pytest / diagnostics | yes |
| `ccb ask` 的 accelerator caller 在 Windows 不因 AF_UNIX 崩 | `accelerator-transport-windows-guard` | Windows ask 路径单测 + AttributeError 回归 | pytest | yes |
| ccbd 进程存活判定在 Windows 正确（不误判活为死、不误投 Ctrl-C） | `ccbd-windows-process-liveness` | 跨平台 process-liveness 单测 + Windows keeper/health 存活回归 | pytest | yes |
| `ccb→ccbd→rmux` 全链路在 native Windows 真跑通（start/ask/kill，非 probe 旁路） | `ccbd-windows-full-chain-smoke` | Windows 真机全链路 command transcript | command transcript / acceptance report | yes |

## 6. 排期思路

先做 capability gate，因为 Rmux 是第三方 mux，命令存在不等于 CCB 依赖的语义成立。capability report 完成后单独做 `rmux-route-approval`，由 owner 根据 required gaps 和 workaround 明确继续、暂停或重新选型。随后先建 backend resolver / opt-in contract，再建 `MuxBackend` contract 和 TmuxAdapter，让现有 tmux 行为作为安全网；再做 Windows runtime boundary、provider runtime session contract 和 Rmux daemon ownership，避免 Rmux 实现把 shell/IPC/job object/session payload/daemon lifecycle 细节扩散。Rmux core 和 send/capture/logging 分开，是因为 pane/session 操作与输入/日志是两类高风险差异；send/capture/logging 必须用 provider completion golden fixtures 证明 `ccb ask` 不因 capture 格式漂移而静默失败。最后再接入 ccbd lifecycle、supervision、验证矩阵和 packaging/docs。

技术依赖顺序必须优先于产品优先级：capability probe → route approval → backend resolver / opt-in → contract → existing tmux adapter → namespace IPC/schema + shell/log + job evidence + provider runtime session contract + daemon ownership → Rmux backend → ccbd lifecycle → recovery → validation → docs/package。route approval 通过后应作为一次显式路线决策点：确认 Rmux 替代旧 psmux 方向，并触发 ADR 或 docs superseded 标记。

## 7. 深度规划底稿

### 目标完成信号

- 原生 Windows 上 `ccb` 可 opt-in 使用 Rmux 创建项目 namespace、启动 configured agents、附着到 UI。
- `ccb ask` 能向至少一个 fake provider 和一个真实 provider 发送请求并收集结果。
- 关闭当前 terminal 后 namespace 和 provider runtime 继续存活，再次 `ccb` 可重新 attach。
- `ccb kill` 后 Rmux session、provider process tree、runtime authority 均被清理。
- pane death / provider process death / Rmux daemon crash 至少有一种自动恢复或明确 degraded diagnostics。
- Linux/macOS/WSL 现有 tmux 路径测试不回退。

### Top 3 风险与缓解

1. **Rmux 命令兼容与 CCB 语义存在细微差异**：先做 capability gate，required gap 阻止实现；所有 partial 必须有 workaround；capture 要做 provider completion 格式保真验证。
2. **抽象层变成浅封装，复杂度仍散落到 ccbd/CLI**：`MuxBackend` 接口必须以 namespace/pane/capture/send/attach 语义表达，不暴露 CLI 拼接；review 检查业务层不得拼 `rmux`/PowerShell 命令，也不得绕过 backend resolver 直接选后端。
3. **Windows pane、provider 进程树与 Rmux daemon 三者脱钩导致 kill/recovery 不完整**：runtime authority 显式记录 process/job evidence 和 daemon health evidence，supervision 同时看 mux evidence、process evidence 与 daemon evidence。

### 非显然依赖

- 需要可用的原生 Windows 真机或 runner；WSL 不能替代。
- Rmux v0.8.0 或更新版本必须可安装并可定位 full helper；tiny CLI 与 full helper差异必须纳入诊断。
- 当前 npm package 的 `os` 仅包含 `linux` / `darwin`，Windows 发布入口要在后期明确策略。
- 真实 provider CLI 在 Windows 下的行为可能独立失败，需区分 backend failure 与 provider failure。
- provider completion parser 对 capture 输出格式敏感；Rmux/ConPTY 的尾部空白、ANSI、wrapping、宽字符差异必须通过 golden fixtures 证伪。
- 关键路径较长，后段从 Rmux backend core 到 validation/package 基本串行；排期需要给 Windows 真机验证和回归修复留缓冲。

### 关键假设

- Rmux 的 `-L` / `-S` / command surface 足以表达项目级 namespace 或可通过 SDK 替代。
- Rmux pane id 和 tmux `%N` 形式在 CCB 所需范围内稳定，至少可通过 backend-local id 映射。
- Rmux 支持 pane user option 或可提供等价 marker；否则 CCB pane identity 需要专门替代机制。
- PowerShell/cmd/pwsh 的默认 shell 策略可以集中处理，不需要 provider adapter 分别特判。
- Rmux daemon 可以通过 backend-local client 被可靠发现和健康检查；如果它是 per-user shared service，项目级 kill 只销毁 namespace 而不终止共享 daemon。

### 基线与验证入口

- 通用回归：`python -m pytest test/ -v --tb=short -m "not provider_blackbox"`。
- 生命周期 smoke：`python -m pytest -q -m ccb_lifecycle_smoke test/test_v2_phase2_entrypoint.py test/test_v2_ccbd_start_matrix.py`。
- 平台/存储相关：`python -m pytest -q test/test_v2_storage_paths.py test/test_project_id.py test/test_registry_project_id.py`。
- Rmux 专项：新增 Windows-only integration tests 和 capability probe；真实 provider 黑盒进入 focused jobs，不进默认矩阵。
- npm 包检查：`npm run pack:check`，但 Windows 发布前需调整 package `os` 策略。

### 交付物落点

- Capability report：`.codestable/roadmap/windows-rmux-native-backend/drafts/` 或正式 docs 路径，由第一条 feature 决定。
- Backend contract：`lib/terminal_runtime/` 下的新协议/类型和 fake backend tests。
- Rmux implementation：`lib/terminal_runtime/rmux_*` 或等价子包。
- Runtime authority/diagnostics：`lib/ccbd/*`、diagnostics docs、bundle 输出。
- Validation：`.github/workflows/*`、`docs/*runbook*`、test suites。

### 知识回写点

- Rmux capability gate 的 blocking/partial 结果若影响长期路线，acceptance 后应触发 `cs-domain` 写 ADR。
- Windows shell/log quoting 规则一旦验证稳定，应通过 `cs-keep` 或 `cs-note` 沉淀。
- 如果 package `os` 策略从 linux/darwin 扩展到 Windows，需要同步 README、install docs 与 release contract。

## 8. 观察项

- 旧 `docs/ccbd-windows-psmux-plan.md` 的方向与本 roadmap 高度相关，但基座从 psmux 转向 Rmux；如果 Rmux 路线确认，应后续用 docs-neat 或 domain/ADR 标注 superseded/updated 关系。
- `docs/plantree/plans/windows-wezterm-native/README.md` 仍可作为“为什么不选 WezTerm 主路径”的参考，但不作为本 roadmap 的实现输入。
- 当前 `.codestable/requirements/` 还没有 Windows 原生支持的 requirement；若 owner 希望先固化愿景，可以补一份 `cs-req`。
- Rmux 作为第三方关键依赖，若正式选型落地，建议在 capability gate 或 contract adapter 完成后写 ADR。
- **AF_UNIX 硬编码实测点（v8.2.1，transport track 输入）**：失败形态分两类——有 guard 者抛干净错误/返回不可用（可诊断），无 guard 者裸 `AttributeError`（不被现有 except 接住）。
  - ccbd 控制面（有 guard）：`lib/ccbd/socket_client_runtime/transport.py:31`（`connect_socket`，guard@23 仅 raise）、`lib/ccbd/socket_server_runtime/lifecycle.py:19`（`listen_server`，guard@15 抛 `RuntimeError`，非裸 `AttributeError`）、`lib/ccbd/system.py:59`（`unix_socket_connectable`，guard@57 返回 False）。
  - ccbd 控制面（无 guard，裸 `AttributeError`）：`lib/ccbd/socket_server_runtime/lifecycle.py:86`（`_socket_path_connectable`）、`lib/ccbd/socket_server_runtime/bootstrap_probe.py:33`（self-ping）。
  - accelerator（无 guard）：`lib/runtime_accelerator/client.py:53`、`lib/runtime_accelerator/ownership.py:534`（`AttributeError` 不被 `except OSError`/`except AcceleratorError` 接住）。
- **进程存活判定 blocker（独立审查发现，第四个控制面 blocker）**：`lib/ccbd/system.py:43` `process_exists` 用 `os.kill(pid, 0)`。Windows 上 `os.kill` 对 signal 0 == `CTRL_C_EVENT`——不是存活探测：普通 pid 抛 OSError 被吞 → 活进程恒判死；pid 恰为 console group 时**真的投递 Ctrl-C**（副作用）。被 `ccbd/keeper.py`、`ccbd/services/health.py`、`ccbd/services/ownership.py` 等约 10 个文件消费，破坏 ccbd 存活与 recovery 判定。由 `ccbd-windows-process-liveness`（item 20）覆盖。
- **ADR 提示**：Windows 控制面 transport seam（AF_UNIX vs TCP loopback）符合 ADR 三判据（难回退 + 不显然 + 真实权衡：token 鉴权 vs Unix 文件权限）。`ccbd-windows-tcp-loopback-transport` 落地、接口稳定后应由 `cs-domain` 补一条 ADR。另一 checkout 曾就此拍板 Option 1（TCP loopback）并 approved，但那份决策不在本 checkout，本轮须在 v8.2.1 重新确认后再记 ADR。
- **probe-bypass 观察**：历史 `scripts/probe_rmux_*.py` 直驱 rmux，绕过 ccbd，不能作为全链路证据；`ccbd-windows-full-chain-smoke` 必须走真链路。

## 9. 变更日志

- **2026-07-19（v8.2.1 再基线，update）**：基线 v8.0.16→v8.2.1（§4 锚点文件、`backend_selection.py` tmux-only、AF_UNIX 硬编码点均已在 v8.2.1 复核）。新增模块 “CCBD Control Plane Transport” 与 “Accelerator Transport Guard”；新增接口契约 §4.9 ccbd 控制面 RPC transport seam；新增 items 17–21（`ccbd-control-plane-transport-seam`、`ccbd-windows-tcp-loopback-transport`、`accelerator-transport-windows-guard`、`ccbd-windows-process-liveness`、`ccbd-windows-full-chain-smoke`）；`ccbd-rmux-namespace-lifecycle` 依赖增加 `ccbd-windows-tcp-loopback-transport`；新增「本轮里程碑范围」界定 `windows-rmux-native-working` 终点边界（supervision-recovery / 多项目矩阵 / packaging 列为 post-milestone）。触发因素：原 roadmap 缺失 ccbd 控制面 transport blocker，导致 `ccb→ccbd→rmux` 全链路在 native Windows 从未成立。
- **2026-07-19（独立审查 round 5 修订）**：独立 reviewer 判 changes-requested。修 §8 对 `lifecycle.py:19` guard 误标（实为有 guard 抛 `RuntimeError`）；补第四个控制面 blocker `ccbd-windows-process-liveness`（`process_exists` 的 `os.kill(pid,0)` 在 Windows 破坏 liveness）并纳入 full-chain-smoke 依赖；§4.9 补 client 侧端点发现归属；收紧 item 19 accelerator「默认 codex ask 必经」措辞。
