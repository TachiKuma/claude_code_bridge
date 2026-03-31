# Phase 7: Windows 原生环境专项检查 - Research

**Researched:** 2026-03-31
**Domain:** Windows 原生环境性能/兼容性/安全性审计
**Confidence:** HIGH

## Summary

Phase 7 对 CCB (Claude Code Bridge) 在原生 Windows 10 Pro 环境中的性能、兼容性和安全性进行全面自动化审计。通过代码审查和现有测试分析，已识别出 5 个已知 Windows 问题线索和多个需要深入检查的关键区域。

项目当前运行环境为 Windows 10 Pro (Build 19041) + PowerShell 5.1 + Python 3.14.2 + pytest 9.0.2。代码库约 98 个 Python 模块分布在 `lib/` 目录下，其中约 20+ 处使用 `os.name == "nt"` 或 `sys.platform == "win32"` 进行 Windows 特定处理。

核心发现：**daemon 架构的 socket 通信安全存在结构性缺陷**（token 明文写入 state JSON 文件、无 TLS 加密、仅绑定 127.0.0.1 但无 SO_EXCLUSIVEADDRUSE 防端口劫持）；**兼容性方面 mbcs 编码回退和 os.chmod(0o600) 在 Windows 上失效是已确认问题**；**性能方面 daemon 冷启动受 Python 导入时间和 WSL 探测延迟双重影响**。

**Primary recommendation:** 以 pytest 测试套件为核心产出，覆盖三大维度 20+ 测试场景，先输出问题清单再逐项修复。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 全面覆盖性能、兼容性、安全性三大维度，不做裁剪
- **D-02:** 性能和兼容性列为重点关注方向
- **D-03:** 使用 pytest 测试套件实现全面自动化测试，集成到现有测试体系
- **D-04:** 在当前原生 Windows 10 Pro 环境中直接运行所有测试和检查
- **D-05:** 检查深度为"全面自动化测试"——建立可回归的自动化测试套件覆盖核心场景
- **D-06:** daemon 冷启动 < 3 秒
- **D-07:** 命令响应 < 500ms（从用户输入到响应输出）
- **D-08:** 内存占用 < 50MB（daemon 常驻进程）
- **D-09:** 全面编码覆盖——不仅 UTF-8，还必须验证 GBK、Windows-1252、Shift-JIS 等其他 Windows 常见编码的回退行为
- **D-10:** 重点关注中文路径、中文内容、PowerShell 5.1 兼容性
- **D-11:** 深入渗透级别——包含代码注入风险评估、socket 通信安全审计、daemon 提权路径检查
- **D-12:** 检查范围：文件权限、敏感信息泄露、进程隔离、token 处理、eval/exec 滥用、subprocess 参数注入、socket 认证机制
- **D-13:** 先输出完整问题清单 + 提升方案文档
- **D-14:** 然后按优先级逐项实施修复，覆盖所有发现的问题（Critical/High/Medium/Low 全部修复）
- **D-15:** 使用 pytest 编写测试用例，覆盖 Windows 特定场景
- **D-16:** 测试应覆盖以下核心场景：编码处理、路径转换、daemon 生命周期、socket 通信、文件锁、进程管理、install.ps1 安装流程

### Claude's Discretion
- 测试文件的组织结构和命名约定
- 性能测试的具体实现方式（timeit、pytest-benchmark 或自定义计时器）
- 问题严重程度的分级标准（基于影响范围和发生概率）
- 修复的优先级排序策略
- pytest fixture 和 conftest 的组织方式

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WIN-01 | 性能审计：daemon冷启动<3s、命令响应<500ms、内存<50MB | 审计 daemon 启动路径（askd/daemon.py + askd_server.py）、socket 通信延迟、Python 导入开销 |
| WIN-02 | 兼容性审计：编码UTF-8/GBK/其他、路径转换、PS版本、终端差异 | audit compat.py decode_stdin_bytes()、ccb WSL 路径处理、install.ps1 PS 5.1 限制 |
| WIN-03 | 安全性审计：文件权限、token泄露、进程隔离、socket安全 | audit askd_server.py token 明文、os.chmod(0o600) Windows 失效、subprocess 参数构造 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | 测试框架 | CONTEXT.md D-03/D-15 锁定选择，已安装并验证 |
| Python | 3.14.2 | 运行时 | 当前 Windows 10 Pro 环境已安装 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psutil | TBD | 内存/进程测量 | daemon 内存占用测试（需安装） |
| timeit (stdlib) | builtin | 性能计时 | daemon 冷启动计时 |
| subprocess (stdlib) | builtin | 进程管理测试 | daemon 生命周期、install.ps1 验证 |
| tempfile (stdlib) | builtin | 临时文件 | 中文路径测试、编码测试 |
| unittest.mock (stdlib) | builtin | Mock 子进程/网络 | socket 通信隔离测试 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psutil | tracemalloc (stdlib) | tracemalloc 仅追踪 Python 内存分配，不包含进程总 RSS；psutil 可获取进程完整内存信息但需额外安装 |
| timeit 手写 | pytest-benchmark | pytest-benchmark 提供统计对比和可视化但需额外安装；timeit 更轻量且零依赖 |
| psutil | Windows `tasklist` 命令解析 | tasklist 输出解析脆弱且不准确，psutil 提供跨平台 API |

