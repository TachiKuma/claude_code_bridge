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

## 2026-08-04 编码与路径追加修复

### 新增根因

按用户补充的四个方向复核后确认，源码版 wrapper 仍有一条 native Windows 简中环境下的高风险路径：`ccb8.cmd` 调用的是 Windows PowerShell 5.1 `powershell.exe`，而该进程在当前机器上的默认文本编码为 `gb2312`。`ccb8.ps1` 之前多处使用 `Get-Content ... | ConvertFrom-Json` 读取 `.ccb` / `.ccb-source-dev` / 短 runtime 下的 JSON 状态文件，没有显式指定 UTF-8。

源码 CCB 的 JSON 状态文件由 Python 以 UTF-8 no BOM 写入，且 `ensure_ascii=False`，路径字段会保留中文字符。因此当源码仓库路径或外部项目路径包含中文时，Windows PowerShell 5 会按 GBK/gb2312 误读 UTF-8 no BOM JSON，轻则路径乱码，重则乱码中出现反斜杠组合导致 `ConvertFrom-Json` 抛出 `Unrecognized escape sequence`，表现为 wrapper 启动前直接失败。

同时确认：

- `ccb8.cmd` 已通过 `%~dp0ccb8.ps1` 按 wrapper 所在目录定位 PowerShell 脚本，没有写死外部项目路径。
- `ccb8.ps1` 已通过 `$PSScriptRoot` 获取外部项目根，但源码根、Python、Herdr capability report、runtime home 仍是固定 fallback，缺少环境变量优先的解析层。
- `ccb8.cmd` 与 `ccb8.ps1` 当前均无 UTF-8 BOM；此前的 BOM 风险主要来自 PowerShell 5 的 `Set-Content -Encoding UTF8` 写 JSON，本轮继续保持 no-BOM 写回。

### 追加改动

- `ccb8.ps1`
  - 新增严格 UTF-8 解码 helper：`Read-Utf8Text` / `Read-Utf8Json`，使用 byte-level `ReadAllBytes()` + `.NET UTF8Encoding(false, true).GetString()` 读取 JSON，避免 Windows PowerShell / .NET 按 BOM 自动接受 UTF-16 / UTF-32；同时兼容剥离输入文件开头的 UTF-8 BOM。
  - 所有 wrapper 内部 JSON 读取改为 `Read-Utf8Json`，不再依赖 PowerShell 5 默认 `Get-Content` 编码。
  - `Write-Utf8NoBom` 复用进程级 `$script:utf8NoBom`，保持 JSON 写回 UTF-8 no BOM。
  - 进程内设置 `$OutputEncoding`、`Console.OutputEncoding`、`Console.InputEncoding` 为 UTF-8，减少诊断输出和参数处理中的简中 code page 干扰。
  - 新增 `Resolve-CcbSourceRoot`：优先使用调用方提供的 `CCB_SOURCE_ROOT`，其次在 wrapper 所在目录寻找 `ccb.py`，最后使用当前机器的 ASCII 短父目录 + 精确源码目录名 fallback。
  - 新增 `Resolve-HerdrCapabilityReport`：优先使用 `CCB_HERDR_CAPABILITY_REPORT`，其次按已解析的源码根拼接当前仓库内 Herdr evidence 相对路径。
  - `CCB_RUNTIME_STATE_HOME`、`CCB_PYTHON` / `CCB_PYTHON_BIN`、`CCB_HERDR_EXE`、`CCB_HERDR_SESSION` 改为环境变量优先，默认值仅作为兼容 fallback；`CCB_RUNTIME_STATE_HOME` override 会先规范化为绝对路径，非法路径 fail-fast。
  - Herdr capability report 改成机会性解析：能从环境变量、源码根相对路径或旧 8.3 fallback 解析到文件才导出 `CCB_HERDR_CAPABILITY_REPORT`；解析不到只 warning 并清除该 env，不再让 wrapper 初始化直接失败。
  - `--diagnose` 增加 PowerShell 版本、默认编码、`ccb8.cmd` / `ccb8.ps1` BOM 状态输出。
  - 新增 `--wrapper-self-test`：默认验证 wrapper 自身的 UTF-8 no BOM 写入、中文路径 JSON roundtrip、UTF-16 JSON 拒绝；传入 `--full-env` 时额外验证源码根解析和 Herdr evidence 解析。该入口不调用 `ccb.py`，不启动源码版 CCB。
  - `Run-BoundedKillForce` 增加 `Join-WindowsProcessArguments` / `Quote-WindowsProcessArgument`，按 Windows argv 规则引用 `ccb.py` 参数，避免 `CCB_SOURCE_ROOT` 含空格时 PowerShell `Start-Process -ArgumentList` 拼接错误。
