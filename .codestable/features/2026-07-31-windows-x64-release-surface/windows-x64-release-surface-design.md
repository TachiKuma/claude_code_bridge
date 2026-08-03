---
doc_type: feature-design
feature: 2026-07-31-windows-x64-release-surface
requirement: native-windows-ccb-via-herdr
roadmap: windows-native-herdr-ccb
roadmap_item: windows-x64-release-surface
execution_lane: goal
status: approved
summary: 补齐 Windows x64 的 npm/install/update/native helper/managed Python/doctor 发布面 gate，并让 Python、Node、PowerShell 入口消费同一 JSON 发布面投影
tags: [windows, x64, release-surface, npm, install, update, doctor, managed-python, native-helper, epic-child]
---

# windows-x64-release-surface feature design

## 0. 术语约定

| 术语 | 定义 | 防冲突结论 |
|---|---|---|
| 发布面投影 | 给 `npm install`、`install.ps1`、`ccb update`、`ccb doctor`、README/docs 提供的同一组机器字段与诊断文案。 | 不是最终 support tier，也不是 publish/promotion 授权。 |
| Windows x64 发布面门 | 把 baseline gate、package metadata、安装/更新路由、managed Python、native helper 和 doctor 输出收束成一个 fail-closed 结果。 | 不是后端能力门，也不是 Herdr socket API gate。 |
| managed Python | Windows 安装/更新链路中可发现、可验证的 Python 运行时。 | 这里只投影其可用性、位宽和诊断，不重新定义 Python 安装策略。 |
| native helper packaging | `ccb-rs-helper`、`ccb-agent-sidebar` 等本机 helper 随 Windows x64 发布面一起被发现、校验和描述的方式。 | 不是重新做 helper 功能，只是让发布面能说明 helper 是否到位。 |

仓库事实：

- `package.json` 仍只声明 `os: ["linux", "darwin"]`，`cpu: ["x64", "arm64"]`，没有 Windows npm 发布面。
- `bin/ccb-npm-install.js` 目前只支持 macOS universal 和 Linux x64；Windows 会直接抛 unsupported。
- `lib/cli/management_runtime/commands_runtime/update.py::cmd_update()` 当前把 Windows 直接判为不支持。
- `install.ps1` 已经是 native Windows source/install 入口，包含 Python 发现、Windows Store alias 拒绝和 `RmuxCheck` 投影。
- `lib/cli/services/doctor.py` 与 `lib/cli/render_runtime/ops_views_doctor.py` 目前只投影 `rmux_packaging_support_summary()`，没有 Windows release-surface rows。
- `docs/ccbd-diagnostics-contract.md` 只定义了 Rmux 的 Windows npm disabled 口径，没有 Windows x64 release-surface 口径。

## 1. 决策与约束

### 需求摘要

本 feature 定义 Native Windows x64 的发布面契约：`npm install`、`install.ps1`、`ccb update`、`ccb doctor` 和相关 docs 都要消费同一份 Windows x64 release-surface JSON 投影；该投影必须 fail closed 地描述 Windows x64 是否可进入、安装/更新入口怎么选、managed Python 和 native helper 是否到位，以及失败时下一步该做什么。

成功标准：

- Windows x64 发布面由单一 projection owner 产出稳定 JSON 投影，Python、Node、PowerShell 调用方不分别解释 `win32`、`x64`、managed Python 或 helper 位宽。
- 代码层 Windows `npm install` dry-run 在 native Windows x64 上有明确的 release route 契约；`package.json.os` 必须显式放开 `win32`，但当前 upstream/baseline 未 admitted 时只能输出 blocked/default projection 与诊断，不能打开真实 available/degraded route；`bin/ccb-npm-install.js` 必须继续在 Windows ia32、Windows arm64、WOW64 和缺 artifact 时 fail closed。
- `ccb update` 与 `install.ps1` 读取同一投影，给出一致的安装/更新入口和错误语义，不再各自发明平台判断。
- `ccb doctor`、`ccb doctor --output` 和相关 docs 能看到 Windows x64 发布面状态、managed Python、native helper、install/update 入口与下一步。
- 本 feature 不授权 `npm publish`、`git push`、`git tag`、release promotion 或 support tier 最终宣称。

明确不做：

- 不做后端能力改造，不碰 provider completion、recovery owner 或 Mobile/Config UI 语义。
- 不新增 32-bit Windows、arm64 Windows 或 WOW64 支持。
- 不在本 feature 里把 Windows x64 发布面直接宣称为 `supported`。
- 不自动下载 Herdr、不自动 promotion、不把发布面投影写成 publish 授权。
- 不做大范围重构；只做必要的 wiring 和单一 projection owner。

### 方案深度 pre-pass

候选方案：

1. 只改 docs/doctor，让用户看见 Windows x64 说明。
2. 只改 `package.json` / `bin/ccb-npm-install.js`，不统一 install/update/doctor。
3. 建一个单一发布面 projection owner，再由 npm/install/update/doctor/docs 共同消费。

选择第 3 个方案。理由不是为了“更完整”，而是因为 npm 安装、Windows source 安装、`ccb update`、doctor 和 docs 会同时消费同一条平台判断；如果不集中，`win32`、x64、managed Python 和 helper 状态会在不同入口里分叉，后续 support projection 也没法收口。

### Top 3 风险与缓解

1. **风险：npm、install.ps1、update、doctor 分别解释 Windows x64。**  
   缓解：单一 projection owner + 统一测试入口，任何入口都只读 projection。
2. **风险：把 `win32` 误读成 32-bit Windows。**  
   缓解：文档、doctor 和测试都显式写明 `win32` 是 Windows OS 名称，32-bit 由 projection 的 fail-closed 结果判断。
3. **风险：把发布面门偷偷升级成支持宣称。**  
   缓解：design、checklist、scope guard 一律禁止 `supported`、publish、promotion 和 release 授权。

### 非显然依赖与关键假设

- 依赖 `windows-x64-v852-baseline-gate` 的可验证输出；本 feature 不重新实现 baseline 位宽探测，只消费其结果。
- 依赖 `herdr-user-surfaces-parity` 的用户可见面投影结果；如果该 upstream 没有可引用的 beta gaps、degraded next action 或 support tier 语义，本 feature 必须保持 `surface_state="blocked"`，不得私自补定义用户可见面语义。
- 假设 Windows x64 的 npm/install/update 路由可以从同一份 projection 推导，不需要 caller 自己拼 host 逻辑。
- 假设 native helper 的位宽/可用性可以通过 release metadata、文件名约定或本机探针描述；无法证明时必须 fail closed。
- 假设 managed Python 的可用性可以在 install/update/doctor 中被投影为可行动诊断，而不是静默吞掉。

