# 修复方案：WezTerm 1-tab / 2-tab 前台输入失效对照诊断

- 状态：`draft`，待审核
- 日期：2026-08-27
- 关联 spec：`.scratch/windows-native-all-agent-ready-time-optimization/spec.md`
- 关联任务：`.scratch/windows-native-all-agent-ready-time-optimization/issues/06-wezterm-frontend-handoff.md`
- 关联 ADR：`docs/adr/0001-三层运行时权威边界.md`、`docs/adr/0003-windows-native-all-agent-ready-time-optimization.md`
- 关联提交：`176b674e` 修复 WezTerm 前台 socket 复用与 Herdr 输入定位
- 关联代码：`ccb.cmd`、`lib/cli/services/start_foreground.py`、`test/test_v2_start_foreground.py`

---

## 目标

先增加一个可审核的诊断开关，让 `.\ccb.cmd` 能强制指定前台启动形态：

- `--foreground-tabs 1`：强制当前 WezTerm pane 交接给 `herdr session attach <session>`，目标是启动后只剩当前 tab 中的 Herdr UI。
- `--foreground-tabs 2`：强制跳过当前 pane 交接，改走 `wezterm cli spawn` 新建 Herdr UI tab，目标是保留命令 tab + UI tab 两个 tab。

审核通过后，再用 WezTerm CLI 直接向 pane 发送命令，分别实机启动两种模式并采集证据，比较差异后选择修复。本文只落方案，不实施代码修改，不启动实机对照。

---

## 已知事实

1. `ccb.cmd` 当前只是 Windows 源码 checkout 的 Python wrapper：解析 Python、设置 `CCB_SOURCE_RUNTIME_OK=1`，随后把 `%*` 原样交给 `ccb.py`，没有任何前台 tab 模式开关。
2. `start_foreground.py` 中 `_launch_herdr_ui()` 当前有三条前台路径：
   - 当前处于 WezTerm pane：调用 `_replace_current_wezterm_pane_with_herdr_ui()`，最终 `execvpe(herdr, ["herdr", "session", "attach", session])`。
   - 不在当前 WezTerm pane，但 WezTerm mux 可用：调用 `_run_wezterm_spawn()`，执行 `wezterm cli spawn --cwd <cwd> -- herdr session attach <session>`。
   - WezTerm 不可用：调用 detached fallback，打开独立 Herdr 控制台窗口。
3. `176b674e` 已修复 `WEZTERM_UNIX_SOCKET` 的记录与复用，`wezterm cli list / activate-pane / spawn` 已能带着目标 socket 执行。
4. 当前 `execvpe` 路径仍直接把 `os.environ` 传给 Herdr。该路径会保留当前进程的标准输入输出、进程上下文和终端状态，是最需要和 `wezterm_spawn` 做差分验证的路径。
5. 用户实机现象是：Herdr UI 可见，但键盘输入和鼠标点击不按 Herdr UI 预期响应；滚轮有反应；异常字符出现在 `codex2api` pane 的输入框。这说明“前台可见”已经不等于“输入路由正确”，必须把输入探针纳入验收。
6. 当前 agent shell 中 `wezterm` 不在 PATH。后续实机脚本必须复用目标 pane 内的 `WEZTERM_EXECUTABLE` / `WEZTERM_EXECUTABLE_DIR`，或按常见安装目录解析 `wezterm.exe`，不能假定全局 PATH 可用。

---

## 诊断反馈环

审核通过后，新增一个只用于诊断的脚本，建议路径：

`scripts/diagnostics/wezterm-foreground-tabs-compare.ps1`

