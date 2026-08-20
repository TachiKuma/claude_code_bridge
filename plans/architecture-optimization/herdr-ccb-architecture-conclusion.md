**当前判断**

我核实到 Herdr 最新稳定版是 `v0.8.2`，发布时间为 **2026 年 8 月 19 日**。这个版本已经具备更强的 Agent 状态识别、启动就绪等待、阻塞状态判断、Windows 原生 Agent 支持、远程客户端、服务端停止绕过 pane/API 等能力。

CCB 当前仍然是：

> CCB 负责启动编排，Herdr 只是被调用的终端后端。

建议演进为：

> **Herdr 负责 Host Runtime，CCB 负责 Collaboration Control Plane。**

**当前主要耦合点**

1. `ccb.py` 在进程导入阶段探测平台和 Herdr，并执行硬门禁。  
   见 [ccb.py](/E:/GitHub开源项目/TachiKuma/NativeWin_CCB_Herdr/ccb.py:42)。

2. `handle_start()` 仍然负责 Herdr capability 探测、自动启动 server、写临时 capability 文件、注入环境变量。  
   见 [handlers_start.py](/E:/GitHub开源项目/TachiKuma/NativeWin_CCB_Herdr/lib/cli/phase2_runtime/handlers_start.py:89)。

3. `bootstrap.py` 自己发现 Herdr session、启动 server、轮询 server readiness、执行 capability probes。  
   见 [bootstrap.py](/E:/GitHub开源项目/TachiKuma/NativeWin_CCB_Herdr/lib/platforms/windows/herdr/bootstrap.py:38)。

4. CCB 的 backend resolver 维护了大量 Herdr operation/capability 白名单。  
   见 [backend_resolver.py](/E:/GitHub开源项目/TachiKuma/NativeWin_CCB_Herdr/lib/terminal_runtime/backend_resolver.py:28)。

5. CCB 仍需要显式调用 `report_pane_agent` 创建 Herdr Agent 身份。代码中已经明确注明当前 Herdr 不会仅凭 session 自动创建 Agent。  
   见 [tmux_runtime.py](/E:/GitHub开源项目/TachiKuma/NativeWin_CCB_Herdr/lib/cli/services/runtime_launch_runtime/tmux_runtime.py:289)。

6. **Agents 面板的状态跟踪仍不完整。**
   即使 Herdr 已具备 idle/working/blocked 等运行时状态识别，Agents 面板仍依赖
   CCB 的 Agent 注册、Herdr 的 pane 生命周期以及 CCB 的 Provider/job 状态投影。
   当前在启动就绪、pane 重启、重新 attach、快速状态切换、事件乱序或连接中断后，
   可能出现 pane/Agent 身份映射丢失、状态滞后、旧状态残留，或将运行时空闲误显示为
   业务完成。因此，“Herdr 能识别状态”不等于“Agents 面板能可靠追踪状态”。

**建议的职责边界**

| 能力 | 应由 Herdr 负责 | 应由 CCB 负责 |
|---|---|---|
| server/session/workspace 生命周期 | 是 | 否 |
| tab/window/pane 创建、布局、焦点、attach | 是 | 否 |
| pane 进程启动、就绪、退出、重启 | 是 | 仅制定策略 |
| Agent idle/working/blocked 状态 | 是 | 消费状态 |
| Provider 命令和 Provider home | 否 | 是 |
| Provider session/resume/fork | 否 | 是 |
| ask、队列、取消、回复、协作图 | 否 | 是 |
| ccbd、keeper、startup fence | 暂时仍由 CCB | 是 |
| pane 崩溃后的通用重启 | 是 | 决定是否允许 |
| Provider 语义恢复 | 否 | 是 |
| terminal UI、远程连接、窗口标题 | 是 | 否 |

Agents 面板需要一个明确的统一读模型：Herdr 提供稳定的 `agent_id`、`pane_id`、
`runtime generation`、有序状态事件和可重同步快照；CCB 负责将这些运行时状态与
Provider/job/ask 状态合并。面板必须能够区分运行时状态、业务状态、断线状态和未知状态，
并在重启或重新 attach 后按 generation 丢弃过期事件，不能依赖当前 pane 文本或最后一次
轮询结果作为唯一事实来源。

**Immediate**

1. **建立单一 Herdr Runtime Contract**

   CCB 不再组合多个命令：

   ```text
   herdr server status
   herdr session list
   herdr api snapshot
   herdr workspace create
   herdr pane create
   ```

   改成一次结构化请求：

   ```text
   ensure_runtime(manifest, restore_token)
   ```

   返回：

   ```json
   {
     "server_id": "...",
     "session_name": "...",
     "workspace_id": "...",
     "generation": 12,
     "panes": [],
     "ready": true,
     "capabilities": {}
   }
   ```

2. **移除临时 `CCB_HERDR_CAPABILITY_REPORT` 机制**

   当前 capability report 是 CCB 临时写文件，再通过环境变量传递。建议改成：

   - Herdr API 握手时直接返回 capability；
   - CCB 将已接受的 contract/version/generation 写入自己的 runtime binding；
   - 每次启动只做轻量版本和 generation 校验。

   这样可以删除 `ensure_herdr_bootstrap_env()` 的大部分职责。