**Installation:**
```bash
pip install pytest psutil
```

**Version verification:**
```
pytest: 9.0.2 (verified 2026-03-31)
psutil: needs install (pip install psutil)
```

## Architecture Patterns

### Recommended Test Structure
```
tests/
├── conftest.py                    # shared fixtures (Windows-specific env setup)
├── windows/
│   ├── __init__.py
│   ├── conftest.py                # Windows-only fixtures (中文路径 tmpdir 等)
│   ├── test_perf_daemon.py        # WIN-01: daemon 冷启动/命令响应/内存
│   ├── test_perf_socket.py        # WIN-01: socket 通信效率
│   ├── test_compat_encoding.py    # WIN-02: 编码回退链测试
│   ├── test_compat_path.py        # WIN-02: 路径转换 (中文路径/UNC/空格)
│   ├── test_compat_powershell.py  # WIN-02: PS 5.1 兼容性
│   ├── test_security_token.py     # WIN-03: token 处理与泄露
│   ├── test_security_permission.py # WIN-03: 文件权限 (chmod 行为)
│   ├── test_security_process.py   # WIN-03: 进程隔离与提权
│   ├── test_security_socket.py    # WIN-03: socket 通信安全
│   └── test_install.ps1.py        # install.ps1 安装流程验证
```

### Pattern 1: 编码回退链测试 (compat.py)
**What:** 验证 `decode_stdin_bytes()` 在不同编码输入下的行为
**When to use:** WIN-02 兼容性测试
**Example:**
```python
def test_decode_gbk_fallback():
    """GBK 编码内容应通过 locale 回退路径正确解码"""
    gbk_bytes = "中文测试".encode("gbk")
    # 设置 locale.getpreferredencoding 返回 gbk
    with mock.patch("locale.getpreferredencoding", return_value="gbk"):
        result = decode_stdin_bytes(gbk_bytes)
    assert "中文" in result

def test_decode_windows_1252():
    """Windows-1252 编码内容应通过 mbcs 回退正确解码"""
    cp1252_bytes = "\u2014em dash\u2014".encode("windows-1252")
    with mock.patch("locale.getpreferredencoding", return_value="cp1252"):
        with mock.patch("sys.platform", "win32"):
            result = decode_stdin_bytes(cp1252_bytes)
    assert "em dash" in result

def test_decode_mbcs_data_loss():
    """mbcs 回退可能丢失非 ANSI 字符——验证不崩溃但可能丢失数据"""
    shift_jis_bytes = "テスト".encode("shift_jis")
    with mock.patch("locale.getpreferredencoding", return_value="utf-8"):
        with mock.patch("sys.platform", "win32"):
            result = decode_stdin_bytes(shift_jis_bytes)
    # mbcs 不会匹配 Shift-JIS，最终回退到 utf-8 with replace
    assert isinstance(result, str)  # 不应崩溃
```

### Pattern 2: 性能基准测试
**What:** 测量 daemon 冷启动、命令响应和内存占用
**When to use:** WIN-01 性能测试
**Example:**
```python
import time
import subprocess
import psutil

def test_daemon_cold_start_under_3s():
    """D-06: daemon 冷启动 < 3 秒"""
    start = time.perf_counter()
    proc = subprocess.Popen(
        [sys.executable, "bin/askd"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    # 等待 state 文件写入
    # ... (轮询 state file)
    elapsed = time.perf_counter() - start
    proc.terminate()
    assert elapsed < 3.0, f"daemon cold start took {elapsed:.2f}s (limit: 3s)"
```