目标是一条 agent 可运行的命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnostics\wezterm-foreground-tabs-compare.ps1 -RepoRoot "E:\GitHub开源项目\TachiKuma\NativeWin_CCB_Herdr"
```

该命令必须产出一个对照目录：

`.scratch/windows-native-all-agent-ready-time-optimization/fix-plan/runs/<timestamp>/`

每轮至少采集：

- `wezterm-list-before.json`：启动前 `wezterm cli list --format json`。
- `mode-1-list-after.json` / `mode-2-list-after.json`：两种模式启动后 pane/window/tab/workspace 列表。
- `mode-1-frontend.json` / `mode-2-frontend.json`：`.ccb` 中的 `Runtime Binding.frontend` 或 `ProjectNamespaceState.frontend`。
- `mode-1-pane-text.txt` / `mode-2-pane-text.txt`：Herdr UI pane 的 `wezterm cli get-text --pane-id <pane>` 输出。
- `mode-1-pane-text-escapes.txt` / `mode-2-pane-text-escapes.txt`：带 `--escapes` 的屏幕内容，用于确认鼠标协议字符是否泄漏到 agent pane。
- `mode-1-process.csv` / `mode-2-process.csv`：`Win32_Process` 中 `wezterm-gui`、`wezterm`、`cmd.exe`、`python.exe`、`herdr.exe` 的父子关系和 command line，敏感参数需脱敏。
- `mode-1-input-probe.txt` / `mode-2-input-probe.txt`：发送键盘文本和 SGR 鼠标序列前后的 pane 文本差异。
- `summary.md`：人工可读对照结论，只列事实，不提前宣判根因。

WezTerm CLI 依据官方接口使用：

- [`wezterm cli list --format json`](https://wezterm.org/cli/cli/list.html) 枚举 window/tab/pane/workspace。
- [`wezterm cli spawn --cwd <repo> -- powershell.exe -NoLogo`](https://wezterm.org/cli/cli/spawn.html) 创建可控命令 pane，成功后 stdout 返回新 pane id。
- [`wezterm cli send-text --pane-id <pane> --no-paste <text>`](https://wezterm.org/cli/cli/send-text.html) 直接向指定 pane 发送命令或输入探针。
- [`wezterm cli get-text --pane-id <pane> --escapes`](https://wezterm.org/cli/cli/get-text.html) 采集 pane 屏幕文本和转义序列。
- `wezterm cli activate-pane --pane-id <pane>` 聚焦对照 pane。

---

## 开关设计

### 命令语义

支持两种写法：

```powershell
.\ccb.cmd --foreground-tabs 1
.\ccb.cmd --foreground-tabs=1
.\ccb.cmd --foreground-tabs 2
.\ccb.cmd --foreground-tabs=2
```

该开关只影响 Windows Native Herdr 前台 attach 路径，不改变 start 业务语义、ready gate、provider runtime、Herdr 状态观测或 CCB 业务完成判定。

### `ccb.cmd` 侧

`ccb.cmd` 负责识别并剥离 `--foreground-tabs`，设置环境变量：

```bat
set "CCB_FOREGROUND_TABS=1"
```

要求：

- 只接受 `1` 或 `2`，其他值直接报错并退出。
- 该开关不传给 `ccb.py` 的正常参数解析，避免出现 unknown argument。
- 未提供开关时保持当前默认行为。
- 参数转发必须保留现有用户参数和引号语义。若 batch 中做全量重写风险过高，可以把 `ccb.py` 中的早期全局参数剥离作为保护层，但 `.\ccb.cmd --foreground-tabs ...` 必须是用户入口。

### Python 前台调度侧

在 `lib/cli/services/start_foreground.py` 增加一个小函数：

```python
def _foreground_tabs_override(env: Mapping[str, str]) -> int | None:
    ...
