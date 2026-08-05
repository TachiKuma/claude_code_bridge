---
doc_type: issue-analysis
issue: 2026-08-05-herdr-ui-spike-run-findings
status: draft
root_cause_type: config
related: [herdr-ui-spike-run-findings-report.md]
tags:
  - ccb8-cli
  - ccbd-socket
  - run_spike.ps1
  - herdr-session
  - windows
---

# Herdr UI Spike 全量采集运行发现 根因分析

## 1. 问题定位

### F1: `ccb8 ps` 子命令路由错误

| 关键位置 | 说明 |
|---|---|
| `lib/cli/parser_runtime/constants.py:10` | `'ps'` 已在 `SUBCOMMANDS` 集合中 |
| `lib/cli/parser.py:61` | `'ps': parse_ps` 已在 `_COMMAND_PARSERS` 字典中 |
| `lib/cli/parser.py:95-96` | `command not in SUBCOMMANDS` → `parse_start()` 是路由到 start 的分叉点 |
| `lib/cli/parser_runtime/start.py:36-39` | 错误消息 `"start does not accept agent names or extra arguments"` 的来源 |
| `lib/cli/parser_runtime/commands.py:1190-1192` | `parse_doctor` 通过 `tokens[:1] in (['ps'], ['--runtime'])` 手动将 `doctor ps` 路由到 `parse_ps` |
| `lib/cli/parser_runtime/commands.py:1048-1050` | `parse_ps` 正确实现：不接受额外参数，返回 `ParsedPsCommand` |
| `lib/cli/phase2_runtime/dispatch.py:74` | `'ps': handle_ps` 在 dispatch 表中 |
| `lib/cli/phase2_runtime/handlers_ops.py:174-177` | `handle_ps` 正确调用 `services.ps_summary` |
| 外部项目 `ccb8.ps1:534-543` (external-ccb8.ps1.txt) | `Test-ShouldPrestartKill` 未处理 `start` 别名，直接透传 `ps` 给 `ccb.py` |
| 外部项目 `ccb8.ps1:821` | `& $env:CCB_PYTHON ... @CcbArgs` 直接传递参数 |
| 本仓库 `ccb8.ps1:830-838` | 新增 `start` 别名转换逻辑（`$CcbArgs[0] -ieq 'start'` → 跳过第一个参数） |

**定位结论：Python CLI 代码中 `ps` 子命令路由完全正确**（`SUBCOMMANDS` 包含 `ps`，`_COMMAND_PARSERS` 有 `parse_ps`，dispatch 表有 `handle_ps`）。`ccb8 doctor ps` 正常工作的原因是通过 `parse_doctor` 的手动检查（`tokens[:1] in (['ps'], ...)`）绕过了 `CliParser.parse()` 的正常路由，但**正常路由也应该能处理 `ps`**。

在 Python 代码层面，`CliParser.parse(['ps'])` 的执行路径为：
```
tokens=['ps'] → command='ps' → command in SUBCOMMANDS → True
→ parser_fn = _COMMAND_PARSERS['ps'] = parse_ps
→ parse_ps([], project=None, ...) → ParsedPsCommand(project=None)
```

这个路径**不会**到达 `parse_start`。因此错误几乎肯定发生在 **Python CLI 到达之前**的包装层——外部项目的 `ccb8.cmd` 或 `ccb8.ps1` 可能：
- 包含与本地版本不同的 batch 逻辑，导致参数被错误转换
- 通过 PATH 中的 `ccb.cmd` shim 调用而非直接调用 `ccb.py`
- 或存在 Python 字节码缓存（`.pyc`）过期问题

### F2: CCB Herdr 会话 socket 文件缺失

