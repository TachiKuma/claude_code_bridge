# 修复方案：WezTerm 前台 `os.execvpe` 输入冲突诊断与解决

- 状态：`draft`（待审核）
- 日期：2026-08-27
- 关联 ADR：`docs/adr/0001-三层运行时权威边界.md`
- 关联实现：`lib/cli/services/start_foreground.py`
- 关联提交：`176b674e` 修复 WezTerm 前台 socket 复用与 Herdr 输入定位

---

## 问题现象

在 WezTerm tab 内运行 `ccb` 后，Herdr UI 正常显示（agent pane 可见），但：

1. 用户**无法通过键盘输入**任何内容
2. 鼠标**点击无响应**
3. 鼠标**滚轮有反应**（说明 Herdr TUI 进程正常运行，只是输入层出问题）
4. 在 `codex2api` pane 的输入框出现**无法识别的字符**
5. Herdr 的用户交互像是被其他软件"抢走"了一样

## 当前实现回顾

### 前台启动流程

在 `lib/cli/services/start_foreground.py` 中，`_attach_herdr_project_namespace` 调用 `_launch_herdr_ui` 决定如何展示 Herdr UI：

1. **`current_pane_exec`**：如果当前在 WezTerm pane 中，用 `os.execvpe` 将当前 Python 进程替换为 `herdr session attach <session>`
2. **`wezterm_spawn`**：不在 WezTerm pane 中但有 WezTerm mux 时，`wezterm cli spawn` 创建新 tab
3. **`detached_fallback`**：无 WezTerm 时用 `subprocess.Popen` 启动独立 Herdr 窗口

### 修复提交 176b674e 的内容

该提交主要修复了 WezTerm socket 的传递和复用问题：

- `_current_wezterm_pane_fact` 现在返回 `wezterm_socket` 字段
- `_replace_current_wezterm_pane_with_herdr_ui` 在 frontend fact 中记录 `wezterm_socket`
- `_probe_existing_herdr_frontend` 用 `wezterm_socket` 构建 `WEZTERM_UNIX_SOCKET` 环境变量传给 `wezterm cli` 子命令
- `_subprocess_kwargs_herdr_ui_control` 现在接受并传递 `env` 参数

**但在关键路径 `_replace_current_wezterm_pane_with_herdr_ui:582` 中，`execvpe` 仍然使用未经净化的 `os.environ`**：

```python
command = [herdr_exe, 'session', 'attach', session_name]
try:
    runner.execvpe(herdr_exe, command, os.environ)  # ← 问题在这里
```

## 根因分析

### 核心问题：`execvpe` 的环境继承污染

`execvpe` 的工作原理是：在当前进程空间加载新程序 `herdr session attach`，**替换整个进程映像**，但**保持进程 ID、打开的文件描述符、TTY 控制不变**。第三个参数 `os.environ` 直接传递给新程序。

当 CCB Python 进程被 `herdr` 替换时，`os.environ` 中携带了大量 CCB 运行时痕迹：

| 环境变量类别 | 具体变量                              | 潜在问题                                                                |
| ------------ | ------------------------------------- | ----------------------------------------------------------------------- |
| WezTerm 原生 | `WEZTERM_PANE`、`WEZTERM_UNIX_SOCKET` | WezTerm 可能仍将键盘输入路由到"原始 pane PID"而不是新进程               |
| tmux 残留    | `TMUX`、`TMUX_PANE`                   | Herdr 可能误以为自己运行在 tmux 中，初始化错误的 TUI 后端               |
| CCB 内部     | `CCB_*` 系列                          | Herdr 进程携带 CCB 环境变量，可能影响其行为判断                         |
| Python 相关  | `PYTHON*`、`PYTHONHOME`、`PYTHONPATH` | 与 Herdr（Rust 程序）无关，但可能通过 Python C 扩展或嵌入解释器造成干扰 |
| PATH 修改    | 被 CCB bootstrap 修改过的 `PATH`      | 可能导致 Herdr 调用的子进程找到错误的可执行文件                         |

### 可能的机理

**假设 1：WezTerm pane 输入路由混乱**

WezTerm 的 pane 模型基于进程组与会话。`execvpe` 替换进程后，进程 PID 不变但是程序语义变了。WezTerm 的 PTY 层可能：

- 仍然根据 `WEZTERM_PANE` 的值将输入路由到某个"预期"的进程（原 Python 进程所属的 pane）
- 但实际进程中运行的是 `herdr`，其 TUI 库（如 ratatui/tui-rs）初始化时检测终端能力
- 残留的 `TMUX` 环境变量导致 Herdr 以为自己在 tmux pane 中，初始化错误的终端模式