### Pattern 3: 安全审计测试
**What:** 验证 token 不泄露到日志、文件权限正确、socket 有认证
**When to use:** WIN-03 安全测试
**Example:**
```python
def test_state_file_token_not_in_logs():
    """State file 中的 token 不应出现在日志中"""
    state_file = Path(tempfile.mktemp(suffix=".json"))
    state_file.write_text(json.dumps({"token": "secret123", "port": 12345}))
    # 模拟 write_log 调用
    log_file = Path(tempfile.mktemp(suffix=".log"))
    write_log(log_file, "[INFO] daemon started")
    log_content = log_file.read_text()
    assert "secret123" not in log_content

def test_chmod_600_windows_ntfs():
    """os.chmod(0o600) 在 Windows NTFS 上无效——验证文件实际权限"""
    test_file = Path(tempfile.mktemp())
    test_file.write_text("sensitive")
    os.chmod(test_file, 0o600)
    stat_info = test_file.stat()
    # Windows 上 st_mode 不反映 Unix 权限位
    import stat as stat_mod
    has_owner_only = (stat_info.st_mode & 0o777) == 0o600
    # 在 Windows 上这个断言大概率失败
    if os.name == "nt":
        assert not has_owner_only, "os.chmod(0o600) should have no effect on NTFS"
```

### Anti-Patterns to Avoid
- **在测试中使用 shell=True：** 项目代码中没有使用 shell=True 的 subprocess 调用（已验证），测试也不应引入。始终传递参数列表。
- **在 Windows 测试中硬编码路径分隔符：** 使用 `os.path.join()` 或 `Path()` 对象，不要使用 `/` 或 `\\`。
- **测试性能时不隔离环境变量：** 每个性能测试应通过 monkeypatch 或 subprocess 隔离 CCB_* 环境变量。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 进程内存测量 | 手动解析 tasklist 输出 | psutil.Process().memory_info() | psutil 提供跨平台 RSS/VMS/USPS 测量，无需解析脆弱的命令行输出 |
| 文件权限检测 | 手动调用 Windows API | os.stat() + stat 模块 | Python 标准库已提供跨平台 stat，无需 ctypes 调用 |
| Socket 安全审计 | 手动实现 port scanning | socket.create_connection() + 异常检测 | 标准 socket 库足够检测端口绑定和连接 |
| 编码转换测试 | 手动构造各种编码字节 | Python codecs 模块 + str.encode() | codecs 模块提供完整的编码注册表 |

**Key insight:** Windows 平台测试最大风险不是缺少库，而是平台行为差异（chmod 无效、编码回退链复杂、进程隔离机制不同）。应优先用标准库 API 测量实际行为，而非假设 Unix 语义在 Windows 上成立。

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | daemon state files: `~/.cache/ccb/askd.json` (含 token 明文、port、host、PID) | 需安全审计：token 是否可被其他用户读取 |
| Stored data | lock files: `~/.ccb/run/*.lock` (含 PID) | 无需迁移 |
| Stored data | pane logs: `~/.cache/ccb/pane-logs/*.log` | 需验证：日志中是否包含敏感信息 |
| Stored data | registry files: `~/.ccb/run/ccb-session-*.json` | 无需迁移 |
| Live service config | PowerShell profile 中可能注入的 CCB 配置 | 手动检查（非代码问题） |
| Live service config | WezTerm `~/.wezterm.lua` 中注入的 default_prog | 手动检查（install.ps1 管理） |
| Live service config | `~/.claude/settings.json` 权限配置 | 无需迁移 |
| OS-registered state | None — CCB 不注册 Windows Task Scheduler 或服务 | 无 |
| Secrets/env vars | `CCB_RUN_DIR` 环境变量指向 daemon state 目录 | code edit only |
| Secrets/env vars | `CCB_PARENT_PID`、`CCB_MANAGED` 等运行时环境变量 | 无需修改 |
| Build artifacts | `scripts/devos-cli/devos_cli.egg-info/` — 不存在 | 无 |