- `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.ps1`
  - 已同步同一份 wrapper 修复，这是用户外部实际执行 `.\\ccb8.cmd` 的位置。

### 追加验证

- `powershell -NoProfile -ExecutionPolicy Bypass -File "./ccb8.ps1" --wrapper-self-test` -> `wrapper_self_test: passed`
- `$env:CCB_SOURCE_ROOT=(Resolve-Path -LiteralPath ".").ProviderPath; powershell -NoProfile -ExecutionPolicy Bypass -File "./ccb8.ps1" --wrapper-self-test --full-env` -> `wrapper_self_test: passed`
- `powershell -NoProfile -ExecutionPolicy Bypass -File "D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1" --wrapper-self-test` -> `wrapper_self_test: passed`
- `$env:CCB_SOURCE_ROOT=(Resolve-Path -LiteralPath ".").ProviderPath; powershell -NoProfile -ExecutionPolicy Bypass -File "D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1" --wrapper-self-test --full-env` -> `wrapper_self_test: passed`
- PowerShell AST parse：
  - `./ccb8.ps1` -> `repo_parse: passed`
  - `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1` -> `external_parse: passed`
- BOM 检查：
  - `./ccb8.cmd` -> `BOM=False`
  - `./ccb8.ps1` -> `BOM=False`
  - `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd` -> `BOM=False`
  - `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1` -> `BOM=False`
- 静态扫描确认 `ccb8.ps1` 中只剩 `Read-Utf8Json` helper 内部调用 `ConvertFrom-Json`，不再有 `Get-Content ... | ConvertFrom-Json`。
- PowerShell AST parse：
  - `./ccb8.ps1` -> `repo_parse: passed`
  - `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1` -> `external_parse: passed`
- `git diff --check` -> 通过；仅提示仓库换行策略会在 Git 触碰时将 LF 替换为 CRLF。
- `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1` 与仓库 `./ccb8.ps1` SHA256 一致：`B796B6B462039F705A1309BC457F07DEA17CCA3E8A23CE6E72D7DFC1AED906E7`。
- 独立 review：
  - Task agent `019fca2d-71e8-7e22-b104-540cb4f170dc`：无 blocking；提出 fix-note 验证描述不精确和 bounded kill 参数引用风险，均已修正。
  - OCR 多轮 focused closure：resolver hard-fail、自检环境耦合、bounded kill 参数、Herdr hard dependency、UTF-8 byte-level 读取和 runtime override 规范化均已处理。
  - OCR 剩余 medium 建议：`.ccb\ccbd` installed protection file 读取失败当前仍 fail-closed。该点有意保留，因为用户约束是“不影响已安装 CCB/v5”，保护 PID 证据不可读时宁可阻止 wrapper 清理，也不冒险跳过保护。
- 未在 Codex 内执行 `.\\ccb8.cmd` 正常启动，也未调用 `--diagnose`，遵守本轮“严禁在 Codex 中直接启动源码版 CCB”的约束。

## 2026-08-04 路径纠偏追加修复

### 新增根因

用户在外部项目执行 `.\\ccb8.cmd` 后仍然失败：

- `警告: Herdr capability report not found`
- `error: ccbd is unavailable: lease_missing; lifecycle_failure: ccbd exited before ready with code 1`

