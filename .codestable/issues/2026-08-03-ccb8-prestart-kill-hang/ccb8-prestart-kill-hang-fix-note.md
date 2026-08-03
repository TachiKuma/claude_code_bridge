---
doc_type: issue-fix-note
issue: 2026-08-03-ccb8-prestart-kill-hang
status: review-passed
fix_path: standard
tags: [windows, ccb8, kill, startup]
---

# ccb8 启动前 kill 残留清理 Fix Note

## 根因

`ccb8.cmd` 之前直接在启动前调用 `ccb.py kill -f`。但 `kill -f` 在进入本地强制清理前，会先尝试连接 mounted daemon 的 control-plane endpoint。Windows 下该探测链路可能卡在 token 读取或 TCP socket 探测，导致本地 PID 清理没有执行，`.ccb-source-dev` 残留 daemon/keeper 继续存活。

外部复现失败后，进一步定位到第一次定向清理实现的 Windows 匹配条件也有缺陷：wrapper 项目根可表现为 `D:/...`，而进程命令行是 `D:\...`；同时正则没有稳定命中 `ccbd\main.py` / `ccbd\keeper_main.py`。因此脚本虽然从 `.ccb-source-dev` 状态文件识别出了 PID，但在命令行校验阶段跳过了源码态 keeper/daemon。

拆分为 `ccb8.ps1` 后继续复现出多个 wrapper 状态收尾问题：

- Windows PowerShell 5 的 `Set-Content -Encoding UTF8` 会写入 UTF-8 BOM，导致 CCB 后续以严格 `utf-8` 读取 `.ccb-source-dev` JSON 时失败：`Unexpected UTF-8 BOM`。
- 预启动清理只复位了 `lease.json`，没有复位 `lifecycle.json` / `keeper.json`。当源码态 keeper/daemon 被杀后，`lifecycle.json` 仍可能停在 `phase=starting`、`startup_stage=spawn_requested`，启动逻辑不会把它当成可重新 spawn 的 `unmounted/failed` 状态。
- `.ccb-source-dev/state/runtime-state/.../ccbd/{ccbd,tmux}.sock` 路径长度约 152 字节，超过典型 Unix socket 路径上限后触发 fallback 到 `\tmp\ccb-runtime\...`。旧 `state.json` / `startup-report.json` 记录的失败原因显示 psmux 在 fallback tmux socket 上反复报 `no server running`，成为新的启动干扰项。
- 将 runtime root 切换到短路径后，项目 `.ccb\runtime-root-ref.json` 仍记录旧 `.ccb-source-dev\state\runtime-state\{project_id}`，而源码 CCB 会校验 ref 与当前 `CCB_RUNTIME_STATE_HOME` 计算出的 runtime root 完全一致，因此启动前报 `runtime_state_root mismatch`。

短 runtime 下继续复现后，最新 `D:\.c8\rs\{project_id}\ccbd\ccbd.stderr.log` 暴露源码层根因：`ensure_project_identity()` 会读取项目 `.ccb` 里的旧 runtime 证据，`identity_store._process_exists()` 通过 `os.kill(pid, 0)` 判断 PID 是否存活。Windows / Python 3.14 上该调用对实际存活的已安装 CCB PID `12652` / `12720` 返回 `OSError`，导致源码 CCB 把 live daemon/keeper 误判为不活，进而进入旧 socket 探测分支并污染 `active_runtime` 判断。`ccbd.system.process_exists()` 存在同类实现，属于同一 daemon 生命周期风险点。

## 改动

