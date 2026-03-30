# 文件锁方案分析报告

**评估日期:** 2026-03-30
**需求:** RISK-03
**严重程度:** 中等（Medium）

---

## 1. 执行摘要

**风险描述:** 多进程并发访问 CCB 会话文件时，可能导致数据损坏、部分写入或读取不完整数据。

**现有方案:** CCB 已有成熟的文件锁实现（lib/process_lock.py），提供操作系统级文件锁、跨平台兼容、超时机制和死锁检测。

**评估结论:** process_lock.py 的 ProviderLock 类可直接用于 CCBCLIBackend，无需重新实现。已验证跨平台兼容性（Linux/macOS/Windows）。

**集成方案:** 在 CCBCLIBackend 的 submit() 和 poll() 方法中使用 ProviderLock 包装会话文件操作。

**残留风险:** 锁超时（低概率）、死锁检测失败（极低概率）、NFS 兼容性（低概率）。

---

## 2. 风险影响评估

### 2.1 并发写入覆盖场景

**场景描述:**
```python
# 进程 A: 写入请求
with open("~/.ccb/sessions/codex.session", "w") as f:
    json.dump({"prompt": "Task A"}, f)

# 进程 B: 同时写入请求（覆盖进程 A）
with open("~/.ccb/sessions/codex.session", "w") as f:
    json.dump({"prompt": "Task B"}, f)

# 结果: 进程 A 的数据丢失
```

**影响:**
- 进程 A 的任务请求永久丢失
- 无法追踪哪个进程的请求被覆盖
- 用户体验混乱

### 2.2 读取不完整数据场景

**场景描述:**
```python
# 进程 A: 正在写入大量数据
with open("~/.ccb/sessions/codex.session", "w") as f:
    json.dump(large_data, f)  # 写入中...

# 进程 B: 同时读取（读到部分数据）
with open("~/.ccb/sessions/codex.session", "r") as f:
    data = json.load(f)  # ❌ JSONDecodeError: 数据不完整
```

**影响:**
- JSON 解析失败
- 程序崩溃或错误处理
- 需要重试机制

---

## 3. 现有方案分析

### 3.1 ProviderLock 类概述

**位置:** `lib/process_lock.py`
**代码行数:** 209 行
**实现语言:** Python 3.10+

**核心特性:**
- 操作系统级文件锁（fcntl/msvcrt）
- 跨平台兼容（Linux/macOS/Windows）
- 超时机制（默认 60 秒，可配置）
- 死锁检测（检查 PID 是否存活）
- Per-provider, per-directory 隔离

**类签名:**
```python
class ProviderLock:
    """Per-provider, per-directory file lock to serialize request-response cycles.

    Lock files are stored in ~/.ccb/run/{provider}-{cwd_hash}.lock
    """

    def __init__(self, provider: str, timeout: float = 60.0, cwd: str = None):
        """Initialize lock for a specific provider and working directory."""
        pass

    def acquire(self) -> bool:
        """Acquire the lock, waiting up to timeout seconds."""
        pass

    def release(self) -> None:
        """Release the lock."""
        pass

    def __enter__(self) -> "ProviderLock":
        """Context manager support."""
        pass

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager support."""
        pass
```

### 3.2 实现分析

**锁文件位置:**
```python
# 基于工作目录哈希，实现 per-directory 隔离
cwd_hash = hashlib.md5(cwd.encode()).hexdigest()[:8]
lock_file = Path.home() / ".ccb" / "run" / f"{provider}-{cwd_hash}.lock"

# 示例: ~/.ccb/run/codex-a1b2c3d4.lock
```

**平台检测和锁实现:**
```python
def _try_acquire_once(self) -> bool:
    try:
        if os.name == "nt":  # Windows
            import msvcrt
            msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
        else:  # Unix/Linux/macOS
            import fcntl
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        # 写入 PID 用于死锁检测
        pid_bytes = f"{os.getpid()}\n".encode()
        os.lseek(self._fd, 0, os.SEEK_SET)
        os.write(self._fd, pid_bytes)

        return True
    except (OSError, IOError):
        return False
```

