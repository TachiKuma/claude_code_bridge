---
doc_type: issue-review
issue: 2026-08-03-ccb8-prestart-kill-hang
status: passed
reviewer: subagent+ocr
reviewed: 2026-08-04
round: 4
lane_a_state: completed
lane_a_ref: "019fca2d-71e8-7e22-b104-540cb4f170dc"
lane_a_reason: ""
lane_b_state: completed
lane_b_ref: ""
lane_b_reason: ""
---

# ccb8-prestart-kill-hang 代码审查报告

## 1. Scope And Inputs

- Issue report: `.codestable/issues/2026-08-03-ccb8-prestart-kill-hang/ccb8-prestart-kill-hang-report.md`
- Issue analysis: `.codestable/issues/2026-08-03-ccb8-prestart-kill-hang/ccb8-prestart-kill-hang-analysis.md`
- Fix note: `.codestable/issues/2026-08-03-ccb8-prestart-kill-hang/ccb8-prestart-kill-hang-fix-note.md`
- Implementation evidence: `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd`
- Diff basis: 外部 wrapper 文件内容审查 + 本仓库 issue 产物新增；`ccb8.cmd` 不在当前 git 仓库内，无法用本仓库 `git diff` 归因。
- Review mode: initial + focused-closure + PID liveness rereview
- Baseline dirty files: 当前仓库存在多处既有 dirty 文件，非本轮 wrapper 修复范围。

### Independent Review

- Detection: multi-agent 独立 reviewer 可用；`ocr llm test` 通过。
- 环节 A 独立隔离 Task agent: independent-agent completed。
- 环节 B OCR CLI: skipped。
- OCR severity mapping: High→blocking/important, Medium→nit/suggestion, Low→discarded。
- Merge policy: 独立 reviewer finding 已逐条本地核验；针对 changes-requested 做 focused closure 后通过。
- Gate effect: `reviewer: subagent`，放行。

## 2. Diff Summary

- 新增：`.codestable/issues/2026-08-03-ccb8-prestart-kill-hang/*`
- 修改：`D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd`
- 新增：`lib/process_liveness.py`
- 修改：`lib/project/identity_store.py`、`lib/ccbd/system.py`、`test/test_project_identity_store.py`
- 删除：none
- 未跟踪 / staged：issue 目录为未跟踪；wrapper 位于仓库外。
- 风险热点：Windows batch/PowerShell 引号与 errorlevel 传播；避免误杀已安装 CCB/v5。

## 3. Adversarial Pass

- 假设的生产 bug：定向清理失败被吞掉，源码开发态残留继续干扰启动。
- 主动攻击过的反例：errorlevel 传播、PID 复用、项目 `.ccb` 与 `.ccb-source-dev` 双 daemon、bounded `kill -f` 超时。
- 结果：独立 reviewer 首轮发现 errorlevel 被吞，已修复并完成 focused closure；PID 复用保守跳过列为残余风险。

## 4. Findings

### blocking

none

### important

none

### nit

- [ ] REV-001 `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd:133` PID 读取仍基于 `findstr` 和冒号分隔，适配当前 pretty JSON；若将来状态文件变成单行 JSON，可能漏清理。当前不阻塞。

### suggestion

none

### learning

- Windows wrapper 中调用 batch 子例程时，内部失败必须逐层检查 `errorlevel`，否则顶层清理 gate 会失效。

### praise

- 新增负向保护优先保守跳过项目 `.ccb` 中已记录的 PID，符合“不影响已安装 CCB/v5”的约束。

## 5. Test And QA Focus

- QA 必须重点复核：在外部项目执行 `.\\ccb8.cmd`，确认 `.ccb-source-dev` 旧 daemon/keeper 被清掉，项目 `.ccb` 的 v5 daemon/keeper 未被停止。
- Evidence pack residual risks / gate warnings：正常启动未在 Codex 内执行，需外部验证。
- 建议新增或加强的测试：若后续把该 wrapper 逻辑产品化，应改为 PowerShell 脚本或 CCB 内部命令测试。
- 不能靠 review 完全确认的点：Windows 实机上 `Stop-Process` 与 bounded `kill -f` 的真实启动前行为。

## 6. Residual Risk

- 极端 PID 复用场景下，如果项目 `.ccb` 状态文件过期且恰好记录源码态 PID，负向保护会保守跳过源码态清理。这符合“不能影响已安装 CCB/v5”的优先级，但可能需要手动清理源码态残留。