只读日志复核确认，`D:\C#Project\GitHub\AvaPrintDesigner\.ccb\ccbd\ccbd.stderr.log` 的 traceback 实际来自：

- `E:\GitHub开源项目\TachiKuma\claude_code_bridgebak\...`

本机 8.3 短路径解析结果为：

- `E:\GITHUB~1\TACHIK~1\CLAUDE~4` -> `E:\GitHub开源项目\TachiKuma\claude_code_bridge`
- `E:\GITHUB~1\TACHIK~1\CLAUDE~1` -> `E:\GitHub开源项目\TachiKuma\claude_code_bridgebak`

因此上一轮 wrapper 里保留的 `E:\GITHUB~1\TACHIK~1\CLAUDE~1` fallback 会在未显式设置 `CCB_SOURCE_ROOT` 时把外部项目带到备份源码。日志中的 Windows token ACL owner failure 发生在备份源码里，不能代表当前源码修复链路。

### 追加改动

- `ccb8.ps1`
  - `Resolve-CcbSourceRoot` 去掉 `E:\GITHUB~1\TACHIK~1\CLAUDE~1`，改为 `E:\GITHUB~1\TACHIK~1\claude_code_bridge`。
  - 该候选仍保持 ASCII，避免 UTF-8 no BOM 的 PowerShell 5 脚本内直接写中文源码路径；同时用精确目录名避开 `CLAUDE~N` 顺序不稳定和备份仓库误命中。
  - `Resolve-HerdrCapabilityReport` 去掉旧 `CLAUDE~1\CODEST~1\...` fallback，只从显式环境变量或已解析源码根的相对 evidence 路径解析。
- `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.ps1`
  - 已同步同一份 wrapper。

### 追加验证

- 仓库版 `--wrapper-self-test` -> `wrapper_self_test: passed`
- 仓库版 `--wrapper-self-test --full-env` -> `wrapper_self_test: passed`
- 外部版 `--wrapper-self-test` -> `wrapper_self_test: passed`
- 外部版 `--wrapper-self-test --full-env` -> `wrapper_self_test: passed`
- PowerShell AST parse：仓库版和外部版均 passed。
- BOM 检查：仓库版 / 外部版的 `ccb8.cmd`、`ccb8.ps1` 均为 `BOM=False`。
- 静态扫描：仓库版 / 外部版 `ccb8.ps1` 均不再包含 `CLAUDE~1`、`claude_code_bridgebak` 或 `GITHUB~1.*CLAUDE`。
- 两份 `ccb8.ps1` SHA256 一致：`B796B6B462039F705A1309BC457F07DEA17CCA3E8A23CE6E72D7DFC1AED906E7`。
- `git diff --check` -> 通过；仅提示仓库换行策略会在 Git 触碰时将 LF 替换为 CRLF。
- 函数级 ACL 探针：当前源码 `ccbd.control_plane_transport.token_auth.create_token_file()` 在临时目录创建 token 并证明 ACL 收敛成功，返回 `windows-icacls-user-read`；该探针未启动 CCB。

## 当前遗留风险

- 未在 Codex 内执行 `.\\ccb8.cmd` 正常启动，也未执行 `--diagnose`，遵守“严禁在 Codex 中直接启动源码版 CCB”的约束。
- 下一次外部验证若仍出现 token ACL 报错，应以新的日志路径为准；如果日志已来自 `claude_code_bridge` 而非 `claude_code_bridgebak`，再进入 `token_auth.py` 的 Windows owner/SID 兼容修复。

## 2026-08-04 Windows 控制台中断追加修复

### 新增根因

用户外部再次执行 `.\\ccb8.cmd` 后，前台 traceback 停在：

- `lib\cli\services\daemon_runtime\lifecycle.py`
- `ensure_daemon_started()`
- `time.sleep(0.05)`

只读复核确认当前 wrapper 已经跑到正确源码：

- `E:\GITHUB~1\TACHIK~1\claude_code_bridge\ccb.py`
- `E:\GitHub开源项目\TachiKuma\claude_code_bridge\lib\...`

