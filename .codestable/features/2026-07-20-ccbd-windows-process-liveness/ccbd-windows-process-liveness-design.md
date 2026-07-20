---
doc_type: feature-design
feature: 2026-07-20-ccbd-windows-process-liveness
requirement:
roadmap: windows-rmux-native-backend
roadmap_item: ccbd-windows-process-liveness
execution_lane: goal
status: approved
summary: 为 ccbd 控制面提供无副作用的跨平台 pid 存活判定，避免 Windows 上 os.kill(pid, 0) 误判或投递 Ctrl-C
tags: [ccbd, windows, process-liveness, keeper, health, ownership, epic-child]
---

# ccbd-windows-process-liveness feature design

## 0. 术语约定

| 术语 | 定义 | 防冲突结论 |
|---|---|---|
| process liveness | 对单个 pid 是否仍表示一个未退出进程的只读判定。 | 本 feature 只回答 pid alive/dead，不证明进程属于某 project / daemon instance。 |
| signal probe | POSIX 常见 `os.kill(pid, 0)` 探测。 | Windows 上 `os.kill(pid, 0)` 不是只读探测，必须从 ccbd 默认路径移除。 |
| Windows handle probe | 用 WinAPI `OpenProcess` + `WaitForSingleObject(handle, 0)` 查询进程是否已 signaled。 | 本 feature 选择标准库 `ctypes`；psutil 不进入当前交付。 |
| job-object evidence | Windows Job Object 提供的进程树/kill/recovery evidence。 | 属于 `windows-job-object-runtime-evidence`，本 feature 不实现进程树 authority。 |

仓库事实：

- `lib/ccbd/system.py::process_exists()` 当前用 `os.kill(pid, 0)`；roadmap 记录 Windows 上该调用会误判普通活进程为 dead，且 pid 恰为 console group 时可能投递 Ctrl-C。
- `ccbd.system.process_exists` 被 `ccbd/keeper.py`、`ccbd/keeper_runtime/state.py`、`ccbd/services/ownership.py`、`ccbd/services/health.py` 默认消费，影响 keeper running、lease health、takeover、provider runtime orphan 判定。
- `cli.kill_runtime.processes.is_pid_alive()` 也是共享 pid alive helper，并已有 POSIX zombie 语义测试；但它同样用 `os.kill(pid, 0)`，Windows 下也不适合作为只读探测。
- 现有测试大量通过 `pid_exists=lambda ...` 注入行为；本 feature 可以通过 helper 单测 + 少量 integration tests 证明默认依赖替换，不需要改所有业务测试。

## 1. 决策与约束

### 需求摘要

本 feature 为 ccbd 控制面建立无副作用、跨平台的 pid 存活判定：Windows 不再使用 `os.kill(pid, 0)`，而是通过 WinAPI 句柄查询；POSIX 保持现有信号探测和 zombie 处理语义。ccbd keeper、ownership、health 等默认路径使用同一 helper，避免 Windows 把活着的 daemon/keeper/provider runtime 错判为 dead 或误投 Ctrl-C。

成功标准：

- Windows 分支不调用 `os.kill(pid, 0)`，不向目标进程/console group 发送信号或 Ctrl-C。
- alive / exited / invalid pid / access denied 的行为有稳定映射：invalid/dead=false，alive=true，access denied 在能证明 pid 存在时按 alive 处理，无法打开按 false 或 unknown→false fail-safe。
- `ccbd.system.process_exists()` 和 `cli.kill_runtime.processes.is_pid_alive()` 消费同一 liveness owner 或同一底层 helper，避免两个默认路径分叉。
- `OwnershipGuard`、`keeper_state_is_running()`、`HealthMonitor.runtime_health()` 的默认 pid 判定不再直接依赖 Windows signal probe。
- POSIX 现有行为不漂移，尤其 zombie 进程仍判 dead。

明确不做：