## 2. 名词与编排

### 2.1 名词层

#### 现状

- `package.json` 仍是 Linux/macOS only 的 npm envelope。
- `bin/ccb-npm-install.js` 只认识 macOS universal 与 Linux x64。
- `cmd_update()` 直接拒绝 Windows。
- `install.ps1` 已经能在 native Windows 上做 Python 发现、rmux 提示和 source/install。
- doctor 里已有 Rmux packaging projection owner，但没有 Windows x64 release-surface projection owner。

#### 变化

新增一个单一发布面投影 owner，建议由三层组成：

- `lib/terminal_runtime/windows_x64_release_surface.py`：Python builder，负责 schema defaults、repo evidence 读取、baseline gate 与 user-surface 输入合并。
- `lib/terminal_runtime/windows_x64_release_surface_projection.json`：随包发布的稳定 JSON payload，作为 Node 与 PowerShell 可消费的跨语言载体；缺仓库 evidence 时也必须能给出保守默认值。
- Python 唯一 public loader：`load_windows_x64_release_surface_projection(root, host_evidence)`。Python builder、packaged JSON fallback 和 default blocked 都只能通过这个 loader 返回同一 record；跨语言唯一稳定 seam 是 packaged JSON + `host_gate.rules`，Node/PowerShell adapter 读取同一个 packaged JSON record 并叠加 host evidence。
- 轻量 adapter：`bin/ccb-npm-install.js` 和 `install.ps1` 只读取 JSON payload、校验 `schema_version` 与必要字段，并在缺 required field、未知 enum/op、非法 rule shape 或 schema_version 不匹配时 fail closed；额外字段默认忽略，schema_version 变更必须另行处理。Python doctor/update 调用同一个 public loader，不能各自选择 builder 或 fallback。PowerShell 边界建议命名为 `Get-WindowsX64ReleaseSurfaceProjection` 与 `Test-WindowsX64ReleaseHostGate`，即使暂不拆文件，也要把 JSON/schema/host evidence 逻辑收在这两个小函数语义内。

这个 owner 只做发布面判断，不做后端能力判断。

```python
class WindowsX64ReleaseHostEvidence(TypedDict, total=False):
    os_platform: Literal["win32", "linux", "darwin", "unknown"]
    cpu_arch: Literal["x64", "arm64", "ia32", "unknown"]
    node_arch: Literal["x64", "arm64", "ia32", "unknown"]
    process_arch: Literal["x64", "arm64", "ia32", "unknown"]
    wow64: bool | None
    python_executable: str | None
    python_bitness: Literal["64bit", "32bit", "unknown"] | None
    managed_python_ref: str | None
    helper_arch: dict[str, Literal["x64", "arm64", "ia32", "missing", "unknown"]]
    helper_probe_ref: str | None
    npm_lifecycle_event: str | None
    installer_entrypoint: Literal["npm", "install_ps1", "update", "doctor", "test"] | None

class WindowsX64ReleaseHostGateRule(TypedDict):
    field: str
    op: Literal["equals", "in", "not_equals", "is_false", "exists"]
    value: object
    failure_reason: str
    diagnostic: str
    next_action: str

class WindowsX64ReleaseHostGate(TypedDict):
    rules: tuple[WindowsX64ReleaseHostGateRule, ...]
    default_failure_reason: str
    default_next_action: str

class WindowsX64ReleaseSurfaceProjection(TypedDict):
    schema_version: Literal[1]
    projection_source: Literal["repo_evidence", "packaged_json", "default_blocked"]
    baseline_gate_ref: str | None
    user_surfaces_parity_ref: str | None
    packaged_projection_ref: str | None
    implementation_admission: Literal["admitted", "blocked_upstream_pending", "blocked_baseline_mismatch"]
    baseline_version_ref: str | None
    baseline_version_status: Literal["v8.5.2", "mismatch", "unknown"]
    package_os: tuple[str, ...]
    package_cpu: tuple[str, ...]
    package_metadata_policy: Literal["win32-enabled-postinstall-gated", "win32-disabled", "blocked"]
    host_gate: WindowsX64ReleaseHostGate
    windows_npm_enabled: bool
    artifact_status: Literal["ready", "missing", "mismatch", "unknown"]
    artifact_basename: str | None
    archive_name: str | None
    extract_dir: str | None
    checksum_entry: str | None
    release_artifact_ref: str | None
    windows_installer_entry: str | None
    windows_executable_entry: str | None
    windows_bin_entries: dict[str, str]
    release_install_entry: Literal["npm", "install_ps1", "diagnostic_only"]
    source_install_allowed: bool
    source_install_entry: Literal["install_ps1", "none"]
    update_entry: Literal["npm", "install_ps1", "source", "diagnostic_only"]
    managed_python_status: Literal["ready", "missing", "degraded", "unknown"]
    native_helper_status: Literal["ready", "partial", "missing", "unknown"]
    upstream_gate_status: Literal["ready", "blocked", "pending", "unknown"]
    upstream_failure_ref: str | None
    upstream_detail_reason: str | None
    beta_gaps: tuple[str, ...]
    surface_state: Literal["blocked", "degraded", "available"]
    failure_reason: Literal[
        "not-windows",
        "not-x64",
        "wow64",
        "python-not-x64",
        "managed-python-missing",
        "managed-python-degraded",
        "helper-missing",
        "helper-not-x64",
        "release-artifact-missing",
        "release-artifact-mismatch",
        "installer-entry-invalid",
        "projection-schema-invalid",
        "baseline-gate-missing",
        "baseline-version-mismatch",
        "upstream-not-admitted",
        "user-surfaces-parity-missing",
        "unknown",
    ] | None
    release_gate_detail: str
    diagnostic: str
    next_action: str | None
```

JSON 兼容规则：

