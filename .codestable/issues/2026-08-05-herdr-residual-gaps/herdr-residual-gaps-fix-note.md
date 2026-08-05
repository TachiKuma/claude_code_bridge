---
doc_type: issue-fix-note
issue: herdr-residual-gaps
status: fixed
root_cause_type: logic
tags:
  - native-windows
  - herdr-integration
  - residual
---

# Herdr 集成残留问题修复记录

## 根因

### 根因一（闪窗）：cmd.exe 作为控制台子系统程序在 Herdr GUI 父进程下触发 Windows 自动分配控制台

`ccb8.cmd` 由 cmd.exe 解释执行（`/SUBSYSTEM:CONSOLE`）。Herdr (GUI 应用，无控制台) 调用 `CreateProcess("ccb8.cmd", ...)` 时，Windows 检测到新进程是控制台子系统且父进程无控制台，自动创建新控制台窗口供 cmd.exe 使用。窗口在 cmd.exe 转发到 PowerShell 后退出，但已短暂可见。

### 根因二（PermissionError）：`D:\.c8\rs\` 下文件 ACL 未被 prestart cleanup 刷新

`Reset-SourceDevStateFiles` 使用 `WriteAllText` 覆盖文件内容，保留目标文件的现有 ACL。如果 ACL 缺少 DELETE 权限（由上一代 keeper 在不同用户上下文中设置），`os.replace(tmp, target)` 需要父目录的 `FILE_DELETE_CHILD` 权限会失败。

### 根因三（snapshot session）：spike 未从 CCB namespace 解析实际 Herdr session

CCB 在 `_create_session_scope()`（`cli.py:1282-1286`）中使用 `project_id` 创建独立的 Herdr session（如 `ccb-avaprintdesigner-575a971f`），而 spike 采集使用 wrapper 环境变量中的 session（`ccb-herdr-avaprintdesigner-source-dev`），两者不一致导致 `api snapshot` 返回空 workspace。

## 改动

### 问题一：ccb8.cmd 闪窗

- `ccb8.cmd:1-8` — 改用 `start "" /B powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "ccb8.ps1" %*`
  - `start "" /B` 在同一控制台窗口中启动进程（不创建新窗口）
  - `-WindowStyle Hidden` 确保 PowerShell 窗口不可见
  - 去掉 cmd.exe 中间层的窗口创建（cmd 自身在 `/B` 模式下不创建新控制台）

### 问题二：keeper 文件 ACL 刷新

- `ccb8.ps1:386-440` — `Reset-SourceDevStateFiles` 改为 **delete + recreate** 模式
  - 先 `Remove-Item -Force` 删除旧文件（清除旧 ACL）
  - 再 `Write-Utf8NoBom` 重新创建（继承当前用户 ACL）
  - 删除失败不阻塞（继续尝试重建），读取失败跳过该文件

### 问题三：spike snapshot session

- `run_spike.ps1:740-768` — 新增 CCB namespace session 提取逻辑
  - 从 `ccb8-ps` 输出 grep `session_name=<value>`
  - 回退到 `ccb8-layout-status` JSON 中 `"session_name": "..."` 
  - 若提取到的 session 与 `$effectiveHerdrSession` 不同，额外采集 `herdr-api-snapshot-ccb-namespace`
- `run_spike.ps1:819-831` — pane verification 优先使用 CCB namespace snapshot

## 验证

- `python -m pytest test/test_herdr_backend_client.py -q`
  - `169 passed`
- `python -m pytest test/test_json_store.py test/test_ccbd_bootstrap_probe.py test/test_ccbd_windows_tcp_loopback_transport.py test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py test/test_v2_project_namespace_backend.py -q`
  - `88 passed, 1 skipped`
- `powershell -NoProfile -ExecutionPolicy Bypass -File "run_spike.ps1" -SelfTest`
  - `herdr_ui_integration_spike_selftest: passed`

## 遗留风险

- 闪窗修复依赖 `start /B` + `-WindowStyle Hidden`，在非 Herdr 环境的普通控制台中 `start /B` 可能行为不同
- ACL 刷新依赖文件可删除，若 `D:\.c8\rs\` 目录本身 ACL 损坏则仍需手动修复
- snapshot session 自动发现依赖 `ccb8-ps` 输出格式稳定（`session_name=<value>` 正则匹配）