- 不实现 Job Object 进程树 evidence、tree kill、provider process recovery 或 pane/job 双信号融合。
- 不改变 `terminate_pid_tree()` / `kill_pid()` 的实际终止语义；这些仍可调用 taskkill / signal。
- 不引入 psutil 作为必需依赖；psutil 只能作为未来可选 backend，当前不需要。
- 不修改 ccbd control-plane transport、Rmux backend、accelerator guard、provider parser 或 packaging/docs。
- 不用命令行 `tasklist` 作为核心判断；本 feature 的核心 Windows 判定应可单测 monkeypatch WinAPI wrapper。

### 关键契约

1. **单一 liveness owner**

唯一落点固定为 `lib/process_liveness.py`：

```python
def process_exists(pid: int | None) -> bool: ...
```

`ccbd.system.process_exists()` 可成为薄 wrapper；`cli.kill_runtime.processes.is_pid_alive()` 也应复用该 helper，并保留 zombie dead 语义。实现阶段不得另起 `lib/system/process_liveness.py` 或把 Windows liveness owner 放进 ccbd/cli 私有模块，避免 guard 命令漏扫真实 owner。

2. **Windows WinAPI 语义**

候选内部接口：

```python
def _windows_process_exists(pid: int) -> bool:
    handle = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return _open_process_failure_means_alive_or_false(GetLastError())
    try:
        return WaitForSingleObject(handle, 0) == WAIT_TIMEOUT
    finally:
        CloseHandle(handle)
```

错误码映射固定如下：

| WinAPI 观察 | 返回 | 理由 |
|---|---|---|
| `OpenProcess` 成功 + `WaitForSingleObject(handle, 0) == WAIT_TIMEOUT` | true | 进程 handle 未 signaled，仍运行 |
| `OpenProcess` 成功 + `WAIT_OBJECT_0` | false | 进程已退出 |
| `OpenProcess` 成功 + `WAIT_FAILED` 或其他未知 wait result | false | fail-safe，避免阻止 stale takeover |
| `OpenProcess` 失败 + `GetLastError() == ERROR_ACCESS_DENIED` | true | OS 能定位该 pid 但当前用户无权打开；为避免误 takeover，按 alive |
| `OpenProcess` 失败 + `ERROR_INVALID_PARAMETER` | false | Windows 常见 invalid pid / exited pid |
| `OpenProcess` 失败 + `ERROR_NOT_FOUND` 或等价 not-found code | false | pid 不存在 |
| `OpenProcess` 失败 + 其他错误码 | false | unknown fail-safe；由 full-chain smoke 和日志/QA 复核 |

`GetLastError()` 必须在 `OpenProcess` 失败后立即读取并传入映射函数；不能在其他 ctypes 调用后再读。

约束：

- 不调用 `os.kill(pid, 0)`。
- 所有 handle 都必须 `CloseHandle`。
- `WAIT_TIMEOUT` 表示仍运行；`WAIT_OBJECT_0` 表示已退出；其他 wait error fail-safe false 并可在测试中覆盖。
- 上表每个分支必须有单测锁定；`ERROR_ACCESS_DENIED` 按 alive 是避免误杀/误 takeover 的保守选择。

3. **POSIX 语义**

- POSIX 分支继续使用 `os.kill(pid, 0)`，区分 `ProcessLookupError=false`、`PermissionError=true`、其他 `OSError=false`。
- zombie state 继续通过 `/proc/<pid>/stat` 判 `Z` 为 dead，保护现有 `test_cli_kill_runtime_zombies.py`。

4. **ccbd 默认依赖**

- `ccbd.system.process_exists`、`ProjectKeeper(process_exists_fn=process_exists)`、`KeeperStateStore` running 判断、`OwnershipGuard(pid_exists=process_exists)`、`HealthMonitor(pid_exists=process_exists)` 通过 import/default 参数自然消费新 helper。
- 注入式测试仍可传 `pid_exists=lambda...`；本 feature 不删除可注入 seam。

### Top 3 风险与缓解

1. **风险：修 ccbd.system 但漏掉共享 `is_pid_alive`，full-chain kill/keeper 仍走 Windows signal probe。**  
   缓解：单一 liveness owner；scope 内同步 `ccbd.system.process_exists` 和 `cli.kill_runtime.processes.is_pid_alive`。