- `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.cmd`
  - 默认设置 `CCB_NO_ATTACH=1`、`CCB_CCBD_FAULTHANDLER=1`、`PYTHONUNBUFFERED=1`，减少外部复现时必须额外拼环境变量的需求，并改善异常日志可读性。
  - 启动入口前先读取 `.ccb-source-dev` 隔离运行态下的 `lease.json`、`keeper.json`、`lifecycle.json`。
  - 只对这些文件中的 `ccbd_pid`、`keeper_pid`、`owner_pid` 做定向处理，并在停止前验证进程命令行必须是 `ccbd/main.py` 或 `ccbd/keeper_main.py`，且包含当前项目根。
  - 对项目根和进程命令行统一做 `/` 到 `\` 的路径归一化，并使用大小写不敏感的 `IndexOf` 判断项目归属，避免 Windows 路径分隔符差异导致漏清理。
  - 修正 `ccbd\main.py` / `ccbd\keeper_main.py` 的正则匹配，确保当前实物进程命令行可命中。
  - 清理后把 `.ccb-source-dev` lease 标记为 `mount_state=unmounted`，避免后续启动继续对旧 mounted endpoint 做探测。
  - JSON 写回改为显式 .NET `UTF8Encoding(false)`，避免 PowerShell 5 写入 BOM。
  - 清理后同步复位 `.ccb-source-dev` 的 `lifecycle.json` 为 `phase=unmounted` / `desired_state=running`，并把 `keeper.json` 标为 `state=stopped`，确保下一次启动会重新 spawn keeper。
  - 将源码开发态 `CCB_RUNTIME_STATE_HOME` 从项目深路径迁移到短路径 `D:\.c8\rs`；旧 `.ccb-source-dev\state\runtime-state` 保留为 `CCB_LEGACY_RUNTIME_STATE_HOME`，仅用于预启动清理旧干扰项。
  - 增加 `Repair-SourceDevRuntimeRootRef`：仅当 `.ccb\runtime-root-ref.json` 指向旧 `.ccb-source-dev` runtime 时，把它修正为当前短 runtime root；如果指向其他未知位置则 fail-closed，避免误改已安装态状态。
  - 定向 PID 清理后再执行有超时边界的 `ccb.py kill -f` 收尾；如果 `kill -f` 超时或非零退出，记录 warning 后继续，避免再次依赖 Ctrl+C 中断排障。
- `lib/process_liveness.py`
  - 新增共享 PID 存活判断。POSIX 保持原 `os.kill(pid, 0)` 语义；Windows 改为 `OpenProcess(SYNCHRONIZE, False, pid)`，避免 Python 3.14 `os.kill(pid, 0)` 的 false-negative。
  - Windows HANDLE 使用 `ctypes.wintypes.HANDLE` 声明返回值，并在 `finally` 中关闭，避免 64 位句柄截断和资源泄露风险。
- `lib/project/identity_store.py`
  - `_process_exists()` 改为委托共享 `process_liveness.process_exists()`，确保 legacy runtime evidence 能正确识别 Windows live PID。
- `lib/ccbd/system.py`
  - `process_exists()` 同步委托共享 helper，避免 daemon 生命周期其他分支继续使用不可靠的 Windows `os.kill(pid, 0)`。
- `test/test_project_identity_store.py`
  - 增加 Windows OpenProcess 分支测试。
  - 增加 `ensure_project_identity()` 默认路径的回归测试：移动后的既有 identity 遇到 active legacy runtime 时必须 fail-closed。
  - 增加 `ccbd.system.process_exists()` 委托共享 helper 的测试。

## 验证

- 已运行 `cmd /d /c ""D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd" --diagnose"`。
- 结果：wrapper 能正常解析并输出隔离环境、默认诊断环境变量和 CCB 版本 `v8.5.2`。
- 已执行只读 dry-run 校验最终匹配条件，不停止进程：
  - `.ccb-source-dev` 状态文件数：3。
  - 源码态 PID `14312` / `14572`：`Regex=True`、`ProjectIndex>=0`、`WouldStop=True`。
  - 该验证未执行正常启动，也未停止任何进程。
- 已扫描 `.ccb-source-dev` 下所有 JSON，确认当前均无 UTF-8 BOM。
- 已用 Python `json.loads(... encoding='utf-8')` 严格解析 `.ccb-source-dev` 下所有 JSON，结果通过。
- 已手动复位当前残留 source-dev 状态：`lease=unmounted`、`lifecycle=unmounted/desired running`、`keeper=stopped`。
- 已通过 `.\ccb8.cmd --diagnose` 确认新环境变量：`CCB_RUNTIME_STATE_HOME=D:\.c8\rs`，`CCB_LEGACY_RUNTIME_STATE_HOME=D:\C#Project\GitHub\AvaPrintDesigner\.ccb-source-dev\state\runtime-state`。
- 已计算新短路径下 socket 路径长度约 89 字节，低于旧路径 152 字节，预期不再触发 `\tmp\ccb-runtime` fallback。
- 已将当前 `.ccb\runtime-root-ref.json` 从旧 `.ccb-source-dev` runtime 修正为 `D:\.c8\rs\{project_id}`，并再次运行 `.\ccb8.cmd --diagnose` 通过。
- 已读取最新短 runtime `ccbd.stderr.log`，定位到源码层 `os.kill(pid, 0)` Windows false-negative。
- 已用函数级验证确认修复前 `_process_exists(12652)=False` / `_process_exists(12720)=False`，修复后 `_process_exists(12652)=True` / `_process_exists(12720)=True`，且 `_legacy_evidence(...).active_runtime=True`。
- 已运行 `python -m pytest test/test_project_identity_store.py test/test_ccbd_startup_identity.py`，结果 `14 passed`。
- 修复独立 review 反馈后再次运行 `python -m pytest test/test_project_identity_store.py`，结果 `11 passed`。
- 已运行 `python -m py_compile lib/process_liveness.py lib/project/identity_store.py lib/ccbd/system.py`，结果通过。
- 已通过只读 `ensure_project_identity(Path('D:/C#Project/GitHub/AvaPrintDesigner'))` 验证现有 project identity 可返回，不触发正常 CCB 启动。
- 独立 code review 已通过：`ccb8-prestart-kill-hang-review.md`（最终 PID liveness 复审）。
- 未在 Codex 内执行正常启动，遵守“执行外部验证时严禁在 Codex 中直接启动 CCB”的约束。