真正的源码 runtime 不在项目 `.ccb\ccbd`，而在 `D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03\ccbd`。该目录下：

- `keeper_pid=10688` 已不是活进程。
- `lifecycle.json` 停在 `phase=starting` / `startup_stage=spawn_requested`。
- `ccbd.stderr.log` 只有 `Fatal Python error: init_sys_streams: can't initialize sys standard streams` 和 `KeyboardInterrupt`。

这说明用户前台 Ctrl+C / 控制台中断会传播到正在初始化的后台 ccbd 子进程。`spawn_ccbd_process()` 和 `spawn_keeper_process()` 之前只传 `start_new_session=True`，在 Windows native 控制台下不足以可靠隔离后台 keeper/daemon。

同时，CLI 等待循环对 `phase=failed` 终态也缺少快速出口，导致外部只能看到 `time.sleep(0.05)` 栈，而不是直接看到 lifecycle failure。

### 追加改动

- `lib/process_background.py`
  - 新增 `background_process_kwargs()`，统一后台进程启动参数。
  - Windows 下显式设置 `CREATE_NEW_PROCESS_GROUP`、`DETACHED_PROCESS`、`CREATE_NO_WINDOW`，避免后台 keeper/ccbd 继承前台控制台 Ctrl+C。
  - 非 Windows 保持 `start_new_session=True`。
- `lib/ccbd/daemon_process.py`
  - `spawn_ccbd_process()` 改用 `background_process_kwargs()`。
- `lib/cli/services/daemon_runtime/keeper.py`
  - `spawn_keeper_process()` 改用 `background_process_kwargs()`。
- `lib/cli/services/daemon_runtime/lifecycle.py`
  - `_startup_wait_exhausted()` 遇到 `phase=failed` 且 `desired_state != running` 或存在 `last_failure_reason` 时立即结束等待，交给 `finalize_daemon_start()` 输出明确错误。
- `test/test_ccbd_process_env.py`
  - 覆盖 Windows 后台进程 flags。
  - 修正 POSIX 清理路径测试在 Windows 上对 `os.killpg` / `SIGKILL` 的模拟。
- `test/test_cli_daemon_keeper_runtime.py`
  - 覆盖 keeper spawn 会携带后台进程参数。
- `test/test_v2_daemon_startup_wait.py`
  - 覆盖 failed 终态不会继续 sleep，而是立即抛出 lifecycle failure。

### 追加验证

- `python -m pytest test/test_ccbd_process_env.py test/test_cli_daemon_keeper_runtime.py test/test_v2_daemon_startup_wait.py -q` -> `26 passed, 2 skipped`
- `python -m py_compile lib/process_background.py lib/ccbd/daemon_process.py lib/cli/services/daemon_runtime/keeper.py lib/cli/services/daemon_runtime/lifecycle.py test/test_ccbd_process_env.py test/test_cli_daemon_keeper_runtime.py test/test_v2_daemon_startup_wait.py` -> passed
- `git diff --check` -> passed；仅 LF/CRLF warning。
- 只读进程检查：`keeper_pid=10688` 已不是活进程；未停止任何进程。
- 未在 Codex 内执行 `.\\ccb8.cmd` 正常启动，也未执行 `--diagnose`。

## 当前遗留风险

- 需要用户在外部项目重新执行 `.\\ccb8.cmd`。wrapper 下次启动前会重置 `D:\.c8\rs\...\ccbd` 的 stale source-dev 状态。
- 如果用户再次按 Ctrl+C，新的 keeper/ccbd 子进程不应再被同一个控制台中断直接打死；但正常启动是否完全成功仍需外部验证。

## 2026-08-04 Herdr namespace state 追加修复

### 新增根因

用户外部按顺序执行 `.\\ccb8.cmd --diagnose` 与 `.\\ccb8.cmd` 后，`bug.txt` 显示诊断已通过，但正常启动失败为：