## 7. Verdict

- Status: passed
- Next: 用户在外部项目执行正常启动验证；通过后确认修复完成。

## 8. Focused Closure

- Closed findings: 首轮 independent reviewer 的 important finding：定向清理失败 errorlevel 被上层子例程吞掉。
- Attributed delta: `ccb8.cmd` 的 `:StopSourceDevRuntimePids`、`:StopPidsFromJson`、`:StopPidKey` 增加 errorlevel 传播；`:StopSourceDevPid` 增加项目 `.ccb` PID 负向保护。
- Targeted verification: `cmd /d /c ""D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd" --diagnose"`，结果通过并输出 `v8.5.2`。
- Classification: wrapper 逻辑修复；未改 CCB 主程序、公开 API、数据结构或已安装态配置。

## 9. Focused Closure After External Repro Failure

- Trigger: 用户外部执行 `.\\ccb8.cmd` 后故障依旧；只读 dry-run 发现旧清理条件对当前 Windows 命令行返回 `Regex=False`、`ProjectLike=False`，导致 `.ccb-source-dev` PID `14312/14572` 被跳过。
- Delta: `ccb8.cmd:116` 对 `$project` 和 `$cmd` 统一做 `/` 到 `\` 的路径归一化；用大小写不敏感 `IndexOf` 判断项目根；修正 `ccbd\main.py` / `ccbd\keeper_main.py` 的正则匹配。
- Local read-only verification: 最终表达式对 source-dev PID `14312/14572` 返回 `Regex=True`、`ProjectIndex>=0`、`WouldStop=True`；未停止进程，未执行正常启动。
- Independent focused closure: reviewer `019fc804-0dcc-77e2-9085-c48d6ff1ad5e` 复审通过，blocking/important 均为 none。
- Reviewer conclusion: 停止候选仍只来自 `.ccb-source-dev/state/runtime-state/.../ccbd/{lease,keeper,lifecycle}.json`；`.ccb/ccbd` 只用于保护 PID，当前保护 `12652/12720`，不会误杀已安装 `.ccb` v5。
- Residual risk: 若 `.ccb` 保护文件严重陈旧且 PID 被源码态复用，最坏是过度保护导致漏杀 source-dev，不是误杀 v5。

## 10. Final PID Liveness Rereview

- Trigger: 短 runtime 下最新 `ccbd.stderr.log` 暴露源码层根因：Windows / Python 3.14 上 `os.kill(pid, 0)` 对活的已安装 CCB PID 返回 `OSError`，导致 `identity_store._process_exists()` 和 `ccbd.system.process_exists()` 误判 daemon/keeper 不活。
- Delta: 新增 `lib/process_liveness.py`，Windows 分支改用 `OpenProcess(SYNCHRONIZE, False, pid)`；`identity_store.py` 与 `ccbd/system.py` 委托共享 helper；测试覆盖 helper、`ensure_project_identity()` 默认回归路径和 `ccbd.system` 委托。
- Independent rereview: reviewer `019fc843-9fe9-7910-930e-06eedd203355` 复审后 blocking 为 none；原 important finding 均已关闭。其指出的新文件未跟踪交付风险已通过将 `lib/process_liveness.py` 纳入 index 关闭。
- Targeted verification:
  - `python -m pytest test/test_project_identity_store.py test/test_ccbd_startup_identity.py` -> `14 passed`。
  - `python -m py_compile lib/process_liveness.py lib/project/identity_store.py lib/ccbd/system.py` -> passed。
  - `cmd /d /c ""D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd" --diagnose"` -> 输出 `v8.5.2`。
  - 只读函数级验证：`_process_exists(12652)=True`、`_process_exists(12720)=True`、`_legacy_evidence(...).active_runtime=True`。
- Verdict: passed。

## 11. Full Rereview After State File Enumeration Fix

- Trigger: 用户外部再次执行 `.\\ccb8.cmd`，wrapper 报 `failed to reset source-dev state file: D:\.c8\rs\...\ccbd\ccbd.stderr.log`，随后源码 CLI 仍卡在 `ensure_daemon_started()` startup wait loop。
- Delta:
  - `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1:127` 新增当前项目 `project_id` 恢复。
  - `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1:148` 将状态文件枚举限定到 `<runtimeRoot>/<project_id>/ccbd`，不再递归扫描共享 runtime home。
  - `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1:174` 使用非递归 `Get-ChildItem -File` + `Name` 白名单，只允许 `lease.json`、`keeper.json`、`lifecycle.json`。
  - `lib/project/identity_store.py:405` Windows 下跳过 legacy AF_UNIX socket evidence 探测，避免把 Windows control-plane 恢复带入旧 Unix socket 路径。
  - `test/test_project_identity_store.py:284` 与 `test/test_project_identity_store.py:296` 覆盖直接 helper 和 `ensure_project_identity()` 默认路径。
- Independent rereview:
  - 第一轮 reviewer `019fc861-02fa-7a62-8024-ec7b1466ee8a` 给出 `changes-requested`：跨项目 runtime reset 为 blocking，默认路径测试缺口为 important。
  - 修复后第二轮 reviewer `019fc867-def5-7b92-b37c-d6e4c7961763` 复审通过：blocking none，important none；确认上一轮两项均已关闭。
  - OCR 复审完成：`ocr review --audience agent --exclude "笔记.md" ...` -> `0 finding(s)`。
- Targeted verification:
  - 只读 PowerShell 枚举验证只返回当前 AvaPrintDesigner `project_id` 下的 `ccbd\keeper.json`、`ccbd\lease.json`、`ccbd\lifecycle.json`，不再返回 `*.log`、`*.lock`、`state.json`，也不扫其他 `D:\.c8\rs\*` 项目。
  - `cmd /d /c ""D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd" --diagnose"` -> 输出 `v8.5.2`。
  - `python -m pytest test/test_project_identity_store.py test/test_ccbd_startup_identity.py` -> `16 passed`。
  - `python -m py_compile lib/project/identity_store.py` -> passed。
- Findings:
  - blocking: none
  - important: none
  - nit: none
  - suggestion: 可后续把 `ccb8.ps1` 的状态文件收集改成逐个 `Join-Path` + `Test-Path`，进一步机械化边界；不作为本轮要求。
- Residual risk: 未在 Codex 内执行外部正常启动；仍需用户在 `D:\C#Project\GitHub\AvaPrintDesigner` 执行 `.\\ccb8.cmd` 做实机验证。
- Verdict: passed。

