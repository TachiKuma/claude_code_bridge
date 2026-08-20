# Herdr Runtime Hosting 架构优化方案

日期：2026-08-20

## 当前位置

当前 CCB 版本为 `8.6.10`，Herdr 当前稳定版为 `v0.8.2`。Herdr
`v0.8.2` 在 2026-08-19 发布，GitHub release 将其标为 Latest，并新增
Qwen Code 的 `idle`、`working`、用户确认状态检测和可选原生 session
restore，同时继续强化 Agent 文档入口、窗口标题同步等宿主运行时能力：
<https://github.com/herdrdev/herdr/releases/tag/v0.8.2>。

Herdr 官方文档当前将自身定义为 Agent terminal runtime：它负责让终端、
workspace、pane 和 agent 状态长期存在，并通过 CLI/socket API 暴露同一控制面；
Agent 状态包含 `blocked`、`working`、`done`、`idle` 和 `unknown`，其中
`unknown` 表示 Herdr 不能可靠分类，不表示业务成功：
<https://herdr.dev/docs/concepts/>、
<https://herdr.dev/docs/cli-reference/>、
<https://herdr.dev/docs/socket-api/>。

这说明 CCB/Herdr 的目标边界应该从：

```text
CCB 编排启动和恢复，Herdr 作为终端后端被动执行命令
```

演进为：

```text
Herdr 负责 Host Runtime，CCB 负责 Collaboration Control Plane
```

但这不是把 CCB 的业务语义迁移给 Herdr。Herdr 的 `idle/working/blocked/done`
只能作为运行时状态源；Provider turn 完成、ask/job 成败、恢复可行性、取消语义、
凭据和 Provider session 权威仍必须留在 CCB。

本轮尝试重新运行 `archi .`，但当前环境访问 Architec 认证入口失败，错误为
`CERTIFICATE_VERIFY_FAILED`。因此本方案以仓库内已记录的最后有效结构数据为基线：
最终成功快照为 overall `54.75`、structure `67.14`、governance/full `42.37`。
该分数说明问题主要不是包拓扑崩坏，而是 runtime/control-plane 边界过宽、启动路径
分散、状态权威重叠导致的治理复杂度。

## 现状证据

当前 CCB 仍承担了过多 Host Runtime 职责：

- `ccb.py` 在模块导入阶段执行 Native Windows Herdr 探测，并把非 introspection
  命令挡在 `main()` 前的全局状态之后。
- `lib/cli/phase2_runtime/handlers_start.py` 的 `handle_start()` 仍负责 Herdr
  runtime evidence 注入；`_ensure_herdr_runtime_evidence()` 会调用 bootstrap，
  自动启动 Herdr server 并设置 `CCB_HERDR_CAPABILITY_REPORT`。
- `lib/platforms/windows/herdr/bootstrap.py` 同时负责 Herdr executable 解析、
  session 发现、server 启动、readiness 等待、read-only capability probe，
  并写出临时 capability JSON。
- `lib/platforms/windows/herdr/runtime/cli.py` 的 `HerdrCliRequestAdapter` 仍将
  `create_session`、`restore_session`、`ensure_window`、`create_pane`、
  `report_pane_agent`、`respawn_pane`、`capture_pane`、`attach_namespace` 等大量
  CCB 操作拆成独立 CLI 请求。
- `lib/platforms/windows/herdr/backend.py` 的 `HerdrBackend` 在很多操作前重复调用
  `client.server_info()`，说明连接、capability 和 generation 尚未收敛为一次握手。
- `lib/cli/services/runtime_launch_runtime/tmux_runtime.py` 仍显式 release/report
  Herdr pane agent 身份，并注明 Herdr 仅凭 `report-agent-session` 不会创建 Agent
  身份。
- `lib/terminal_runtime/backend_resolver.py` 仍维护 Herdr capability 文件和 operation
  白名单；这让 CCB 必须理解 Herdr 的低层 capability 组合，而不是消费一个稳定
  runtime contract。
- `docs/plantree/plans/sidebar-provider-activity/decisions/003-provider-activity-is-execution-state-authority.md`
  已经明确 Provider activity 是执行状态权威，`project_view` 必须按 project、
  agent、runtime generation、pane 和 workspace 校验状态归属；这与 Herdr runtime
  event 投影必须合并，而不能互相替代。