- `package.json` 是 npm envelope，只负责声明允许 npm 进入 postinstall；Windows x64 是否真的可走必须由 projection + postinstall 决定。
- `package.json.os` 在实现时必须加入 `win32`，否则 `npm install` 无法到达 Windows release route；`package.json.cpu` 不能单独表达“只允许 Windows x64”，因为 macOS arm64 仍是既有支持路径，所以 Windows arm64 必须由 postinstall adapter fail closed。
- `package.json.cpu` 是否继续保持 `["x64", "arm64"]` 是 npm envelope 决策：若保持现状，Windows ia32 在普通 `npm install` 中可由 npm prefilter 拒绝，postinstall 不保证运行；本 feature 对 Windows ia32 的明确 diagnostic 只要求 projection / adapter unit 证据，不要求普通 npm registry install 触达 postinstall。Windows arm64 / WOW64 必须由 postinstall adapter fail closed，因为它们可能通过 npm envelope 或 host 伪装进入脚本。
- `package.json.files` 必须包含 npm postinstall 读取的 projection JSON；默认选择加入 `lib/terminal_runtime/windows_x64_release_surface_projection.json`，并用 `npm pack --dry-run` 或 pack manifest 断言该文件实际进入包。
- `bin/ccb-npm-install.js`、`install.ps1`、`cmd_update()` 和 doctor 只能消费这份投影，不各自推导 Windows x64 是否可用。
- Node / PowerShell adapter 只能做 schema 校验、`WindowsX64ReleaseHostEvidence` 事实采集、`projection.host_gate.rules` 的通用布尔求值和结果展示，不能复制 Python builder 里的路由矩阵、bitness 判定或 artifact 命名矩阵。
- host evidence 是事实输入，不是判定结果：Node 可以采集 `process.platform` / `process.arch` / lifecycle event，PowerShell 可以采集 `$env:PROCESSOR_ARCHITECTURE` / WOW64 相关事实，Python 可以采集 Python bitness 和 helper probe；`supported`、`failure_reason`、`release_install_entry`、`source_install_allowed`、`source_install_entry`、`update_entry` 只能由 release-surface owner 产出。
- `host_gate.rules` 是跨语言 adapter 唯一允许本地执行的 gate policy：adapter 只实现 `equals`、`in`、`not_equals`、`is_false`、`exists` 这类通用谓词，并返回规则携带的 `failure_reason`、`diagnostic` 与 `next_action`；不得把 Windows x64、WOW64、artifact route 或 helper 位宽矩阵写死在 Node / PowerShell 代码里。
- `host_gate.rules` 按数组顺序确定性求值：所有 rule 通过才允许继续使用 projection 的 release route；第一条失败 rule 的 `failure_reason`、`diagnostic`、`next_action` 是输出结果。缺 key、`null`、空字符串、空数组、类型不匹配、`in` 的 `value` 不是数组、`exists` 命中的值为空、未知 `op` 都是 fail closed；其中未知 `op` / 非法 rule shape 直接使用 `default_failure_reason` 与 `default_next_action`。`equals` / `not_equals` 只比较标量规范化字符串或布尔值；`is_false` 只接受实际布尔 `false`；不得做隐式真值猜测。
- 如果 packaged JSON 缺 `host_gate`、rule 字段非法、rule op 未知或求值输入缺失，adapter 必须 fail closed 到 `default_blocked`，不能回退到自行判断。
- `failure_reason` 是跨 install/update/doctor/docs 的 canonical machine reason，不能把已知失败压成 `unknown`：upstream 未 admitted 映射为 `upstream-not-admitted` 或 `user-surfaces-parity-missing`；schema/stale/malformed packaged JSON 映射为 `projection-schema-invalid`；artifact 名称、checksum、extract dir 或 release ref 不一致映射为 `release-artifact-mismatch`；缺 artifact 映射为 `release-artifact-missing`；staged installer entry 不合法映射为 `installer-entry-invalid`；WOW64 映射为 `wow64`；managed Python 缺失/降级分别映射为 `managed-python-missing` / `managed-python-degraded`；helper 缺失/位宽不符分别映射为 `helper-missing` / `helper-not-x64`；当前 `8.2.1` 或非严格 `v8.5.2` 源头基线映射为 `baseline-version-mismatch`。`upstream_detail_reason`、`release_gate_detail` 和 status 字段可以承载更细文本，但不能替代顶层 stable reason。
- Windows release artifact 名称、archive 名称、extract dir、checksum key 和 release evidence ref 都属于 projection interface；Node postinstall、`ccb update` 和 `install.ps1` 只能读这些字段。
- `windows_installer_entry` 是 staged artifact 内的相对路径；`update_entry="install_ps1"` 时必须为 `install.ps1` 或 fail closed，且解压根目录必须存在该文件。若未来改名，必须先改 projection schema 和测试。
- `windows_executable_entry` 与 `windows_bin_entries` 是 npm runner / installed entrypoint 的唯一 artifact contract；Windows postinstall 完成后必须能用这些字段定位 `ccb` 以及其它 npm bin 对应可执行文件，不能假设无扩展名 Unix `ccb` 路径。
- 合法组合 invariant：`package_metadata_policy="blocked"` 时 `windows_npm_enabled` 必须为 `false`；`package_metadata_policy="win32-disabled"` 时 `package_os` 不含 `win32` 且 `windows_npm_enabled=false`；`package_metadata_policy="win32-enabled-postinstall-gated"` 只表示 npm 可进入 postinstall，`windows_npm_enabled=true` 还要求 `artifact_status="ready"`、native Windows x64 host evidence、baseline/user-surface upstream ready。
- `windows_npm_enabled` 只表示 Windows npm 发布面门是否打开，不表示最终支持。
- `surface_state="available"` 也不等于 `supported`；最终 support projection 属后续 feature。
- `upstream_detail_reason` 与 `beta_gaps` 只能透传或 redacted 映射 upstream evidence，不能在本 feature 中重新定义 support tier。
- `implementation_admission!="admitted"` 时，release artifact / npm / release update route 只能是 `surface_state="blocked"`、`windows_npm_enabled=false`、`release_install_entry="diagnostic_only"`、`update_entry="diagnostic_only"`；实现不能消费草稿 upstream 语义进入 available/degraded route。
- source/dev `install.ps1` 是 checkout 安装路径，不属于 release artifact / npm / update admission。当前 README 已公开 Native Windows Rmux beta source route，因此 upstream 未 admitted 时不得回归既有 `install.ps1 install` source/dev 入口；projection 必须用 `source_install_allowed=true` 与 `source_install_entry="install_ps1"` 表示 source route 可继续执行，同时 doctor/install/docs 必须清楚展示 release route blocked。若 owner 决定阻断 source/dev `install.ps1`，必须另开 owner 决策并同步 README/docs，本 feature 默认不阻断。
- `baseline_version_status` 必须来自 `windows-x64-v852-baseline-gate` 的 accepted evidence、`VERSION`/`package.json`/build info 和 CCB `v8.5.2` 源头/新分支 admission ref；当前工作区仍为 `8.2.1` 或未证明 strict `v8.5.2` 时只能 blocked。
- `next_action` 必须是可行动的，不能是空洞描述。
- `rmux_packaging_support_projection.json` 只能作为“单 owner + packaged JSON 放置位置”的参考；不得复制 `rmux_packaging_support.py` 的宽松 `data.get(... default ...)` reader 行为。release-surface JSON 缺 `schema_version`、必要字段、合法 enum 或 executable/artifact 字段时必须 fail closed，并用严格 schema fixture 覆盖 stale/malformed packaged JSON。
- packaged JSON 必须由 Python builder 的 canonical 输出生成或验证；实现要提供 freshness gate，断言提交/打包的 `windows_x64_release_surface_projection.json` 与 builder 在相同 repo/default-blocked 输入下的 canonical JSON 一致。`npm pack --dry-run` 只证明文件入包，不证明 freshness；freshness 归 CMD-003 或独立 focused test 覆盖。

