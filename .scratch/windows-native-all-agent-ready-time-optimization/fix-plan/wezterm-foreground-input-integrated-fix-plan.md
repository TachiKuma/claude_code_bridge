# 综合修复方案：WezTerm 前台 tab 模式对照与 Herdr 输入失效修复

- 状态：`diagnosed-H1-confirmed`
  （诊断完成：2026-08-27，设计树共 14 个问题，H1 确认为根因，H2-H5 记录监视，见下方「诊断设计树」）
- 日期：2026-08-27
- 来源方案：
  - `.scratch/windows-native-all-agent-ready-time-optimization/fix-plan/wezterm-foreground-tabs-differential-diagnosis-fix.md`
  - `.scratch/windows-native-all-agent-ready-time-optimization/fix-plan/wezterm-execvpe-input-conflict-fix.md`
- 关联 spec：`.scratch/windows-native-all-agent-ready-time-optimization/spec.md`
- 关联任务：`.scratch/windows-native-all-agent-ready-time-optimization/issues/06-wezterm-frontend-handoff.md`
- 关联 ADR：`docs/adr/0001-三层运行时权威边界.md`、`docs/adr/0003-windows-native-all-agent-ready-time-optimization.md`
- 关联提交：`176b674e` 修复 WezTerm 前台 socket 复用与 Herdr 输入定位
- 关联代码：`ccb.cmd`、`lib/cli/services/start_foreground.py`、`test/test_v2_start_foreground.py`

---

## 一句话结论

**H1 已确认为根因**：`current_pane_exec` 路径中的 `os.execvpe` 透传了原始 `os.environ`（未做任何环境净化），且未复位终端模式，导致 herdr 进程继承了 CCB wrapper 环境中的 TMUX/PYTHON/CCB 残留变量和异常终端模式（鼠标报告、bracketed paste 等），造成输入失效。

证据链：

- WezTerm 新 tab 中直接运行 `herdr session attach <session>` **键盘/鼠标均正常** → 排除 H2/H5 作为主因
- `--foreground-tabs 1`（走 `execvpe` 路径）**100% 复现输入故障** → 确认 H1
- 旧版 2-tab 模式（`wezterm cli spawn` + PowerShell 拼接）**工作正常** → 进一步确认环境继承而非 Herdr 本身的问题
- 代码第 582 行确认为 `runner.execvpe(herdr_exe, command, os.environ)`，直接传递原始环境

故障每次启动均复现，排除了竞态条件（H4）和 frontend binding 复用错误（H3）作为主因的可能性。

修复方向：先实施环境净化（第一阶段），如仍不足则追加终端复位（第二阶段）。其他假设（H2-H5）记录存盘并持续监视，不直接排除。

---

## 当前问题

实机现象：

1. 在 WezTerm tab 内运行 `ccb` 后，当前 tab 能进入 Herdr UI，且无额外 tab 残留这一目标已基本实现。
2. Herdr UI 可见，但键盘无法正常输入，鼠标点击无法正常响应。
3. 鼠标滚轮有反应，但会在 `codex2api` pane 的输入框出现无法识别的字符。
4. 用户体感像是 Herdr 的用户交互被其他软件或其他 pane 抢走。

这说明问题已经从“前台是否 attach”升级为“前台 attach 后输入是否落到正确控制层”。后续修复不能只检查 tab 数或进程是否存在，必须检查输入事件最终被谁消费。

---

## 已知实现事实

1. `ccb.cmd` 当前只负责选择 Python、设置 `CCB_SOURCE_RUNTIME_OK=1`，然后把参数原样传给 `ccb.py`。
2. `start_foreground.py` 的 Herdr 前台展示有三条路径：
   - `current_pane_exec`：当前在 WezTerm pane 中时，用 `os.execvpe` 把 CCB Python 进程替换成 `herdr session attach <session>`。
   - `wezterm_spawn`：不交接当前 pane 时，通过 `wezterm cli spawn --cwd <cwd> -- herdr session attach <session>` 新建 Herdr UI tab。
   - `detached_fallback`：WezTerm 不可用时，打开独立 Herdr 控制台窗口。
3. `176b674e` 已补充 `wezterm_socket` 的记录和复用，使 `wezterm cli list / activate-pane / spawn` 能针对正确 mux socket 运行。
4. `current_pane_exec` 当前仍直接把 `os.environ` 交给 `runner.execvpe(...)`。该路径继承 CCB wrapper 环境、进程上下文、标准输入输出和当前终端模式，是输入异常的高优先级嫌疑点。
5. 但仅凭现象不能直接认定 `execvpe` 是根因。若 `wezterm_spawn` 同样复现输入泄漏，问题更可能在 Herdr attach/input mode、frontend binding 指向或二次 attach 竞争。