## 12. Full Rereview After Encoding And Path Hardening

- Trigger: 用户补充四个重点怀疑方向：native Windows 简中默认 GBK/gb2312 编解码、UTF-8 BOM、源码仓库 / 外部项目中文或特殊字符路径、`ccb8.cmd` / `ccb8.ps1` 所在路径与硬编码路径。
- Delta:
  - `ccb8.ps1` 新增 byte-level `Read-Utf8Text` / `Read-Utf8Json`，所有 wrapper JSON 读取不再依赖 PowerShell 5 `Get-Content` 默认编码；UTF-8 BOM 仅在输入开头兼容剥离，UTF-16 JSON 会被 self-test 拒绝。
  - `ccb8.ps1` 写 JSON 继续使用 UTF-8 no BOM，避免 PowerShell 5 `Set-Content -Encoding UTF8` 写 BOM。
  - `ccb8.ps1` 对 `CCB_SOURCE_ROOT`、`CCB_PYTHON` / `CCB_PYTHON_BIN`、`CCB_HERDR_EXE`、`CCB_HERDR_SESSION`、`CCB_RUNTIME_STATE_HOME` 采用环境变量优先；源码根和 Herdr evidence 保留兼容 fallback。
  - Herdr capability report 改为机会性导出，解析不到只 warning，不再让 wrapper 初始化直接失败。
  - `CCB_RUNTIME_STATE_HOME` override 会规范化为绝对路径，非法值 fail-fast。
  - `Run-BoundedKillForce` 使用 `Join-WindowsProcessArguments` / `Quote-WindowsProcessArgument` 生成 Windows argv 字符串，避免源码路径含空格时 `Start-Process` 参数边界出错。
  - `--wrapper-self-test` 验证 UTF-8 no BOM 写入、中文路径 JSON roundtrip、UTF-16 JSON 拒绝；`--full-env` 额外验证源码根和 Herdr evidence 解析。该入口不调用 `ccb.py`。
  - 已同步同一份 `ccb8.ps1` 到外部项目 `D:\C#Project\GitHub\AvaPrintDesigner`，仓库版和外部版 SHA256 一致。
