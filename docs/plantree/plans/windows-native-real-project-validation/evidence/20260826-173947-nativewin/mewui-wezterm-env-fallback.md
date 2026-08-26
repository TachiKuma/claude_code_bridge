# MewUI WezTerm 环境 fallback 修复记录

执行时间：2026-08-26 +08:00

## 用户问题

用户在 WezTerm 中从真实项目目录运行：

```powershell
E:\GitHub开源项目\TachiKuma\NativeWin_CCB_Herdr\ccb.cmd
```

PowerShell 提示符返回，但没有出现 Herdr UI。进一步问题是：

- Herdr UI 是否应该在当前 WezTerm pane 内出现；
- 是否必须把 `wezterm` 加到全局 `PATH`。

## 现场事实

当前环境确实是 WezTerm 子进程环境：

```text
WEZTERM_PANE=0
WEZTERM_EXECUTABLE=D:\Tools\AI Tools\WezTerm\wezterm-gui.exe
WEZTERM_EXECUTABLE_DIR=D:\Tools\AI Tools\WezTerm
WEZTERM_UNIX_SOCKET=C:\Users\Administrator\.local/share/wezterm\gui-sock-9160
```

但 PATH 查询失败：

```text
Get-Command wezterm -> 未找到
Get-Command wezterm.exe -> 未找到
```

因此旧实现只执行 `runner.which('wezterm')` 时，会误判 WezTerm CLI 不可用。

## 设计结论

Herdr UI 不会渲染在当前 pane 里面。CCB 的前台 attach 语义是在现有 WezTerm mux 中创建新的
tab/pane：

```text
wezterm cli spawn -- <herdr> session attach <session>
```

所以 CCB 需要的是“能调用当前 WezTerm mux 的 CLI”，而不是必须依赖全局 PATH。PATH 只是第一优先级。

## 修复

`lib/cli/services/start_foreground.py` 新增 WezTerm CLI 解析顺序：

1. `wezterm` / `wezterm.exe` on PATH；
2. `WEZTERM_EXECUTABLE`，并在其指向 `wezterm-gui.exe` 时优先派生同目录 `wezterm.exe`；
3. `WEZTERM_EXECUTABLE_DIR` 下的 `wezterm.exe` / `wezterm`；
4. 当前 WezTerm 环境变量存在时，从默认 Windows 安装目录兜底：
   - `%LOCALAPPDATA%\Programs\WezTerm\wezterm.exe`
   - `%ProgramFiles%\WezTerm\wezterm.exe`
   - `%ProgramFiles(x86)%\WezTerm\wezterm.exe`

这样在 WezTerm 内运行时，即使 PATH 没有 `wezterm`，CCB 也能通过当前环境变量找到 CLI。

## 验证

当前进程在 `which_fn=lambda name: None` 模拟 PATH 缺失时，resolver 返回：

```text
D:\Tools\AI Tools\WezTerm\wezterm.exe
```

真实 CLI 验证：

```text
wezterm 20251201-075747-d3b0fdad
wezterm cli list --format json -> 返回当前 default workspace / pane 0
```

无 pytest harness 已覆盖并通过：

- `WEZTERM_EXECUTABLE` 直接指向 `wezterm.exe`；
- `WEZTERM_EXECUTABLE` 指向 `wezterm-gui.exe` 时派生 sibling CLI；
- `WEZTERM_EXECUTABLE_DIR` 指向 WezTerm 安装目录；
- `WEZTERM_PANE` + `LOCALAPPDATA` 默认安装目录 fallback。

语法检查通过：

```text
.venv\Scripts\python.exe -m py_compile lib\cli\services\start_foreground.py test\test_v2_start_foreground.py
```

pytest 仍受环境限制：

```text
.venv\Scripts\python.exe: No module named pytest
python.exe: No module named pytest
```