**Nothing found in category:** OS-registered state — CCB 不注册任何 Windows 系统级状态（Task Scheduler、Windows Service、注册表）。

## Common Pitfalls

### Pitfall 1: os.chmod(0o600) 在 Windows NTFS 上静默失败
**What goes wrong:** `lib/askd_server.py:299` 和 `lib/mail/*.py` 中多处使用 `os.chmod(file, 0o600)` 保护敏感文件，但 Windows NTFS 不支持 Unix 权限位。Python 调用不报错但权限不变。
**Why it happens:** Windows 使用 ACL (Access Control List) 而非 Unix permission bits。`os.chmod` 在 Windows 上仅能设置只读标志。
**How to avoid:** 使用 Windows ACL API (icacls 或 Python `win32security`) 或至少用 `os.chmod(file, 0o400)` 设置只读位作为最小缓解。
**Warning signs:** `stat.S_IMODE(st.st_mode) & 0o777` 在 Windows 上返回 0o666 而非预期值。

### Pitfall 2: mbcs 编码回退可能丢失数据
**What goes wrong:** `lib/compat.py:63` 使用 `"mbcs"` 作为 Windows 编码回退的最后一步。mbcs 映射到系统 ANSI 代码页（通常为 cp1252 或 cp936），无法正确解码非对应编码的字节。
**Why it happens:** 当输入既不是 UTF-8 也不是 locale preferred encoding 时，mbcs 是 Windows 上的"最终回退"，但它假设输入符合当前系统代码页。
**How to avoid:** 对无法识别的编码，使用 `errors="replace"` 而非 mbcs，或让用户通过 `CCB_STDIN_ENCODING` 显式指定。
**Warning signs:** 中日韩混合内容在纯 Windows 环境中出现乱码。

### Pitfall 3: daemon state file 中 token 明文存储
**What goes wrong:** `askd_runtime.py:random_token()` 生成 16 字节随机 token，明文写入 `askd.json` state 文件。在 NTFS 上由于 chmod 无效（见 Pitfall 1），任何同用户进程都可读取。
**Why it happens:** 设计为单用户本地 daemon，未考虑多用户共享机器场景。
**How to avoid:** 至少使用 Windows DACL 限制文件访问，或使用 DPAPI 加密存储。
**Warning signs:** 非 admin 用户可读取 `%LOCALAPPDATA%\ccb\askd.json`。

### Pitfall 4: bin/ask 生成的 PowerShell 脚本中消息未转义
**What goes wrong:** `bin/ask:712` 的 PowerShell 脚本将用户消息通过 `Get-Content` 传递给 Python，但如果消息文件路径包含特殊字符（如 `$()`、反引号），可能被 PowerShell 解释。
**Why it happens:** 消息通过临时文件传递（`Get-Content -Path "{msg_file}"`），文件路径通过 f-string 嵌入到 PowerShell 脚本中，未做 PowerShell 特殊字符转义。
**How to avoid:** 对路径中的 PowerShell 特殊字符（`$`、`` ` ``、`"`）进行转义，或使用单引号包裹路径。
**Warning signs:** 用户消息中包含 `$()` 等 PowerShell 语法时脚本行为异常。

### Pitfall 5: WSL 探测在纯 Windows 环境的超时延迟
**What goes wrong:** `lib/ccb_config.py:128-168` 的 `_wsl_probe_distro_and_home()` 在非 WSL 环境中会调用 `wsl.exe -e sh -lc echo`，该调用在无 WSL 安装时超时（默认 10 秒）。
**Why it happens:** 函数未先检测 WSL 是否可用，直接调用 wsl.exe 命令。
**How to avoid:** 先用 `wsl.exe --list -q` 快速检测（1-2 秒超时），失败则立即返回默认值。
**Warning signs:** daemon 启动时 10 秒延迟（`apply_backend_env()` 被调用）。

### Pitfall 6: subprocess 调用缺少 CREATE_NO_WINDOW 标志
**What goes wrong:** 部分 subprocess 调用（如 `lib/ccb_config.py` 中的 WSL 探测）直接使用 `subprocess.run()` 而非 `terminal._run()`，在 Windows 上可能弹出 CMD 窗口。
**Why it happens:** `_subprocess_kwargs()` 封装在 `terminal.py` 中，但不是所有模块都导入使用。
**Warning signs:** 用户看到短暂闪烁的 CMD 窗口。