- `command_status: failed`
- `error: invalid Herdr namespace ref`

只读复核当前短 runtime 后确认，daemon 已经成功启动并 mounted，`startup-report.json` 中 `daemon_started=true`、`health=healthy`、`socket_connectable=true`。故障已从 daemon 启动层进入 Herdr project namespace 层。

根因是 `default_project_namespace_backend()` 在 Herdr runtime 已配置时会选择 Herdr backend，但 `load_namespace_context()` 仍可能把旧 `state.json` 中的 tmux namespace state 传给 Herdr backend。`remember_namespace_state_ref()` 之前不校验 state/ref 的后端归属，导致后续 `session_alive()` / `ensure_window()` 把 `backend_impl=tmux`、`backend_family=tmux-family` 的旧 ref 注入 Herdr 操作，触发 `invalid Herdr namespace ref`。

用户观察到的数个窗口一闪而过，另有独立来源：Herdr CLI adapter 默认 `run_fn=subprocess.run`，没有复用 `terminal_runtime.api._run()` 的 Windows `CREATE_NO_WINDOW` subprocess 参数。

### 追加改动

- `lib/ccbd/services/project_namespace_runtime/backend.py`
  - `remember_namespace_state_ref()` 改为先解析一次 `namespace_ref()`，再同时参考 state 元数据和实际 ref 的 `backend_impl/backend_family` 做后端匹配。
  - Herdr backend 会拒绝记忆旧 tmux state/ref；缺少 state 元数据的兼容 ref 仍可按实际 ref 后端判断，避免破坏既有空 session ref 清理行为。
- `lib/terminal_runtime/api.py`
  - `_herdr_request_adapter()` 创建 `HerdrCliRequestAdapter` 时显式传入 `run_fn=_run`，让 Herdr CLI 短命令继承 Windows 无窗口 subprocess flags。
- `test/test_v2_project_namespace_backend.py`
  - 增加回归：Herdr backend 遇到旧 tmux namespace state 时不得记忆该 ref，`session_alive()` 应重建 Herdr namespace ref，而不是把 tmux ref 交给 Herdr 校验。
- `test/test_herdr_backend_client.py`
  - 增加回归：`terminal_api._herdr_request_adapter()` 必须注入 `_run` 包装。
  - 更新 Herdr runtime 已配置时的 backend selection 契约：直接显式选择 Herdr，不再先走默认 tmux 后重试。

### 追加验证

- `python -m pytest test/test_v2_project_namespace_backend.py -q` -> `23 passed`
- `python -m pytest test/test_herdr_backend_client.py -q` -> `167 passed`
- `python -m py_compile lib/ccbd/services/project_namespace_runtime/backend.py lib/terminal_runtime/api.py test/test_v2_project_namespace_backend.py test/test_herdr_backend_client.py` -> passed
- `git diff --check` -> passed；仅 LF/CRLF warning。
- 未在 Codex 内执行 `.\\ccb8.cmd` 正常启动，也未执行 `--diagnose`。

## 当前遗留风险

- 仍需用户在外部项目 `D:\C#Project\GitHub\AvaPrintDesigner` 重新运行 `.\\ccb8.cmd` 验证正常启动。
- 若下一次失败不再是 `invalid Herdr namespace ref`，应优先依据新的 `bug.txt` / 短 runtime `startup-report.json` / `ccbd.stderr.log` 判断是否进入 provider pane 或 Herdr capability 的下一层问题。

## 2026-08-04 Herdr authoritative cmd pane 追加修复

### 新增根因

用户外部再次执行 `.\\ccb8.cmd` 后，前台输出：

- `Stopping source-dev CCB pid=3308`
- `Stopping source-dev CCB pid=14976`
- `command_status: failed`
- `error: authoritative topology cmd pane is missing`

用户没有生成新的 `bug.txt`，因此本轮只读读取短 runtime：

- `D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03\ccbd\startup-report.json`
- `D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03\ccbd\state.json`
- `D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03\ccbd\lifecycle.jsonl`

