---
doc_type: feature-design
feature: 2026-07-21-windows-runtime-import-lock-compat
requirement:
execution_lane: standard
status: approved
summary: 让 storage/heartbeat/terminal 运行时模块在原生 Windows 可 import 并提供跨平台文件锁与原子写，对齐既有 ProviderLock 范式，Unix 语义零漂移
tags: [windows, compat, file-lock, atomic-write, storage, import-safety]
---

# windows-runtime-import-lock-compat feature design

## 0. 术语约定

| 术语 | 定义 | 防冲突结论 |
|---|---|---|
| import-safe | 模块在缺 `fcntl`/`pty`/`termios` 的平台（Windows）上 `import` 不抛错。 | 只保证可 import；Unix-only 运行时逻辑仍可按平台分支或延迟 import。 |
| advisory lock | `fcntl.flock`：协作进程都主动加锁才互斥。 | 现状 Unix 语义；Windows 侧需提供等价"同 app 内跨进程互斥"。 |
| mandatory byte-range lock | `msvcrt.locking`：OS 强制锁定文件字节区间。 | Windows 用它模拟互斥，语义差异在本 design 显式约束。 |
| durable atomic write | 写 tmp→fsync 文件→`os.replace`→**fsync 目录**，crash 后要么旧要么新且 rename 已落盘。 | Unix 全链路成立；Windows 无目录 fsync，rename 可见性原子但 crash 持久性弱化。 |

代码事实（当前提交基线）：
- `lib/storage/locks.py::file_lock()`：`fcntl.flock(LOCK_EX)` 阻塞咨询锁；`ModuleNotFoundError`→**无锁 yield**（Windows 现状即此路径 = 临界区无保护）。
- `lib/maintenance_heartbeat/lock.py::MaintenanceHeartbeatLock`：`fcntl.flock(LOCK_EX|LOCK_NB)` 非阻塞；`BlockingIOError`→`MaintenanceHeartbeatLockBusy`。**锁文件即状态文件**（`_write_state` 对同句柄 `seek(0)+truncate(0)+write(json)+fsync`）。
- `lib/storage/atomic.py::atomic_write_text()`：全程 `dir_fd` + 目录 fsync；无 `os.O_DIRECTORY`（Windows）时 `_open_directory` 抛 `NotImplementedError`，Windows 完全不可用。
- `lib/mobile_gateway/terminal.py`：顶层 `import fcntl/pty/termios`，Windows import 即失败（CMD-005 collection blocker）。`pty` 无任何使用（死 import）；`fcntl`/`termios` 仅 `_resize()`（Unix ioctl）用。
- **既有范式**：`lib/provider_core/runtime_lock.py::ProviderLock` 已实现跨平台字节锁（Windows `msvcrt.locking(LK_NBLCK,1)` + 占位字节、Unix `fcntl.flock`、阻塞 `acquire(timeout)` + 非阻塞 `try_acquire`）；`lib/provider_core/platform_info.py::is_windows()` 是平台判定规范单一来源。

## 1. 决策与约束

### 需求摘要

让四个运行时模块在原生 Windows（1）可 `import`，（2）提供与 Unix **可观察等价**的文件锁与原子写，且 **Unix 行为零漂移**。这是 `ccbd-control-plane-transport-seam` 拆出的 CMD-005 fcntl collection blocker 的根因修复（种子见 `pending-split/windows-runtime-import-lock-compat/`）。

**动机不止 import**：`file_lock` 有 15 文件、约 50 处 `with file_lock(): <read-modify-write>` 调用，**全部依赖阻塞语义 + 跨进程互斥**；Windows 现状走无锁降级 = 并发 CLI/dispatcher 进程对同一状态文件的**静默数据竞争**。本 feature 同时消除该正确性隐患。