## 目标架构

目标形态：

```text
CCB config / provider catalog / command authority
        |
        v
CCB Runtime Manifest
        |
        v
Herdr runtime.ensure(manifest, restore_token?)
        |
        v
Runtime Binding + Snapshot + Ordered Events
        |
        v
CCB Project Control Plane
        |
        v
Provider/job/ask 状态 + Herdr runtime 状态
        |
        v
project_view / Agents 面板 / mobile gateway
```

职责边界：

| 能力 | Herdr | CCB |
|---|---:|---:|
| server/session/workspace/tab/pane 生命周期 | 是 | 否 |
| pane 进程启动、就绪、退出、重启、attach、布局、焦点 | 是 | 仅声明策略 |
| Agent 运行时检测：`idle`、`working`、`blocked`、`done`、`unknown` | 是 | 消费并校验 |
| Provider command、Provider home、凭据、原生 session | 否 | 是 |
| `ccbd`、keeper、startup fence、项目控制面状态 | 暂不接管 | 是 |
| ask、job、队列、取消、回复、协作图、memory | 否 | 是 |
| Provider completion、resume/fork、continuation、恢复策略 | 否 | 是 |
| Agents 面板单一读模型 | 提供运行时事实 | 合并业务事实并发布 |

核心约束：

- Herdr 是运行时事实源，不是业务完成权威。
- `unknown`、断线、过期 generation 和事件缺口必须显式暴露，不能静默降级为
  `idle`。
- 所有 runtime handle 都必须绑定 project、namespace/workspace、pane、agent slot、
  provider kind、session 和 runtime generation。
- manifest 不传原始凭据；CCB 只传授权引用或经过裁剪的环境投影。

## 核心契约草案

### Runtime Manifest

CCB 生成 `.ccb/runtime/herdr-runtime-manifest.json`。首版只描述 CCB 当前已经拥有的
拓扑和策略，不引入 Provider 新语义：

```json
{
  "schema": "ccb.herdr.runtime-manifest.v1",
  "project_id": "proj-...",
  "project_root": "E:/path/to/project",
  "session_name": "ccb-project-abc12345",
  "generation": 12,
  "services": [
    {
      "id": "ccbd",
      "command": ["python", "-m", "ccbd"],
      "cwd": "E:/path/to/project",
      "ready": {"kind": "ccb-lifecycle", "phase": "mounted"}
    }
  ],
  "workspaces": [
    {
      "name": "project",
      "cwd": "E:/path/to/project",
      "panes": [
        {
          "slot": "codex",
          "agent_name": "codex",
          "provider_kind": "codex",
          "command": ["codex"],
          "cwd": "E:/path/to/project",
          "role": "agent",
          "env_refs": [
            {"name": "OPENAI_API_KEY", "source": "ccb-provider-home"}
          ],
          "restart": {"policy": "manual-or-ccb-approved"}
        }
      ]
    }
  ]
}
```

### Runtime Ensure Response

Herdr 的目标接口可以叫 `runtime.ensure` 或 `workspace.ensure-runtime`。名字可在实现时
与 Herdr 上游对齐，但语义必须一次性返回 binding 所需事实：

```json
{
  "schema": "herdr.runtime-binding.v1",
  "server_id": "server-...",
  "server_version": "0.8.2",
  "api_schema": "Herdr API",
  "session_name": "ccb-project-abc12345",
  "workspace_id": "w1",
  "runtime_generation": 12,
  "ready": true,
  "capabilities": {
    "agent_state": true,
    "agent_events": true,
    "pane_restart": true,
    "service_lifecycle": false
  },
  "panes": [
    {
      "slot": "codex",
      "pane_id": "w1:p2",
      "agent_id": "codex",
      "provider_kind": "codex",
      "state": "idle",
      "state_seq": 1
    }
  ]
}
```

CCB 将该响应持久化为 runtime binding，而不是传递临时
`CCB_HERDR_CAPABILITY_REPORT`：

```text
.ccb/runtime/herdr-binding.json
```

binding 是 CCB 重连、teardown、project_view 投影和事件去重的唯一 Herdr 运行时锚点。

### Runtime Events

Herdr 需要向 CCB 提供可重同步的事件流。首版事件最少包含：

```text
runtime_snapshot
workspace_ready
pane_started
pane_ready
agent_state_changed
agent_session_changed
pane_exited
pane_restarted
workspace_stopped
runtime_disconnected
```