##### Roadmap contract reconciliation

Roadmap 把目标平台写成 `os=win32,cpu=x64`，这是 Windows 支持范围的硬约束，不是要求 `package.json.cpu` 能表达 OS-specific tuple。npm 的 `cpu` 字段作用于整个包；当前包仍需要保留 macOS arm64 入口，因此 `package.json.cpu` 可以继续是 envelope 级 `["x64", "arm64"]`。Windows x64-only 由 `package.json.os += win32`、`projection.host_gate` 和 postinstall / install / update adapter 的 fail-closed 共同满足：`os_platform=win32` 且 host gate 证明 x64 才能进入 Windows release route，Windows arm64、WOW64、ia32 或未知 host evidence 都不能进入 `available` route。

这是本 feature 对 roadmap 中 “npm `os=win32,cpu=x64` package gate” 表述的正式 contract refinement：`cpu=x64` 是 Windows support tuple 的约束，由 release-surface projection 与 postinstall gate 执行；`package.json.cpu` 仍是全包 envelope。新一轮 design-review 通过后，implementation / acceptance 必须按这个 refinement 验收，不得为了机械匹配 roadmap 文案把 `package.json.cpu` 改成只含 `x64` 而误伤 macOS arm64，也不得因此放宽 Windows arm64 / 32-bit 范围。该 refinement 需要在 epic 的所有 child design 统一确认 checkpoint 中由 owner 一次性承接；确认前不得把它回写成最终 roadmap/ADR 事实。

##### Interface 设计检查

- Module：`lib/terminal_runtime/windows_x64_release_surface.py` + `lib/terminal_runtime/windows_x64_release_surface_projection.json`，新 owner 与跨语言 payload。
- Interface：caller 必须知道这是 fail-closed 的发布面投影，能给出 install/update/doctor 的入口与失败理由，但不能当成 support tier。
- Seam：npm 安装、Windows install/update、doctor 和 docs 都走同一个 JSON projection seam。
- Depth / locality：深。否则同样的 Windows x64 判断会散到 package、npm installer、update、install.ps1 和 doctor render。
- Dependency strategy：local-substitutable。测试用 fake baseline gate、fake artifact map、fake helper/python probes。
- Adapter：production builder、packaged JSON fallback、Node reader、PowerShell reader 与 test fixtures；不是假 seam，因为不同语言入口都要消费同一门。
- Test surface：package metadata、pack payload、artifact route、Windows `npm install` dry-run route、Windows update route、doctor render、README/docs contract。

### 2.2 编排层

```mermaid
flowchart TD
  A[baseline gate / user-surface parity / package metadata / helper probe] --> B[Python builder]
  B --> P[windows_x64_release_surface_projection.json]
  P --> C[Node npm install adapter]
  P --> D[PowerShell install.ps1 adapter]
  P --> E[Python ccb update]
  P --> F[ccb doctor / doctor --output]
  P --> G[README / diagnostics contract / support docs]
  C --> H{Windows x64?}
  D --> H
  E --> H
  F --> H
  H -- yes --> I[release route available + actionable diagnostics]
  H -- no --> J[structured blocked / degraded output]
```

流程级约束：

- 所有入口必须先消费同一 JSON projection，再决定自己显示什么。
- 非 Windows、Windows ia32、Windows arm64、WOW64、缺 baseline gate、缺 helper 或缺 managed Python 时都要 fail closed。
- 缺 `herdr-user-surfaces-parity` upstream evidence 时必须 fail closed，不能由本 feature 自行生成 beta gaps、degraded next action 或 support tier 口径。
- `ccb update` 不再用自己的平台分支单独判断 Windows；它只问 release-surface projection。
- doctor 与 docs 展示的字段必须能回到同一 projection，不允许 README、doctor 和安装脚本各写各的事实。

### 2.3 挂载点

- `lib/terminal_runtime/windows_x64_release_surface.py`：发布面 Python builder；放在 `terminal_runtime` 是为了复用 packaged projection 放置约定，不表示 release/update ownership 迁入 terminal runtime。
- `lib/terminal_runtime/windows_x64_release_surface_projection.json`：跨语言稳定 payload，模式参考 `rmux_packaging_support_projection.json`。
- `bin/ccb-npm-install.js`：Windows x64 artifact mapping、JSON reader 与 postinstall gate。
- `bin/ccb.js` / `bin/ccb-npm-runner.js`：public npm bin entry 与 runner smoke 挂载点；若无需修改代码，也必须由 S7 的 `windows_executable_entry` / `windows_bin_entries` 契约测试证明 staged Windows executable 可被定位。
- `lib/cli/management_runtime/commands_runtime/update.py`：Windows update 路由和 blocked/degraded 语义。
- `install.ps1`：Windows source/install 入口要消费同一 JSON 投影，展示 managed Python 与 native helper 状态。
- `lib/cli/services/doctor.py`、`lib/cli/render_runtime/ops_views_doctor.py`：doctor payload/render 的发布面 rows。
- `docs/ccbd-diagnostics-contract.md`、`README.md`、`README/*.md`：对外口径、诊断字段与安装/更新说明；npm 包包含 `README/*.md`，实现必须同步检查多语言/分文件说明，避免包内安装平台口径漂移。