2. **风险：Windows WinAPI 错误码映射不清，access denied / exited 被误判。**  
   缓解：封装 ctypes wrapper，可 monkeypatch `OpenProcess` / `WaitForSingleObject` / `GetLastError` / `CloseHandle`；每种 mapping 有单测。
3. **风险：POSIX zombie 或 PermissionError 行为漂移。**  
   缓解：保留/扩展现有 zombie tests，新增 POSIX PermissionError/ProcessLookupError regression。

### 非显然依赖与关键假设

- 依赖 Python 标准库 `ctypes` 可用；不新增第三方依赖。
- 假设 basic pid liveness 是 ccbd ownership/health 的输入之一，不替代 heartbeat/socket/job evidence。
- 假设 Windows full-chain smoke 会在后续验证真实 `ccb→ccbd→rmux` 行为，本 feature 的单元测试先锁住无副作用 liveness 语义。

## 2. 名词与编排

### 2.1 名词层

#### 现状

- `ccbd.system.process_exists(pid)` 是 ccbd 默认 pid 判定入口，但当前实现直接 `os.kill(pid, 0)`。
- `cli.kill_runtime.processes.is_pid_alive(pid)` 是 kill/keeper/daemon runtime 常用 helper，POSIX 上额外过滤 zombie。
- `OwnershipGuard`、`HealthMonitor` 和 keeper state 都已通过 `pid_exists` / `process_exists_fn` 注入，说明 seam 已存在，缺的是正确默认实现。

#### 变化

新增/收敛的契约：

```text
ProcessLivenessProbe
  input: pid: int | None
  output: bool
  invariant: read-only; no signal delivery; no process termination
  windows backend: OpenProcess + WaitForSingleObject + CloseHandle
  posix backend: os.kill(pid, 0) + PermissionError true + zombie dead
```

Interface 设计检查：

- Module：process liveness 是基础系统能力，固定放在 `lib/process_liveness.py`，让 `ccbd.system` 与 `cli.kill_runtime` 共用。
- Interface：只暴露 bool，不把 WinAPI handle、error code、process tree 泄漏给 caller。
- Seam：现有业务 seam 是 `pid_exists` 注入；本 feature 只替换默认 provider。
- Depth / locality：medium；核心逻辑小，但影响 keeper/ownership/health 的生命周期判定。
- Dependency strategy：local-substitutable；WinAPI wrapper 可 monkeypatch，不需要真实 Windows 进程才能覆盖大部分分支。

### 2.2 编排层

```mermaid
flowchart TD
  A[ccbd ownership/keeper/health asks pid alive] --> B[process liveness owner]
  B --> C{platform}
  C -- Windows --> D[OpenProcess pid]
  D --> E{handle?}
  E -- no --> F[map GetLastError]
  E -- yes --> G[WaitForSingleObject handle, 0]
  G --> H[CloseHandle]
  H --> I[alive bool]
  C -- POSIX --> J[os.kill pid, 0]
  J --> K[/proc zombie filter]
  K --> I
```

流程级约束：

- Windows 分支不得调用 `os.kill(pid, 0)`；测试要用 monkeypatch 断言。
- handle lifecycle 必须异常安全关闭。
- `process_exists(None|<=0)` 直接 false，不触发平台 API。
- access denied mapping 必须被测试锁定，不能用 bare except 全吞后默认 alive。
- keeper/ownership/health 的状态机不重写；只替换其默认 pid signal。

### 2.3 挂载点清单

- `lib/process_liveness.py`：单一 owner。
- `lib/ccbd/system.py`：`process_exists` wrapper 消费 helper。
- `lib/cli/kill_runtime/processes.py`：`is_pid_alive` 消费 helper，并保留 kill/tree 终止函数不变。
- `test/test_process_liveness.py`：Windows/POSIX helper 单测。
- `test/test_cli_kill_runtime_zombies.py`：POSIX zombie regression。
- `test/test_v2_ccbd_mount_ownership.py` / `test/test_cli_daemon_keeper_runtime.py` / `test/test_ccbd_service_graph.py`：默认依赖 integration smoke 或 focused tests。