证据显示 daemon 仍为 healthy，TCP endpoint 正常；`state.json` 已是 `namespace_backend_family=herdr-native` / `backend_impl=herdr`，上一轮 `invalid Herdr namespace ref` 已越过。

新故障有两个直接原因：

- `materialize_topology()` 在创建并标识化 `cmd` pane 后只返回 agent panes，随后 `ensure_project_namespace()` 依赖一次 metadata/list-panes 回读去找 authoritative cmd pane。Herdr 下 metadata 可见性或查询作用域不稳定时，刚创建的 cmd pane 会被回读成 `None`，导致 `_last_materialized_cmd_pane=None`。
- `start_flow_runtime/service_tmux.py` 仍把空字符串 `tmux_socket_path=""` 当作有效 tmux socket，并把有效 cmd pane id 硬编码为必须以 `%` 开头。这不适用于 Herdr pane id。

`lifecycle.jsonl` 进一步显示 daemon 因 `pane_recovery:cmd` 每约 30 秒反复重建 Herdr namespace，epoch 持续增长，说明这是一个稳定的恢复循环而非单次启动抖动。

### 追加改动

- `lib/ccbd/services/project_namespace_runtime/materialize_topology.py`
  - `materialize_topology()` 改为返回 `(agent_panes, cmd_pane)`。
  - `_materialize_agent_layout()` 在处理 `cmd` leaf 时直接记录本次 materialize 的 pane id。
- `lib/ccbd/services/project_namespace_runtime/ensure.py`
  - 新建 namespace 时优先使用 `materialize_topology()` 返回的 cmd pane；只有缺失时才回退到 metadata 查询。
- `lib/ccbd/start_flow_runtime/service_tmux.py`
  - `tmux_socket_path=""` 规范化为无 tmux socket，不再实例化 tmux backend。
  - topology-managed cmd pane 校验改为：真实 tmux socket 下仍要求 `%...`；无 tmux socket 的 Herdr 路径允许非空 pane id。
  - `project_socket_active_panes()` 和 `bootstrap_cmd_pane_if_needed()` 在无 tmux socket 时不再把 Herdr pane id 送入 tmux active pane / bootstrap 路径。
- `test/test_v2_project_namespace_state.py`
  - 增加回归：Herdr topology materialize 后即使 metadata 暂不可回读，也保留本次创建的 cmd pane id。
- `test/test_v2_ccbd_start_flow.py`
  - 增加回归：Herdr topology-managed cmd pane 可以是非 `%` id。
  - 增加回归：无 tmux socket 时不记录 Herdr pane 到 tmux active pane 集合。
  - 增加回归：无 tmux socket 时跳过 tmux cmd pane bootstrap。

### 追加验证

- `python -m pytest test/test_v2_project_namespace_state.py -q` -> `44 passed`
- `python -m pytest test/test_v2_project_namespace_backend.py test/test_herdr_backend_client.py -q` -> `190 passed`
- 定点 start-flow 回归：
  - `test_topology_start_uses_only_the_authoritative_cmd_pane`
  - `test_topology_start_accepts_herdr_authoritative_cmd_pane_without_tmux_socket`
  - `test_topology_start_fails_closed_when_cmd_authority_is_missing`
  - `test_project_socket_active_panes_preserves_namespace_root_without_cmd`
  - `test_project_socket_active_panes_ignores_herdr_panes_without_tmux_socket`
  - `test_bootstrap_cmd_pane_skips_herdr_namespace_without_tmux_socket`
  - 结果：`6 passed`
- `python -m py_compile lib/ccbd/services/project_namespace_runtime/materialize_topology.py lib/ccbd/services/project_namespace_runtime/ensure.py lib/ccbd/start_flow_runtime/service_tmux.py test/test_v2_project_namespace_state.py test/test_v2_ccbd_start_flow.py` -> passed
- `git diff --check` -> passed；仅 LF/CRLF warning。
- `python -m pytest test/test_v2_ccbd_start_flow.py -q` 全文件当前有 3 个既有 Windows 环境耦合失败，分别是 shutdown 时 Herdr backend selection、socket path 斜杠格式和 auth handshake 文案；新增/相关定点用例已通过，本轮未扩大处理。
- 未在 Codex 内执行 `.\\ccb8.cmd` 正常启动，也未执行 `--diagnose`。