### 2.4 推进策略

1. **projection schema and strict loader**：先把 Windows x64 release-surface projection 定义成 Python builder、strict schema、default-blocked record 和 Python 唯一 public loader。
   退出信号：fake baseline gate / user-surface parity / artifact / helper / python probe 下，`load_windows_x64_release_surface_projection(root, host_evidence)` 能稳定给出 `available | degraded | blocked`；缺 required field、非法 enum、stale/malformed JSON 都 fail closed。
2. **host gate evaluator and cross-language seam**：实现 `WindowsX64ReleaseHostEvidence` / `WindowsX64ReleaseHostGate` 的确定性求值 fixture，并固定 Node / PowerShell adapter 的通用求值边界。
   退出信号：Node 与 PowerShell fixture 能读取同一 JSON、只采集事实字段、只执行 `projection.host_gate.rules` 的 all-pass / first-failure 通用布尔求值，且不会复制 Windows x64 / WOW64 / helper / artifact 路由矩阵。
3. **canonical packaged JSON freshness**：让 packaged JSON 由 Python builder canonical 输出生成或验证，并纳入 npm pack 前 freshness gate。
   退出信号：提交/打包的 `windows_x64_release_surface_projection.json` 与 builder 在相同 repo/default-blocked 输入下的 canonical JSON 一致；`npm pack --dry-run` 只作为文件入包证明。
4. **dependency and baseline admission**：验证 `windows-x64-v852-baseline-gate` 与 `herdr-user-surfaces-parity` 两个 roadmap item 已 `done`，且各自有 passed acceptance/evidence refs；同时证明当前实现线严格来自 CCB `v8.5.2` 源头并在新分支推进。
   退出信号：依赖未满足时只能生成 blocked/default projection；依赖与基线满足后才允许 available/degraded release route。

当前仓库事实下，`windows-x64-v852-baseline-gate` 与 `herdr-user-surfaces-parity` 仍是 `in-progress`，且当前工作区版本仍显示 `8.2.1`。因此本 feature 在这些 upstream acceptance/evidence refs 出现前，可实现的最高形态是 strict schema、host gate、blocked/default projection、diagnostics wiring 和回归保护；不得打开 available/degraded release route。

Dependency admission 的机器谓词必须固定为：

- parent `items.yaml` 中 `windows-x64-v852-baseline-gate` 与 `herdr-user-surfaces-parity` 均为 `status: done`。
- 两个 parent feature 均存在 `{slug}-acceptance.md`，frontmatter 为 `doc_type: feature-acceptance` 且 `status: passed`。
- baseline parent acceptance/evidence refs 能证明 strict `v8.5.2` 源头/新分支、native Windows x64-only gate 和 bitness failure reasons。
- user-surfaces parent acceptance/evidence refs 能证明 beta gaps、degraded next action 与 support tier projection 已验收。
- 任一条件缺失时，本 feature implementation 只能测试和产出 blocked/default projection，不能进入 available/degraded release route。
5. **package metadata and payload**：把 `package.json.os += win32`、package files 与 projection JSON 入包断言分开落地；`package.json.cpu` 保持 envelope 级策略，Windows x64-only 不在 npm metadata 里硬编码。
   退出信号：npm 能进入 Windows postinstall dry-run；projection JSON 出现在 npm pack payload；`package.json.cpu` 未误伤 macOS arm64，且该 roadmap refinement 仍等待 epic owner 统一确认承接。
6. **Node postinstall host gate**：让 `bin/ccb-npm-install.js` 读取 projection、采集 host evidence、执行 `host_gate.rules`，并在 fake admitted upstream + strict v8.5.2 fixture 下开放 native Windows x64 dry-run release route。
   退出信号：fake admitted upstream + strict v8.5.2 fixture 下 native Windows x64 可通过 `npm install` dry-run release route；当前真实 repo/upstream 未 admitted 时只能进入 postinstall diagnostic 或 blocked/default projection；Windows arm64/WOW64 不能误装；Windows ia32 至少有 projection / adapter unit 的 blocked diagnostic。
7. **npm runner executable contract**：把 `windows_executable_entry` 与 `windows_bin_entries` 接到 public npm bin runner smoke。
   退出信号：枚举 `package.json.bin` 的全部 key（当前为 `ccb`、`ask`、`autonew`、`ctx-transfer`），断言 `projection.windows_bin_entries` 覆盖每个 bin，并用 fake staged root / stub spawn 验证 runner 对每个 command 都使用 projection 映射；`node bin/ccb.js --print-version` 只是 smoke 的一个代表用例，不能替代其它 bin。
8. **PowerShell source install adapter**：让 `install.ps1` 消费同一 JSON projection，但明确 source/dev checkout install 不受 release artifact admission 阻断。
   退出信号：当前 upstream 未 admitted 时，release route 显示 blocked/default projection；既有 `install.ps1 install` source/dev 路径仍可按 `source_install_allowed=true` 继续执行并显示可行动诊断，除非存在单独 owner 决策要求阻断。
9. **Windows update branch and rollback**：让 `ccb update` 读取同一 JSON projection，并按 `update_entry` 的 `diagnostic_only`、`install_ps1`、`npm`、`source` 分支执行，不能落到 Unix installer。
   退出信号：Windows x64 update 路由和 release-surface diagnostic 一致；fake staged root / fake `install.ps1` failure 单测证明 Windows update branch restore-or-retain backup 且不调用 Unix installer。
10. **doctor/docs projection**：把 release surface rows 输出到 doctor、`--output` 和 docs contract，并清理旧 `doctor --bundle` 文案。
   退出信号：doctor/README/docs 都能看到 `release_install_entry`、`source_install_allowed`、`source_install_entry`、`update_entry`、managed_python_status、native_helper_status 和 next_action；`docs/ccbd-diagnostics-contract.md` 不再把旧 `doctor --bundle` 作为当前公开命令。
11. **non-Windows / Rmux regression**：保持 Linux/macOS/WSL 现有安装更新路径和既有 Windows Rmux 诊断面稳定。
   退出信号：非 Windows 更新安装回归与 Rmux packaging/diagnostics 回归通过，没有把 release-surface 逻辑注入旧路径。
12. **Windows cleanup / rollback evidence**：证明 `install.ps1 uninstall`、PATH/skills cleanup 和 Windows update failure rollback 可观察。
   退出信号：Native Windows transcript 或 blocked evidence 存在；真实 Windows transcript 对齐 S8/S9 已由 fake rollback 单测覆盖的 rollback 语义。
