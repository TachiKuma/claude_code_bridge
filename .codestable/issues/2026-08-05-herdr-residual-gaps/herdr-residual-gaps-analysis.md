---
doc_type: issue-analysis
issue: herdr-residual-gaps
status: confirmed
root_cause_type: logic
related: [herdr-residual-gaps-report.md]
tags:
  - native-windows
  - herdr-integration
  - residual
---

# Herdr 集成残留问题根因分析

## 1. 问题定位

### 问题一：cmd 窗口闪现

| 关键位置 | 说明 |
|---|---|
| `ccb8.cmd:11` | `powershell -NoProfile -ExecutionPolicy Bypass -File "%CCB8_PS1%" %*` — `.cmd` 文件本身启动时 cmd.exe 窗口短暂可见 |
| `ccb8.ps1:803` | `& $env:CCB_PYTHON (Join-Path $env:CCB_SOURCE_ROOT 'ccb.py') @CcbArgs` — 启动 python 子进程，非 detach |

`CreateNoWindow=true` 只在 `ProcessStartInfo` 层面生效。`ccb8.cmd` 本身由用户从 Herdr pane 内调用时，cmd.exe 的宿主进程是 Herdr（创建时已隐藏），但 **cmd.exe 解释器自己的窗口** 可能在 Herdr 创建子进程时短暂闪现。这与 `Inkoke-DetachedCommand`（`run_spike.ps1` 中）的 `CreateNoWindow=true` 不同——spike 是直接从 PowerShell 以 `UseShellExecute=false` 启动，而 wrapper 链是 `cmd.exe → powershell.exe → python.exe`，cmd.exe 环节无法用 `ProcessStartInfo` 控制。

### 问题二：keeper `D:\.c8\rs\` PermissionError

| 关键位置 | 说明 |
|---|---|
| `lib/storage/atomic.py:150` | `os.replace(tmp_path, target)` — Windows 上要求目标父目录 DELETE 权限 |
| `lib/ccbd/keeper_runtime/stores.py:36` | `self._store.save(self._layout.ccbd_keeper_path, state, ...)` — 写入 `D:\.c8\rs\<project_id>\ccbd\keeper.json` |
| `lib/ccbd/keeper_runtime/loop.py:27` | `app._state_store.save(state)` — keeper 主循环每次循环写状态 |