3. **去掉 CCB 导入阶段的 Herdr 检查**

   `ccb.py` 不应在模块加载时执行 Herdr 探测。建议改为：

   - `ccb --help`、`ccb version` 完全不触碰 Herdr；
   - 只有需要创建运行时的命令才调用 Herdr adapter；
   - Herdr 不可用时，由 adapter 返回结构化错误。

4. **使用持久 IPC，减少 CLI 子进程启动**

   当前 `HerdrCliRequestAdapter` 通过命令行反复调用 Herdr。并且 `HerdrBackend` 多个操作前都重复调用 `server_info()`。

   建议：

   - CCB 启动时建立一个 Herdr IPC client；
   - 缓存 `server_info` 和 capability；
   - 只在连接断开或 generation 变化时重新握手；
   - pane/window 操作全部复用同一个连接。

**Next**

1. **把拓扑改成声明式 manifest**

   CCB 只生成：

   ```json
   {
     "project_id": "...",
     "cwd": "...",
     "windows": [
       {
         "name": "main",
         "panes": [
           {
             "agent": "codex",
             "command": ["codex"],
             "cwd": "...",
             "role": "planner"
           }
         ]
       }
     ]
   }
   ```

   Herdr 负责比较 manifest 与实际 workspace，执行 create/update/remove/restart。

2. **让 Herdr 负责通用 Agent 生命周期**

   充分利用 `v0.8.2` 的：

   - Agent 启动等待；
   - idle/working/blocked 状态识别；
   - Agent prompt readiness；
   - pane 进程状态；
   - 通用 restart/stop；
   - Windows 原生 CLI 集成。

   CCB 只消费事件，不再主动轮询 pane 文本判断基础状态。

   这一步必须同时解决 Agents 面板的状态一致性问题：事件流需要支持快照初始化、
   断线重连后的重同步、事件序列或 generation 校验，以及 pane/Agent 身份稳定映射。
   在这些能力完成前，面板应显示未知或断线，而不是猜测为 idle。

3. **引入 Herdr 事件流**

   Herdr 应向 CCB 推送：

   ```text
   workspace_created
   pane_started
   pane_ready
   agent_state_changed
   pane_exited
   pane_restarted
   workspace_stopped
   ```

   CCB 仍然负责把这些事件映射到 job、agent、ccbd 状态。

4. **拆分恢复权**

   Herdr 负责：

   - pane 崩溃；
   - 子进程退出；
   - 通用重启；
   - 重启次数和退避；
   - workspace/pane 资源清理。

   CCB 负责：

   - Provider session 是否还能恢复；
   - 是否允许继续发送；
   - provider turn 是否匹配；
   - 是否需要新建 continuation；
   - ask/job 是否失败或重试。

   这样可以把现有 CCB 中一部分 pane recovery 逻辑下放，但不会破坏 Provider 语义安全。

**Later**

1. **让 Herdr 成为 CCB 的外层运行时宿主**

   理想启动方式：

   ```text
   herdr workspace open --manifest .ccb/runtime.json
   ```

   Herdr 负责：

   - 启动或复用 server；
   - 创建 session/workspace；
   - 启动 ccbd control process；
   - 创建 Agent panes；
   - 等待所有 pane ready；
   - 提供 attach/remote UI。

   CCB 只负责生成 manifest、启动 ccbd 业务逻辑、连接已有 runtime。

2. **增加 Herdr 的 managed service API**

   如果 Herdr 目前只能管理 pane，而不能结构化管理 ccbd 这类后台服务，建议增加：

   ```text
   service ensure
   service status
   service stop
   service restart
   service wait-ready
   ```

   CCB 不应再通过 PowerShell、WezTerm 或 lifecycle 文件间接管理启动过程。

3. **安全地传递环境变量**

   manifest 不建议直接携带 API key。可以引入：

   ```json
   {
     "env": {
       "OPENAI_API_KEY": {
         "source": "ccb-agent-home",
         "name": "OPENAI_API_KEY"
       }
     }
   }
   ```

   CCB 保留凭据和 Provider home 的所有权，Herdr 只负责按授权引用注入。

**最值得优先做的重构**

第一阶段不要先改所有 Provider。优先实现：

```text
CCB Runtime Manifest
        |
        v
Herdr ensure_runtime()
        |
        v
workspace/session/pane handles + readiness events
        |
        v
CCB ccbd attaches to the runtime
```

具体落点：

- 新增 `HerdrRuntimeContract`；
- 重写 `bootstrap.py`，只保留兼容层；
- 将 `handle_start()` 改成 manifest 提交；
- 删除启动路径中的临时 capability 文件；
- 将 Herdr 连接和 server 信息缓存到一个 client；
- 保留 `ccbd`、Provider session、ask/job、恢复策略在 CCB 内。

核心原则是：

> **Herdr 管“进程和终端世界”，CCB 管“Agent 业务和协作世界”。**

其中 Agents 面板是两者之间的投影层，不应成为第三个状态权威。必须先定义运行时事件、
业务状态和面板读模型的映射，以及重启、断线、乱序和重同步语义，才能解决当前状态跟踪
不够完美的问题。

不要把 Provider session、消息队列、取消语义、权限审批和恢复判断移入 Herdr，否则只是把 CCB 的复杂度转移成两个互相耦合的控制面。