### 2.4 推进策略

1. **liveness owner skeleton**：新增 `lib/process_liveness.py`，定义 `process_exists()`、platform dispatch、invalid pid fast false、ctypes wrapper seam。  
   退出信号：invalid pid fast false；`ccbd.system` / `kill_runtime` 可 import 该 owner；Windows/POSIX backend 细节仍由后续步骤完成。
2. **Windows backend**：实现 OpenProcess/WaitForSingleObject/CloseHandle 查询，不调用 `os.kill(pid, 0)`，并固定错误码映射表。  
   退出信号：monkeypatch `os.kill` 为 fail，Windows alive/exited/access denied/invalid/not-found/unknown/wait-failed 分支测试通过；CloseHandle 调用被断言。
3. **POSIX regression**：迁移或复用 zombie state 逻辑，保持现有 zombie dead 和 PermissionError alive。  
   退出信号：`test_cli_kill_runtime_zombies.py` 与新增 POSIX liveness tests 通过。
4. **ccbd default wiring**：`ccbd.system.process_exists` 和 ccbd keeper/ownership/health 默认依赖消费新 helper。  
   退出信号：focused integration tests 证明默认 `OwnershipGuard` / keeper state / health monitor 使用新 helper，可注入 seam 保持。
5. **shared kill_runtime wiring and blast-radius regression**：`cli.kill_runtime.processes.is_pid_alive` 复用 helper；`kill_pid` / `terminate_pid_tree` 终止语义不改；传递消费者做显式回归/审查。  
   退出信号：kill_runtime tests 通过；`runtime_accelerator/ownership`、daemon runtime processes、mobile host、provider helper cleanup、ccbd stop-flow pid cleanup 等消费者有 rg 清单和风险分层测试/审查证据。
6. **scope guard and full-chain handoff**：禁止扩入 job object、transport、Rmux、provider parser；记录 full-chain smoke 仍需真机验证。  
   退出信号：diff scope 清楚，roadmap item 20 可由 design-review 追踪到实现验收。

### 2.5 结构健康度与微重构

##### 评估

- 文件级：`ccbd/system.py` 是杂项系统 helper；继续把 Windows ctypes 细节塞进去会扩大职责。
- 文件级：`cli/kill_runtime/processes.py` 同时包含 kill 和 liveness；直接加 Windows OpenProcess 会让 kill/runtime 文件更混杂。
- 目录级：当前没有 `system/` 包；新增一个窄 `process_liveness.py` 顶层模块或小包可以让 ccbd 与 cli 共用，且不影响业务层。

##### 结论：新增窄 liveness owner，不重构 kill/runtime

实现时只抽出 pid alive 判定；`kill_pid`、`terminate_pid_tree`、job-object evidence、daemon lifecycle 状态机不搬迁。若未来需要更完整 Windows process authority，应由 job-object / process identity feature 另行设计。

## 3. 验收契约

### 3.1 关键场景清单

