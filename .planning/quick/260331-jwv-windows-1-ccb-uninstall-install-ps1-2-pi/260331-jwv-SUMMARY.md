---
phase: quick
plan: 260331-jwv
subsystem: windows-compat
tags: [windows, bugfix, installer, daemon, test]
dependency_graph:
  requires: []
  provides: [ccb-uninstall-windows-fix, daemon-ping-test-isolation]
  affects: [ccb, tests/windows/test_perf_daemon.py]
tech_stack:
  added: []
  patterns: [fallback-path-lookup, fixture-parameter-isolation]
key_files:
  created: []
  modified:
    - ccb
    - tests/windows/test_perf_daemon.py
decisions:
  - "fallback 到 Path(__file__).resolve().parent 而非依赖 _find_install_dir() 的返回值"
  - "从 daemon_proc fixture 直接提取 state_file，避免调用系统默认路径函数"
metrics:
  duration: "5min"
  completed_date: "2026-03-31"
  tasks_completed: 2
  files_modified: 2
---

# Phase quick Plan 260331-jwv: Windows CCB Uninstall & Daemon Ping Fix Summary

**One-liner:** `_run_installer` fallback to script source dir when install.ps1 absent in install_dir, plus daemon ping test isolation via `daemon_proc` fixture.

## Objective

修复两个 Windows 兼容性问题：
1. `ccb uninstall/reinstall` 在已安装环境中报错 "install.ps1 not found"
2. `test_daemon_ping_returns_true_when_running` 测试因 state_file 路径不一致失败

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | 修复 _run_installer fallback 路径 | f86f1a6 | ccb |
| 2 | 修复 ping 测试使用 daemon_proc state_file | b76705b | tests/windows/test_perf_daemon.py |

## Changes Made

### Task 1: ccb `_run_installer()` fallback

**File:** `ccb` (line ~4617)

**Before:**
```python
script = install_dir / "install.ps1"
if not script.exists():
    print(f"❌ install.ps1 not found in {install_dir}", file=sys.stderr)
    return 1
```

**After:**
```python
script = install_dir / "install.ps1"
if not script.exists():
    # Fallback: try the script's own source directory
    script_root = Path(__file__).resolve().parent
    script = script_root / "install.ps1"
if not script.exists():
    print(f"❌ install.ps1 not found in {install_dir} or {script.parent}", file=sys.stderr)
    return 1
```

### Task 2: `test_daemon_ping_returns_true_when_running` fixture 修复

**File:** `tests/windows/test_perf_daemon.py` (line ~242)

**Before:** 调用 `state_file_path("askd.json")` 返回系统默认路径，与 `daemon_proc` 使用的隔离 tmp_dir 不一致。

**After:** 从 `daemon_proc` fixture 解包 `state_file`，确保 `ping_daemon` 连接到实际运行的 daemon socket。

## Verification Results

完整 Windows 测试套件结果：

```
68 passed, 1 skipped in 9.14s
```

- `test_daemon_ping_returns_true_when_running`: PASSED
- 1 skip: `TestDaemonMemory::test_daemon_memory_under_50mb`（环境限制，非本次改动）

## Deviations from Plan

### Pre-existing Issue Discovered

**发现：** 单独运行 `tests/windows/test_perf_daemon.py::TestDaemonPing` 时（不通过完整测试套件），两个测试均报 `ModuleNotFoundError: No module named 'askd'`。

**根因：** conftest.py 未将项目根目录加入 `sys.path`，单独子集运行时 pytest 不从根目录启动。这与本次任务无关。

**验证：** git stash 后运行同样命令，相同错误——确认是预先存在问题。

**处置：** 记录为超出范围的已知问题，完整套件正常通过，任务目标达成。

## Known Stubs

无。

## Self-Check: PASSED

- [x] `ccb` 已修改，fallback 逻辑存在
- [x] `tests/windows/test_perf_daemon.py` 已修改，使用 daemon_proc fixture
- [x] Commit f86f1a6 存在
- [x] Commit b76705b 存在
- [x] 完整套件 68/69 通过（1 skip 为内存测试环境限制）