成功标准（均可 grep / 测试核对）：
- **import 安全（真实交付物只 2 个模块）**：`mobile_gateway.terminal` 与 `maintenance_heartbeat.lock` 有**顶层 `import fcntl`**，Windows import 真失败——本 feature 让其可 import。`storage.locks`（fcntl 惰性 import，`locks.py:13`）与 `storage.atomic`（无 fcntl import）**基线即可 import**，import guard 对它们只是回归守卫、真实交付物是功能（AC-002/AC-006）。CMD-005 collection 根因**特指 `terminal.py`**。
- `file_lock` 在 Windows 提供**阻塞式**跨进程互斥（第二 acquirer 等到释放才取得锁），锁定**固定 byte-0 区间**（先 `seek(0)`，不随文件大小漂移）；Unix 分支逐字不变。
- `MaintenanceHeartbeatLock` 在 Windows 保持**非阻塞**"已持有→`MaintenanceHeartbeatLockBusy`"，且**不把非锁竞争的 OSError 误判为 busy**。
- `atomic_write_text/json` 在 Windows 可用、rename 可见性原子；Unix 全 durability 链路不变。

### 明确不做

- 不改对外契约：`file_lock`、`MaintenanceHeartbeatLock`、`MaintenanceHeartbeatLockBusy`、`atomic_write_*` 的签名/返回/异常类型不变。
- 不改 Unix 平台锁与 durability 分支（与基线逐字等价）。
- 不实现 Windows 目录 fsync 真 durability（Windows 无稳定 API），只界定并记录弱化边界。
- **不把 `file_lock`/`MaintenanceHeartbeatLock` 合并进 `ProviderLock`**（见 D-REUSE）：二者内容/回收语义不同，收敛属独立 refactor。
- 不触碰 ccbd transport / RPC / 其它 roadmap item。

### 复杂度档位

- 行为兼容 = L3（Unix 零漂移，Windows 可观察等价）。
- 安全 / 数据语义 = high（锁互斥与原子写 crash 一致性是数据完整性边界）。
- 并发 = 显式（阻塞 vs 非阻塞、异常映射、占位字节是核心，需并发占用测试锁定）。

### 关键决策（含待 owner 拍板的选项）

1. **D-PLATFORM 平台判定**：统一用 `provider_core.platform_info.is_windows()`，不新增局部 `_is_windows()`（对齐规范单一来源）。
2. **D-REUSE 复用 vs 独立**：已有 `ProviderLock` 解决同类问题。
   - 选项 A（推荐，本 feature 采用）：**各模块保留独立锁封装但对齐 `ProviderLock` 的 msvcrt 手法**（占位字节、`LK_NBLCK`、errno 映射），不耦合其 PID-stale 回收。理由：`file_lock` 不需要 PID 回收语义变化；`MaintenanceHeartbeatLock` 的锁文件同时承载 JSON 状态，`ProviderLock` 会写自己的 PID 内容，冲突。
   - 选项 B：把三处收敛到一个共享底层字节锁 primitive（含 `ProviderLock`）。范围更大、触及 provider_core，属独立 `cs-refactor`。
   - **决策**：A。B 作为"超出范围的观察"提示后续 refactor。
3. **D-BLOCK `file_lock` 阻塞语义**：50 处调用依赖"等到取锁"。Windows `msvcrt.locking(LK_LOCK)` 阻塞 ~10s 后抛 `OSError`，**不等价**。
   - 决策：Windows 分支用 `LK_NBLCK` + 有界退避**重试直到取得锁**，模拟无限阻塞（对齐 `ProviderLock.acquire`）；仅在遇非竞争 `OSError` 时上抛。
4. **D-SENTINEL 占位字节**：`msvcrt.locking` 需区间存在字节，空文件先写 1 字节。
   - `MaintenanceHeartbeatLock`：加锁后 `_write_state` `truncate(0)` 覆盖，占位被清除 → 安全。
   - `file_lock`：Explore 反向核验**无任何消费方读取锁文件内容**（调用点均对*其它*文件做 RMW，锁文件为纯 sentinel）→ 占位 `\0` 无害。**已核验，非假设**。