## 2026-08-04 跟进修复

### 新增根因

用户外部再次执行 `.\\ccb8.cmd` 后出现：

- `failed to reset source-dev state file: D:\.c8\rs\...\ccbd\ccbd.stderr.log`
- `Warning: source-dev ccb kill -f did not complete cleanly`
- 主 CLI 随后卡在 `ensure_daemon_started()` 的 startup wait loop。

复核后确认两个追加问题：

- `ccb8.ps1` 使用 `Get-ChildItem -Recurse -File -Include lease.json, keeper.json, lifecycle.json`。Windows PowerShell 在该调用形态下实际返回了 `ccbd.stderr.log`、`keeper.lock`、`state.json` 等非目标文件，导致 reset 阶段尝试把日志当 JSON 状态文件处理。
- 第一版修正虽然改成 `Name` 白名单，但仍从共享 `D:\.c8\rs` 递归枚举全部项目 runtime。PID 停止阶段有当前项目命令行保护，状态 reset 阶段没有项目边界，存在跨项目重置其他 source-dev runtime 状态的风险。
- 最新 `ccbd.stderr.log` 还显示 `ensure_project_identity()` 会在 Windows 下探测 legacy `.ccb/ccbd/*.sock` Unix socket 证据。该路径不属于 Windows control-plane TCP endpoint，且会把启动身份恢复带入无意义的旧 socket 文件系统探测。

### 追加改动

- `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.ps1`
  - 增加 `Get-SourceDevProjectId`，优先从 `.ccb\runtime-root-ref.json` 读取当前项目 `project_id`，必要时回退 `.ccb\project.identity.json`。
  - `Get-SourceDevStateFiles` 不再递归扫描整个 `CCB_RUNTIME_STATE_HOME` / `CCB_LEGACY_RUNTIME_STATE_HOME`，而是只访问 `<runtimeRoot>\<project_id>\ccbd`。
  - 状态文件筛选改为显式 `Name` 白名单：`lease.json`、`keeper.json`、`lifecycle.json`。
  - runtime root 去重改为 full path + lowercase key，避免同一路径不同写法导致重复 reset。
- `lib/project/identity_store.py`
  - `_socket_connectable()` 在 Windows 下直接返回 `False`，并注明该 helper 只服务 legacy AF_UNIX socket evidence；Windows control-plane endpoint 不走这条探测路径。
- `test/test_project_identity_store.py`
  - 增加直接回归：Windows 下 `_socket_connectable()` 不触碰 legacy socket 文件路径。
  - 增加默认路径回归：不注入 `socket_connectable_fn` 时，`ensure_project_identity()` 在 Windows 下遇到 dead legacy lease + socket evidence 不应因 socket 探测阻止 rebind。

### 追加验证

