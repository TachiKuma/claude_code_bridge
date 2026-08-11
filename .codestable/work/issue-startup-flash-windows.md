---
type: issue
slug: startup-flash-windows
status: active
created: 2026-08-11
---

# CCB 启动链路闪窗治理

## 目标

Native Windows 下 CCB 启动链路不应出现非预期可见控制台窗口。预期可见的 UI 仅限 WezTerm / Herdr 前台界面；Herdr 探测、server 启动、keeper、ccbd、后台更新刷新等控制面子进程必须隐藏控制台。

## 现场

- 用户要求先将方案落盘到 CodeStable 工作流文档，再正式实施。
- main_claude 审核结论为“方向正确、需调整”，必须补 G1-G3：
  - G1：`query_herdr_server_status()` 也是每次 `ccb herdr open` 会调用的启动热路径探测。
  - G2：Herdr UI 有 `ccb8.ps1` 和 Python `start_foreground._launch_herdr_ui()` 两条路径，必须统一 intentional-visible / must-hide 语义。
  - G3：已有 ETW 诊断脚本和多处 `CREATE_NO_WINDOW` 改动，实施前不得重复造新 harness。

## 边界

- 不把 Herdr dispatch 改成 `Start-Process` 或 detached `Popen`；当前 Herdr dispatch 仍依赖交互式终端。
- 不动 mobile、install、update 主流程等非启动热路径。
- 不删除或替换 `ccb8.cmd` 兼容入口；本轮只可新增隐藏入口候选或补文档语义。
- 不运行会 kill 现有 runtime 或打开外部 UI 的一键启动复现，除非后续单独获得确认。

## 证据

- `.ccb/reviewer-flashwindow-feedback.md`：审核确认 G1-G3。
- `.codestable/lessons/2026-08-10-herdr-dispatch-interactive-terminal.md`：Herdr dispatch 不可用后台子进程替代。
- `.codestable/lessons/2026-08-10-ccb8-wezterm-spawn-herdr-xdg-env.md`：WezTerm direct spawn 需要清理 XDG 并设置真实 `HERDR_CONFIG_PATH`。
- `.codestable/issues/2026-08-05-herdr-residual-gaps/herdr-residual-gaps-analysis.md`：`.cmd`/`conhost` 分叉点已被记录。
- `.codestable/issues/2026-08-03-ccb8-prestart-kill-hang/ccb8-prestart-kill-hang-fix-note.md`：Herdr CLI adapter 短命令缺 Windows `CREATE_NO_WINDOW` 曾被记录为独立闪窗来源。
- 当前源码：
  - `lib/cli/services/herdr_common.py::query_herdr_server_status()` 直接 `subprocess.run`。
  - `lib/cli/services/herdr_bootstrap.py::_probe_herdr_read_capabilities()` 直接 `subprocess.run`。
  - `lib/cli/services/herdr_bootstrap.py::_discover_running_ccb_sessions()` 直接 `subprocess.run`。
  - `lib/cli/management_runtime/startup_update_refresh.py::_spawn_background_refresh()` 只有 `start_new_session=True`。
  - `lib/process_background.py::background_process_kwargs()` 已提供 Windows 后台进程隐藏参数。

## 方案

### P0：观测口径

复用现有 `.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/diagnose_flash_windows.ps1` 作为真实启动观测工具；不扩展 `perf_ccb_startup.py`。本轮自动化只做单元级断言，真实 ETW 运行需要用户另行确认。

### P1：启动热路径隐藏补漏

- 新增或复用一个小型 Windows no-window subprocess helper。
- `query_herdr_server_status()`、`_probe_herdr_read_capabilities()`、`_discover_running_ccb_sessions()` 统一通过 helper 执行 Herdr read probe。
- `_spawn_background_refresh()` 在 Windows 下复用 `background_process_kwargs()`，保持非 Windows `start_new_session=True` 行为。

### P2：UI 可见性语义

- `ccb8.ps1` 的 WezTerm direct spawn / send-text fallback 是 intentional-visible UI 路径；XDG guard 不变。
- `start_foreground._launch_herdr_ui()` 的 WezTerm spawn 是 intentional-visible UI 路径；fallback 的 standalone `herdr session attach` 需保持“打开 UI”的语义，隐藏的只能是控制面包装窗口，不能压掉 Herdr UI 本身。
- 本轮优先补代码注释和测试语义，不引入新的 dispatch 机制。

### P3：入口替代候选

`.cmd` 本身无法保证零可见控制台。后续可在 `.lnk` / `.vbs` / `pythonw` 之间选择隐藏入口；本轮不默认替换兼容入口。

## 验收

- 单元测试能断言 Windows 下启动热路径 Herdr read probe 带 `CREATE_NO_WINDOW`。
- 单元测试能断言后台更新刷新在 Windows 下带 `background_process_kwargs()` 的 creation flags。
- 现有 Herdr bootstrap、startup update、foreground attach 聚焦测试通过。
- 报告中明确真实 ETW 观测未运行，或列出 ETW 运行结果。

## 状态与未决

- 状态：implemented，待收尾确认。
- 已实施：
  - `process_background.no_window_process_kwargs()` 作为非 UI 短命令隐藏 helper。
  - Herdr status / capability / session discovery 三类启动热路径 read probe 使用 no-window helper。
  - startup update 后台刷新复用 `background_process_kwargs()`。
  - `start_foreground._subprocess_kwargs_herdr_ui()` 注释明确只隐藏控制包装，WezTerm / Herdr attach 仍是 intentional-visible UI。
- 验证：
  - `python -m pytest -q "test/test_herdr_bootstrap.py" "test/test_cli_startup_update.py::test_schedule_background_update_refresh_creates_lock_and_spawns_internal_command" "test/test_v2_start_foreground.py" "test/test_ccbd_process_env.py"` -> 77 passed。
- 观察：
  - 曾运行 `python -m pytest -q "test/test_cli_startup_update.py" "test/test_v2_start_foreground.py" "test/test_ccbd_process_env.py"`；其中 `test/test_cli_startup_update.py` 多项 release-update prompt 测试在当前 Windows/source-dev 环境下未进入更新路径，表现为既有平台/环境假设失败。本次改动相关的后台刷新测试单独通过。
- 未决：`.cmd` 替代入口属于用户体验取舍，本轮不自动选择默认方案。
- 未决：真实 `ccb8` 一键 ETW 复现会打开外部 UI 并可能清理旧 runtime，本轮不自动执行。