5. **D-EXC heartbeat 异常映射收窄**：patch 把 `except BlockingIOError` 放宽为 `(BlockingIOError, OSError)` 会吞掉权限/磁盘错误。
   - 决策（**作用域收窄优先，errno 白名单为辅**）：主保险是把 try/except **紧包 `msvcrt.locking` 单一调用点**——`open`/`write`/占位写入的 OSError 天然落在 except 之外，只有加锁本身的失败进入 busy 判定分支。二次判别再用 `errno`：Windows `msvcrt.locking(LK_NBLCK)` 竞争实测常抛 `EDEADLOCK`(36)，故白名单取 `{EACCES, EDEADLOCK, EDEADLK}` 并在 impl 以实测校准；命中→`MaintenanceHeartbeatLockBusy`，其它 `OSError` 上抛。Unix 分支仅捕 `BlockingIOError`（不变）。
6. **D-DURABLE Windows 原子写**：Windows 回退无目录 fsync。`os.replace` 仍原子替换（half-write 不可见）；接受"crash 后目录项可能未落盘"的弱化，文件内容仍 `fsync`。**注意此弱化触及崩溃恢复 journal 完整性**：事务链路（frontdesk handoff 的 `recover_frontdesk_direct_handoffs` 崩溃回读、task_set closure settlement、import transaction、workspace binding、json_store）在 Windows crash 后可能因目录项未落盘而漏读已提交记录 → 效果丢失，属正确性相邻后果。降级为"进程存活期原子、非 crash-durable"，在 §4 与 `atomic.py` 注释显式记录，且 **acceptance 时须确认 owner 已按 goal-protocol §3.1 在 approval-report 落盘接受该目标平台弱化**（不仅留待未来 ADR）。
7. **D-DIRSYNC `ensure_durable_directory` 也需平台门控**：`atomic_write_text` 无条件先调 `ensure_durable_directory`（`atomic.py:84`），后者创建缺失目录时走 `_fsync_directory→_open_directory`（`atomic.py:70→24→17`），Windows 抛 `NotImplementedError`。且 `ensure_durable_directory` 被 `frontdesk_direct_handoff.py:52,97` 等**直接调用**（不经 atomic_write_text）。决策：把 `_supports_directory_fsync()` 门控下沉到 `_fsync_directory`（Windows 早返回 no-op），使 `ensure_durable_directory` 在 Windows 创建缺失嵌套目录不抛错；列入挂载点与 AC/DOD。

### Top 3 风险与缓解

1. **锁语义不等价→互斥失效或误判 busy**（最危险）。缓解：D-BLOCK 重试 + D-EXC 收窄；同进程双句柄 + 子进程并发占用测试锁定"第二 acquirer 阻塞 / busy"。
2. **改动破坏现有 atomic crash-safety 测试簇**。`test/test_storage_atomic.py` 中依赖 dir-fsync 的**一簇**测试（顺序 `test_atomic_write_text_orders_file_and_directory_sync`、嵌套 `test_nested_parent_entries_are_synced`、`test_ensure_durable_directory_*`、`test_directory_fsync_failure_*`、inode `test_parent_replacement_is_detected`、`test_directory_close_failure_*` 等约 6-8 个）在 Windows 回退下无 `dir-fsync` fd 会红。缓解：给该整簇加 Unix-only skip 守卫（Windows skip 而非 fail），Windows 顺序断言迁至新测试文件断言 `['write','flush','file-fsync','replace']`。
3. **Unix 行为回归**。缓解：所有改动走 `is_windows()` 分支，Unix 分支与基线逐字等价；跑现有 storage/heartbeat 全测试 + diff 复核。

### 非显然依赖与关键假设