- 已用只读 PowerShell 枚举验证：新逻辑只返回当前 AvaPrintDesigner `project_id` 下的 `ccbd\keeper.json`、`ccbd\lease.json`、`ccbd\lifecycle.json`，不再包含 `*.log`、`*.lock`、`state.json`，也不再枚举其他 `D:\.c8\rs\*` 项目。
- 已运行 `cmd /d /c ""D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd" --diagnose"`，结果通过并输出 `v8.5.2`。
- 已运行 `python -m pytest test/test_project_identity_store.py test/test_ccbd_startup_identity.py`，结果 `16 passed`。
- 已运行 `python -m py_compile lib/project/identity_store.py`，结果通过。
- OCR 复审已运行：`ocr review --audience agent --exclude "笔记.md" ...`，结果 `0 finding(s)`。
- 第二轮独立复审 agent `019fc867-def5-7b92-b37c-d6e4c7961763` 结论：blocking none，important none；上一轮跨项目 reset 与默认路径测试缺口均已关闭。

## 遗留风险

- 正常启动路径仍需要用户在外部项目执行 `.\\ccb8.cmd` 验证。
- 本次只修 wrapper 的源码开发态启动前清理边界，以及当前启动路径直接触发的 Windows PID liveness false-negative；仓库内其他与本复现路径无关的 `os.kill(pid, 0)` 调用未扩大处理。
- `ccb kill -f` 主程序自身“远端探测先于本地强制清理”的通用问题尚未修复，可后续另开 issue。

## 2026-08-04 追加修复

### 新增根因

外部再次执行 `.\\ccb8.cmd` 后，日志虽然还是沿用旧 traceback，但源码侧实际又暴露出一条 Windows 专属问题：`CcbdLifecycle` 和 `ProjectDaemonInspection` 会在只有 `socket_path`、没有显式 `tcp_loopback` endpoint 的情况下，把 legacy socket path 自动补成 `unix_socket`。这会把 Windows 启动早期“endpoint 还没发布”误写成 Unix 端点，污染诊断和后续接管判断。

### 追加改动

- `lib/ccbd/services/lifecycle.py`
  - `build_lifecycle()` 与 `_control_plane_endpoint_from_record()` 在 Windows 下不再从 `socket_path` 合成 `unix_socket` endpoint。
  - 只有显式 `control_plane_endpoint` 才会被保留。
- `lib/ccbd/services/project_inspection.py`
  - `control_plane_endpoint` 在 Windows 下不再回退到 legacy socket path。
- `lib/ccbd/keeper.py`
  - 新建 `spawn_requested` startup transaction 时显式清空旧 `control_plane_endpoint`，避免历史 `unix_socket` 字段被 `with_phase()` 继承。
- `lib/ccbd/app_runtime/lifecycle.py`
  - daemon 进入 `socket_listening` 阶段时写入当前 socket server 的真实 endpoint。
- `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.ps1`
  - reset source-dev `lifecycle.json` 时同步清空 `control_plane_endpoint`。
- `test/test_ccbd_windows_tcp_loopback_transport.py`
  - 增加 Windows 回归：`build_lifecycle()` 不再合成 legacy endpoint。
  - 增加 Windows 回归：`ProjectDaemonInspection.control_plane_endpoint` 不再回退为 `unix_socket`。
- `test/test_v2_ccbd_keeper.py`
  - 增加回归：历史 `unix_socket` endpoint 不会被新的 keeper startup transaction 继承。

### 追加验证

- `python -m pytest test/test_ccbd_windows_tcp_loopback_transport.py -q` -> `22 passed`
- `python -m pytest test/test_v2_daemon_startup_wait.py -q` -> `9 passed`
- `python -m pytest test/test_v2_ccbd_keeper.py::test_keeper_releases_startup_lock_before_spawn_and_preserves_child_mounted_record test/test_ccbd_windows_tcp_loopback_transport.py test/test_v2_daemon_startup_wait.py -q` -> `32 passed`
- `python -m pytest test/test_ccbd_startup_fence_app.py test/test_ccbd_startup_identity.py -q` -> `11 passed`
- `python -m py_compile lib/ccbd/keeper.py lib/ccbd/app_runtime/lifecycle.py lib/ccbd/services/lifecycle.py lib/ccbd/services/project_inspection.py test/test_v2_ccbd_keeper.py test/test_ccbd_windows_tcp_loopback_transport.py` -> passed
- `cmd /d /c ""D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd" --diagnose"` -> 通过并输出 `v8.5.2`