每个事件必须包含：

```json
{
  "event_id": "monotonic-or-uuid",
  "server_id": "server-...",
  "session_name": "ccb-project-abc12345",
  "workspace_id": "w1",
  "pane_id": "w1:p2",
  "agent_id": "codex",
  "provider_kind": "codex",
  "runtime_generation": 12,
  "seq": 44,
  "state": "working",
  "occurred_at": "2026-08-20T12:00:00Z"
}
```

CCB 的消费规则：

- 启动时先读 `runtime_snapshot`，再订阅增量事件。
- 断线重连后必须重新读取 snapshot，并按 `runtime_generation` 和 `seq` 丢弃旧事件。
- `pane_id` 变化必须视为新 runtime ownership，旧状态不能沿用。
- Herdr `done` 只能映射为“运行时完成但未确认业务结果”，不能直接关闭 job。
- Herdr `unknown` 必须进入 `project_view.runtime_status.state = "unknown"` 或
  `"reconnecting"`，不能等同 idle。

## 分阶段实施方案

### Phase 0：契约冻结和证据补齐

目标：先固定边界，不改启动行为。

任务：

- 新增 `HerdrRuntimeManifest`、`HerdrRuntimeBinding`、`HerdrRuntimeEvent` 数据模型。
- 为现有 `HerdrSocketClient.server_info()` 增加 contract fixture，记录 Herdr
  `v0.8.2` 的稳定字段和缺口。
- 给 `CCB_HERDR_CAPABILITY_REPORT`、`report_pane_agent`、`server_info()` 重复调用、
  import-time gate 建立 characterization tests。
- 在计划内明确 `runtime.ensure` 先可由 CCB compatibility adapter 分解为现有
  Herdr CLI/socket 调用，上游 Herdr 原生接口成熟后再切换。

验收：

- 无行为变更。
- 新模型不接触 Provider 凭据。
- 测试能证明旧路径仍 fail-closed。

### Phase 1：CCB 内部收敛为持久 Runtime Client

目标：把 Herdr 连接、server info、capability 和 generation 变成一个进程内握手对象。

任务：

- 在 `lib/platforms/windows/herdr/runtime/client.py` 增加 `handshake()`，缓存
  `server_info`、capabilities、socket ref、server/session identity。
- 在 `lib/platforms/windows/herdr/backend.py` 中停止每个操作都无条件调用
  `server_info()`；仅在首次握手、连接恢复或 generation 改变时刷新。
- 在 `lib/terminal_runtime/backend_resolver.py` 中引入新的 runtime binding 选择路径；
  旧 capability report 保留为兼容输入。
- `ccb.py` 移除导入期 Herdr 探测；`--help`、`version`、配置检查等 introspection
  命令完全不触碰 Herdr。需要 runtime 的命令在 operation-time 调用 Herdr adapter，
  并返回结构化错误。

验收：

- `ccb --help`、`ccb version` 在 Native Windows 且 Herdr 缺失时仍成功。
- 明确选择 Herdr 且 Herdr 不可用时仍 fail-closed。
- Herdr 操作前的重复 `server_info()` 调用显著减少。

### Phase 2：声明式 Manifest 和 `ensure_runtime` 兼容层

目标：让 CCB 只声明拓扑，Herdr 或 compatibility adapter 负责收敛实际 runtime。

任务：

- CCB start path 生成 manifest，并写入 `.ccb/runtime/herdr-runtime-manifest.json`。
- 在 CCB 内先实现 `ensure_runtime(manifest, restore_token)` 兼容层，内部仍可调用
  `create_session`、`ensure_window`、`create_pane`、`set_pane_identity`。
- `handle_start()` 和 `handle_herdr_open()` 改为提交 manifest，不再直接触发
  `_ensure_herdr_runtime_evidence()`。
- `bootstrap.py` 降级为 compatibility bootstrap：只负责解析 Herdr executable 和启动
  初始 server；capability 证据来自握手/binding，不再写临时 capability 文件。

验收：

- 启动、restore、attach、teardown 的持久 namespace 状态仍兼容旧字段。
- manifest 中无原始 API key、OAuth token、完整 prompt/reply 内容。
- 旧 `ccb herdr open --wait-ready` 语义仍能等到 ccbd mounted。