`D:\.c8\rs\` 由 `ccb8.ps1` wrapper 以当前用户身份创建，`mkdir` 创建的目录默认 owner 是当前用户、有完全控制权。`os.replace` 的 `PermissionError` 通常是因为：
- 目标文件 `keeper.json` 由上一代 keeper（不同 PID）创建，继承的 ACL 可能残留
- `D:\.c8\rs\` 目录本身的 owner 或 ACL 因某些原因不包含 DELETE 权限
- `os.replace` 在 Win32 API 层面调用 `MoveFileExW` + `MOVEFILE_REPLACE_EXISTING`，需要 `FILE_DELETE_CHILD` 对父目录

当前已有 fallback：keeper 写入失败后会崩溃重试（`restart_count` 递增），最终或成功或进入 suppressed。prestart cleanup 的 `Reset-SourceDevStateFiles` 已经 reset 了 `D:\.c8\rs\` 下的 `keeper.json` 内容，但**未重置文件 ACL**。如果 ACL 错误是文件级别的，重置内容不会修复 ACL。

### 问题三：spike `api snapshot` session 与 CCB namespace session 不一致

| 关键位置 | 说明 |
|---|---|
| `run_spike.ps1:657-665` | `$effectiveHerdrSession` 从 `$HerdrSession` → `$env:CCB_HERDR_SESSION` → `$env:HERDR_SESSION` 链解析 |
| `host-context.json` 记录 | `CCB_HERDR_SESSION: ccb-herdr-avaprintdesigner-source-dev`（wrapper session） |
| `ccb8-ps` stdout | `herdr_namespace_ref: session_name=ccb-avaprintdesigner-575a971f`（CCB 实际 session） |

CCB 在 `ensure_project_namespace` → `HerderCliRequestAdapter.create_session` 时创建了自己的 session `ccb-avaprintdesigner-575a971f`（由 `_create_session_scope` 从 `project_id` 衍生，`cli.py:1282-1286`）。spike 脚本采集用的 `$effectiveHerdrSession` 是 wrapper 环境变量中的值，两者不一致。

`herdr api snapshot --session ccb-herdr-avaprintdesigner-source-dev` 返回的是 wrapper session 的 snapshot（`workspaces=[]`），而 CCB namespace `wB1` 在 `ccb-avaprintdesigner-575a971f` session 中。

## 2. 失败路径还原

### 问题一：cmd 闪窗

**路径**：用户在 Herdr pane 内输入 `.\ccb8.cmd start` → cmd.exe 启动（窗口短暂可见）→ cmd.exe 调用 powershell → powershell 调用 python ccb.py → CCB 启动

**分叉点**：`ccb8.cmd:11` — cmd.exe 本身在 Herdr 创建子进程时，Herdr 使用 `CreateProcess` 启动 cmd.exe，Herrdr 传了 `CREATE_NO_WINDOW` 标志…但 **cmd.exe 是控制台子系统程序**，Windows 对控制台子系统程序会分配一个控制台窗口（如果父进程没有）。Herdr 作为 GUI 应用没有控制台，所以 cmd.exe 启动时 Windows 会**临时创建一个新控制台窗口**，然后 cmd.exe 内部发现要转发到 PowerShell 并退出——但这个新控制台窗口已经闪现过了。

### 问题二：PermissionError

**路径**：keeper 主循环 → `app._state_store.save(state)` → `atomic_write_text(path, text)` → `_atomic_write_text_path_replace(target, text)` (因为 Windows 没有 `O_DIRECTORY`) → `os.replace(tmp_path, target)` → `PermissionError`

**分叉点**：`lib/storage/atomic.py:150` — `os.replace` 在 Windows 上要求目标父目录有 DELETE 权限。上一代 keeper 创建的 `D:\.c8\rs\<project_id>\ccbd\keeper.json` 文件的 ACL 可能因进程上下文不一致而阻止当前进程的 `os.replace`。

### 问题三：snapshot session mismatch

**路径**：spike 运行 → `$effectiveHerdrSession = "ccb-herdr-avaprintdesigner-source-dev"` → `herdr api snapshot --session ccb-herdr-avaprintdesigner-source-dev` → 返回 wrapper session 的空 workspace → pane-evidence 中 panes=0

**分叉点**：`run_spike.ps1:657-665` — `$effectiveHerdrSession` 只从 spike 参数/环境变量解析，不会从 CCB 的 `namespace_ref` 反推实际 session。需要 spike 脚本主动从 `ccb8-ps` 的 `herdr_namespace_ref` 中提取真实 session。

## 3. 根因

### 根因一（闪窗）：`ccb8.cmd` 作为控制台子系统程序在 Herdr GUI 父进程下触发 Windows 自动分配控制台

**根因类型**：config（cmd.exe 的子系统类型与控制台分配行为）

**根因描述**：`ccb8.cmd` 由 cmd.exe 解释执行。cmd.exe 是控制台子系统程序（`/SUBSYSTEM:CONSOLE`）。当 Herdr (GUI 应用，无控制台) 调用 `CreateProcess("ccb8.cmd", ...)` 时，Windows 检测到新进程是控制台子系统且父进程无控制台，会自动创建一个新控制台窗口供 cmd.exe 使用。cmd.exe /c 标志虽然会使 cmd.exe 在执行完命令后退出，但控制台窗口已经创建并显示过了。

**解决方案**：将 `ccb8.cmd` 替换为直接调用 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ccb8.ps1` 的二进制包装，或在 Herdr pane 内直接执行 `. .\ccb8.ps1`（dot-source）而非通过 cmd.exe。

### 根因二（PermissionError）：`D:\.c8\rs\` 下文件 ACL 未被 prestart cleanup 重置

**根因类型**：config（文件 ACL 残留）