## Code Examples

### 已确认的 Windows 问题代码 (HIGH confidence)

**1. os.chmod 在 Windows 上无效 (lib/askd_server.py:297-301)**
```python
if os.name != "nt":  # 正确：跳过 Windows
    try:
        os.chmod(self.state_file, 0o600)
    except Exception:
        pass
```
这是正确做法。但 `lib/mail/*.py` 中的 chmod 调用**没有** `os.name != "nt"` 守卫：
```python
# lib/mail/daemon.py:96 — 缺少 Windows 守卫
state_path.chmod(0o600)

# lib/mail/credentials.py:113 — 缺少 Windows 守卫
fallback_path.chmod(0o600)
```

**2. mbcs 编码回退 (lib/compat.py:61-65)**
```python
if sys.platform == "win32":
    try:
        return data.decode("mbcs", errors="strict")
    except Exception:
        pass
return data.decode("utf-8", errors="replace")
```
问题：`mbcs` 严格模式可能失败，但即使成功也可能因代码页不匹配而返回错误内容。

**3. WSL 探测无快速失败 (lib/ccb_config.py:128-136)**
```python
def _wsl_probe_distro_and_home() -> tuple[str, str]:
    try:
        r = subprocess.run(
            ["wsl.exe", "-e", "sh", "-lc", "echo $WSL_DISTRO_NAME; echo $HOME"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            **_subprocess_kwargs()
        )
```
10 秒超时在纯 Windows 环境中每次调用都浪费。

**4. bin/ask PowerShell 路径未转义 (bin/ask:675-677)**
```python
status_file_win = str(status_file).replace('"', '`"')
log_file_win = str(log_file).replace('"', '`"')
```
仅转义了双引号，未转义 `$`、`` ` ``、`'` 等 PowerShell 特殊字符。

### Socket 安全模式 (lib/askd_server.py:104-119)
```python
class Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        # ... 读取消息
        if msg.get("token") != self.server.token:
            self._write({"type": response_type, ..., "reply": "Unauthorized"})
            return
```
Token 对比使用 Python 字符串比较（`!=`），无 timing-safe 比较。在本地 socket 上 timing attack 风险较低，但作为审计发现应记录。

### daemon 冷启动路径分析
```
bin/ask -> _maybe_start_unified_daemon()
  -> ping_daemon() (读取 state file, socket connect)
  -> subprocess.Popen([sys.executable, "bin/askd"])
    -> lib/askd/daemon.py: UnifiedAskDaemon.serve_forever()
      -> AskDaemonServer.serve_forever() (askd_server.py)
        -> socketserver.ThreadingTCPServer 初始化
        -> _idle_monitor thread
        -> _parent_monitor thread (如果 parent_pid 设置)
        -> _start_heartbeat_thread
        -> write state file
```
启动延迟来源：(1) Python 模块导入 (2) WSL 探测 (apply_backend_env) (3) socket 绑定 (4) 磁盘 I/O 写 state file

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| shell=True subprocess | 参数列表 subprocess (无 shell) | 项目初始设计 | 消除 shell injection 风险 |
| 各 provider 独立 daemon | UnifiedAskDaemon 单进程 | Phase 5-6 重构 | 减少进程数、统一管理 |
| os.chmod(0o600) 权限保护 | Windows 上被跳过或静默失败 | 始终如此 | Windows 需要替代方案 |
| msvcrt.locking 文件锁 | 同时支持 msvcrt + fcntl | 项目初始设计 | 跨平台锁已正确实现 |

**Deprecated/outdated:**
- `ProviderLock` 在 `process_lock.py` 中与 `FileLock` 在 `file_lock.py` 中功能重复 — 应统一使用 FileLock
- `_is_pid_alive()` 在三个文件中重复实现（process_lock.py、file_lock.py、askd_server.py） — 应提取为共享工具函数

## Open Questions

1. **daemon 冷启动的 Python 导入时间**
   - What we know: daemon 通过 `subprocess.Popen([sys.executable, "bin/askd"])` 启动，需要导入 threading、socketserver、json 等模块
   - What's unclear: Python 3.14 在 Windows 上的实际模块导入时间（3.14 是非常新的版本）
   - Recommendation: 先测量再优化，timeit 测量 isolated import time