| 关键位置 | 说明 |
|---|---|
| `lib/ccbd/main.py:31-54` | `CcbdApp` 启动入口，`serve_forever()` 驱动完整生命周期 |
| `lib/ccbd/services/project_namespace_runtime/backend.py:274-292` | `create_session()` —— Herdr 后端通过 `backend.create_session(project_id=..., cwd=..., title=...)` 创建命名空间 |
| `lib/ccbd/services/project_namespace_runtime/ensure_identity.py:24` | ccbd 启动时调用 `create_session()` 建立命名空间 |
| `lib/terminal_runtime/herdr_backend_runtime/cli.py` | ⚠ 此文件在当前 git diff 中被修改，可能包含 Herdr server socket 创建逻辑 |
| Herdr 状态输出（证据） | `"socket": "C:\\ccb8v\\.ccb-source-dev\\state\\xdg-config\\herdr\\sessions\\ccb-herdr-avaprintdesigner-source-dev\\herdr.sock"` — 这是**包装器**会话的 socket |
| CCB 自身会话（证据） | `session_name=ccb-avaprintdesigner-575a971f` —— CCB 使用不同的会话名，其 socket 路径在包装器会话的 xdg 目录之外 |

**定位结论：** CCB 创建的 Herdr 会话 (`ccb-avaprintdesigner-575a971f`) 与 spike 脚本运行的包装器会话 (`ccb-herdr-avaprintdesigner-source-dev`) 是**两个独立的 Herdr server 进程**。CCB 会话的 socket 文件在第二次 run 期间不存在（`NotFound`），但在第一次 run 期间存在（exit=0 但 stdout 为空）。

两次 run 之间的差异表明 socket 生命周期存在问题：
- Run 133244：CCB 会话 server 正在运行且 socket 可连接（但 `api snapshot` 返回空）
- Run 165854：CCB 会话 server socket 文件完全不存在

可能原因：
1. 两次 run 之间执行了 `ccb kill` 或其他清理操作，销毁了 CCB Herdr 会话
2. CCB Herdr server 进程在第一次 run 后崩溃/退出，未能保留 socket
3. socket 路径依赖临时或会话范围的目录，在 Herdr 重启时被清理

### F3: 分类逻辑 ping-ccbd vs ping-all 竞争

| 关键位置 | 说明 |
|---|---|
| `run_spike.ps1:1181-1196` | `$pingAllSuccess` 判定：检查 ping-all exit_code + mount_state |
| `run_spike.ps1:1230-1244` | 分类决策链：`hasHerdrUiEvidence` → `startStatus` → **`pingText -notmatch 'mount_state:\s*mounted'`** → `pingAllSuccess` → `layoutMaterializationComplete` → `panelText` |
| `run_spike.ps1:1186-1189` | `$pingText` 读取的是 `ccb8-ping-ccbd` 的输出，**不是** `ccb8-ping-all` |
| 证据：ping-ccbd stdout | `mount_state: unmounted, reason: lease_unmounted` |
| 证据：ping-all attempt-2 stdout | 两个 agent 均为 `mount_state: mounted, runtime_state: idle, health: restored` |

**定位结论：** 分类逻辑在第 1234 行检查 `$pingText`（来自 `ping-ccbd`）的 `mount_state`。当 ccbd 仍在启动时（`ping-all attempt-1` 返回 "project ccbd is starting"），`ping-ccbd` 可能先于 ccbd 完全启动而被执行，导致读到过渡状态 `unmounted`。随后 `ping-all` 的重试机制正确等待并获得了 `mounted` 结果，但分类已经在前一步用 `unmounted` 做出了判断。

### F4: Herdr 会话分叉

| 关键位置 | 说明 |
|---|---|
| `run_spike.ps1:857-861` | Herdr baseline 采集始终使用 `$effectiveHerdrSession`（包装器会话） |
| `run_spike.ps1:896-898` | post-start Herdr 采集也使用包装器会话 |
| `run_spike.ps1:938-964` | 新增 CCB namespace session 提取和采集（`$ccbHerdrSession`），仅在 `$ccbHerdrSession -ne $effectiveHerdrSession` 时执行 |
| 证据：包装器会话 `api snapshot` | 两次均返回 `agents:[], layouts:[], panes:[], workspaces:[]` |
| 证据：CCB 会话 Herdr server | `herdr.exe server --session ccb-avaprintdesigner-575a971f`（pid 10804，进程采样器中可见） |

**定位结论：** 这是结构性设计，并非 bug。CCB 创建独立的 Herdr 会话是为了隔离其 pane/workspace 管理，避免与用户的其他 Herdr 会话冲突。spike 脚本已经正确处理了这种情况（通过 `$ccbHerdrSession` 提取和 `herdr-api-snapshot-ccb-namespace` 采集），但 CCB 会话的 socket 不稳定（F2）导致无法获取快照数据。