**根因描述**：`ccb8.ps1` 的 `Invoke-PrestartCleanup` 已重置 `D:\.c8\rs\` 下 keeper.json 的**内容**（`state=stopped`, `restart_count=0`），但 `Reset-SourceDevStateFiles` 使用 `Write-Utf8NoBom` → `[System.IO.File]::WriteAllText` 写入，这会保留目标文件的现有 ACL。如果 ACL 本身已损坏（缺少 DELETE 权限），写入内容成功（FILE_WRITE_DATA 权限）但后续 keeper 尝试 `os.replace` 时仍会失败（缺少 FILE_DELETE_CHILD）。

**解决方案**：在 prestart cleanup 中，对 `D:\.c8\rs\` 下的状态文件执行 delete + recreate 而非仅内容覆盖，以强制重建文件 ACL。

### 根因三（snapshot session）：spike 未从 CCB namespace 解析实际 Herdr session

**根因类型**：logic（采集维度缺失）

**根因描述**：采集脚本使用 `$effectiveHerdrSession`（来自 wrapper 环境变量），但 CCB 在 `_create_session_scope()`（`cli.py:1282-1286`）中使用 `project_id` 创建独立的 Herdr session。spike 脚本需要从 `ccb8-ps` 或 `ccb8-layout-status` 的输出中解析 CCB 实际使用的 Herdr session name，并在 snapshot 采集中使用该 session。

## 4. 影响面

- **影响范围**：三个问题均仅影响开发体验和调试效率，不影响 CCB 核心功能
- **潜在受害模块**：仅采集脚本和 wrapper，无其他模块受影响
- **数据完整性风险**：无。PermissionError 不导致数据损坏，有重试兜底
- **严重程度复核**：维持 **P3**，三个问题均可独立修复且改动极小

## 5. 修复方案

### 方案 A：分别修复三个问题（推荐）

- **问题一**：在 `ccb8.cmd` 中直接启动 PowerShell 而不通过 cmd.exe 中间层，或改为 `.ps1` 直接执行
  - **做什么**：`ccb8.cmd` 改为 `@powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ccb8.ps1" %*`（使用 `@` 前缀抑制 echo），在 Herdr pane 中直接 . .\ccb8.ps1 避免 cmd.exe 窗口
  - **优点**：去掉 cmd.exe 中间层，Herdr 直接启动 powershell.exe（也是控制台程序，但 Herdr 的终端模拟器已处理）
  - **缺点**：Herdr pane 内直接 `. .\ccb8.ps1` 需要用户知道这个约定；`ccb8.cmd` 本身仍在，只是内容最小化
  - **影响面**：`ccb8.cmd` 1 行改动

- **问题二**：prestart cleanup 中对 `D:\.c8\rs\` 下状态文件先 delete 再 recreate
  - **做什么**：`Reset-SourceDevStateFiles` 中，对 `keeper.json`、`lease.json`、`lifecycle.json` 改用 `Remove-Item` + `Write-Utf8NoBom` 重新创建，而非直接覆盖
  - **优点**：强制刷新文件 ACL 为当前用户/当前进程上下文
  - **缺点**：删+建之间有极短窗口（`Write-Utf8NoBom` 会立即重建），但 keeper 正在被 kill，不存在并发写风险
  - **影响面**：`ccb8.ps1` `Reset-SourceDevStateFiles` 函数

- **问题三**：spike 脚本从 CCB 输出中提取真实 Herdr session
  - **做什么**：在 `ccb8-ps` 或 `ccb8-layout-status` 输出中 grep `session_name=`，用该 session 做第二次 `api snapshot --session <real_session>` 采集
  - **优点**：确保 snapshot 覆盖 CCB 实际 workspace
  - **缺点**：增加一次 Herdr CLI 调用
  - **影响面**：`run_spike.ps1` 采集逻辑

- **优点**：改动最小、各自独立、互不干扰
- **缺点 / 风险**：问题一可能无法完全消除闪窗（powershell.exe 同样是控制台程序，Herdr 如何处理取决于其终端模拟器实现）

### 方案 B：激进修复

- **做什么**：移除 `ccb8.cmd`，改为纯 PowerShell 模块（`.psm1`），wrapper 函数由 Herdr 直接调用；keeper 状态改用 SQLite 替代 JSON 文件解决 Windows 文件锁问题；snapshot 改为通过 Herdr socket API 而非 CLI 获取
- **优点**：根本解决所有问题
- **缺点**：改动过大，风险高，不适合 P3 问题
- **影响面**：整个 wrapper 架构 + 存储层 + 采集层

### 推荐方案

**推荐方案 A**，理由：三个问题均为 P3，改动范围小、独立修复、不互相阻塞。问题一和二的改动各自 1-2 行，问题三约 10 行采集脚本扩展。