2. **psutil 是否需要安装**
   - What we know: 内存测试需要 psutil，当前环境未安装
   - What's unclear: 是否可用 tracemalloc 替代（仅测量 Python 堆内存，不包含 C 扩展）
   - Recommendation: 安装 psutil（`pip install psutil`），它是测量进程 RSS 的标准工具

3. **mail/ 模块是否在本阶段审计范围内**
   - What we know: `lib/mail/` 下有 6 处 `chmod(0o600)` 调用缺少 Windows 守卫
   - What's unclear: mail 模块是否在"原生 Windows 环境"中运行（CONTEXT.md canonical refs 未列出 mail 模块）
   - Recommendation: 审计但降低优先级，mail 模块可能在 WSL 中运行

4. **install.ps1 在 PowerShell 7.x 中的行为差异**
   - What we know: 当前环境仅有 PS 5.1，CONTEXT.md D-10 要求测试 PS 5.1 兼容性
   - What's unclear: PS 7.x 中是否有兼容性问题（`[System.Text.UTF8Encoding]::new($false)` 在 PS 7 中可能行为不同）
   - Recommendation: 优先测试 PS 5.1，PS 7.x 作为扩展测试

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | 全部测试 | Yes | 3.14.2 | -- |
| pytest | 测试框架 | Yes | 9.0.2 | -- |
| PowerShell | install.ps1 测试 | Yes | 5.1 (Build 19041) | -- |
| psutil | 内存测试 (WIN-01) | No | -- | `pip install psutil` |
| WezTerm | 终端后端测试 | TBD | -- | 跳过 WezTerm 测试如果未安装 |
| WSL | WSL 路径探测测试 | TBD | -- | 跳过 WSL 测试如果未安装 |
| tmux | tmux 后端测试 | No (Windows native) | -- | 跳过 tmux 相关测试 |

**Missing dependencies with no fallback:**
- 无阻塞性缺失