### Phase 3：事件投影和 Agents 面板读模型

目标：解决“Herdr 能识别状态”到“Agents 面板可靠追踪状态”之间的缺口。

任务：

- 增加 Herdr runtime event subscriber；没有上游事件时，先用 snapshot polling
  兼容实现，但对外模型保持事件语义。
- 在 `ccbd.project_view` 的 activity/runtime status resolver 中合并 Herdr runtime
  状态、Provider hook 状态、pane/status-line 状态、CCB job/callback metadata 和
  lifecycle guard。
- 继承既有规则：Provider-native activity 是执行状态权威，CCB job 是工作流元数据，
  lifecycle guard 是归属边界。
- 对 `idle`、`working`、`blocked`、`done`、`unknown` 建立明确映射：

| Herdr 状态 | CCB runtime_status | 说明 |
|---|---|---|
| `working` | `working` | 运行时正在工作，可被 Provider 事实增强 |
| `blocked` | `waiting_for_user` | 需要输入、审批或决策 |
| `idle` | `idle` | 仅代表运行时可输入，不代表 job 成功 |
| `done` | `idle` + `unseen_done=true` | 未查看的完成状态，不触发业务完成 |
| `unknown` | `unknown` | 分类不确定，不能自动降级 |

验收：

- pane 重启、pane move、重新 attach、事件乱序、重复事件、断线重连都不会让旧状态泄漏。
- `runtime_status` 缓存按 project id、agent name、runtime generation、pane id 复合键失效。
- Agents 面板能同时显示运行时状态和 job/ask 状态，不把两者混成一个权威。

### Phase 4：运行时生命周期下放给 Herdr

目标：把通用 workspace/pane 生命周期真正交给 Herdr。

任务：

- 若 Herdr 上游支持原生 `runtime.ensure`，将 Phase 2 compatibility adapter 替换为
  原生 socket/CLI 调用。
- 将 pane readiness、pane liveness、通用 restart/backoff、workspace 清理迁移到
  Herdr。
- CCB 只决定 Provider 是否允许恢复、是否 continuation、是否 job 失败或重试。
- 如 Herdr 尚不能结构化管理 `ccbd` 这类后台服务，向 Herdr 增加或对接：

```text
service.ensure
service.status
service.stop
service.restart
service.wait_ready
```

验收：

- CCB 不再通过 shell/PowerShell/lifecycle 文件间接管理通用 pane 进程存活。
- Provider session restore 仍由 CCB 的 Provider-specific contract 保护。
- 通用 pane 崩溃重启不会伪造 Provider session 已恢复。

### Phase 5：旧路径删除和治理收口

目标：删除只为旧边界存在的复杂度。

候选删除/收窄：

- `CCB_HERDR_CAPABILITY_REPORT` 正常启动路径。
- `bootstrap.py` 中 capability probe 和 temp file 写入。
- `HerdrCliRequestAdapter` 的宽操作白名单；保留 CLI fallback 只覆盖诊断和兼容。
- `backend_resolver.py` 中面向 Herdr 低层 operation 的 capability 组合判断。
- `tmux_runtime.py` 中由 CCB 主动创建 Herdr Agent 身份的补丁逻辑；前提是 Herdr
  已能在 runtime ensure/agent start 阶段稳定返回 `agent_id`。

验收：

- `archi .` 可重新运行时，治理分数和 Herdr/CLI runtime hotspot 应继续改善。
- 删除任何旧路径前必须有等价 characterization test 和 live Windows validation。

## 验证矩阵

直接测试：

```bash
python -m compileall -q lib/platforms/windows/herdr lib/terminal_runtime lib/cli/phase2_runtime ccb.py
pytest test/test_windows_bootstrap_script.py test/test_v2_project_namespace_backend.py test/test_v2_project_namespace_state.py test/test_v2_runtime_launch.py -x
pytest test/test_v2_cli_watch_reconnect.py test/test_cli_startup_update.py -x
```

新增测试应覆盖：

- `ccb --help`/`version` 不触发 Herdr；
- Herdr 不可用时 runtime 命令 fail-closed；
- `HerdrSocketClient.handshake()` 缓存和重连；
- manifest 无 secrets；
- runtime binding 的 project/session/workspace/pane/generation 校验；
- snapshot 初始化、事件乱序、重复事件、generation 过期、pane 重启；
- `done` 不等于 job accepted/completed；
- `unknown` 不被投影为 idle；
- `project_view.runtime_status` 向旧 `activity_state` 兼容降级。