- Independent rereview:
  - Task agent `019fca2d-71e8-7e22-b104-540cb4f170dc`：blocking none；important 为 fix-note 验证描述与 `--full-env` 实际行为不一致，已修正文档和验证命令记录；suggestion 为 bounded kill 参数引用风险，已用 Windows argv quoting helper 关闭。
  - OCR CLI 多轮 focused closure：先后指出 resolver hard-fail、自检环境耦合、bounded kill 参数、Herdr hard dependency、UTF-8 byte-level 读取、runtime override 规范化和旧 Herdr hard-fail 校验，均已处理。
  - OCR 剩余 medium：`.ccb\ccbd` installed protection file 读取失败时 wrapper 仍 fail-closed。本地核验后接受为 residual risk；理由是用户明确要求不影响已安装 CCB/v5，保护 PID 证据不可读时应阻止清理而不是跳过保护。
- Targeted verification:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File "./ccb8.ps1" --wrapper-self-test` -> `wrapper_self_test: passed`
  - `$env:CCB_SOURCE_ROOT=(Resolve-Path -LiteralPath ".").ProviderPath; powershell -NoProfile -ExecutionPolicy Bypass -File "./ccb8.ps1" --wrapper-self-test --full-env` -> `wrapper_self_test: passed`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File "D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1" --wrapper-self-test` -> `wrapper_self_test: passed`
  - `$env:CCB_SOURCE_ROOT=(Resolve-Path -LiteralPath ".").ProviderPath; powershell -NoProfile -ExecutionPolicy Bypass -File "D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1" --wrapper-self-test --full-env` -> `wrapper_self_test: passed`
  - PowerShell AST parse：`./ccb8.ps1` -> `repo_parse: passed`；`D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1` -> `external_parse: passed`
  - BOM 检查：`./ccb8.cmd`、`./ccb8.ps1`、`D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd`、`D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1` 均为 `BOM=False`
  - `git diff --check` -> 通过；仅提示仓库换行策略会在 Git 触碰时将 LF 替换为 CRLF。
- Findings:
  - blocking: none
  - important: none
  - nit: none
  - suggestion: none
- Residual risk:
  - 未在 Codex 内执行源码版 CCB 正常启动，也未执行 `--diagnose`，需用户在外部项目验证 `.\\ccb8.cmd`。
  - 保护已安装 CCB 的 `.ccb\ccbd` JSON 若不可读，wrapper 会 fail-closed。这可能降低启动可用性，但符合“不影响已安装 CCB/v5”的优先级。
- Verdict: passed。

## 13. Focused Closure After Backup Source Path Repro

- Trigger: 用户在 `D:\C#Project\GitHub\AvaPrintDesigner` 外部执行 `.\\ccb8.cmd` 后仍失败，外层报 `lease_missing`，最新 stderr traceback 指向 `E:\GitHub开源项目\TachiKuma\claude_code_bridgebak\...`，不是当前源码仓库。
- Root cause: wrapper 的源码根 fallback 仍包含 `E:\GITHUB~1\TACHIK~1\CLAUDE~1`；本机该短路径解析到 `claude_code_bridgebak`，而当前仓库是 `E:\GITHUB~1\TACHIK~1\CLAUDE~4`。
- Delta:
  - `ccb8.ps1` 的 `Resolve-CcbSourceRoot` 去掉 `CLAUDE~1`，改用 `E:\GITHUB~1\TACHIK~1\claude_code_bridge`，保持 ASCII 且精确命中当前源码目录。
  - `Resolve-HerdrCapabilityReport` 去掉旧 `CLAUDE~1\CODEST~1\...` fallback，只跟随显式环境变量或已解析源码根的相对 evidence。
  - 同步同一份 wrapper 到 `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.ps1`。
- Targeted verification:
  - 仓库版 / 外部版 `--wrapper-self-test` 均 passed。
  - 仓库版 / 外部版 `--wrapper-self-test --full-env` 均 passed；该入口不调用 `ccb.py`。
  - 仓库版 / 外部版 PowerShell AST parse 均 passed。
  - 仓库版 / 外部版 `ccb8.cmd`、`ccb8.ps1` 均 `BOM=False`。
  - 静态扫描确认两份 wrapper 不再包含 `CLAUDE~1`、`claude_code_bridgebak` 或 `GITHUB~1.*CLAUDE`。
  - 两份 `ccb8.ps1` SHA256 一致：`B796B6B462039F705A1309BC457F07DEA17CCA3E8A23CE6E72D7DFC1AED906E7`。
  - 当前源码 `token_auth.create_token_file()` 函数级 ACL 探针通过，返回 `windows-icacls-user-read`；未启动 CCB。
  - `git diff --check` -> passed；仅 LF/CRLF 提示。