- 本机（Windows）可验 Windows 分支 + import 安全；Unix 分支由现有测试在 Unix 覆盖，本机以 diff 等价佐证（关键假设：不改 Unix 分支即不漂移）。
- 依赖 `provider_core.platform_info`（已存在）与 `runtime_observability` metrics（Windows 回退保留记账）。
- D-EXC 以作用域收窄为主保险；errno 白名单 `{EACCES, EDEADLOCK, EDEADLK}` 为辅，impl 阶段以实测校准（Windows `msvcrt.locking(LK_NBLCK)` 竞争常抛 `EDEADLOCK`(36)）。

### 必跑验证命令（基线预检先跑，红灯分清既有/本次）

- `python -m pytest -q test/test_storage_atomic.py`（15 用例，含顺序断言 —— 预期需平台条件化）
- `python -m pytest -q test/test_maintenance_heartbeat.py`（busy 语义）
- 新增 `test/test_windows_runtime_import_lock_compat.py`：import guard + 并发锁 + Windows atomic
- `python -m compileall lib/storage lib/maintenance_heartbeat lib/mobile_gateway`
- 根因：`python -m pytest -q test/test_v2_start_service.py test/test_v2_phase2_entrypoint.py -k "ccbd or socket or endpoint or ping"` collection 不再因 fcntl 失败

### 清洁度规则

禁新增调试输出、临时 TODO/FIXME、注释掉代码、死 import（含清理 `terminal.py` 死 `pty` import）；平台分支不留 Windows-TODO 占位。

## 2. 名词与编排

### 2.1 名词层

#### 现状
四模块硬绑 Unix 原语（§0），Windows import/运行失败；`ProviderLock` 已有跨平台范式但未被这三处复用。

#### 变化
每模块内新增**平台分支私有 helper**，对外名词零变化，平台判定统一用 `platform_info.is_windows()`：
- `storage/locks.py`：`_lock_handle(handle) -> bool` / `_unlock_handle(handle)`；Windows msvcrt 阻塞重试（D-BLOCK），Unix `fcntl.flock(LOCK_EX)`，无 fcntl 非 Windows → `False`（无锁降级，保持现状）。
- `maintenance_heartbeat/lock.py`：`_lock_handle` / `_unlock_handle`；Windows msvcrt 非阻塞 + 竞争 errno→busy（D-EXC），Unix `fcntl` 非阻塞。
- `storage/atomic.py`：`_supports_directory_fsync()` + `_fsync_directory` 加 Windows 早返回门控（D-DIRSYNC，使 `ensure_durable_directory` 创建缺失目录不抛错）+ `_atomic_write_text_by_path(...)`（Windows 回退，无目录 fsync，保留 metrics）。
- `mobile_gateway/terminal.py`：删死 `pty` import，`fcntl`/`termios` 延迟到 `_resize`。

对外契约签名/异常类型全部不变。

### 2.2 编排层

线性流程，无需图：
- `file_lock`：`open('a+')` → `_lock_handle`（True→try/finally 内 `_unlock_handle`；False→直接 yield）。Windows `_lock_handle`：空文件先写 1 占位字节，**`seek(0)` 到固定 byte-0**，再 `LK_NBLCK`+退避重试锁定 `[0,1)` 直到取锁或非竞争 error 上抛（**必须锁固定 byte-0，不可用 append 位置，否则区间随文件大小漂移致互斥失效**）。
- `MaintenanceHeartbeatLock.__enter__`：`open('a+')` → `_lock_handle`（try/except **紧包 msvcrt.locking 单点**，竞争 errno→`Busy`，非竞争 OSError 上抛）→ `_write_state(held=True)`；`__exit__`：`_write_state(held=False)` → `_unlock_handle` → 关句柄。
- `atomic_write_text`：`ensure_durable_directory`（其 `_fsync_directory` 在 Windows 经 D-DIRSYNC 门控为 no-op，创建缺失目录不抛错）→ `not _supports_directory_fsync()` 时走 `_atomic_write_text_by_path` 并 return；否则现有 dir_fd 路径。