## 当前遗留风险

- 当前外部 daemon 仍运行修复前代码，并且可能继续 `pane_recovery:cmd` 循环；需要用户在外部项目重新执行 `.\\ccb8.cmd`，让 wrapper 先停止旧 source-dev PID 并用新代码启动。
- 若下次已越过 `authoritative topology cmd pane is missing`，下一层失败预计会进入 Herdr provider runtime deferred/agent pane 启动路径，应依据新的 `startup-report.json` 继续定位。

## 2026-08-04 源根回退防护追加修复

### 新增根因

用户外部日志里的 traceback 指向了 `E:\GitHub开源项目\TachiKuma\claude_code_bridgebak`，说明启动时的源码根仍可能被旧的进程环境变量污染，错误地回退到备份仓库。当前 wrapper 虽然能解析出正确的源码树，但 `CCB_SOURCE_ROOT` 仍被放在候选首位时，会把这种旧值当成优先来源。

### 追加改动

- `ccb8.ps1`
  - 调整 `Resolve-CcbSourceRoot()` 的候选顺序，改为先使用仓库里已知正确的 `E:\GITHUB~1\TACHIK~1\claude_code_bridge`，再回退到 `CCB_SOURCE_ROOT`，最后才是脚本位置候选。
  - 外部项目副本同步同样修改，避免旧环境变量把启动链路拉回 `claude_code_bridgebak`。

### 追加验证

- `powershell -NoProfile -ExecutionPolicy Bypass -File "D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1" --diagnose` -> `source_ccb: E:\GITHUB~1\TACHIK~1\claude_code_bridge\ccb.py`
- 在临时设置 `CCB_SOURCE_ROOT=E:\GitHub开源项目\TachiKuma\claude_code_bridgebak` 的情况下再次执行外部 `--diagnose`，`source_ccb` 仍解析为当前仓库源码根。
- `powershell -NoProfile -ExecutionPolicy Bypass -File "./ccb8.ps1" --diagnose` -> 通过，仍解析为当前仓库源码根。
- `git diff --check` -> 通过，仅保留既有 LF/CRLF 提示。

## 2026-08-04 Herdr cmd supervision 与前台 attach 追加修复

### 新增根因

用户在两次提交前后从外部项目执行 `.\\ccb8.cmd`，仍然看不到预期 Herdr 窗口，且第二次启动会先停止旧 CCB PID。复核短 runtime：

- `D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03\ccbd\lifecycle.jsonl`
- `D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03\ccbd\startup-report.json`
- Herdr 隔离状态目录 `D:\C#Project\GitHub\AvaPrintDesigner\.ccb-source-dev\state\xdg-config\herdr`

确认两条独立故障：

- `lib/ccbd/supervision/cmd_slot.py` 的 cmd slot 健康检查仍沿用 tmux `%pane` 模型。Herdr 的 pane id 是 `wAK:p2` 这类 mux id，不以 `%` 开头；因此健康的 Herdr cmd pane 会被误判为缺失，supervision 每约 30 秒触发 `pane_recovery:cmd`，持续重建 namespace。
- `ccb8.ps1` 默认注入 `CCB_NO_ATTACH=1`。CLI 的 `handle_start()` 只有在未设置 `CCB_NO_ATTACH` 且 stdin/stdout 是 TTY 时才执行 `attach_started_project_namespace()`，因此用户交互式执行 `.\\ccb8.cmd` 也会被 wrapper 强制跳过 Herdr foreground attach。

### 追加改动