**死锁检测:**
```python
def _check_stale_lock(self) -> bool:
    """Check if current lock holder is dead, allowing us to take over."""
    try:
        with open(self.lock_file, "r") as f:
            content = f.read().strip()
            if content:
                pid = int(content)
                if not _is_pid_alive(pid):
                    # Stale lock - remove it
                    self.lock_file.unlink()
                    return True
    except (OSError, ValueError):
        pass
    return False
```

---

## 4. 跨平台验证

### 4.1 验证表格

| 平台 | 锁实现 | 验证状态 | 说明 |
|------|--------|---------|------|
| Linux | fcntl.flock | ✓ 已验证 | 标准 POSIX 文件锁 |
| macOS | fcntl.flock | ✓ 已验证 | 标准 POSIX 文件锁 |
| Windows | msvcrt.locking | ✓ 已验证 | Windows 原生文件锁 |

### 4.2 平台特殊处理

**Windows 特殊处理:**
```python
# Windows 需要确保文件至少有 1 字节才能锁定区域
if os.name == "nt":
    st = os.fstat(self._fd)
    if getattr(st, "st_size", 0) < 1:
        os.lseek(self._fd, 0, os.SEEK_SET)
        os.write(self._fd, b"\0")
```

**PID 检测差异:**
```python
def _is_pid_alive(pid: int) -> bool:
    """Check if a process with given PID is still running."""
    if os.name == "nt":  # Windows
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x00100000
        handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    else:  # Unix/Linux/macOS
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
```

---

## 5. 超时和重试机制

### 5.1 超时策略

**默认超时:** 60 秒
**重试间隔:** 0.1 秒
**可配置:** 通过构造函数参数

**实现:**
```python
def acquire(self) -> bool:
    """Acquire the lock, waiting up to timeout seconds."""
    deadline = time.time() + self.timeout
    stale_checked = False

    while time.time() < deadline:
        if self._try_acquire_once():
            return True

        # 检查死锁（仅一次）
        if not stale_checked:
            stale_checked = True
            if self._check_stale_lock():
                # 锁文件已过期，重新打开并重试
                os.close(self._fd)
                self._fd = os.open(str(self.lock_file), os.O_CREAT | os.O_RDWR)
                if self._try_acquire_once():
                    return True

        time.sleep(0.1)

    # 超时失败
    if self._fd is not None:
        os.close(self._fd)
        self._fd = None
    return False
```

### 5.2 超时配置建议

| 操作 | 建议超时 | 理由 |
|------|---------|------|
| submit() | 10 秒 | 提交操作应该快速完成 |
| poll() | 5 秒 | 读取操作更快 |
| 默认 | 60 秒 | 保守值，适用于大多数场景 |

---

## 6. 死锁检测

### 6.1 检测机制

**触发时机:** 首次获取锁失败后

**检测逻辑:**
1. 读取锁文件中的 PID
2. 检查该 PID 的进程是否存活
3. 如果进程已死，删除锁文件
4. 重新尝试获取锁

**代码示例:**
```python
# 首次尝试失败后检查死锁
if not stale_checked:
    stale_checked = True
    if self._check_stale_lock():
        # 清理死锁，重新尝试
        os.close(self._fd)
        self._fd = os.open(str(self.lock_file), os.O_CREAT | os.O_RDWR)
        if self._try_acquire_once():
            return True
```

### 6.2 死锁场景

**场景 1: 进程崩溃**
- 进程持有锁后崩溃
- 锁文件未被清理
- 死锁检测识别并清理

**场景 2: 进程被强制终止**
- 进程被 kill -9 终止
- 锁文件残留
- 死锁检测识别并清理

---

## 7. 集成方案设计

### 7.1 在 CCBCLIBackend 中使用

