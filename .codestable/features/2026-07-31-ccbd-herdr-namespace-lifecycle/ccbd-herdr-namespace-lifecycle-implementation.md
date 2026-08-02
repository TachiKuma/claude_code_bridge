---
doc_type: feature-implementation
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
status: blocked
implemented: 2026-08-02
blocked_reason: missing-windows-ccbd-tcp-loopback-control-plane
---

# ccbd-herdr-namespace-lifecycle 实现记录

## 当前结论

S0-S6 已完成。S7 自动化回归已完成，CMD-013 也已在真实 Native Windows x64 + Herdr 可执行文件上尝试运行，但 `ccbd` 在进入 Herdr namespace lifecycle 前崩溃：当前 Herdr 分支缺少旧 rmux 路线已验收的 Windows TCP loopback control-plane transport，`socket_server_runtime/lifecycle.py` 仍是 AF_UNIX-only。该修复超出本 feature approved scope，已写 owner-stop：`ccbd-herdr-namespace-lifecycle-approval-report.md`。

## 主要改动

- `lib/ccbd/services/project_namespace_runtime/backend.py`：新增 V2 mux helper path，覆盖 namespace ref 记忆、pane identity、respawn、kill pane、move pane、reflow window 和 per-operation capability gate。
- `lib/ccbd/services/project_namespace_runtime/*patch*.py`：reload add/remove/move/reflow 路径改用 V2 refs/primitives，Herdr 缺 primitive 时 fail closed。
- `lib/ccbd/services/project_namespace_runtime/additive_patch_namespace.py` 与 `lib/ccbd/reload_patch.py`：Herdr namespace readiness/scope proof 改为 namespace transport ref，不再要求 `tmux_socket_path`。
- `lib/ccbd/services/project_namespace_pane.py`：Herdr pane id 不要求 `%` 前缀，非 tmux pane id 走 backend `describe_pane`。
- `lib/ccbd/handlers/project_restart.py`：Herdr namespace 下 restart agent/panes 返回 unsupported/deferred evidence，不静默返回 scheduled success，不修改 provider completion。
- `lib/terminal_runtime/tmux.py` 与 `lib/terminal_runtime/tmux_readiness.py`：修复 S7 tmux regression 中暴露的 Windows 诊断/命令构造漂移，保留默认 `/dev/null` 字面值并稳定 tmux command 诊断文本。

## Step 状态

| Step | 状态 | 证据 |
|---|---|---|
| S5 kill/restart/reload boundary | done | Herdr reload primitive tests 4 passed；restart handler tests 6 passed；restart panes tests 2 passed；tmux add/remove/move reload regression 3 passed。 |
| S6 scope/content guard | done | CMD-007、CMD-008、CMD-009 均 passed。 |
| S7 regression guard + Windows foreground/manual evidence | pending | 自动化 regression passed；CMD-013 真机 transcript 已生成但 blocked，原因是 native Windows 下 ccbd control-plane AF_UNIX-only。 |

## 验证证据

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-checklist.yaml" --yaml-only`：通过。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"`：通过。
- `python -m pytest -q "test/test_mux_backend_contract.py" "test/test_herdr_backend_client.py" -k "V2 or HerdrBackend or attach_namespace or presentation or herdr"`：145 passed, 12 deselected。
- Windows baseline 隔离后：`test/test_v2_project_namespace_state.py test/test_v2_project_namespace_backend.py -k "namespace or mux or herdr or restore_token or redacted or presentation or capability"`：50 passed。
- Windows baseline 隔离后：`test/test_v2_start_foreground.py -k "foreground or attach or herdr or rmux or restore_token or redacted"`：14 passed。
- Windows baseline 隔离后：`test/test_ccbd_project_view.py -k "herdr or restore_token or redacted or namespace_view"`：2 passed。
- Windows baseline 隔离后：`test/test_ccbd_namespace_additive_patch.py -k "herdr or mux or namespace_ref or reload or move or reflow"`：26 passed。
- Windows baseline 隔离后：`test/test_v2_project_namespace_state.py -k "event or summary_fields or log or restore_token or redacted"`：8 passed。
- Windows baseline 隔离后：`test/test_agent_lifecycle_cli.py -k "reload or restart or kill"`：6 passed。
- Windows baseline 隔离后：`test/test_ccb_restart.py -k "restart_agent_handler"`：6 passed。
- Windows baseline 隔离后：`test/test_v2_ccbd_start_flow.py -k "project_restart_panes_handler"`：2 passed。
- `python -m py_compile "lib/terminal_runtime/tmux.py" "lib/terminal_runtime/tmux_readiness.py"`：通过。
- `git diff --check`：exit 0，仅 `.codestable` CRLF/LF warning。

## 已知基线与环境限制

- 原始 pytest 在 Windows 上会因 `storage.atomic` durable directory fsync / dir_fd 不可用失败；业务断言复跑时仅进程内替换为普通写文件。
- 涉及 `mobile_gateway.terminal` 的 collection 会因 POSIX-only `fcntl` / `pty` / `termios` 导入失败；业务断言复跑时仅进程内 stub。
- `test/test_ccbd_project_view.py -k "... or project_view"` 的宽过滤会命中既有 Windows 非法 `:` 路径用例；已收窄到本 feature 相关 `herdr|restore_token|redacted|namespace_view`。
- `evidence/cmd-013-native-windows-herdr-transcript.md`：真实 Native Windows x64 / Python 64bit / Herdr `0.7.5-preview.2026-07-29-44b3adb12552`。失败点为 `ccbd exited before ready`；runtime 日志记录 `RuntimeError: unix domain sockets are not supported on this platform`。
- `evidence/cmd-013-native-windows-herdr-runbook.md` 已记录真实入口 `python <repo>/ccb.py`、source checkout guard、必需环境变量、采集命令和 redaction 检查。

## 清洁度

- 未修改 provider runtime、recovery owner、Mobile/Config UI、doctor/support、package/release/update/installer 或 public validation matrix。
- 没有引入 provider completion / recovery / support tier / release surface 术语越界。
- 发现由测试注入残留的一批仓库根目录无扩展随机临时文件；删除文件需要 owner 明确确认，当前未清理。

## 下一步

owner 批准后，先把旧 `windows-rmux-native-backend` 已验收的 `ccbd-control-plane-transport-seam` / `ccbd-windows-tcp-loopback-transport` 能力移植或重开到当前 Herdr roadmap；通过 focused transport tests 后重跑 CMD-013。CMD-013 通过后恢复 S7，更新 checklist，再进入 `cs-code-review`。