- Findings:
  - blocking: none
  - important: none
  - nit: none
  - suggestion: none
- Residual risk:
  - 未在 Codex 内执行外部正常启动，也未执行 `--diagnose`。
  - 若用户外部验证后仍出现 Windows token ACL owner failure，需要确认新日志路径是否已经来自 `claude_code_bridge`；只有确认不再跑备份源码后，才应继续改 `token_auth.py`。
- Verdict: passed。

## 14. Focused Closure After Windows Ctrl+C Startup Interruption

- Trigger: 用户外部再次执行 `.\\ccb8.cmd` 后，前台 traceback 停在 `ensure_daemon_started()` 的 `time.sleep(0.05)`；源码路径已确认来自当前 `claude_code_bridge`。
- Runtime evidence:
  - `D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03\ccbd\lifecycle.json` 停在 `phase=starting` / `startup_stage=spawn_requested`。
  - `keeper_pid=10688` 已不是活进程。
  - `ccbd.stderr.log` 为 Python 初始化期 `KeyboardInterrupt`：`Fatal Python error: init_sys_streams: can't initialize sys standard streams`。
- Root cause:
  - Windows native 控制台中，keeper/ccbd 子进程仅使用 `start_new_session=True`，不足以可靠脱离前台 Ctrl+C。
  - CLI startup wait 对 `phase=failed` 终态没有快速出口，失败时容易表现为长时间 sleep 或被用户 Ctrl+C 打断后的 traceback。
- Delta:
  - 新增 `lib/process_background.py::background_process_kwargs()`。
  - Windows 后台进程显式使用 `CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS | CREATE_NO_WINDOW`，非 Windows 保持 `start_new_session=True`。
  - `spawn_ccbd_process()` 与 `spawn_keeper_process()` 共用该 helper。
  - `_startup_wait_exhausted()` 对 `phase=failed` 且 `desired_state != running` 或存在 `last_failure_reason` 的终态立即 finalize。
  - 测试覆盖后台 spawn flags、keeper spawn flags、failed 终态不 sleep。
- Targeted verification:
  - `python -m pytest test/test_ccbd_process_env.py test/test_cli_daemon_keeper_runtime.py test/test_v2_daemon_startup_wait.py -q` -> `26 passed, 2 skipped`
  - `python -m py_compile lib/process_background.py lib/ccbd/daemon_process.py lib/cli/services/daemon_runtime/keeper.py lib/cli/services/daemon_runtime/lifecycle.py test/test_ccbd_process_env.py test/test_cli_daemon_keeper_runtime.py test/test_v2_daemon_startup_wait.py` -> passed
  - `git diff --check` -> passed；仅 LF/CRLF warning。
  - 只读进程检查确认 `keeper_pid=10688` 已非活进程；未停止进程。
- Findings:
  - blocking: none
  - important: none
  - nit: none
  - suggestion: none
- Residual risk:
  - 未在 Codex 内执行外部正常启动，也未执行 `--diagnose`。
  - 仍需用户在外部项目重新运行 `.\\ccb8.cmd` 验证。下一次 wrapper prestart 会重置 stale source-dev runtime 状态。
- Verdict: passed。

## 15. Focused Closure After Herdr Namespace Ref Repro

- Trigger: 用户外部执行 `.\\ccb8.cmd --diagnose` 通过后，再执行 `.\\ccb8.cmd` 失败，`bug.txt` 显示 `command_status: failed` / `error: invalid Herdr namespace ref`；同时观察到数个窗口一闪而过。
- Runtime evidence:
  - 短 runtime 位于 `D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03\ccbd`。
  - `startup-report.json` 表明 daemon 已启动并 healthy，socket 可连接。
  - `state.json` 仍保留旧 `backend_impl=tmux`、`namespace_ipc_kind=null`、`namespace_ipc_ref=null`。