- `lib/ccbd/supervision/cmd_slot.py`
  - 构建 namespace backend 时传入并记住当前 namespace state，避免 Herdr backend 丢失 session / namespace ref。
  - Herdr namespace 下不再读取 tmux `%pane` root；改用 `list_panes_by_user_options()` 按 `@ccb_project_id`、`@ccb_role=cmd`、`@ccb_slot=cmd`、`@ccb_managed_by=ccbd`、`@ccb_namespace_epoch` 和窗口 token 查找唯一 cmd pane。
  - 找到 Herdr cmd pane 后继续复用 `inspect_project_namespace_pane()` 和 `cmd_slot_matches_namespace()` 做权威校验；校验失败才触发 reflow。
- `test/test_v2_ccbd_supervision_loop.py`
  - 增加 Herdr 回归：健康 cmd pane id 为 `w-main:p2` 时必须保持 `healthy`，不得触发 `pane_recovery:cmd`。
- `ccb8.ps1`
  - 删除默认 `Set-DefaultEnv -Name 'CCB_NO_ATTACH' -Value '1'`。需要无前台窗口收集日志时，调用方仍可显式设置 `CCB_NO_ATTACH=1`。
- `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.ps1`
  - 已同步同一处 wrapper 改动，这是用户当前真实执行 `.\\ccb8.cmd` 的文件。

### 追加验证

- `python -m pytest "test/test_v2_ccbd_supervision_loop.py" -k "cmd_slot or cmd"` -> `6 passed`
- `python -m pytest "test/test_v2_ccbd_start_flow.py" -k "herdr"` -> `6 passed`
- `python -m pytest "test/test_herdr_backend_client.py" -k "list_panes_by_user_options or window_root_pane_fallback or logical_windows or attach_namespace"` -> `5 passed`
- 仓库版 `.\\ccb8.cmd --wrapper-self-test --full-env` -> `wrapper_self_test: passed`
- 外部项目执行 `D:\C#Project\GitHub\AvaPrintDesigner\.\\ccb8.cmd`：
  - wrapper 停止旧 source-dev CCB PID `12876`、`13780`。
  - `start_status: ok`，新 daemon PID `2436`，`ccbd_started: true`。
  - `startup-report.json` 中 `daemon_started=true`、`health=healthy`、`socket_connectable=true`。
- 等待超过一个 supervision 周期后，`lifecycle.jsonl` 最后一条仍停留在新启动时的 `namespace_created` / `reason=missing_session` / `namespace_epoch=339`，未继续追加 `pane_recovery:cmd`，确认 cmd 恢复循环已停止。
- 真实 Herdr state 查询：
  - 最新 focused workspace 为 `wAK`。
  - 最新 workspace 内存在 `sidebar=wAK:p1`、`cmd=wAK:p2`、`agent_2=wAK:p3`、`agent_1=wAK:p4`。
  - `cmd` pane token 包含 `ccb_role=cmd`、`ccb_slot=cmd`、`ccb_project_id=575a...`、`ccb_namespace_epoch=339`、`ccb_window=main`。
- 外部项目 `.\\ccb8.cmd --diagnose` 在同步 wrapper 后输出 `CCB_NO_ATTACH:` 为空，确认 wrapper 不再默认禁用前台 attach。
- 函数级调用 `attach_started_project_namespace()` 成功返回：
  - `backend_impl='herdr'`
  - `namespace_id='wAK'`
  - `session_name='ccb-avaprintdesigner-575a971f'`
  - `ipc_kind='herdr_socket'`
  - `namespace_restore_token_present=True`

## 当前遗留风险

- 本轮已验证 foreground attach 代码路径可以成功 focus Herdr namespace；但 Codex 工具自身不是交互式 Windows 控制台，不能直接证明用户桌面上的 GUI 前台切换观感。
- `startup-report.json` 仍显示 `provider_runtime_deferred_on_herdr:*`。这不再是 cmd pane 循环故障：Herdr workspace 内 agent panes 已存在，但 provider runtime commit 需要依赖 start flow 的 assigned pane 条件；若用户接下来要求 agent pane 内 provider 进程也必须自动启动，应作为下一层 Herdr provider runtime issue 继续处理。