**Missing dependencies with fallback:**
- psutil: 需安装，否则内存测试降级为 tracemalloc（仅 Python 堆）
- WezTerm: 如果未安装，跳过 WeztermBackend 相关测试
- WSL: 如果未安装，跳过 WSL 路径探测相关测试

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pytest.ini (需在 Wave 0 创建) |
| Quick run command | `python -m pytest tests/windows/ -x -v` |
| Full suite command | `python -m pytest tests/ -v --tb=short` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WIN-01 | daemon 冷启动 < 3s | perf | `pytest tests/windows/test_perf_daemon.py::test_daemon_cold_start_under_3s -x` | No - Wave 0 |
| WIN-01 | 命令响应 < 500ms | perf | `pytest tests/windows/test_perf_daemon.py::test_command_response_under_500ms -x` | No - Wave 0 |
| WIN-01 | 内存占用 < 50MB | perf | `pytest tests/windows/test_perf_daemon.py::test_daemon_memory_under_50mb -x` | No - Wave 0 |
| WIN-01 | socket 通信效率 | unit | `pytest tests/windows/test_perf_socket.py -x` | No - Wave 0 |
| WIN-02 | UTF-8 编码正确处理 | unit | `pytest tests/windows/test_compat_encoding.py::test_decode_utf8 -x` | No - Wave 0 |
| WIN-02 | GBK 编码回退 | unit | `pytest tests/windows/test_compat_encoding.py::test_decode_gbk_fallback -x` | No - Wave 0 |
| WIN-02 | Windows-1252 编码回退 | unit | `pytest tests/windows/test_compat_encoding.py::test_decode_windows_1252 -x` | No - Wave 0 |
| WIN-02 | Shift-JIS 编码回退 | unit | `pytest tests/windows/test_compat_encoding.py::test_decode_shift_jis -x` | No - Wave 0 |
| WIN-02 | 中文路径处理 | unit | `pytest tests/windows/test_compat_path.py::test_chinese_path -x` | No - Wave 0 |
| WIN-02 | UNC 路径处理 | unit | `pytest tests/windows/test_compat_path.py::test_unc_path -x` | No - Wave 0 |
| WIN-02 | PS 5.1 兼容性 | unit | `pytest tests/windows/test_compat_powershell.py -x` | No - Wave 0 |
| WIN-03 | token 不泄露到日志 | unit | `pytest tests/windows/test_security_token.py -x` | No - Wave 0 |
| WIN-03 | os.chmod Windows 行为 | unit | `pytest tests/windows/test_security_permission.py -x` | No - Wave 0 |
| WIN-03 | 无 eval/exec 调用 | unit | `pytest tests/windows/test_security_process.py -x` | No - Wave 0 |
| WIN-03 | subprocess 无 shell=True | unit | `pytest tests/windows/test_security_process.py -x` | No - Wave 0 |
| WIN-03 | socket 有认证机制 | unit | `pytest tests/windows/test_security_socket.py -x` | No - Wave 0 |
| WIN-03 | install.ps1 安装验证 | integration | `pytest tests/windows/test_install.ps1.py -x` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/windows/ -x -v`
- **Per wave merge:** `python -m pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/windows/__init__.py` — package init
- [ ] `tests/windows/conftest.py` — Windows-specific fixtures (中文路径 tmpdir, 环境隔离)
- [ ] `tests/windows/test_perf_daemon.py` — daemon 性能测试 (WIN-01)
- [ ] `tests/windows/test_perf_socket.py` — socket 通信效率测试 (WIN-01)
- [ ] `tests/windows/test_compat_encoding.py` — 编码处理测试 (WIN-02)
- [ ] `tests/windows/test_compat_path.py` — 路径转换测试 (WIN-02)
- [ ] `tests/windows/test_compat_powershell.py` — PowerShell 兼容性测试 (WIN-02)
- [ ] `tests/windows/test_security_token.py` — token 安全测试 (WIN-03)
- [ ] `tests/windows/test_security_permission.py` — 文件权限测试 (WIN-03)
- [ ] `tests/windows/test_security_process.py` — 进程安全测试 (WIN-03)
- [ ] `tests/windows/test_security_socket.py` — socket 安全测试 (WIN-03)
- [ ] `pytest.ini` — pytest 配置（含 Windows markers）
- [ ] psutil 安装: `pip install psutil`

## Sources

### Primary (HIGH confidence)
- Source code audit: lib/compat.py, lib/terminal.py, lib/process_lock.py, lib/file_lock.py, lib/ccb_config.py, lib/askd_server.py, lib/askd_client.py, lib/askd/daemon.py, lib/askd_rpc.py, lib/askd_runtime.py, lib/session_utils.py, lib/pane_registry.py, bin/ask, ccb, install.ps1
- pytest 9.0.2 — verified installed via `python -m pytest --version`
- Python 3.14.2 — verified via `python --version`
- PowerShell 5.1 (Build 19041) — verified via `$PSVersionTable.PSVersion`

### Secondary (MEDIUM confidence)
- grep audit: shell=True (none found), eval/exec (none found), chmod calls (12 found, 7 in mail/), os.name==nt (20+ locations), subprocess calls (20+ locations), token logging (none found in lib/)
- Windows NTFS ACL documentation: os.chmod behavior on Windows
- psutil documentation: Process.memory_info() for RSS measurement

### Tertiary (LOW confidence)
- mbcs encoding behavior on different Windows code pages — needs runtime verification
- Python 3.14 module import performance on Windows — no benchmark data available
- WezTerm Windows CLI compatibility — version-dependent

## Project Constraints (from CLAUDE.md)

- **技术栈**: Python 3.10+, Bash, PowerShell, TOML/JSON
- **兼容性**: 不破坏现有功能和 API
- **测试**: 使用 pytest（已安装 9.0.2）
- **GSD 工作流**: 通过 `/gsd:execute-phase` 执行
- **时间**: 可行性研究阶段，但 Phase 7 要求全部修复
- **输出**: 先问题清单，再按优先级修复

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pytest 9.0.2 verified, Python 3.14.2 verified
- Architecture: HIGH - 基于 98 个 Python 模块的完整代码审查
- Pitfalls: HIGH - 6 个 pitfall 全部有代码行引用
- Security: HIGH - 无 shell=True、无 eval/exec，但 token 明文和 chmod 失效已确认
- Performance: MEDIUM - 需实际运行测量，当前为代码路径分析

**Research date:** 2026-03-31
**Valid until:** 30 days (stable domain — Windows platform behavior does not change)