**假设 2：TUI 库初始化检测到错误的终端能力**

Herdr 的 TUI 初始化读取终端能力时：

- 如果 `TERM` 环境变量是 WezTerm 原生值（如 `wezterm`），而 Herdr 在非 WezTerm 原生环境下编译
- 或者 `LINES`/`COLUMNS` 被 tmux 或 CCB 设置了不正确的值
- 导致 TUI 库选择了错误的输入处理模式

**假设 3：标准输入/输出重绑定问题**

`execvpe` 保持文件描述符不变。如果 CCB 启动链中的某个环节将 stdin/stdout 重定向到了非 TTY 设备，Herdr 的 TUI 虽然能渲染（通过其他路径），但无法接收键盘输入。

**假设 4：鼠标事件协议不匹配**

WezTerm 支持 SGR 鼠标协议（通过 `\x1b[?1006h`），Herdr 和 CCB 可能使用不同版本的鼠标协议。CCB 的 Python 进程可能设置了某些终端模式，而 `execvpe` 后这些模式没有重置，导致 Herdr 收到乱码的鼠标/键盘事件——这与"鼠标滚轮有反应但点击无效+输入乱码"的现象高度吻合。

## 诊断方法：双模式对比开关

### `--foreground-tabs` 开关设计

给 `ccb.cmd` 添加开关，用于强制指定前台启动后的 tab 数量：

```
ccb --foreground-tabs 1    # 强制在当前 pane 中启动（current_pane_exec）
ccb --foreground-tabs 2    # 强制在新 tab 中启动（wezterm_spawn / detached_fallback）
```

**实现方式**：

1. `ccb.cmd` 解析 `--foreground-tabs {1,2}`，设置环境变量 `CCB_FOREGROUND_TABS=1|2`
2. `start_foreground.py` 在 `_launch_herdr_ui` 中读取 `CCB_FOREGROUND_TABS`：
   - `CCB_FOREGROUND_TABS=1`：强制走 `_replace_current_wezterm_pane_with_herdr_ui`（execvpe）
   - `CCB_FOREGROUND_TABS=2`：跳过 `_is_current_wezterm_pane` 检测，直接走 `wezterm_spawn`
   - 未设置：保持现有行为

### 对比验证步骤

| 步骤 | 操作                                                   | 预期                                         |
| ---- | ------------------------------------------------------ | -------------------------------------------- |
| 1    | 在 WezTerm tab 中运行 `ccb --foreground-tabs 2`        | Herdr UI 在新 tab 中打开，输入正常           |
| 2    | 在 WezTerm tab 中运行 `ccb --foreground-tabs 1`        | Herdr UI 在当前 tab 中打开，观察输入是否异常 |
| 3    | 对比步骤 1 和 2 的 frontend fact（`launch_mode` 字段） | 确认两种模式的行为差异                       |

**判断依据**：

- 2 tab 正常 + 1 tab 故障 → 根因在 `execvpe` 路径
- 两者都故障 → 可能是 WezTerm mux 或 Herdr 本身的更底层问题

## 修复方案

### 方案 A：exec 前净化环境（推荐）

在 `_replace_current_wezterm_pane_with_herdr_ui` 中构造一个净化后的环境字典：

```python
def _clean_herdr_exec_env(base_env: Mapping[str, str] | None = None) -> dict[str, str]:
    """构造传递给 herdr session attach 的净化环境，移除 CCB 内部和可能干扰 TUI 的变量"""
    env = dict(base_env or os.environ)

    # 保留 WezTerm 原生变量（WezTerm 需要它们来路由 pane 输入）
    wezterm_keep = {'WEZTERM_PANE', 'WEZTERM_UNIX_SOCKET', 'WEZTERM_EXECUTABLE',
                    'WEZTERM_EXECUTABLE_DIR', 'TERM_PROGRAM'}

    # 移除 CCB 内部变量
    for key in list(env.keys()):
        if key.startswith('CCB_'):
            del env[key]

    # 移除 tmux 残留
    env.pop('TMUX', None)
    env.pop('TMUX_PANE', None)
    env.pop('TMUX_SOCKET', None)

    # 移除 Python 相关
    env.pop('PYTHONHOME', None)
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONSTARTUP', None)
    env.pop('PYTHONUNBUFFERED', None)

    # 确保 TERM 正确
    env['TERM'] = env.get('TERM', 'xterm-256color')

    return env
```

然后在 `execvpe` 时使用净化后的环境：