| ID | 输入 / 触发 | 期望可观察结果 | 证据类型 |
|---|---|---|---|
| AC-001 | `process_exists(None)`、`process_exists(0)`、负 pid | 返回 false，不调用平台 API | unit |
| AC-002 | Windows alive pid，OpenProcess 成功且 WaitForSingleObject 返回 WAIT_TIMEOUT | 返回 true，CloseHandle 被调用，不调用 `os.kill` | unit |
| AC-003 | Windows exited pid，WaitForSingleObject 返回 WAIT_OBJECT_0 | 返回 false，CloseHandle 被调用 | unit |
| AC-004 | Windows OpenProcess access denied / invalid / not-found / unknown / wait-failed | 按错误码表返回：access denied=true，其余 open unknown/invalid/not-found=false，wait failed=false；每类有单测 | unit |
| AC-005 | POSIX ProcessLookupError / PermissionError / generic OSError | false / true / false | unit |
| AC-006 | POSIX zombie state `Z` | 返回 false | unit/regression |
| AC-007 | `ccbd.system.process_exists` 默认入口 | 消费单一 helper，不直接 `os.kill(pid, 0)` on Windows | unit/guard |
| AC-008 | `OwnershipGuard` 默认 pid_exists | Windows liveness false 会形成 stale/takeover，true 会参与 healthy/degraded 判定；可注入 seam 不变 | integration |
| AC-009 | `keeper_state_is_running` 默认 process_exists_fn | Windows liveness false 时 keeper not running，true 时继续检查 project/cmdline | unit |
| AC-010 | `HealthMonitor.runtime_health` provider pid | Windows liveness false 标记 runtime orphaned，true 不误降级 | integration |
| AC-011 | `cli.kill_runtime.processes.is_pid_alive` | 复用 helper且保留 zombie regression；terminate tree 等待逻辑不漂移 | regression |
| AC-012 | 共享 helper 传递消费者 | `runtime_accelerator/ownership`、daemon runtime processes、mobile host、provider helper cleanup、ccbd stop-flow pid cleanup 等消费者已回归或逐项审查无需行为变更 | regression/review |
| AC-013 | scope guard | 不修改 job-object evidence、ccbd transport、Rmux backend、accelerator、provider parser | guard/review |

### 3.2 明确不做的反向核对项

- 不应在 Windows liveness path 中调用 `os.kill(pid, 0)`。
- 不应把 pid alive 当成 daemon ownership proof；lease/heartbeat/socket 仍参与判定。
- 不应改 tree kill/taskkill/terminate semantics。
- 不应新增 psutil 必需依赖。
- 不应实现 Job Object 进程树 evidence 或 provider recovery。

### 3.3 Acceptance Coverage Matrix

| Scenario | Covered By Step | Evidence Type | Command / Action | Core? |
|---|---|---|---|---|
| AC-001 invalid pid | S1 | unit | `test_process_liveness.py` | yes |
| AC-002 Windows alive no-signal | S2 | unit | WinAPI wrapper monkeypatch + os.kill fail guard | yes |
| AC-003 Windows exited | S2 | unit | WaitForSingleObject WAIT_OBJECT_0 | yes |
| AC-004 Windows open failure mapping | S2 | unit | GetLastError mapping tests | yes |
| AC-005 POSIX errors | S3 | unit | POSIX branch tests | yes |
| AC-006 POSIX zombie | S3 | regression | `test_cli_kill_runtime_zombies.py` | yes |
| AC-007 ccbd.system default | S4 | unit/guard | import/default test + rg guard | yes |
| AC-008 OwnershipGuard | S4 | integration | mount ownership focused tests | yes |
| AC-009 keeper state | S4 | unit | keeper state/default process_exists test | yes |
| AC-010 HealthMonitor | S4 | integration | health monitor orphan test | yes |
| AC-011 kill_runtime sharing | S5 | regression | kill_runtime process tests | yes |
| AC-012 transitive consumers | S5 | regression/review | rg consumer review + focused tests | yes |
| AC-013 scope guard | S6 | guard | `git diff --name-only` / review | yes |

### 3.4 DoD Contract

| ID | 要求 | 证据 | 阻塞级别 |
|---|---|---|---|
| DOD-DESIGN-001 | design/checklist/review 完整，且对齐 roadmap item `ccbd-windows-process-liveness` | design review | blocking |
| DOD-IMPL-001 | 单一 process liveness owner，ccbd.system 与 kill_runtime 复用 | unit/diff review | blocking |
| DOD-IMPL-002 | Windows liveness 用 OpenProcess/WaitForSingleObject/CloseHandle，不调用 os.kill(pid,0) | unit/guard | blocking |
| DOD-IMPL-003 | POSIX ProcessLookup/Permission/OSError/zombie 行为不漂移 | unit/regression | blocking |
| DOD-IMPL-004 | OwnershipGuard / keeper / HealthMonitor 默认路径消费新 helper，可注入 seam 保持 | integration | blocking |
| DOD-IMPL-005 | terminate_pid_tree/kill_pid 终止语义不改，共享 `is_pid_alive` 的传递消费者已回归或逐项审查 | regression/review | blocking |
| DOD-IMPL-006 | 不新增 psutil 必需依赖，不扩入 job-object/transport/Rmux/provider parser | guard | blocking |
| DOD-REVIEW-001 | code review passed 且无 unresolved blocking | review report | blocking |
| DOD-QA-001 | QA 覆盖 Windows no-signal mock、POSIX regression、ccbd lifecycle integration | QA report | blocking |
| DOD-ACCEPT-001 | acceptance 回写 roadmap item，并明确 full-chain smoke 仍需真机验证 | acceptance report | blocking |

