# 源码版 ccb Windows 启动失败修复记录

## 根因

在 Windows rmux 控制面启动期间，ccbd 会先执行 TCP loopback 自检。真实启动时前台进程或 keeper 可能抢先建立一个合法控制面连接。原 bootstrap accept 线程只接收第一个已认证连接就退出；如果这个连接不是自检客户端，真正的自检客户端就无人发送 auth ACK，最终报 `ccbd auth handshake was rejected`。

启动成功后仍出现的 `UnicodeDecodeError: 'gbk'` 来自 Git worktree 检测：`git rev-parse --show-toplevel` 和 `git worktree list --porcelain` 输出包含中文路径，Python 在 Windows 默认按 GBK 解码，和 Git 的 UTF-8 输出不匹配。

## 改动

- `lib/ccbd/control_plane_transport/windows_tcp.py`：bootstrap accept 在自检客户端完成前持续接收已认证连接，并将自检连接优先交给 worker，避免被抢先连接饿死或被未发送请求的合法连接阻塞。
- `test/test_ccbd_windows_tcp_loopback_transport.py`：新增抢先合法连接的回归测试。
- `lib/workspace/git_worktree.py`、`lib/workspace/materializer.py`：捕获 Git 文本输出时显式使用 `encoding='utf-8', errors='replace'`。
- `test/test_v2_workspace_manager.py`：新增 Git worktree 文本命令编码断言。

## 验证

- `pytest "test/test_ccbd_windows_tcp_loopback_transport.py" "test/test_v2_workspace_manager.py::test_git_worktree_text_commands_use_utf8_replace" "test/test_cli_kill_runtime_processes.py" "test/test_ccbd_stop_flow_runtime.py" -q`：59 passed。
- `python -m compileall -q "lib/ccbd/control_plane_transport/windows_tcp.py" "lib/workspace/git_worktree.py" "lib/workspace/materializer.py"`：通过。
- `git diff --check`：通过，仅提示既有 YAML 文件换行告警。
- 复跑 `& "./ccb-src.ps1" kill -f; if ($LASTEXITCODE -eq 0) { & "./ccb-src.ps1" } else { exit $LASTEXITCODE }`：`start_status: ok`，`ccbd_state=mounted`，无 `UnicodeDecodeError`。

## 遗留风险

本次未清理 `.ccb/debug-subprocess-run.log`，它是定位 subprocess 编码来源时产生的临时运行日志；删除文件按当前操作规范需要 owner 明确确认。