流程级约束：错误语义 Unix 逐字保持、Windows 竞争→busy 其它上抛；锁的"第二 acquirer"行为是核心验收点；atomic Windows 回退保留 startup metrics。

### 2.3 挂载点清单

- `lib/storage/locks.py`：`_lock_handle`/`_unlock_handle`。
- `lib/maintenance_heartbeat/lock.py`：`_lock_handle`/`_unlock_handle`。
- `lib/storage/atomic.py`：`_supports_directory_fsync` + `_fsync_directory` Windows 门控（D-DIRSYNC）+ `_atomic_write_text_by_path` 回退分支。
- `lib/mobile_gateway/terminal.py`：import 位置调整 + `_resize` 延迟 import。

（删这四处，Windows 兼容能力消失、Unix 回到现状。4 条，符合区间。）

### 2.4 推进策略

1. **import 安全**（terminal.py 删死 import；重点是 terminal.py + heartbeat.lock 两个顶层 fcntl 模块）→ 无 fcntl 可 import 四模块，import guard 通过。
2. **storage/atomic Windows 回退**（`_fsync_directory` D-DIRSYNC 门控 + `_atomic_write_text_by_path` + 依赖 dir-fsync 的一簇 `test_storage_atomic` 测试加 Unix-only skip 守卫）→ Windows 写读回一致（含**父目录不存在**时可创建）、rename 原子；Unix dir_fd 路径与全部顺序断言不变。
3. **storage/locks 跨平台锁**（D-PLATFORM/D-BLOCK/D-SENTINEL，锁固定 byte-0）→ Windows 第二 acquirer 阻塞至取锁；Unix flock 分支不变。
4. **heartbeat 跨平台锁 + 异常收窄**（D-EXC，errno 集合实测校准）→ Windows 已持有→busy、非竞争 OSError 不吞；Unix 不变。
5. **回归 + 根因验证** → 现有 storage/heartbeat 测试 + 新测试全绿；CMD-005 Windows collection 不再因 fcntl 失败。

### 2.5 结构健康度与微重构

- 文件级：四文件均小、职责单一，平台 helper 内联即可，不拆文件。
- 目录级：三目录均合理。
- 结论：**不做微重构**；仅顺带删 `terminal.py` 死 `pty` import（清洁度，不改行为）。
- **超出范围的观察（提示后续 `cs-refactor`）**：
  - `ProviderLock` / `file_lock` / `MaintenanceHeartbeatLock` 三处 msvcrt+fcntl 字节锁逻辑重复，可收敛到共享底层 primitive（D-REUSE 选项 B）；涉及 provider_core 耦合与语义合并，属独立重构。
  - `mobile_gateway/terminal.py::TmuxTerminalSession._resize` 无调用者、`_master_fd` 从不赋值（`write` 的 `os.write(self._master_fd)` 分支不可达），`_resize` 及该分支疑为死代码。本 feature 采**保守惰性 import**（行为等价、scope 克制）而非删除死代码；死代码清理留给 `cs-refactor`。权衡：惰性 import 后 fcntl/termios 实际永不执行，但保留了"死代码里的 import"。

## 3. 验收契约

### 3.1 关键场景清单