Windows live validation：

- 使用独立测试项目，不在 CCB 源码 checkout 内启动真实长期 runtime。
- 启动 Codex、Claude、Gemini 至少一个稳定 lane。
- 验证工作中、阻塞、空闲、pane 重启、重新 attach、server restart、断线重连。
- 验证 Agents 面板和 mobile gateway 不解析原始 Provider transcript，不泄漏 prompt、
  reply、API key、OAuth token。

## 风险和控制

- **Herdr release 能力与目标契约不完全匹配**：先用 CCB compatibility adapter 实现
  `ensure_runtime` 语义，避免把方案阻塞在上游 API。
- **状态权威混淆**：明确 Herdr runtime 状态不是 Provider/job 完成权威；`done`、
  `idle`、`unknown` 的映射必须测试。
- **凭据泄漏**：manifest 只允许 `env_refs`，禁止 raw secret value。
- **事件乱序和重连**：所有事件按 `server_id`、`session_name`、`workspace_id`、
  `pane_id`、`agent_id`、`runtime_generation`、`seq` 校验。
- **兼容路径长期残留**：每个阶段都必须有明确删除候选；旧 capability/temp-file/CLI
  fallback 只能作为过渡层。
- **Windows 行为回归**：所有真实运行时变更先走 characterization tests，再在独立
  Windows 项目做 live validation。

### Windows 闪窗治理

目标：尽量消除 CCB 自己制造的可见中转窗口和控制台闪现，降低 Windows 原生启动
时的“闪窗”体感。

约束：

- 只允许在 CCB 侧配合 Herdr，不修改 Herdr 源码。
- 不承诺把 Herdr 自身窗口行为改成无 UI；Herdr 作为宿主/终端前台展示仍然是其职责。
- 不把用户主动打开 WezTerm、Herdr 主窗口的可见切换当作缺陷；这里仅治理 CCB 触发的
  transient window。

策略：

- 保留 CCB 原生 launcher 对子进程的无控制台启动策略，避免 Python 或脚本子进程短暂
  弹出控制台。
- 尽量移除 `.ps1` 作为主启动中转层，改为 CCB 内部直接调度可执行文件和 runtime
  adapter。
- 将需要等待 Herdr/CCB 就绪的动作放到后台 ensure 流程中，前台只在最终 attach 时
  进入可见 UI。
- 避免“先起一个可见 shell，再在其中拉起 agent CLI”的双层中转；如果必须保留兼容
  路径，也应退化为诊断/手工路径，而不是默认启动路径。

验收：

- CCB 默认启动路径不再依赖可见 PowerShell 中转窗口。
- 在可观测的 Windows live validation 中，CCB 侧不产生额外控制台闪现。
- 若 Herdr 或 WezTerm 本身需要展示窗口，则只出现一次预期前台窗口，不出现重复闪烁。

## 推荐优先级

Immediate：

- 冻结 `HerdrRuntimeManifest`、`HerdrRuntimeBinding`、`HerdrRuntimeEvent`。
- 给现有导入期门禁、capability temp file、重复 `server_info()`、pane agent report
  建 characterization tests。
- 移除 `ccb.py` 导入期 Herdr 探测，把 Herdr 可用性检查移动到 runtime operation。

Next：

- 在 CCB 内落地 `ensure_runtime()` compatibility adapter。
- `handle_start()`/`handle_herdr_open()` 改为 manifest submission。
- 建立 runtime binding 持久化和 generation 校验。
- 给 Agents 面板接入 snapshot/event 风格读模型。

Later：

- 切换到 Herdr 原生 `runtime.ensure`/event API。
- 将通用 pane restart/backoff/readiness 下放给 Herdr。
- 删除旧 capability report、宽 CLI adapter、bootstrap capability probe。

最小可交付切片应该是：

```text
manifest 模型 + runtime binding
    -> CCB 内 ensure_runtime compatibility adapter
    -> operation-time Herdr handshake
    -> ProjectView runtime_status generation 校验
```

这个切片足够小，可验证，并且直接降低当前最核心的架构风险：CCB 同时扮演运行时宿主、
Provider 控制面和状态投影层。
