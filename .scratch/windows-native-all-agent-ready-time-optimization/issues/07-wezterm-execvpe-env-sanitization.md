# 07：WezTerm current_pane_exec 环境净化与输入失效修复

- Type: `task`
- Status: `completed`（2026-08-27 实施完成，54/54 测试通过）
- 日期：2026-08-27
- 关联 spec：`.scratch/windows-native-all-agent-ready-time-optimization/spec.md`
- 关联 issue：`.scratch/windows-native-all-agent-ready-time-optimization/issues/06-wezterm-frontend-handoff.md`
- 关联 fix-plan：`.scratch/windows-native-all-agent-ready-time-optimization/fix-plan/wezterm-foreground-input-integrated-fix-plan.md`
- 关联术语：`CONTEXT.md`（`Frontend Surface`、`attach`、`Runtime Binding`、`managed 模式`）
- 关联 ADR：`docs/adr/0001-三层运行时权威边界.md`、`docs/adr/0003-windows-native-all-agent-ready-time-optimization.md`

---

## Problem Statement

WezTerm tab 内运行 `ccb` 后，当前 tab 能进入 Herdr UI（无额外 tab 残留的目标已实现），但 **键盘无法正常输入、鼠标点击无法响应、鼠标滚轮产生异常字符泄漏到 `codex2api` pane**。在新 WezTerm tab 中直接运行 `herdr session attach <session>` 键盘/鼠标均正常，且在旧版 2-tab 模式（`wezterm cli spawn` + PowerShell 拼接）下也工作正常。

这说明问题集中在 `current_pane_exec` 路径：`os.execvpe(herdr_exe, command, os.environ)` 透传了原始 `os.environ`，未做任何环境净化，且未复位终端模式，导致 `herdr` 进程继承了 CCB wrapper 环境中的 TMUX/PYTHON/CCB 残留变量和异常终端模式（鼠标报告、bracketed paste 等），造成输入失效。

## Solution

在 `_replace_current_wezterm_pane_with_herdr_ui()` 中引入环境净化函数 `_clean_herdr_exec_env()`，对传递給 `execvpe` 的环境做白名单过滤——只保留 Windows 基础变量和 WezTerm 必要变量，移除高风险残留变量（TMUX、PYTHON\*、非必要 CCB\* 等）。

如果环境净化后故障仍未完全解决，追加第二阶段修复：在 `execvpe` 前输出最小终端复位序列（关闭鼠标报告、退出 bracketed paste、恢复光标显示），并加入同步等待确保复位生效。

同时新增诊断开关 `--foreground-tabs 1|2` 和实机差分脚本，使修复效果可量化验证。

## User Stories

1. 作为 CCB 用户在 WezTerm 内启动 `ccb` 后，我希望 Herdr UI 在当前 tab 正常显示，并且**键盘输入能正确被 Herdr 消费**，以便向 agent 发送指令。
2. 作为 CCB 用户，我希望 Herdr UI 中的**鼠标点击能正常响应**（选择 pane、激活输入框等），以便使用 TUI 界面进行导航。
3. 作为 CCB 用户，我希望**鼠标滚轮不会产生异常字符泄漏到 agent pane**，以便正常滚动 Herdr UI 的内容。
4. 作为 CCB 用户，我希望**首次启动和重复启动行为一致**，不会出现第一次正常、第二次异常的随机故障。
5. 作为开发者，我希望有一个**诊断开关**（`--foreground-tabs 1` vs `--foreground-tabs 2`），以便在 WezTerm 环境中强制切换启动模式，快速验证不同路径下的输入行为。
6. 作为开发者，我希望有一个**自动化差分脚本**能采集 1-tab 和 2-tab 两种模式下的 pane 列表、进程树、屏幕文本和输入探针去向，以便量化评估修复效果。
7. 作为开发者，我希望差分脚本的 `summary.md` 能包含**人工点击复核**的强制记录栏，因为自动化 SGR 探针不能完全覆盖真实鼠标行为。
8. 作为维护者，我希望修复期间保留 H2-H5 假设的监视记录（Herdr input mode 转发、frontend binding 错误、attach_namespace 竞争、终端兼容性），以便在触发条件变化时重新排查。
9. 作为维护者，我希望 2-tab 模式（`--foreground-tabs 2`）在修复后仍能正常工作，确保修复不引入退化。