| ID | 输入 / 触发 | 期望可观察结果 | 证据类型 |
|---|---|---|---|
| AC-001 | 无 `fcntl` 解释器 import `terminal` / `heartbeat.lock`（顶层 fcntl 的两个真失败模块）；`locks`/`atomic` 作回归守卫 | 两模块 import 成功无 ModuleNotFoundError；locks/atomic 保持可 import | import guard 单测 |
| AC-002 | Windows `file_lock` 已被持有，第二 acquirer 进入（锁文件含占位字节、两 acquirer 文件大小不同） | 第二 acquirer 阻塞直到释放后取得锁，不 ~10s 抛错；锁固定 byte-0 不随大小漂移 | 并发单测（Windows） |
| AC-003 | Unix `file_lock` | `fcntl.flock(LOCK_EX)` 逐字不变 | diff 复核 + 现有测试（Unix） |
| AC-004 | Windows `MaintenanceHeartbeatLock` 已持有时再进入 | 抛 `MaintenanceHeartbeatLockBusy` | 并发单测（Windows） |
| AC-005 | Windows heartbeat 加锁遇非竞争 OSError（如权限，mock 注入到非加锁调用） | 原样上抛，不被误判 busy（作用域收窄验证） | 单测（mock 注入） |
| AC-006 | Windows `atomic_write_text/json`，含**目标父目录不存在**需创建 | 写入成功、读回一致、完整替换无半写；`ensure_durable_directory` 创建缺失目录不抛错 | 单测（Windows） |
| AC-007 | Unix `atomic_write_text` | dir_fd + 目录 fsync 全链路及**整簇顺序/嵌套/inode 断言**不变 | diff + 现有 `test_storage_atomic.py` |
| AC-008 | Windows atomic 回退 fsync 顺序；依赖 dir-fsync 的 Unix-only 测试簇 | Windows 观察 `['write','flush','file-fsync','replace']`（无 dir-fsync）；Unix-only 测试簇在 Windows skip 而非 fail | 单测（Windows 顺序断言 + skip 守卫） |
| AC-009 | `file_lock` 空文件 Windows 加锁 | 占位字节不破坏锁文件语义（无消费方读内容） | 单测 + 调用面反向核对 |
| AC-010 | 根因：Windows CMD-005 collection | 不再因 `mobile_gateway.terminal -> import fcntl` 失败 | pytest collection 输出 |

### 3.2 明确不做的反向核对项

- 对外签名/返回/异常类型未变（grep）。
- Unix 锁与 durability 分支未改（diff 逐字等价，含 `test_storage_atomic` Unix 顺序断言仍绿）。
- 未把 file_lock/heartbeat 并入 ProviderLock。
- 未实现 Windows 目录 fsync 真 durability。
- 未触碰 ccbd transport / RPC / 其它 roadmap item。

### 3.3 Acceptance Coverage Matrix

| Scenario | Covered By Step | Evidence Type | Command / Action | Core? |
|---|---|---|---|---|
| AC-001 import 安全 | S1 | unit | import guard | yes |
| AC-002 Windows file_lock 阻塞互斥 | S3 | unit | 并发锁测试 | yes |
| AC-003 Unix file_lock 不漂移 | S3 | diff+regression | 现有 storage 测试 | yes |
| AC-004 heartbeat busy | S4 | unit | 并发锁测试 | yes |
| AC-005 heartbeat 异常收窄 | S4 | unit | mock OSError | yes |
| AC-006 Windows atomic 写读回 | S2 | unit | atomic 测试 | yes |
| AC-007 Unix atomic 顺序不漂移 | S2 | regression | test_storage_atomic.py | yes |
| AC-008 Windows atomic 顺序 | S2 | unit | 平台顺序断言 | yes |
| AC-009 sentinel 占位无害 | S3 | unit+grep | 调用面反向核对 | yes |
| AC-010 根因 collection | S5 | regression | CMD-005 collection | yes |

### 3.4 DoD Contract