```python
def _replace_current_wezterm_pane_with_herdr_ui(...) -> dict[str, object]:
    pane_fact = _current_wezterm_pane_fact(...)
    frontend = _herdr_frontend_fact(...)
    if before_exec is not None:
        before_exec(frontend)
    command = [herdr_exe, 'session', 'attach', session_name]
    try:
        herdr_env = _clean_herdr_exec_env()  # ← 净化环境
        runner.execvpe(herdr_exe, command, herdr_env)  # ← 使用净化后的环境
    except (OSError, subprocess.SubprocessError):
        ...
```

### 方案 B：exec 前额外重置终端（增强方案 A）

除了净化环境外，在 exec 前执行终端重置：

```python
import sys
import termios
import tty

def _reset_terminal_for_exec() -> None:
    """重置终端为原始模式，避免 exec 后 TUI 库读到残留的终端设置"""
    try:
        if sys.stdin.isatty():
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, termios.tcgetattr(sys.stdin))
    except Exception:
        pass
    try:
        sys.stdout.write('\x1bc')  # RIS - Reset to Initial State
        sys.stdout.write('\x1b[?1000l\x1b[?1002l\x1b[?1003l\x1b[?1006l')  # 关闭鼠标报告
        sys.stdout.write('\x1b[?25h')  # 确保光标可见
        sys.stdout.flush()
    except Exception:
        pass
```

然后在 `execvpe` 前调用 `_reset_terminal_for_exec()`。

### 方案 C：用 spawn 代替 exec（备选）

放弃 `execvpe`，改用 `subprocess.Popen` 在新进程中启动 Herdr，然后退出当前进程：

```python
worker = runner.popen([herdr_exe, 'session', 'attach', session_name],
                      env=herdr_env)
# 前台进程退出，WezTerm pane 保持打开
# WezTerm 会接管 orphaned 子进程或 pane 会保持进程组
sys.exit(0)
```

**优点**：完全不继承进程上下文，环境独立
**缺点**：

- 当前 pane 在 Python 进程退出后可能被 WezTerm 关闭（取决于进程组设置）
- 失去 `execvpe` 的"无缝替换"语义（用户会看到进程退出和 Herdr 启动的过渡）
- 需要验证 WezTerm 在父进程退出后是否保持 pane 中的子进程运行

## 文件变更范围

| 文件                                   | 变更内容                                                                                                                                                          |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ccb.cmd`                              | 添加 `--foreground-tabs {1,2}` 参数解析，设置 `CCB_FOREGROUND_TABS` 环境变量                                                                                      |
| `lib/cli/services/start_foreground.py` | 添加 `_clean_herdr_exec_env()` 函数；修改 `_replace_current_wezterm_pane_with_herdr_ui` 使用净化环境；修改 `_launch_herdr_ui` 支持 `CCB_FOREGROUND_TABS` 强制模式 |
| `test/test_v2_start_foreground.py`     | 新增测试：`test_launch_herdr_ui_forced_one_tab`、`test_launch_herdr_ui_forced_two_tabs`、`test_replace_current_pane_uses_clean_env`                               |

## 风险与缓解

| 风险                                                     | 缓解措施                                                  |
| -------------------------------------------------------- | --------------------------------------------------------- |
| 环境净化过度导致 Herdr 找不到依赖                        | 白名单机制，保留 `PATH`、`HOME`、`USERPROFILE` 等基础变量 |
| 鼠标/键盘协议复位导致 Herdr 初始化期间终端状态进一步混乱 | 方案 B 的终端复位作为可选增强，先以方案 A 验证            |
| 修改测试需模拟 WezTerm 环境                              | 使用已有的 `HerdrFrontendCommandRunner` 注入 seam         |
| `execvpe` 失败后回退路径不清晰                           | 保留现有 try/except 和 frontend fact 记录机制             |

## 实施步骤

1. **实现诊断开关**（独立可评审的变更）：
   - `ccb.cmd` 添加 `--foreground-tabs` 参数
   - `start_foreground.py` 读取环境变量并强制调度模式
   - 实机验证两种模式的差异

2. **确定根因**（基于开关对比结果）：
   - 如果 2 tab 正常、1 tab 故障 → 执行步骤 3
   - 如果两者都故障 → 重新定位问题

3. **实施修复**（基于根因选择方案）：
   - 优先方案 A（环境净化）
   - 若 A 不足以解决问题 → 叠加方案 B（终端复位）
   - 若 A+B 都不足 → 回退方案 C（spawn 替代 exec）

4. **测试验证**：
   - 自动化测试覆盖
   - 实机 WezTerm 验证