```

调度规则：

1. `None`：完全保留现有 `_launch_herdr_ui()` 行为。
2. `1`：当前环境必须可判定为 WezTerm pane，走 `_replace_current_wezterm_pane_with_herdr_ui()`；如果不是当前 WezTerm pane，返回 `frontend_not_ready`，原因写成 `foreground_tabs_1_requires_current_wezterm_pane`，不自动降级到 spawn。
3. `2`：即使当前环境是 WezTerm pane，也跳过 `_replace_current_wezterm_pane_with_herdr_ui()`，直接进入 `wezterm_spawn` 分支；如果 mux 不可用，记录显式失败或现有可观测 fallback，不能伪装成 2-tab 成功。

`_herdr_frontend_fact()` 建议增加诊断字段：

- `requested_tabs`: `1` 或 `2`
- `actual_launch_mode`: 复用现有 `launch_mode`，或保持 `launch_mode` 原字段并只加 `requested_tabs`
- `origin_pane_id`: 发起 `.\ccb.cmd` 的 pane
- `target_pane_id`: Herdr UI 最终 pane，1-tab 时应等于 `origin_pane_id`，2-tab 时应为新 pane

---

## 实机对照流程

### 准备

1. 用脚本解析 `wezterm.exe`：
   - 先读当前进程环境中的 `WEZTERM_EXECUTABLE`、`WEZTERM_EXECUTABLE_DIR`。
   - 再查 PATH。
   - 再查 `%LOCALAPPDATA%\Programs\WezTerm\wezterm.exe`、`%ProgramFiles%\WezTerm\wezterm.exe`。
2. 采集启动前 `wezterm cli list --format json`。
3. 记录已有 pane，后续只把本轮新建或本轮交接的 pane 作为采集对象，不按标题猜测。

### 模式 1：强制 1-tab

1. 新建一个诊断命令 pane：

```powershell
wezterm cli spawn --cwd "E:\GitHub开源项目\TachiKuma\NativeWin_CCB_Herdr" -- powershell.exe -NoLogo
```

2. 记录返回的 `origin_pane_id`。
3. 发送命令：

```powershell
wezterm cli send-text --pane-id <origin_pane_id> --no-paste ".\ccb.cmd --foreground-tabs 1`r"
```

4. 等待 Herdr UI 可见后采集 `list`、`get-text`、`frontend`、进程树。
5. 发送输入探针：

```powershell
wezterm cli send-text --pane-id <origin_pane_id> --no-paste "ccb-input-probe-1"
wezterm cli send-text --pane-id <origin_pane_id> --no-paste "$([char]27)[<0;10;10M$([char]27)[<0;10;10m"
wezterm cli send-text --pane-id <origin_pane_id> --no-paste "$([char]27)[<64;10;10M"
```

6. 再次采集 `get-text` 与 `get-text --escapes`。

验收事实：

- `origin_pane_id` 应仍存在。
- 启动后不应出现新的 Herdr UI pane。
- `frontend.launch_mode` 应为 `current_pane_exec`。
- 普通文本和鼠标序列不应泄漏到 `codex2api` 输入框；若泄漏，记录泄漏内容。

### 模式 2：强制 2-tab

1. 新建另一个诊断命令 pane，记录 `origin_pane_id`。
2. 发送命令：

```powershell
wezterm cli send-text --pane-id <origin_pane_id> --no-paste ".\ccb.cmd --foreground-tabs 2`r"
```

3. 通过 `wezterm cli list --format json` 找出新产生的 `target_pane_id`，必须依赖 pane 集合差分和 `frontend` 记录，不靠标题猜。
4. 对 `target_pane_id` 发送同样的文本与鼠标协议探针。
5. 采集和模式 1 同结构的证据。

验收事实：

- `origin_pane_id` 和 `target_pane_id` 应同时存在。
- `frontend.launch_mode` 应为 `wezterm_spawn`。
- 若 2-tab 输入正常而 1-tab 输入异常，根因优先收敛到当前 pane `execvpe` 路径。

---

## 对照矩阵

`summary.md` 必须至少填写以下字段：

| 字段                      | 1-tab | 2-tab | 判断点                                         |
| ------------------------- | ----- | ----- | ---------------------------------------------- |
| `requested_tabs`          |       |       | 开关是否生效                                   |
| `launch_mode`             |       |       | 是否真的走不同路径                             |
| `origin_pane_id`          |       |       | 命令 pane 是哪一个                             |
| `target_pane_id`          |       |       | Herdr UI 最终落点                              |
| `window_id` / `workspace` |       |       | 是否同一 mux / workspace                       |
| `wezterm_socket`          |       |       | socket 是否一致                                |
| 新增 pane 数              |       |       | 1-tab 不应新增 UI pane，2-tab 应新增           |
| `herdr.exe` 进程父子关系  |       |       | `execvpe` 与 `spawn` 的进程模型差异            |
| `frontend` 持久化结果     |       |       | binding 是否写到正确 pane                      |
| 普通文本探针去向          |       |       | 是否进入 Herdr UI 或泄漏到 agent pane          |
| SGR 点击探针去向          |       |       | 点击是否被 Herdr 消费或泄漏                    |
| SGR 滚轮探针去向          |       |       | 滚轮现象是否与用户报告一致                     |
| 人工点击复核              |       |       | CLI 无法完全替代真实鼠标，必要时只记录人工事实 |

---

## 待验证假设

按当前证据优先级排列，审核后用上述反馈环逐一证伪。

1. **当前 pane `execvpe` 路径污染了 Herdr TUI 输入环境。**  
   预测：`--foreground-tabs 2` 正常，`--foreground-tabs 1` 复现键盘/点击异常；1-tab 的 `herdr.exe` 继承了 CCB wrapper 环境、终端状态或异常进程关系。修复方向是为 `execvpe` 构造 Herdr 专用环境，并在 exec 前清理可能残留的鼠标/alternate-screen 状态。

2. **Herdr attach 后输入被转发到内部 agent pane，而不是被 Herdr UI 控制层消费。**  
   预测：两种模式都能看到普通文本或 SGR 鼠标序列进入 `codex2api` pane；差异不主要来自 `execvpe`，而是 Herdr attach/focus/input mode。修复方向需要先在 CCB 中调整 attach 方式或启动参数；若 Herdr CLI 本身缺少表达力，再形成 Herdr 上游修复项。

3. **`Runtime Binding.frontend` 或 WezTerm socket 复用仍指向错误 pane。**  
   预测：`frontend.pane_id`、`wezterm_socket`、`wezterm cli list` 中的实际 pane 不一致，或重复启动聚焦到旧 pane，导致用户输入落到非 Herdr UI。修复方向是收紧 frontend binding 的写入、探测和失效规则。

4. **`_attach_herdr_project_namespace()` 的后续 `attach_namespace` 与前台 UI attach 存在竞争。**  
   预测：2-tab 或复用路径出现两个 Herdr attach 客户端，或 workspace focus 与输入焦点状态在短时间内互相覆盖。修复方向是把“前台展示”和“后台 namespace focus/attach”分离，避免启动时产生两个可接收输入的 attach 客户端。

5. **WezTerm 版本或配置影响鼠标协议。**  
   预测：两种模式的键盘输入一致，但鼠标点击/滚轮行为随 WezTerm 配置变化而变化，`get-text --escapes` 能看到不同鼠标协议序列。修复方向是记录最低 WezTerm 版本/配置要求，或在 Herdr attach 前显式复位/启用兼容协议。

---

## 修复决策规则

1. **只有 1-tab 故障、2-tab 正常**：先修 `_replace_current_wezterm_pane_with_herdr_ui()`。
   - 添加 `_clean_herdr_exec_env()`：保留 `PATH`、`SystemRoot`、`ComSpec`、`PATHEXT`、`USERPROFILE`、`APPDATA`、`LOCALAPPDATA`、`TEMP`、`TMP`、`TERM`、`TERM_PROGRAM`、`COLORTERM`、必要的 `WEZTERM_*`；移除 `TMUX`、`TMUX_PANE`、`PYTHONHOME`、`PYTHONPATH`、非必要 `PYTHON*`、非必要 `CCB_*`。
   - 在 `execvpe` 前输出最小 ANSI reset：关闭鼠标报告、恢复光标、退出 bracketed paste。该步骤必须 guarded，避免破坏正常终端。
   - 若仍失败，评估不用 `execvpe`，改为让 WezTerm 或 Herdr 提供“当前 pane 替换/接管”能力；在能力缺失前，默认行为可临时回退 2-tab，但必须显式标注为降级。

2. **1-tab 和 2-tab 都故障**：停止修改 CCB 前台 tab 调度，转向 Herdr attach/input mode。
   - 直接在新 WezTerm tab 运行 `herdr session attach <session>`，绕过 CCB，比较是否仍异常。
   - 若绕过 CCB 仍异常，产出 Herdr 侧上游问题记录。
   - 若绕过 CCB 正常，回到 CCB 对 Herdr session/namespace/focus 的调用顺序。

3. **强制模式正常，默认模式故障**：修 frontend binding 复用和当前 pane 判定。
   - 核查 `existing_frontend` 的 socket/pane/workspace 探测。
   - 对不可达或 legacy binding 严格失效，不聚焦错误 pane。

4. **2-tab 故障但 1-tab 正常**：修 `wezterm_spawn` 和后续 `attach_namespace` 顺序。
   - 检查 spawn 后是否又从命令 pane 执行了会抢焦点的 foreground attach。
   - 必要时让 spawn 只负责 UI attach，后台只做 namespace 可达性验证。

---

## 测试计划

### 自动化测试

新增或调整 `test/test_v2_start_foreground.py`：

- `test_launch_herdr_ui_forces_current_pane_when_foreground_tabs_is_one`
- `test_launch_herdr_ui_rejects_one_tab_when_not_in_wezterm_pane`
- `test_launch_herdr_ui_forces_spawn_when_foreground_tabs_is_two`
- `test_launch_herdr_ui_records_requested_tabs_in_frontend_fact`
- `test_replace_current_pane_exec_uses_clean_herdr_env`，若诊断确认需要环境净化
- `test_replace_current_pane_exec_resets_terminal_modes`，若诊断确认需要终端复位

如果 `ccb.cmd` 参数剥离逻辑较复杂，补一个 Windows-only 脚本级验证，至少覆盖：

- `.\ccb.cmd --foreground-tabs 1 --help` 不把 `--foreground-tabs` 传给普通 parser。
- 非法值返回清晰错误。

### 实机验证

通过 `scripts/diagnostics/wezterm-foreground-tabs-compare.ps1`：

- `--foreground-tabs 1`：当前 tab 进入 Herdr UI，无额外 UI tab 残留，键盘输入、点击、滚轮都作用在 Herdr UI 预期位置。
- `--foreground-tabs 2`：命令 tab + UI tab 两个 tab 可观察，输入探针与人工点击都正常。
- 同一项目重复启动：如果已有健康 Herdr UI，只复用可验证 frontend，不靠标题或 tab 数猜测。
- 故障复现时，必须能在 `summary.md` 中定位输入泄漏到哪个 pane。

---

## 风险与约束

- 诊断采集会接触环境变量、进程 command line 和 pane 内容，必须先脱敏再写入 Markdown 摘要；原始采集只放在 `.scratch`。
- 不能用 tab 标题、tab 数或窗口标题推断 Herdr UI 身份；只能用 `Runtime Binding.frontend`、WezTerm JSON、pane 集合差分和 Herdr session 事实。
- 不能把前台 attach 事实当成业务完成判定；ready gate 和 job completion 不受本开关影响。
- 不能因为 2-tab 正常就直接放弃 1-tab 目标。2-tab 只能作为对照和临时降级，最终目标仍是当前 WezTerm tab 可正常进入 Herdr UI。
- 自动化 `send-text` 可以覆盖键盘输入和转义序列泄漏，但真实鼠标点击仍可能需要人工复核；人工结果必须带时间戳写入 `summary.md`。

---

## 审核后实施顺序

1. 加 `--foreground-tabs` 诊断开关和最小测试，不改变默认行为。
2. 加实机对照采集脚本，先只采集，不自动关闭用户已有 pane。
3. 运行 1-tab / 2-tab 对照，填写 `summary.md`。
4. 按“修复决策规则”选择最小修复。
5. 为被证实的根因补回归测试。
6. 实施修复后重跑自动化测试和实机对照。
7. 清理或保留诊断开关：若仍有长期排障价值，改成隐藏诊断选项；否则从默认帮助中隐藏并仅保留环境变量入口。