---

## 不变量

本修复必须遵守以下边界：

1. **WezTerm 是前台事实源**：只提供 window/tab/pane/workspace/socket 等可见性事实，不提供业务完成判定。
2. **Herdr 是运行时事实源**：Herdr UI 的工作状态和输入消费属于运行时事实，不能被 CCB 业务状态覆盖。
3. **CCB 是业务完成权威**：`--foreground-tabs` 只影响前台 attach 形态，不影响 ready gate、provider runtime、job completion 或 agent 业务判定。
4. **不得靠标题或 tab 数猜测身份**：只能使用 `Runtime Binding.frontend`、WezTerm JSON、pane 集合差分、Herdr session 事实和输入探针结果。
5. **失败必须可观测**：强制 `1-tab` 如果不在当前 WezTerm pane 中，必须显式失败；强制 `2-tab` 如果 mux 不可用，也必须显式记录降级或失败，不能伪装成功。

---

## 目标验收

最终验收分两层：

1. **诊断验收**：能用一条脚本命令稳定跑出 `1-tab` 与 `2-tab` 两种启动形态的差分报告，报告中包含 pane、socket、frontend binding、进程树、屏幕文本和输入探针去向。
2. **修复验收**：默认 WezTerm 内运行 `.\ccb.cmd` 后，当前 tab 进入 Herdr UI，无额外 UI tab 残留；键盘输入、鼠标点击、鼠标滚轮都由 Herdr UI 正常处理，不泄漏到 `codex2api` 或其他 agent pane。

---

## 阶段 1：增加诊断开关

### 命令入口

支持：

```powershell
.\ccb.cmd --foreground-tabs 1
.\ccb.cmd --foreground-tabs=1
.\ccb.cmd --foreground-tabs 2
.\ccb.cmd --foreground-tabs=2
```

含义：

- `1`：强制当前 WezTerm pane 交接给 `herdr session attach <session>`。
- `2`：强制跳过当前 pane 交接，走 `wezterm cli spawn` 新建 Herdr UI tab。
- 未提供：保持现有默认行为。

### `ccb.cmd` 侧要求

`ccb.cmd` 负责识别并剥离 `--foreground-tabs`，设置 `CCB_FOREGROUND_TABS=1|2`。

要求：

- 只接受 `1` 或 `2`。
- 非法值返回清晰错误。
- 不把 `--foreground-tabs` 传给普通 CLI parser。
- 尽量不破坏已有引号和参数转发语义。
- 如果 batch 中做完整参数重写风险过高，可在 `ccb.py` 增加早期剥离保护，但用户入口仍是 `.\ccb.cmd --foreground-tabs ...`。

### `start_foreground.py` 侧要求

新增小函数：

```python
def _foreground_tabs_override(env: Mapping[str, str]) -> int | None:
    ...
```

调度规则：

1. `None`：保留当前 `_launch_herdr_ui()` 默认策略。
2. `1`：必须能判定当前进程在 WezTerm pane 内，才走 `_replace_current_wezterm_pane_with_herdr_ui()`；否则返回 `frontend_not_ready`，原因使用 `foreground_tabs_1_requires_current_wezterm_pane`。
3. `2`：即使当前进程在 WezTerm pane 内，也跳过 `_replace_current_wezterm_pane_with_herdr_ui()`，直接进入 `wezterm_spawn` 分支；如果 WezTerm mux 不可用，记录明确 fallback reason。

建议在 frontend fact 中增加诊断字段：

- `requested_tabs`
- `origin_pane_id`
- `target_pane_id`
- `wezterm_socket`
- `launch_mode`
- `previous_frontend_probe_status`
- `previous_frontend_probe_reason`

---

## 阶段 2：建立实机差分反馈环

新增脚本：

`scripts/diagnostics/wezterm-foreground-tabs-compare.ps1`