| ID | 要求 | 证据 | 阻塞级别 |
|---|---|---|---|
| DOD-IMPL-001 | 四模块无 fcntl 可 import，死 pty import 已删 | import guard + grep | blocking |
| DOD-IMPL-002 | Windows file_lock 阻塞跨进程互斥，Unix 分支不变 | 并发测试 + diff | blocking |
| DOD-IMPL-003 | Windows heartbeat busy 语义正确、异常映射收窄，Unix 不变 | 单测 + diff | blocking |
| DOD-IMPL-004 | Windows atomic 可用、rename 原子、metrics 记账、顺序断言平台条件化 | 单测 | blocking |
| DOD-IMPL-005 | Unix 锁/durability 分支零漂移（含 test_storage_atomic 全绿） | diff + 现有测试 | blocking |
| DOD-IMPL-006 | 对外签名/异常类型不变，平台判定用 platform_info.is_windows() | grep | blocking |
| DOD-REVIEW-001 | code review passed 无 unresolved blocking | review | blocking |
| DOD-QA-001 | 验收覆盖 import/lock/atomic/根因 collection | accept-inline | blocking |
| DOD-ACCEPT-001 | acceptance 确认 owner 已按 goal-protocol §3.1 在 approval-report.md 落盘接受 Windows durability 弱化（崩溃恢复 journal） | approval-report 引用 | blocking |

Validation Commands：

| ID | 命令 | 目的 | 核心性 | 失败处理 |
|---|---|---|---|---|
| CMD-001 | `python -m compileall lib/storage lib/maintenance_heartbeat lib/mobile_gateway` | 编译 | core | fix-or-block |
| CMD-002 | `python -m pytest -q test/test_storage_atomic.py test/test_maintenance_heartbeat.py test/test_windows_runtime_import_lock_compat.py` | 锁/原子写/import/顺序语义 | core | fix-or-block |
| CMD-003 | `python -m pytest -q test/test_v2_start_service.py test/test_v2_phase2_entrypoint.py -k "ccbd or socket or endpoint or ping"` | 根因 collection | core | document-collection-only（用例 AF_UNIX skip/fail 属他 feature） |

### 3.5 自我批判结论

- 可证伪性：每条 AC 有 yes/no 观察点。
- 步骤原子性：import / atomic / locks / heartbeat / 回归五步各自独立可验。
- 最弱依赖：D-EXC 的 errno 集合（impl 实测校准，作用域收窄为主保险）与 test_storage_atomic dir-fsync 测试簇（S2 加 Unix-only skip 守卫）最易翻车，已前置为独立退出信号。
- 证据完整性：Windows 分支本机可验；Unix 分支靠 diff 等价 + 现有测试。
- 清洁度：明确删死 import、禁 TODO/调试输出。

## 4. 与项目级架构文档的关系

- 本 feature 是 `windows-rmux-native-backend` goal 执行中拆出的横切基础设施修复，**非 roadmap items.yaml 条目**；解 `ccbd-control-plane-transport-seam` 的 CMD-005 `document-baseline`（fcntl collection）根因，修复后该 CMD 可在 Windows 真正 collection。
- **无领域模型层现状**：`.codestable/requirements/` 仅 `.gitkeep`，无 `CONTEXT.md`、无 `adrs/`。以下两条结构性约束建议后续走 `cs-domain` 引导建首个 ADR（本 feature 不代写、不 bootstrap ADR 目录）：
  - **durability 契约差异**：`atomic_write_*` 在 Windows 提供 rename 可见性原子，但不提供 Unix 级目录 fsync crash 持久性；事务/交接/闭包链路（frontdesk_direct_handoff、planner_task_set_import_transaction、task_set_closure、workspace/binding、json_store）在 Windows 的强 durability 依赖降级为"进程存活期原子、非 crash-durable"。**此弱化触及崩溃恢复 journal 完整性**（如 `recover_frontdesk_direct_handoffs` 崩溃后回读已提交 handoff），属正确性相邻后果。**acceptance 阶段须确认 owner 已按 goal-protocol §3.1 在 `approval-report.md` 落盘接受该目标平台弱化**，不仅留待未来 ADR。
  - **跨平台锁语义**：`msvcrt.locking`（强制字节区间）与 `fcntl.flock`（咨询）在与非协作进程交互时行为不同；本 feature 以"同 app 内跨进程互斥"为等价目标。
- **收敛机会**：`ProviderLock` 与本 feature 的锁封装重复，建议后续 `cs-refactor` 抽共享 primitive（见 §2.5）。