13. **scope guard and package cleanliness**：运行 package payload 断言、scope guard 和清洁度检查，禁止 publish/promotion/support claim 越界。
   退出信号：`npm pack --dry-run`、Windows `npm install` dry-run、scope guard 和清洁度检查全过，且没有 provider completion、recovery owner、final support claim、publish/promotion 越界。

#### Windows update 子流程

`cmd_update()` 的 Windows 分支不能只删除 `_supported_update_platform()` 的拒绝逻辑。Windows host 必须先读取 release-surface projection，再按 `update_entry` 分流：

- `update_entry="diagnostic_only"`：不下载、不写 install prefix；打印 projection 的 `diagnostic` 与 `next_action` 后返回非零。
- `update_entry="install_ps1"`：使用 projection 的 `archive_name`、`checksum_entry`、`extract_dir` 和 `release_artifact_ref` 下载并校验 staged artifact；校验失败 fail closed；校验成功后要求 `windows_installer_entry="install.ps1"` 且 staged root 存在该文件，再调用 staged `install.ps1`，并沿用现有 update identity / rollback / entrypoint smoke check 语义的 Windows 等价实现。
- `update_entry="npm"`：在本 feature 中仅输出 npm release route 的 `next_action` / diagnostic，不由 Python updater 自动执行 `npm install`；因此不改变 install prefix、权限模型或 rollback 语义。若未来要由 `ccb update` 直接执行 npm route，必须另开 design 明确权限、prefix、identity smoke 和 rollback 规则；当前实现不能落到 Unix `run_staged_unix_installer()`。
- `update_entry="source"`：只允许 source/dev checkout 语义，输出 source 路径下一步；不把它当 release tarball update。
- `install.ps1 install` source/dev 路径只读取 projection 用于诊断和 doctor/docs 对齐，不因 `implementation_admission!="admitted"` 自动失败；release artifact install 则必须服从 `release_install_entry` 与 artifact/admission gate。

实现边界：

- `release_artifacts.py` 可以作为 artifact 名称生成器，但 release-surface projection 必须把 Windows artifact 字段序列化出来；caller 不直接调用自己的平台矩阵。
- Linux/macOS 继续走既有 tarball + `run_staged_unix_installer()` 路径；Windows 分支必须有单独测试，防止误用 Unix installer。
- Windows rollback、identity smoke check 和 failure output 要能从 projection 字段与 staged installer 结果复原为 acceptance 证据。
- Windows update rollback 必须有 focused unit test：用 fake staged root、fake `install.ps1` failure 和 fake install prefix 验证 Windows 分支会 restore 或 retain backup、输出 failure reason，并且不会落到 Unix installer。
- `install.ps1` 的 uninstall 路径、PATH 清理、skills 清理和 update failure rollback 必须作为 release-surface 安装面证据；这里不扩展到 Herdr backend workflow 验收。

### 2.5 结构健康度与微重构

##### 评估

- 文件级：`bin/ccb-npm-install.js`、`update.py` 和 `install.ps1` 都是入口级文件，继续塞分支会变胖。
- 文件级：`ops_views_doctor.py` 仍适合集中渲染，但本 feature 只追加少量 rows，不拆渲染层。
- 目录级：`terminal_runtime` 适合做投影 owner，`cli` 只做 wiring，`docs` 只做口径收口。

##### 结论：不做行为等价微重构

本 feature 不先拆文件或重组目录。只新增一个投影 owner 和必要 wiring；如果 `update.py` 或 `install.ps1` 再度膨胀，留给后续 refactor，不阻塞本次发布面收口。

## 3. 验收契约

### 3.1 关键场景清单

| ID | 输入 / 触发 | 期望可观察结果 | 证据类型 |
|---|---|---|---|
| AC-001 | native Windows x64 + baseline gate ready + user-surface parity evidence ready | 发布面投影为 `available`，npm/install/update/doctor 看到一致的 Windows x64 门状态 | unit |
| AC-002 | Windows ia32 / arm64 / WOW64 | 发布面 fail closed，`surface_state` 不是 `available`，且有明确 `failure_reason` 与 `next_action` | unit |
| AC-003 | `npm install -g @seemseam/ccb` dry-run on Windows x64 | `package.json.os` 允许 Windows 进入 postinstall；在 fake admitted upstream + strict v8.5.2 fixture 下，postinstall 只让 native Windows x64 进入 dry-run release route；当前真实 repo/upstream 未 admitted 时只能输出 postinstall/adapter diagnostic 或 blocked/default projection；Windows arm64/WOW64 不能误装；Windows ia32 若被 npm prefilter 拒绝，则 projection / adapter unit 仍有明确 blocked diagnostic；npm bin runner 能定位 Windows executable entry | unit/CLI |
| AC-004 | `ccb update` on Windows x64 | update 路由按 projection 的 `update_entry` 分流；Windows 不落到 Unix installer，blocked/degraded/available 输出与 release install 投影一致 | unit/CLI |
| AC-005 | managed Python 或 native helper 缺失 | doctor/install/update 都能看见可行动诊断，不静默吞掉 | unit |
| AC-006 | `ccb doctor` / `ccb doctor --output` | 输出 Windows x64 release-surface rows，与 `README.md`、`README/*.md` 和 docs 口径一致 | snapshot |
| AC-007 | Linux/macOS/WSL 现有路径 | 不退化，仍保留现有安装、更新和 Rmux 诊断面 | regression |
| AC-008 | scope guard | 不修改 provider completion、recovery owner、support tier 最终宣称、publish/promotion | diff review |
| AC-009 | Native Windows x64 transcript | 能从真实机器证据看到 install/update/doctor 的同一投影或 blocked 结果 | manual transcript |
| AC-010 | upstream dependency 或 v8.5.2 baseline 未满足 | 只能生成 `implementation_admission!="admitted"` 的 blocked/default projection，不能进入 available/degraded release route | unit |
| AC-011 | Windows install cleanup / update failure rollback | `install.ps1 uninstall`、PATH/skills 清理和 update failure rollback 有 transcript 或 blocked evidence | manual/unit |
| AC-012 | upstream 未 admitted + Windows source/dev install | release artifact/npm/update route blocked，但既有 `install.ps1 install` source/dev 入口不回归，并能显示 release-surface blocked diagnostic | unit/CLI |