Validation Commands:

| ID | 命令 | 目的 | 核心性 | 失败处理 |
|---|---|---|---|---|
| CMD-001 | `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml" --yaml-only` | checklist YAML 合法性 | core | fix-or-block |
| CMD-002 | `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` | roadmap items 回写合法性 | core | fix-or-block |
| CMD-003 | `python -m pytest -q test/test_process_liveness.py test/test_cli_kill_runtime_zombies.py` | process liveness owner Windows/POSIX/zombie 单测，含固定 WinAPI 错误码表 | core | fix-or-block |
| CMD-004 | `python -m pytest -q test/test_v2_ccbd_mount_ownership.py test/test_cli_daemon_keeper_runtime.py test/test_ccbd_service_graph.py` | ccbd ownership/keeper/health 默认路径 regression | core | fix-or-block |
| CMD-005 | `python -m pytest -q test/test_v2_kill_service.py test/test_cli_kill_runtime_zombies.py test/test_runtime_accelerator_ownership.py test/test_mobile_host_service.py` | kill_runtime sharing 与传递消费者 regression | core | fix-or-block |
| CMD-006 | `rg -n "from cli\\.kill_runtime\\.processes import is_pid_alive|is_pid_alive\\(" lib test` | 共享 helper 传递消费者清单；实现/QA 逐项标注 covered-by-test 或 unaffected | core | inspect-output |
| CMD-007 | `rg -n "os\\.kill\\(pid, 0\\)|os\\.kill\\([^,]+, 0\\)" lib/ccbd lib/cli/kill_runtime lib/process_liveness.py test/test_process_liveness.py` | Windows liveness signal-probe guard；POSIX-only helper/test 例外需 review | core | inspect-output |
| CMD-008 | `git diff --name-only -- lib/ccbd lib/cli/kill_runtime lib/process_liveness.py test` | scope guard | core | inspect-output |

Required Artifacts：design、checklist、design-review、process liveness helper、ccbd.system wrapper diff、kill_runtime is_pid_alive diff、WinAPI wrapper tests、WinAPI error-code mapping tests、POSIX/zombie regression output、ownership/keeper/health integration output、transitive consumer review、scope guard diff、acceptance report、items.yaml 回写。

### 3.5 自我批判结论

- 可证伪性：Windows path 用 os.kill fail guard、WinAPI wrapper return values、CloseHandle 计数验证。
- 步骤原子性：helper、Windows backend、POSIX regression、ccbd wiring、kill_runtime sharing、scope guard 分离。
- 最弱依赖：access denied mapping 容易含糊，已要求测试锁定 chosen mapping。
- 证据完整性：既覆盖 helper 单测，也覆盖 OwnershipGuard/keeper/HealthMonitor 默认消费路径。
- 交付物可核验性：acceptance 可从 helper、wrapper、tests、rg guard、diff scope 反查。
- 清洁度规则：不新增临时 TODO/FIXME、调试输出、注释掉代码、死 import；不新增 psutil dependency；Windows liveness 不使用 `os.kill(pid, 0)`。

## 4. 与项目级架构文档的关系

- 本 feature 实现 roadmap item 20，是 native Windows full-chain smoke 的独立 blocker。
- 本 feature 与 `windows-job-object-runtime-evidence` 区分：前者是 basic pid liveness，后者是 job tree evidence 和 recovery authority。
- 本 feature 不替代 ccbd transport seam、Rmux backend lifecycle、accelerator guard 或最终 true-host full-chain smoke。