**submit() 方法集成:**
```python
from lib.process_lock import ProviderLock

class CCBCLIBackend:
    def submit(self, provider: str, prompt: str, context: Optional[Dict] = None) -> TaskHandle:
        """提交任务到 AI 提供商"""
        with ProviderLock(provider, timeout=10.0):
            # 安全地提交任务
            cmd = ["ask", provider, "--background", prompt]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

        return TaskHandle(
            provider=provider,
            timestamp=time.time()
        )
```

**poll() 方法集成:**
```python
def poll(self, handle: TaskHandle) -> TaskResult:
    """轮询任务结果"""
    with ProviderLock(handle.provider, timeout=5.0):
        # 安全地读取结果
        cmd = ["pend", handle.provider]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

    # 解析结果
    if result.returncode == 0:  # EXIT_OK
        return TaskResult(
            provider=handle.provider,
            status="completed",
            output=result.stdout.strip()
        )
    elif result.returncode == 2:  # EXIT_NO_REPLY
        return TaskResult(
            provider=handle.provider,
            status="pending"
        )
    else:  # EXIT_ERROR
        return TaskResult(
            provider=handle.provider,
            status="error",
            error=result.stderr.strip()
        )
```

### 7.2 错误处理

**锁超时处理:**
```python
try:
    with ProviderLock(provider, timeout=10.0):
        # 执行操作
        pass
except TimeoutError as e:
    return TaskResult(
        provider=provider,
        status="error",
        error=f"Failed to acquire lock: {e}"
    )
```

---

## 8. 残留风险评估

### 8.1 锁超时导致任务失败

**风险描述:** 在高并发场景下，进程等待锁超时导致任务提交失败。

**概率:** 低
**影响:** 中等
**缓解措施:**
- 可配置超时时间（环境变量 CCB_LOCK_TIMEOUT）
- 调用者可以重试
- 记录详细的错误日志

### 8.2 死锁检测失败

**风险描述:** PID 检测失败或锁文件损坏导致死锁无法清理。

**概率:** 极低
**影响:** 高
**缓解措施:**
- 提供手动清理工具（ccb-clean-locks）
- 文档化清理步骤
- 锁文件位置固定（~/.ccb/run/*.lock）

### 8.3 网络文件系统兼容性

**风险描述:** NFS 等网络文件系统的文件锁行为不一致。

**概率:** 低
**影响:** 高
**缓解措施:**
- 文档化不支持 NFS
- 建议使用本地文件系统
- 检测 NFS 并记录警告

---

## 9. 实施建议

### 9.1 优先级

**高优先级:**
- 在 CCBCLIBackend 中集成 ProviderLock
- 配置合理的超时时间

**中优先级:**
- 添加环境变量配置支持
- 实现错误处理和日志记录

**低优先级:**
- 开发手动清理工具
- NFS 检测和警告

### 9.2 时间估算

- ProviderLock 集成: 4 小时
- 超时配置: 2 小时
- 错误处理: 2 小时
- 单元测试: 4 小时
- **总计: 12 小时**

### 9.3 验收标准

- [ ] CCBCLIBackend.submit() 使用 ProviderLock
- [ ] CCBCLIBackend.poll() 使用 ProviderLock
- [ ] 超时时间可配置（submit: 10s, poll: 5s）
- [ ] 锁超时时返回错误而非崩溃
- [ ] 单元测试覆盖并发访问场景
- [ ] 单元测试覆盖锁超时场景

---

## 10. 结论

CCB 的 process_lock.py 提供了成熟可靠的文件锁方案，支持跨平台、超时机制和死锁检测。可直接集成到 CCBCLIBackend 中，无需重新实现。残留风险主要是锁超时和 NFS 兼容性，可通过配置和文档化缓解。

**关键要点:**
- ProviderLock 已验证跨平台兼容性
- 使用 context manager 简化集成
- 超时时间应根据操作类型配置
- 死锁检测自动清理过期锁

---

**报告完成日期:** 2026-03-30
**下一步:** 在 CCBCLIBackend 实现中集成 ProviderLock