### 3.2 明确不做的反向核对项

- 不把 `win32` 写成 32-bit Windows 支持。
- 不把本 feature 当成最终 `supported` 宣称。
- 不授权 `npm publish`、`git push`、`git tag`、release promotion。
- 不改 provider completion、recovery owner、Mobile/Config UI 语义。
- 不删 Linux/macOS/WSL 的现有安装更新路径。

### 3.3 Acceptance Coverage Matrix

| Scenario | Covered By Step | Evidence Type | Command / Action | Core? |
|---|---|---|---|---|
| AC-001 发布面可用 | S1,S2,S3,S4,S5,S6 | unit | projection tests | yes |
| AC-002 32-bit/arm64/WOW64 fail closed | S1,S2,S6,S8,S9 | unit | projection + installer/update tests | yes |
| AC-003 npm install Windows dry-run route | S5,S6,S7 | unit/CLI | npm install dry-run focused tests + all npm bin runner smoke | yes |
| AC-004 update 路由一致 | S9 | unit/CLI | update tests + rollback unit | yes |
| AC-005 managed Python / helper 诊断 | S1,S8,S10 | unit | projection + doctor tests | yes |
| AC-006 doctor/render/docs 一致 | S10 | snapshot/docs | doctor render tests | yes |
| AC-007 非 Windows 回归 | S11 | regression | Linux/macOS/WSL tests | yes |
| AC-008 scope guard | S13 | diff review | forbidden change guard | yes |
| AC-009 Windows 真机 transcript | S10,S12 | manual | Native Windows x64 transcript | yes |
| AC-010 dependency/baseline admission | S4 | unit | dependency admission + baseline version check | yes |
| AC-011 cleanup/rollback evidence | S9,S12 | manual/unit | uninstall transcript + rollback tests | yes |
| AC-012 source/dev install preservation | S8 | unit/CLI | install.ps1 source route test + README/docs check | yes |

### 3.4 DoD Contract

| ID | 要求 | 证据 | 阻塞级别 |
|---|---|---|---|
| DOD-DESIGN-001 | design/checklist/review 完整，且对齐 roadmap item `windows-x64-release-surface` | design review | blocking |
| DOD-IMPL-001 | 单一 release-surface owner 产出 Python builder、host evidence / host gate contract 与 JSON projection，caller 不各自解释 Windows x64、artifact route、executable entry 或 upstream failure detail | unit/diff review | blocking |
| DOD-IMPL-002 | npm/install/update/doctor 都消费同一 JSON projection，Windows ia32/arm64/WOW64 fail closed | unit tests | blocking |
| DOD-IMPL-003 | managed Python 与 native helper 状态被投影到 doctor/docs，并给出 next_action | snapshot | blocking |
| DOD-IMPL-004 | `ccb update` 不再单独用 Linux/macOS/WSL 拒绝 Windows x64；按 `update_entry` 执行 Windows 专用分支，不复用 Unix installer | unit/CLI | blocking |
| DOD-IMPL-005 | 不修改 provider completion、recovery owner、publish/promotion、final support claim | diff review | blocking |
| DOD-IMPL-006 | implementation admission 要求两个 upstream roadmap item done 且有 passed acceptance/evidence refs；否则只能产出 blocked/default projection | unit | blocking |
| DOD-IMPL-007 | 当前实现线必须是 strict `v8.5.2` 源头新分支 evidence；当前 `8.2.1` 工作区不能进入 available/degraded release route | unit/diff review | blocking |
| DOD-IMPL-008 | release route admission 不得阻断既有 `install.ps1` source/dev checkout install；source route 只能读取 projection 用于诊断，除非存在单独 owner 决策要求阻断 | unit/CLI | blocking |
| DOD-IMPL-009 | `package.json.cpu` envelope refinement 必须有 epic owner 统一确认或 roadmap follow-up 证据；确认前实现不得把 refinement 当作已沉淀架构事实，也不得机械改成只含 `x64` 误伤 macOS arm64 | epic checkpoint / acceptance artifact | blocking |
| DOD-REVIEW-001 | code review passed 且无 unresolved blocking | review report | blocking |
| DOD-QA-001 | QA 覆盖 Windows x64 发布面、一致性、回归和 scope guard | QA report | blocking |
| DOD-ACCEPT-001 | acceptance 回写 roadmap item，并保留 Windows x64 evidence refs | acceptance report | blocking |

Validation Commands:

| ID | 命令 | 目的 | 核心性 | 失败处理 |
|---|---|---|---|---|
| CMD-001 | `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml" --yaml-only` | checklist YAML 合法性 | core | fix-or-block |
| CMD-002 | `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` | roadmap items 回写合法性 | core | fix-or-block |
| CMD-003 | `python -m pytest -q test/test_windows_x64_release_surface.py` | 发布面 projection / canonical JSON freshness / host evidence / host gate rule semantics / strict schema / package payload / artifact route / executable entry / all npm bin runner / install / update 核心单测 | core | fix-or-block |
| CMD-004 | `python -m pytest -q test/test_cli_doctor_windows_x64_release_surface.py test/test_windows_bootstrap_script.py test/test_cli_management_update.py -k "windows or release_surface or install or update or doctor"` | doctor/install/update/wiring 回归，包含 upstream 未 admitted 时 `install.ps1` source/dev 路径不回归 | core | fix-or-block |
| CMD-005 | `python -m pytest -q test/test_cli_doctor_rmux_packaging.py test/test_install_windows_rmux_contract.py test/test_rmux_packaging_docs_contracts.py` | 既有 Windows Rmux/诊断回归 | core | fix-or-block |
| CMD-006 | `node -e "const cp=require('child_process'); const out=process.platform==='win32'?cp.execFileSync('cmd',['/d','/s','/c','npm.cmd pack --dry-run --json'],{encoding:'utf8'}):cp.execFileSync('npm',['pack','--dry-run','--json'],{encoding:'utf8'}); const files=JSON.parse(out)[0].files.map(f=>f.path); if(!files.includes('lib/terminal_runtime/windows_x64_release_surface_projection.json')) throw new Error('projection JSON missing from npm pack payload')"` | package 产物与 metadata dry-run，机器断言 projection JSON 进入 npm 包；不执行 publish | core | fix-or-block |
| CMD-007 | `python -c "import pathlib,re,subprocess; roots=('lib','test','docs','README','README.md','package.json','bin','install.ps1'); run=lambda a: subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='ignore',check=True).stdout; tracked=run(['git','diff','--',*roots])+run(['git','diff','--cached','--',*roots]); others=[p for p in run(['git','ls-files','--others','--exclude-standard','--',*roots]).splitlines() if p]; extra=''.join(pathlib.Path(p).read_text(encoding='utf-8',errors='ignore') for p in others if pathlib.Path(p).is_file()); lower=(tracked+extra).lower(); q='['+chr(34)+chr(39)+']?'; patterns=('npm\\s+publish','git\\s+push','git\\s+tag','support_tier\\s*[:=]\\s*'+q+'supported'+q,'windows\\s+x64\\s+(is\\s+)?(fully\\s+|stable\\s+)?supported','full\\s+windows\\s+x64\\s+support','stable\\s+windows\\s+x64\\s+support','release[_ -]?promotion\\s*[:=]\\s*(true|enabled)','provider_completion','recovery_owner'); hits=[p for p in patterns if re.search(p,lower)]; assert not hits,hits"` | publish/promotion/support/completion scope guard，含未跟踪新文件；覆盖单/双引号 `support_tier` 与 README.md、README/*.md、docs/doctor 中的 Windows x64 final supported 文案，PowerShell-safe | core | fix-or-block |
| CMD-008 | `MANUAL Native Windows x64: capture code-level npm install dry-run / install.ps1 / ccb update / ccb doctor transcript` | 真实机器发布面 dry-run 证据 | core | blocked-if-no-host-or-herdr |
| CMD-009 | `python -m pytest -q test/test_windows_x64_release_surface_dependency_admission.py` | 断言两个 upstream roadmap item `done`、parent acceptance `doc_type=feature-acceptance status=passed`、baseline/user-surface evidence refs 存在；缺任一项时只能产出 blocked/default projection | core | fix-or-block |
| CMD-010 | `python -m pytest -q test/test_windows_x64_release_surface_baseline_version.py` | strict v8.5.2 源头/新分支基线准入；当前 8.2.1 工作区只能 blocked | core | fix-or-block |
| CMD-011 | `MANUAL Native Windows x64: capture install.ps1 uninstall cleanup and ccb update failure rollback transcript` | Windows 安装面可卸载、PATH/skills 清理和 update rollback 证据 | core | blocked-if-no-host-or-herdr |
| CMD-012 | `python -m pytest -q test/test_windows_x64_release_surface_update_rollback.py` | fake staged root / fake install.ps1 failure 下验证 Windows update branch restore-or-retain backup、identity smoke/failure output，且不调用 Unix installer | core | fix-or-block |
| CMD-013 | `python -c "import pathlib,re; p=pathlib.Path('docs/ccbd-diagnostics-contract.md'); bad=[(i+1,line.rstrip()) for i,line in enumerate(p.read_text(encoding='utf-8').splitlines()) if 'doctor --bundle' in line.lower() and not re.search(r'deprecated|unsupported|no longer supported|not supported', line, re.I)]; assert not bad,bad"` | docs contract 旧 `doctor --bundle` 口径清理；只允许 deprecated/unsupported 语境，当前公开命令必须是 `doctor --output` | core | fix-or-block |

Required Artifacts：

- design、checklist、design-review
- `WindowsX64ReleaseSurfaceProjection` owner 模块与 packaged JSON projection
- `WindowsX64ReleaseHostEvidence` 最小契约与 host evidence fixture
- `WindowsX64ReleaseHostGate` 确定性求值 fixture
- packaged JSON canonical generation / freshness 测试
- Node / PowerShell JSON adapter 测试 fixture
- package payload 断言，证明 projection JSON 位于 npm 包内
- artifact route 字段与 checksum key 的 projection 测试
- executable entry / npm bin runner smoke 测试
- all npm bin runner mapping 测试，覆盖 `package.json.bin` 每个 key
- stale/malformed packaged JSON strict schema 测试
- upstream dependency admission 与 strict v8.5.2 baseline admission 测试
- `bin/ccb-npm-install.js` / `package.json` / `update.py` 的发布面 wiring
- doctor payload/render 更新
- `docs/ccbd-diagnostics-contract.md`、`README.md` 与 `README/*.md` 口径更新，包含旧 `doctor --bundle` 文案清理
- docs contract focused guard，确保 `doctor --bundle` 只在 deprecated/unsupported 语境出现
- Windows x64 真实 transcript 或 blocked evidence
- install.ps1 uninstall cleanup transcript 或 blocked evidence
- ccb update failure rollback evidence
- source/dev `install.ps1` preservation test
- epic owner batch confirmation 或 roadmap follow-up 证据，用于承接 `package.json.cpu` envelope refinement
- roadmap items.yaml 回写

### 3.5 自我批判结论

- 可证伪性：每个核心场景都能被 yes/no 地证明，不靠“更好看”这类弱词。
- 步骤原子性：projection、dependency/baseline admission、npm postinstall/package gate、install.ps1/update、doctor/docs、非 Windows/Rmux 回归、Windows cleanup/rollback 与 scope guard 已分开。
- 最弱依赖：upstream dependency admission、strict v8.5.2 baseline gate 和 Windows 真机 dry-run transcript 是最弱依赖，已单独写进步骤与验收。
- 证据完整性：unit、snapshot、CLI、manual transcript 都有对应位置，不只靠文案。
- 基线可执行性：`npm pack --dry-run --json` 与 Windows `npm install` dry-run 断言、baseline admission 和 pytest 命令明确，既有回归与新增测试分开。
- 交付物可核验性：acceptance 能从 diff、文件、doctor 输出和 transcript 反查。
- 清洁度覆盖：禁止调试输出、临时 TODO/FIXME、注释掉代码和无用 import；若有例外，必须在实现前另写说明。

## 4. 与项目级架构文档的关系

- 本 feature 是 `windows-native-herdr-ccb` 的第 9 个 child，负责把 Windows x64 发布面做成可消费的单一契约。
- 本 feature 只消费 `windows-x64-v852-baseline-gate` 的 platform gate，不重新实现位宽探测。
- 后续 `native-windows-public-workflow-validation-matrix` 和 `herdr-supportability-projection` 才负责最终 support tier 与更完整的发布说明。
- 如果实现确认 `WindowsX64ReleaseSurfaceProjection` 会长期存在，建议后续用 `cs-note` 或 `cs-domain` 记录 `os=win32,cpu=x64` 的长期口径。