- Root cause:
  - Herdr runtime 已配置时会选择 Herdr backend，但旧 tmux namespace state 仍被 `remember_namespace_state_ref()` 注入 Herdr backend。
  - Herdr CLI adapter 未复用 `terminal_runtime.api._run()`，短命令会直接走 `subprocess.run`，在 Windows 下缺少 `CREATE_NO_WINDOW` 参数。
- Delta:
  - `lib/ccbd/services/project_namespace_runtime/backend.py`：`remember_namespace_state_ref()` 解析 state ref 后校验后端归属；Herdr backend 拒绝旧 tmux state/ref。
  - `lib/terminal_runtime/api.py`：`_herdr_request_adapter()` 显式传入 `run_fn=_run`。
  - `test/test_v2_project_namespace_backend.py`：覆盖 Herdr backend 忽略旧 tmux namespace state 并重建 Herdr ref。
  - `test/test_herdr_backend_client.py`：覆盖 Herdr adapter 使用无窗口 `_run` 包装；更新 runtime configured 时直接显式选择 Herdr 的契约测试。
- Targeted verification:
  - `python -m pytest test/test_v2_project_namespace_backend.py -q` -> `23 passed`
  - `python -m pytest test/test_herdr_backend_client.py -q` -> `167 passed`
  - `python -m py_compile lib/ccbd/services/project_namespace_runtime/backend.py lib/terminal_runtime/api.py test/test_v2_project_namespace_backend.py test/test_herdr_backend_client.py` -> passed
  - `git diff --check` -> passed；仅 LF/CRLF warning。
- Findings:
  - blocking: none
  - important: none
  - nit: none
  - suggestion: none
- Residual risk:
  - 未在 Codex 内执行外部正常启动，也未执行 `--diagnose`。
  - 仍需用户在外部项目重新运行 `.\\ccb8.cmd` 验证；若失败形态变化，应以新日志进入下一层定位。
- Verdict: passed。

## 16. Focused Closure After Herdr Authoritative Cmd Pane Repro

- Trigger: 用户外部执行 `.\\ccb8.cmd` 后失败为 `authoritative topology cmd pane is missing`；未生成新的 `bug.txt`。
- Runtime evidence:
  - `startup-report.json` 显示 daemon healthy、TCP endpoint 可连接，失败位于 start flow。
  - `state.json` 已为 `herdr-native/herdr`，但 `control_window_id=null`。
  - `lifecycle.jsonl` 显示 namespace 从 epoch 2 持续递增，并重复记录 `reason=pane_recovery:cmd`。
- Root cause:
  - Herdr topology materialize 产生的 cmd pane 未作为权威结果直接返回，随后 metadata 回读失败会使 `_last_materialized_cmd_pane` 变为 `None`。
  - start flow 把 `tmux_socket_path=""` 当成有效 tmux 路径，并对 authoritative cmd pane 强制 `%` 前缀，错误套用到了 Herdr pane。
- Delta:
  - `materialize_topology()` / `_materialize_agent_layout()` 返回并捕获本次 materialize 的 cmd pane。
  - `ensure_project_namespace()` 优先使用该 pane，metadata 查询仅作 fallback。
  - `service_tmux.py` 将空 tmux socket 归一化为无 tmux socket；Herdr pane 不参与 tmux active pane / bootstrap，非 `%` id 可作为 Herdr authoritative cmd pane。
  - 新增 Herdr metadata 延迟、非 `%` pane、无 tmux socket active-pane/bootstrap 回归测试。
- Targeted verification:
  - `python -m pytest test/test_v2_project_namespace_state.py -q` -> `44 passed`
  - `python -m pytest test/test_v2_project_namespace_backend.py test/test_herdr_backend_client.py -q` -> `190 passed`
  - 6 个 start-flow 定点回归 -> `6 passed`
  - py_compile -> passed
  - `git diff --check` -> passed；仅 LF/CRLF warning。
- Test gap:
  - `python -m pytest test/test_v2_ccbd_start_flow.py -q` 当前有 3 个既有 Windows 环境耦合失败，涉及 Herdr shutdown selection、socket path 分隔符和 auth handshake 文案；不在本轮改动堆栈内，新增/相关定点用例通过。
- Findings:
  - blocking: none
  - important: none
  - nit: none
  - suggestion: 下次外部实机验证需优先检查 `startup-report.json` 的 `failure_reason` 是否已变更，确认已越过 cmd pane 恢复循环。
- Verdict: passed。