## Implementation Decisions

### 修改范围

修改只限制在 `lib/cli/services/start_foreground.py` 中的以下函数：

1. **新增 `_clean_herdr_exec_env()`** — 从原始 `os.environ` 中过滤出白名单变量，返回净化后的环境字典。
2. **修改 `_replace_current_wezterm_pane_with_herdr_ui()`** — 在 `runner.execvpe()` 调用处将 `os.environ` 替换为 `_clean_herdr_exec_env()` 的返回值。
3. **新增 `_foreground_tabs_override()`** — 从环境变量 `CCB_FOREGROUND_TABS` 读取诊断开关值，返回 `int | None`。
4. **修改 `_launch_herdr_ui()`** — 在调度入口处调用 `_foreground_tabs_override()`，按诊断开关值强制走对应分支。
5. 可选第二阶段：**终端复位** — 在 `execvpe` 前通过 `sys.stdout.write()` 输出复位序列，然后 `time.sleep(0.1)` 或发送 DSR 等待。

### 环境净化白名单

```python
_KEEP_ENV_KEYS = {
    # Windows 系统基础
    'PATH', 'SystemRoot', 'ComSpec', 'PATHEXT',
    'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP',
    # 终端标识
    'TERM', 'TERM_PROGRAM', 'COLORTERM',
    # WezTerm 运行时必要
    'WEZTERM_PANE', 'WEZTERM_UNIX_SOCKET', 'WEZTERM_EXECUTABLE',
    'WEZTERM_EXECUTABLE_DIR',
    # Herdr 启动必需
    'CCB_HERDR_EXE',
    # 编码与语言
    'LANG', 'LC_ALL', 'LC_CTYPE',
}
```

### 诊断开关取值规则

`--foreground-tabs` 的剥离全部在 `ccb.py` 中实现，`ccb.cmd` 不做任何参数改写，仅透传全部参数给 `ccb.py`。

- 未设置（`None`）：保留当前 `_launch_herdr_ui()` 默认策略
- `1`：强制当前 pane exec 路径，不在 WezTerm pane 内时返回 `frontend_not_ready`
- `2`：强制 spawn 路径，WezTerm mux 不可用时记录 fallback reason

### 变更新增的 frontend fact 字段

- `requested_tabs` — 诊断开关值（`1` 或 `2`）
- `origin_pane_id` — 命令启动 pane
- `target_pane_id` — Herdr UI 最终落点
- 已有字段继续沿用

## Testing Decisions

### 测试原则

测试只验证外部行为，不验证实现细节：

- 对于 `_clean_herdr_exec_env()`：只验证输入环境 → 输出环境字典的映射正确性（哪些变量保留、哪些移除）
- 对于 `_foreground_tabs_override()`：只验证环境变量值 → 返回值的映射
- 对于 `_replace_current_wezterm_pane_with_herdr_ui()`：验证 `execvpe_fn` 接收到的 env 是净化后的版本
- 对于 `_launch_herdr_ui()`：验证诊断开关值不同时走不同分支

### Seam

唯一的 seam 是 `test/test_v2_start_foreground.py`，继续使用现有的 `HerdrFrontendCommandRunner` 注入模式。不新增 seam。

### 新增测试

**开关调度测试：**