目标命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnostics\wezterm-foreground-tabs-compare.ps1 -RepoRoot "E:\GitHub开源项目\TachiKuma\NativeWin_CCB_Herdr"
```

输出目录：

`.scratch/windows-native-all-agent-ready-time-optimization/fix-plan/runs/<timestamp>/`

### WezTerm 解析

脚本解析 `wezterm.exe` 的顺序：

1. 当前环境的 `WEZTERM_EXECUTABLE`。
2. 当前环境的 `WEZTERM_EXECUTABLE_DIR`。
3. PATH。
4. `%LOCALAPPDATA%\Programs\WezTerm\wezterm.exe`。
5. `%ProgramFiles%\WezTerm\wezterm.exe`。

原因：当前 agent shell 中 `wezterm` 不在 PATH，不能假定非 WezTerm 环境能直接运行 `wezterm`。

### 对照采集

每个模式都采集：

- `wezterm-list-before.json`
- `mode-<n>-list-after.json`
- `mode-<n>-frontend.json`
- `mode-<n>-pane-text.txt`
- `mode-<n>-pane-text-escapes.txt`
- `mode-<n>-process.csv`
- `mode-<n>-input-probe.txt`
- `summary.md`

其中 `process.csv` 至少包含 `wezterm-gui.exe`、`wezterm.exe`、`cmd.exe`、`powershell.exe`、`python.exe`、`herdr.exe` 的 PID、PPID、可执行路径、脱敏 command line。

### 1-tab 流程

1. 用 `wezterm cli spawn --cwd <repo> -- powershell.exe -NoLogo` 新建诊断命令 pane。
2. 记录该 pane 为 `origin_pane_id`。
3. 用 `wezterm cli send-text --pane-id <origin_pane_id> --no-paste ".\ccb.cmd --foreground-tabs 1`r"` 启动。
4. 等待 Herdr UI 可见。
5. 采集 frontend fact、pane 列表、进程树、屏幕文本。
6. 向同一 pane 发送普通文本、SGR 点击、SGR 滚轮探针。
7. 再次采集屏幕文本和转义序列。

预期事实：

- `origin_pane_id` 仍存在。
- `target_pane_id == origin_pane_id`。
- `launch_mode == current_pane_exec`。
- 不出现新的 Herdr UI pane。

### 2-tab 流程

1. 新建另一个诊断命令 pane。
2. 记录该 pane 为 `origin_pane_id`。
3. 用 `wezterm cli send-text --pane-id <origin_pane_id> --no-paste ".\ccb.cmd --foreground-tabs 2`r"` 启动。
4. 通过 pane 集合差分和 frontend fact 找出 `target_pane_id`。
5. 对 `target_pane_id` 发送同样的普通文本、SGR 点击、SGR 滚轮探针。
6. 采集同结构证据。

预期事实：

- `origin_pane_id` 和 `target_pane_id` 同时存在。
- `target_pane_id != origin_pane_id`。
- `launch_mode == wezterm_spawn`。
- 命令 tab + UI tab 两种前台事实都可观察。

### 输入探针

探针分三类：

1. 普通键盘文本：确认键盘输入最终落点。
2. SGR 点击序列：确认点击事件是否被 Herdr UI 消费或泄漏到 agent pane。
3. SGR 滚轮序列：复现用户报告中“滚轮有反应但异常字符进入 `codex2api`”的关键现象。

自动化探针不能完全替代人工点击。若 CLI 结果不够明确，`summary.md` 必须追加人工复核记录，包含具体时间、模式、点击位置、观察到的 pane。

---

## 阶段 3：差分判定矩阵

`summary.md` 至少填以下矩阵：

| 字段                      | 1-tab | 2-tab | 判定用途                             |
| ------------------------- | ----- | ----- | ------------------------------------ |
| `requested_tabs`          |       |       | 开关是否生效                         |
| `launch_mode`             |       |       | 是否真的走不同路径                   |
| `origin_pane_id`          |       |       | 命令 pane                            |
| `target_pane_id`          |       |       | Herdr UI 最终落点                    |
| `window_id` / `workspace` |       |       | 是否同一 mux / workspace             |
| `wezterm_socket`          |       |       | socket 是否一致                      |
| 新增 pane 数              |       |       | 1-tab 不应新增 UI pane，2-tab 应新增 |
| `herdr.exe` PID/PPID      |       |       | `execvpe` 与 `spawn` 的进程模型差异  |
| frontend binding          |       |       | 持久化是否指向正确 pane              |
| 普通文本探针去向          |       |       | 键盘输入是否泄漏                     |
| SGR 点击探针去向          |       |       | 点击是否泄漏                         |
| SGR 滚轮探针去向          |       |       | 是否匹配用户报告                     |
| 人工点击复核              |       |       | CLI 无法覆盖的真实鼠标行为           |

---

## 诊断设计树（2026-08-27 完成）

本次诊断共 14 个问题，覆盖全部 5 个假设。设计树收敛情况如下：

### 假设状态总表

| 假设                                  | 优先级       | 结论         | 依据                                            |
| ------------------------------------- | ------------ | ------------ | ----------------------------------------------- |
| **H1** `current_pane_exec` 继承污染   | **确认根因** | 修复中       | `execvpe` 透传原始 `os.environ`，代码 L582 确证 |
| **H2** Herdr attach/input mode        | **监视**     | 已排除为主因 | 新 tab `herdr session attach` 正常              |
| **H3** frontend binding 指向错误 pane | **监视**     | 已排除为主因 | 故障每次启动均复现，非重复启动场景              |
| **H4** `attach_namespace` 竞争        | **监视**     | 已排除为主因 | `execvpe` 成功后旧进程不复存在，竞争窗口不成立  |
| **H5** 终端/WezTerm 兼容性            | **监视**     | 已排除为主因 | 新 tab `herdr session attach` 正常              |

### 设计树问答纪要

| Q#  | 主题                | 结论                                                                                     |
| --- | ------------------- | ---------------------------------------------------------------------------------------- |
| Q1  | 输入探针局限性      | 使用建议：增加 `get-text --escapes` 对比 + 人工复核强制化                                |
| Q2  | Herdr 工作基线      | 新 tab `herdr session attach` 键盘/鼠标正常 → 排除 H2/H5                                 |
| Q3  | 终端复位竞态        | 使用建议：复位后加 `sleep 100ms` 或 DSR 等待                                             |
| Q4  | batch 参数剥离      | 使用建议：全部在 `ccb.py` 做剥离，batch 仅透传                                           |
| Q5  | pane vs tab 激活    | 方案缺失：`activate-pane` 跨 tab 行为依赖 WezTerm 版本，`existing_frontend_reuse` 需兜底 |
| Q6  | H4 竞争窗口分解     | `execvpe` 路径无竞争窗口；`wezterm_spawn` 路径有秒级窗口                                 |
| Q7  | 诊断脚本超时        | 使用建议：超时 60s，发 Ctrl+C，记录 `timed_out`                                          |
| Q8  | 旧版 2-tab 实现方式 | 之前通过 `wezterm cli spawn` + PowerShell 拼接，工作正常 → 进一步确认 H1                 |
| Q9  | 故障复现率          | `--foreground-tabs 1` 100% 复现 → 确定性 bug，非竞态                                     |
| Q10 | 重复启动表现        | 每次启动均复现 → 排除 H3（existing_frontend）作为主因                                    |
| Q11 | 环境变量检查        | 无法现场检查，但高概率 `TMUX`/`TMUX_PANE` 残留                                           |
| Q12 | 终端复位分阶段      | 使用建议：先环境净化，仍不足再追加终端复位                                               |
| Q13 | 2-tab 回归测试      | 立即验证，确认修复不退步                                                                 |
| Q14 | H4 可排除性         | 同意 H4 排除，但 H2-H5 需记录监视                                                        |

### H2-H5 监视条目（存档备查）

以下假设虽已排除为主因，但不排除在特定场景下作为**次要因素或回归触发点**出现。

#### H2：Herdr attach/input mode 把输入转发给内部 agent pane（监视中）

当前证据：新 tab `herdr session attach` 正常。触发条件未满足，如发现 paddle 持续运行后某次测试出现输入泄漏时重新排查。

#### H3：frontend binding 指向错误 pane（监视中）

当前证据：故障每次启动均复现，非重复启动/复用场景。但 `existing_frontend_reuse` 路径（`_probe_existing_herdr_frontend`）的 `activate-pane` 跨 tab/跨 window 行为未经实机验证，作为已知边界风险存盘。

#### H4：前台 UI attach 与 `attach_namespace` 竞争（监视中）

当前证据：`execvpe` 成功后旧进程不复存在。但 `wezterm_spawn` 路径中，`ccb.py` 进程在 spawn 后继续运行并调用 `attach(namespace_ref, ...)`（代码 L273），存在秒级竞争窗口。该路径在 1-tab 作为默认模式后为非活跃路径，如未来恢复 2-tab 为默认或备选路径时需重新评估。

#### H5：WezTerm 或终端鼠标协议兼容问题（监视中）

当前证据：新 tab `herdr session attach` 正常。如 WezTerm 版本更新或 Herdr 修改初始化序列时重新排查。

---

## 阶段 4：测试计划

### 开关与调度测试

新增或调整 `test/test_v2_start_foreground.py`：

- `test_launch_herdr_ui_forces_current_pane_when_foreground_tabs_is_one`
- `test_launch_herdr_ui_rejects_one_tab_when_not_in_wezterm_pane`
- `test_launch_herdr_ui_forces_spawn_when_foreground_tabs_is_two`
- `test_launch_herdr_ui_records_requested_tabs_in_frontend_fact`

### 环境净化修复测试（H1 已确认，立即实施）

- `test_replace_current_pane_exec_uses_clean_herdr_env`
- `test_replace_current_pane_exec_removes_tmux_and_python_env`
- `test_replace_current_pane_exec_keeps_wezterm_socket`
- `test_replace_current_pane_exec_resets_terminal_modes`（仅第二阶段启用）

### frontend binding 测试（H3 监视中，暂缓实施，备查）

待出现 H3 触发条件时新增：

- legacy binding 缺少 `wezterm_socket` 时重建。
- pane 不存在时不 activate。
- workspace 不匹配时不复用。
- `window_id` 改变但 socket/workspace/pane 可验证时仅作诊断，不直接判错。

### `ccb.cmd` 验证

至少覆盖：

- `.\ccb.cmd --foreground-tabs 1 --help` 不把开关传给普通 parser。
- `.\ccb.cmd --foreground-tabs=2 --help` 能设置环境变量后剥离开关。
- `.\ccb.cmd --foreground-tabs 3` 返回清晰错误。

### 回归验证（强制）

- `--foreground-tabs 2`（wezterm_spawn 路径）运行两次验证不退化
- `pytest -q test/test_v2_start_foreground.py` 全部通过
- 实机差分脚本确认 1-tab 输入正常、2-tab 输入正常

---

## 阶段 5：实施顺序

1. **诊断开关**：新增 `--foreground-tabs`，剥离逻辑全部在 `ccb.py` 实现，`ccb.cmd` 仅透传。
2. **差分脚本**：新增 `scripts/diagnostics/wezterm-foreground-tabs-compare.ps1`，超时默认 60s，发 Ctrl+C 并记录 `timed_out`；输入探针增加 `get-text --escapes` 对比 + 人工复核强制化。
3. **环境净化**：实现 `_clean_herdr_exec_env()`，先做最小环境净化，不改终端模式。
4. **第一阶段实机验证**：运行差分脚本 1-tab / 2-tab 对照，确认键盘/鼠标输入正常。
5. **终端复位**（如需）：若环境净化不足，追加复位序列 + DSR 等待（复位后 100ms 间隔确保生效）。
6. **第二阶段实机验证**：重跑差分脚本确认原始故障消除。
7. **回归测试**：`--foreground-tabs 2` 运行两次确认无退化；`pytest` 全量通过。
8. **清理**：清理临时调试日志；标记 `--foreground-tabs` 为隐藏诊断开关。

---

## 风险与缓解

| 风险                              | 缓解                                                        |
| --------------------------------- | ----------------------------------------------------------- |
| 环境净化过度导致 Herdr 找不到依赖 | 采用保守删除列表，保留 Windows 基础变量和必要 `WEZTERM_*`   |
| 终端复位破坏 Herdr 初始化         | 先只在 H1 证实后启用，复位序列保持最小，并由实机脚本验证    |
| `ccb.cmd` 参数重写破坏引号        | 优先小范围剥离；必要时在 `ccb.py` 加早期保护                |
| 自动化探针不能覆盖真实鼠标        | `summary.md` 增加人工点击复核栏，强制化非可选               |
| 2-tab 正常诱导放弃 1-tab 目标     | 2-tab 只作为对照或临时降级，默认目标仍是当前 tab 可正常交接 |
| H2-H5 未确认但未来可能回归        | 已在诊断设计树中记录监视条目，触发条件变化时重新排查        |

---

## 本方案取舍

本方案吸收两份草案的重点：

1. 从 `wezterm-foreground-tabs-differential-diagnosis-fix.md` 保留 `--foreground-tabs` 开关、WezTerm CLI 直接驱动 pane、结构化采集和差分矩阵。
2. 从 `wezterm-execvpe-input-conflict-fix.md` 保留 `execvpe` 环境污染、终端模式残留、环境净化、终端复位和 spawn 备选修复。
3. **诊断设计树已收敛**：经 14 个问询轮次确定 H1 为根因，H2-H5 均已记录监视条目并存盘备查。
4. 任何修复都必须回到输入探针与真实 UI 验收：差分脚本优先于修复实施。