### F5: 启动状态文件缺失 3/5

| 关键位置 | 说明 |
|---|---|
| `run_spike.ps1:973-1018` | startup-state-files 采集维度 |
| `run_spike.ps1:978-989` | 从 `.ccb/` 复制 `runtime-root-ref.json` 和 `project.identity.json`——**成功** |
| `run_spike.ps1:990-1003` | 从 `.ccb/ccbd/` 复制 `lease.json`, `keeper.json`, `lifecycle.json`——**全部失败**（目录不存在或文件缺失） |
| `run_spike.ps1:1006-1017` | 从 doctor output 复制 `startup-report.json`——**失败**（doctor output 目录不存在） |
| 证据：`startup-state-files-manifest.txt` | 仅包含 2 个文件：`runtime-root-ref.json`, `project.identity.json` |

**定位结论：** `.ccb/ccbd/` 目录在外部项目（AvaPrintDesigner）的文件系统中不存在。这些文件（`lease.json`, `keeper.json`, `lifecycle.json`）实际上存储在**运行时状态根目录** `D:\.c8\rs\{project_id}\ccbd\` 下，而非项目 `.ccb/ccbd/` 目录。Doctor output 目录也不存在——`ccb8 doctor --output` 命令返回了 `doctor_bundle_status: ok, file_count: 72`，但 `bundle_path` 指向 spike 证据目录内的 `doctor-output` 子目录，而非脚本期望的路径。

CCB 的 runtime state home 重定位机制（`CCB_RUNTIME_STATE_HOME=D:\.c8\rs`）将 ccbd 状态文件移出了项目目录，但 spike 脚本仍假设它们在 `.ccb/ccbd/` 下。

### F6: 用户观察字段为空

| 关键位置 | 说明 |
|---|---|
| `run_spike.ps1:700-723` | `New-ManualObservationTemplate` 生成模板 |
| 证据：`manual-observation.md:9-13` | 5 个问题字段均为尾随冒号无内容 |

**定位结论：** 用户尚未在 Herdr UI 中运行后手动填写观察结果。这不是代码缺陷。

## 2. 失败路径还原

### F1 失败路径

```
用户输入: ccb8 ps
→ ccb8.cmd: powershell -File ccb8.ps1 ps
→ ccb8.ps1: Initialize-WrapperEnvironment → Test-ShouldPrestartKill → Invoke-PrestartCleanup
→ ccb8.ps1: & python ccb.py ps
→ entrypoint_runtime.py: run_cli_entrypoint(['ps'], ...)
→ _dispatch_auxiliary → None（不处理 ps）
→ _dispatch_management → None（不处理 ps）
→ _dispatch_rich/_tools/_theme/_roles → None
→ _dispatch_auto_rich_start → None（'ps' 不在 allowed 集合中）
→ maybe_handle_phase2(['ps'], ...)
→ parse_phase2_command → CliParser().parse(['ps'])
→ command='ps' → command in SUBCOMMANDS → True
→ parse_ps([], ...) → ParsedPsCommand(project=project)
→ dispatch: handle_ps → ps_summary → 正常输出
```

**正常路径应能工作。** 但由于 `ccb8 ps` 实际 exit=2 且 stderr 显示 `start does not accept agent names`，说明实际执行的是 `parse_start` 而非 `parse_ps`。这意味着 Python 进程收到的 argv 不是 `['ps']`，或者运行的 Python 代码版本与源代码不一致。

**最可能的分叉点：** 外部项目 `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.cmd` 或 `ccb8.ps1` 的版本与 `external-ccb8.ps1.txt` 中捕获的快照不同——可能包含将 `ps` 错误传参的逻辑。或者 `$devBin\ccb.cmd` shim 在 wrapper 启动时创建后，PATH 中存在另一个 `ccb`（已安装版本）先被解析。

### F2 失败路径

```
正常路径:
  ccbd serve_forever() → ensure_identity → create_session(backend=herdr, ...)
  → backend.create_session(project_id=..., cwd=..., title=...)
  → Herdr server 启动，socket 文件在 {herdr_state}/sessions/{session_name}/herdr.sock
  → herdr api snapshot --session {session_name} → exit=0, 返回快照