- `test_launch_herdr_ui_forces_current_pane_when_foreground_tabs_is_one` — 注入 `execvpe_fn`，设置环境变量为 1，验证走 current_pane_exec
- `test_launch_herdr_ui_rejects_one_tab_when_not_in_wezterm_pane` — 注入 `execvpe_fn` 无 pane 环境，验证返回 frontend_not_ready
- `test_launch_herdr_ui_forces_spawn_when_foreground_tabs_is_two` — 注入 `run_fn`，设置环境变量为 2，验证走 wezterm_spawn
- `test_launch_herdr_ui_records_requested_tabs_in_frontend_fact` — 验证 fact 中包含 requested_tabs 字段

**环境净化测试：**

- `test_replace_current_pane_exec_uses_clean_herdr_env` — 注入 `execvpe_fn`，捕获 env，验证不含 TMUX/PYTHONHOME
- `test_replace_current_pane_exec_removes_tmux_and_python_env` — 注入携带 TMUX/PYTHON 的 os.environ，验证被移除
- `test_replace_current_pane_exec_keeps_wezterm_socket` — 注入携带 WEZTERM 变量的 os.environ，验证被保留

**`_clean_herdr_exec_env()` 纯函数测试：**

- 正向：输入包含白名单和非白名单变量 → 只输出白名单变量
- TMUX 移除：输入包含 TMUX → 输出不包含 TMUX
- 空输入：输入空字典 → 输出空字典
- 边界：输入只含白名单变量 → 输出与输入一致

**`ccb.cmd` 验证：**

- `.\ccb.cmd --foreground-tabs 1 --help` 不把开关传给普通 parser
- `.\ccb.cmd --foreground-tabs=2 --help` 能设置环境变量后剥离开关
- `.\ccb.cmd --foreground-tabs 3` 返回清晰错误

**回归验证（手动）：**

- `--foreground-tabs 2`（wezterm_spawn 路径）运行两次确认无退化
- 实机差分脚本确认 1-tab 输入正常、2-tab 输入正常

### 先例

现有测试使用以下模式，新测试保持风格一致：

- `test_launch_herdr_ui_replaces_current_wezterm_pane_without_spawning` — 通过 `execvpe_fn` 注入验证函数按预期调用
- `test_launch_herdr_ui_uses_injected_runner_without_real_processes` — 通过注入 runner 避免真实进程

## Out of Scope

- **H2-H5 的正式修复**：H2（Herdr input mode）、H3（frontend binding 指向错误）、H4（attach_namespace 竞争）、H5（终端兼容性）在当前诊断中已排除为主因，仅在监视状态下记录备查。触发条件变化时重新排查。
- **非 WezTerm 终端的行为验证**：Conhost/Windows Terminal 中启动 `ccb` 不在本次修复范围，旧有 fallback 行为不变。
- **Herdr 自身输入处理逻辑修改**：Herdr 在新 tab 中工作正常，不在 CCB 侧修复 Herdr。
- **tmux 路径行为修改**：非 Herdr backend 的 `attach_started_project_namespace()` 函数（tmux 路径）操作不变。

## Further Notes

### 诊断设计树摘要

本次修复基于 2026-08-27 完成的设计树诊断（共 14 个追问轮次，覆盖全部 5 个假设）：

- **H1 确认根因**：代码 L582 `runner.execvpe(herdr_exe, command, os.environ)` 直接传递原始环境
- **H2-H5 记录监视**：证据确凿排除为主因，但不排除作为次要因素回归

完整诊断树记录在 `fix-plan/wezterm-foreground-input-integrated-fix-plan.md` 的「诊断设计树」章节。

### 实施顺序

1. 新增 `--foreground-tabs` 诊断开关（剥离在 `ccb.py`）
2. 新增实机差分脚本（超时 60s，含人工复核强制栏）
3. 实现环境净化（第一阶段）
4. 实机验证：运行差分脚本 1-tab/2-tab 对照
5. 如需，追加终端复位（第二阶段）
6. 二阶段实机验证
7. 回归测试 + 清理