失败路径 (run-165854):
  同上直到 create_session → Herdr server 启动
  → herdr api snapshot --session ccb-avaprintdesigner-575a971f
  → exit=1, "系统找不到指定的文件"
  → socket 文件不存在

失败路径 (run-133244):
  同上直到 create_session → Herdr server 启动，socket 存在
  → herdr api snapshot --session ccb-avaprintdesigner-575a971f
  → exit=0, stdout 为空 → 快照内容为空
```

**分叉点：** Herdr server 的 socket 文件生命周期不稳定。Run 133244 中 socket 存在但可能已被部分清理（内容为空），Run 165854 中 socket 完全不存在。表明 socket 在两个 run 之间被清理、覆盖或从未正确写入。

## 3. 根因

### F1 根因

**根因类型**：config（外部项目的包装器版本与 Python 源代码不一致）

**根因描述**：Python CLI 代码中 `ps` 子命令路由完整且正确。`ccb8 doctor ps` 能正常工作证明了底层 `ps_summary` 和 `handle_ps` 实现正确。`ccb8 ps` 失败是因为 Python 进程实际收到的 argv 或运行的 Python 代码与源代码不一致——最可能的原因是外部项目 `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.ps1` 或 `ccb8.cmd` 的版本与仓库中捕获的快照不同，或者 `$devBin\ccb.cmd` shim 调用的是已安装的 `ccb` 而非源码版本。

**是否有多个根因**：是。主因是包装器层参数传递不一致，次因可能是 Python 字节码缓存（`.pyc`）或模块导入路径问题。

### F2 根因

**根因类型**：concurrency / state-pollution

**根因描述**：CCB Herdr 会话 (`ccb-avaprintdesigner-575a971f`) 的 socket 文件在两次 spike run 之间丢失。第一次 run 中 socket 存在（exit=0），第二次 run 中 socket 不存在（NotFound）。这表明 Herdr server 的 socket 文件没有被可靠地持久化，或者在 ccbd 启动/停止周期中被过早清理。ccbd 的 `serve_forever()` 循环在第一次 run 后可能触发了 Herdr session 销毁（通过 `ccb kill -f` prestart cleanup），而第二次 run 的 Herdr server 未能及时完成 socket 绑定。

**是否有多个根因**：否。

### F3 根因

**根因类型**：concurrency（时序竞争）

**根因描述**：`run_spike.ps1:1234` 的分类逻辑使用 `ping-ccbd`（守护进程级状态，可能在 ccbd 完全启动前被采集）的 `mount_state` 作为"CCB 是否已挂载"的判断依据。实际上 `ping-all`（agent 级状态，带重试）才是权威的挂载证据。ping-ccbd 在 ccbd 启动中期被调用（elapsed=2510ms），此时 ccbd 的 `mount_state` 仍为 `unmounted`；而 ping-all 在重试后（elapsed=3852ms）正确报告两个 agent 均为 `mounted`。

**是否有多个根因**：否。单一时序问题。

### F4 根因

**根因类型**：config（结构性设计，非 bug）

**根因描述**：CCB 创建独立 Herdr 会话是其设计的隔离策略。这不是 bug，而是 spike 需要适配的结构性事实。spike 脚本已经正确处理了这种情况（通过提取 `$ccbHerdrSession`），但需要 CCB 会话的 socket 稳定存在（F2）才能完成验证。

**是否有多个根因**：否。

### F5 根因

**根因类型**：config（路径假设错误）

**根因描述**：spike 脚本假设 ccbd 状态文件（`lease.json`, `keeper.json`, `lifecycle.json`）存储在项目目录 `.ccb/ccbd/` 下。但由于 `CCB_RUNTIME_STATE_HOME` 重定位机制，这些文件实际存储在 `D:\.c8\rs\{project_id}\ccbd\` 下。同样，doctor output 的 `startup-report.json` 路径假设与 `ccb8 doctor --output` 的实际输出结构不匹配。

**是否有多个根因**：否。

### F6 根因

**根因类型**：missing-guard（用户操作步骤未完成）

**根因描述**：用户尚未在 Herdr UI 运行后填写 `manual-observation.md` 中的观察字段。非代码缺陷。

## 4. 影响面

### F1

- **影响范围**：所有使用 `ccb8 ps` 的用户。`ccb8 doctor ps` 是可用替代方案。
- **潜在受害模块**：ccb8 CLI 的所有使用者。如根因是包装器版本不一致，则影响所有通过该包装器调用的命令。
- **数据完整性风险**：无。
- **严重程度复核**：维持 **P1**。核心 CLI 命令不可用，但有可用的替代命令（`ccb8 doctor ps`）。

### F2

- **影响范围**：所有需要从外部查询 CCB Herdr 会话状态的工具（监控、诊断、spike 采集）。
- **潜在受害模块**：`run_spike.ps1` 的 pane-verification 维度、任何依赖 `herdr api snapshot` 的 CCB 会话监控工具。
- **数据完整性风险**：无。socket 缺失不会导致数据丢失，仅导致查询不可用。
- **严重程度复核**：维持 **P1**。CCB Herdr 会话对外不可查询，影响诊断和监控链路。

### F3

- **影响范围**：仅影响 `run_spike.ps1` 的分类准确性。对 CCB 实际运行无影响。
- **潜在受害模块**：无其他模块依赖此分类。
- **数据完整性风险**：无。
- **严重程度复核**：维持 **P2**。分类误导但采集数据完整，不影响 CCB 运行。

### F4

- **影响范围**：所有需要在外部观察 CCB pane 状态的工具。
- **潜在受害模块**：spike 脚本、CCB 监控/诊断工具。
- **数据完整性风险**：无。
- **严重程度复核**：维持 **P2**。结构性设计，有绕行方案（使用 CCB 自身会话）。

### F5

- **影响范围**：仅影响 spike 脚本的 startup-state-files 采集维度。
- **潜在受害模块**：无。
- **数据完整性风险**：无。
- **严重程度复核**：维持 **P3**。

### F6

- **影响范围**：仅影响 spike 报告完整性。
- **潜在受害模块**：无。
- **严重程度复核**：维持 **P3**。

## 5. 修复方案

### F1: `ccb8 ps` 路由错误

#### 方案 A：验证并修复外部项目包装器（推荐）

- **做什么**：检查外部项目 `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.ps1` 的实际内容，确认其 `Test-ShouldPrestartKill` 和参数传递逻辑是否正确。如与仓库 `ccb8.ps1` 不一致，同步更新。如已一致，检查 `$devBin\ccb.cmd` shim 内容和 PATH 优先级。
- **优点**：不改动 Python CLI 代码，修复在问题发生的准确位置。
- **缺点 / 风险**：需要访问外部项目文件系统。如果外部项目有自定义修改，需要评估兼容性。
- **影响面**：仅 `ccb8.ps1` 和/或 `ccb8.cmd`。

#### 方案 B：在 Python CLI 增加防御层

- **做什么**：在 `CliParser.parse()` 或 `entrypoint_runtime.py` 中增加日志，记录实际收到的 argv 和路由决策，方便下次出现时定位。
- **优点**：不依赖外部项目文件访问，增加系统可观测性。
- **缺点 / 风险**：不直接修复问题，只是改善诊断能力。
- **影响面**：`lib/cli/parser.py` 或 `lib/cli/entrypoint_runtime.py`。

### F2: CCB Herdr 会话 socket 缺失

#### 方案 A：ccbd 启动时验证 socket 可用性（推荐）

- **做什么**：在 `CcbdApp.serve_forever()` 或 `ensure_identity` 完成后，增加一个显式的 socket 可用性验证步骤——通过 Herdr CLI（`herdr status server --session {session_name}`）或直接检查 socket 文件路径，确认 socket 已就绪。如果不可用，记录诊断日志并重试（最多 N 次）。
- **优点**：确保 CCB Herdr 会话在 ccbd 报告"mounted"之前真正可达。
- **缺点 / 风险**：增加启动延迟（约 1-3 秒）。需要确定正确的 socket 路径推导逻辑。
- **影响面**：`lib/ccbd/main.py`、`lib/ccbd/services/project_namespace_runtime/ensure_identity.py`，可能需要新增 socket 验证函数。

#### 方案 B：在 spike 脚本中增加 socket 等待/重试

- **做什么**：在 `run_spike.ps1` 的 `herdr-api-snapshot-ccb-namespace` 调用前增加重试循环，等待 CCB Herdr 会话 socket 就绪。
- **优点**：改动小，仅影响采集脚本。
- **缺点 / 风险**：不解决根本问题——CCB Herdr 会话在外部工具中仍不可查询。
- **影响面**：仅 `run_spike.ps1`。

### F3: 分类逻辑竞争

#### 方案 A：重构分类逻辑使用 ping-all 结果（推荐）

- **做什么**：将 `run_spike.ps1:1230-1244` 的分类决策链改为优先使用 `ping-all` 的 agent 级状态，而非 `ping-ccbd` 的守护进程级状态。
  具体修改：将第 1234 行的 `$pingText -notmatch 'mount_state:\s*mounted'`（检查 ping-ccbd）替换为 `-not $pingAllSuccess`（检查 ping-all），并将此检查移到 ping-all 检查之后。
- **优点**：分类结果与 CCB 实际挂载状态一致。ping-all 的重试机制已经处理了 ccbd 启动中期问题。
- **缺点 / 风险**：需要确认 ping-all 失败时（ccbd 真的未挂载）的兜底分类是否仍有意义。
- **影响面**：仅 `run_spike.ps1:1230-1244`。

#### 方案 B：延迟 ping-ccbd 调用时机

- **做什么**：将 `ccb8-ping-ccbd` 命令移到 `ccb8-ping-all` 成功之后执行，确保 ccbd 已完成启动。
- **优点**：ping-ccbd 返回的数据更准确。
- **缺点 / 风险**：改变了采集维度执行顺序，可能影响其他维度对 ping-ccbd 数据的依赖。
- **影响面**：`run_spike.ps1:900-928`。

### F4: Herdr 会话分叉

- **做什么**：在 spike 报告的 Interpretation 节中增加说明，标注包装器会话 `api snapshot` 为空是预期行为（CCB pane 在独立会话中）。确保 CCB 会话 snapshot 采集（`herdr-api-snapshot-ccb-namespace`）稳定可用（依赖于 F2 修复）。
- **优点**：澄清结构性设计，避免后续疑惑。
- **缺点 / 风险**：无。
- **影响面**：仅 `run_spike.ps1` 报告模板或 Interpretation 注释。

### F5: 启动状态文件采集不完整

#### 方案 A：更新采集路径指向运行时状态根目录（推荐）

- **做什么**：在 `run_spike.ps1:990-1003` 中，将 ccbd 状态文件的搜索路径从 `.ccb/ccbd/` 改为同时检查 `$runtimeStateHome/{project_id}/ccbd/`。从 `runtime-root-ref.json` 中提取 `project_id` 和 `runtime_state_root` 以构建正确路径。
- **优点**：与实际文件位置一致，采集完整。
- **缺点 / 风险**：需要解析 `runtime-root-ref.json` 获取 `project_id`，增加少量复杂度。
- **影响面**：仅 `run_spike.ps1:973-1018`。

#### 方案 B：仅记录缺失原因，不修改路径逻辑

- **做什么**：在复制失败时输出诊断日志（如"runtime state relocated to {path}，skipping .ccb/ccbd/"），并记录 `startup-state-files-manifest.txt` 中的跳过原因。
- **优点**：改动最小。
- **缺点 / 风险**：仍采集不到文件，但至少知道原因。
- **影响面**：仅 `run_spike.ps1:990-1017`。

### F6: 用户观察字段为空

- **做什么**：无代码修改。提醒用户在 Herdr UI 运行 spike 后填写 `manual-observation.md`。

### 推荐方案

- **F1**：方案 A（验证并修复外部项目包装器）——在实际出错位置修复，不改动已验证正确的 Python CLI 代码。
- **F2**：方案 A（ccbd 启动时验证 socket 可用性）——从根源解决问题，确保 CCB Herdr 会话在报告"mounted"之前真正可达。
- **F3**：方案 A（使用 ping-all 结果分类）——最小改动，最高准确性。
- **F4**：文档说明——不改代码，增加 Interpretation 注释。
- **F5**：方案 A（更新采集路径）——采集完整文件。
- **F6**：用户提醒——不改代码。
