# Phase 7: Windows Native Audit — Fix Plan

**Generated:** 2026-03-31T03:39:00Z
**Source:** 07-ISSUE-LIST.md (13 issues)
**Scope:** All issues (Critical, High, Medium, Low) per D-14

## Priority Order

Fixes are ordered by dependency and impact:
1. WIN-01-001 (protocol prefix) — unblocks 4 of 5 test failures
2. WIN-01-002 (import path) — unblocks remaining test failure
3. WIN-02-002 (WSL probe timeout) — highest user-impact performance fix
4. WIN-02-004 (chmod guards) — security intent fix for 7 locations
5. WIN-02-001 (mbcs fallback) — encoding robustness
6. WIN-02-003 (PowerShell escaping) — path edge case
7. WIN-03-001 (token plaintext) — security hardening
8. WIN-03-002 (timing-unsafe comparison) — defense in depth
9. WIN-03-004 (SO_EXCLUSIVEADDRUSE) — Windows-specific hardening
10. WIN-03-003 (TLS/SSL) — design-level, lowest priority
11. WIN-02-005 (CREATE_NO_WINDOW) — import path resilience
12. WIN-01-003 (psutil for memory) — test infrastructure
13. WIN-01-004 (WSL conditional delay) — derived from WIN-02-002

---

## Fix: WIN-01-001 — Wrong protocol prefix in perf/e2e tests

**Priority:** 1 (unblocks 4 of 5 test failures)
**Files:**
- `tests/windows/test_e2e_commands.py:110` (`"type": "askd.ping"`)
- `tests/windows/test_perf_daemon.py:113` (`"type": "askd.ping"`)
- `tests/windows/test_perf_socket.py:32` (`_make_ping_request` helper)
- `tests/windows/test_perf_socket.py:142` (concurrent test inline)
**Risk:** Low (test-only change, aligns with working protocol)

### Current Code

```python
# tests/windows/test_e2e_commands.py:109-114
req = json.dumps({
    "type": "askd.ping",
    "v": 1,
    "id": "e2e-ping-test",
    "token": token,
}) + "\n"

# tests/windows/test_perf_daemon.py:112-117
req = json.dumps({
    "type": "askd.ping",
    "v": 1,
    "id": "perf-test-ping",
    "token": token,
}) + "\n"

# tests/windows/test_perf_socket.py:31-36
def _make_ping_request(token: str) -> str:
    """Build a JSON ping request string."""
    return json.dumps({
        "type": "askd.ping",
        "v": 1,
        "id": "socket-perf-test",
        "token": token,
    }) + "\n"

# tests/windows/test_perf_socket.py:141-146
req = json.dumps({
    "type": "askd.ping",
    "v": 1,
    "id": f"concurrent-{idx}",
    "token": token,
}) + "\n"
```

### Fixed Code

```python
# tests/windows/test_e2e_commands.py:109-114
req = json.dumps({
    "type": "ask.ping",
    "v": 1,
    "id": "e2e-ping-test",
    "token": token,
}) + "\n"

# tests/windows/test_perf_daemon.py:112-117
req = json.dumps({
    "type": "ask.ping",
    "v": 1,
    "id": "perf-test-ping",
    "token": token,
}) + "\n"

# tests/windows/test_perf_socket.py:31-36
def _make_ping_request(token: str) -> str:
    """Build a JSON ping request string."""
    return json.dumps({
        "type": "ask.ping",
        "v": 1,
        "id": "socket-perf-test",
        "token": token,
    }) + "\n"

# tests/windows/test_perf_socket.py:141-146
req = json.dumps({
    "type": "ask.ping",
    "v": 1,
    "id": f"concurrent-{idx}",
    "token": token,
}) + "\n"
```

### Why This Fix
The unified daemon protocol (ASKD_SPEC) uses prefix `"ask"`, not `"askd"`. This was already fixed in Plan 03's security tests (`test_security_socket.py`), but the perf and e2e tests were not updated. The fix is a simple string replacement from `"askd.ping"` to `"ask.ping"` across 4 locations in 3 files.

### Verification
- Test: `python -m pytest tests/windows/test_perf_daemon.py::TestCommandResponse -x`
- Test: `python -m pytest tests/windows/test_perf_socket.py -x`
- Test: `python -m pytest tests/windows/test_e2e_commands.py::TestE2EAskPing -x`
- Test: `python -m pytest tests/windows/ -v --tb=short` (full suite, expect 1 failure instead of 5)

---

## Fix: WIN-01-002 — Import path error in E2E test

**Priority:** 2 (unblocks remaining test failure)
**Files:** `tests/windows/test_e2e_commands.py:192`
**Risk:** Low (test-only change)

### Current Code

```python
# tests/windows/test_e2e_commands.py:192
from lib.askd.daemon import shutdown_daemon
```

### Fixed Code

```python
# tests/windows/test_e2e_commands.py:192
import subprocess
# Use direct subprocess to stop daemon instead of importing internal module
# The askd package may not be importable from tests/
```

Then replace the shutdown_daemon call with:
```python
# Instead of: shutdown_daemon(state_file)
# Use: direct process termination
proc.terminate()
proc.wait(timeout=5)
```

The full fix requires reading the test function and adapting it to not rely on the internal `shutdown_daemon` import. The test's intent is to verify daemon lifecycle (start -> verify state -> stop -> verify cleanup). The stop step can be achieved by terminating the daemon process directly.

```python
# tests/windows/test_e2e_commands.py:190-210 (full function rewrite)
def test_e2e_ccb_start_stop_cycle(self, tmp_path):
    """Full lifecycle: start daemon -> verify state -> stop daemon -> verify cleanup."""
    import tempfile

    tmp_dir = Path(tempfile.mkdtemp(prefix="askd_e2e_lifecycle_"))
    try:
        proc, state_file, ok = _start_isolated_daemon(tmp_dir)
        assert ok, "Daemon crashed during startup"

        # Verify state file exists and has expected fields
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert "token" in state
        assert "port" in state
        assert "pid" in state

        # Stop daemon by terminating process
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)

        # Verify cleanup: state file should remain (daemon doesn't auto-delete)
        assert state_file.exists(), "State file should persist after clean shutdown"
    finally:
        _stop_daemon(proc, tmp_dir)
```

### Why This Fix
The `lib.askd.daemon` module imports from `askd.adapters.base` which is a separate package. Importing internal daemon modules from tests creates fragile coupling. Direct process termination is the correct test approach for lifecycle verification.

### Verification
- Test: `python -m pytest tests/windows/test_e2e_commands.py::TestE2ECcbStartStop -x`
- Test: `python -m pytest tests/windows/ -v --tb=short` (full suite, expect 0 failures)

---

## Fix: WIN-02-002 — WSL probe timeout on native Windows

**Priority:** 3 (highest user-impact performance fix)
**Files:** `lib/ccb_config.py:128-168`
**Risk:** Medium (changes startup behavior, needs testing with/without WSL)

### Current Code

```python
# lib/ccb_config.py:128-168
def _wsl_probe_distro_and_home() -> tuple[str, str]:
    """Probe default WSL distro and home directory"""
    try:
        r = subprocess.run(
            ["wsl.exe", "-e", "sh", "-lc", "echo $WSL_DISTRO_NAME; echo $HOME"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            **_subprocess_kwargs()
        )
        if r.returncode == 0:
            lines = r.stdout.strip().split("\n")
            if len(lines) >= 2:
                return lines[0].strip(), lines[1].strip()
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["wsl.exe", "-l", "-q"],
            capture_output=True, text=True, encoding="utf-16-le", errors="replace", timeout=5,
            **_subprocess_kwargs()
        )
        # ... fallback logic
    except Exception:
        pass
    # ... more fallback
```

### Fixed Code

```python
# lib/ccb_config.py:128-168
def _wsl_probe_distro_and_home() -> tuple[str, str]:
    """Probe default WSL distro and home directory.

    On native Windows without WSL, returns defaults immediately after
    a fast check (< 2s timeout) instead of waiting 10+ seconds.
    """
    # Fast check: is WSL installed at all?
    try:
        r = subprocess.run(
            ["wsl.exe", "--list", "--quiet"],
            capture_output=True, text=True, encoding="utf-16-le",
            errors="replace", timeout=2,
            **_subprocess_kwargs()
        )
        if r.returncode != 0:
            # WSL not available or not installed
            return "", ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # wsl.exe doesn't exist or timed out — no WSL
        return "", ""

    # WSL is available, probe distro and home
    try:
        r = subprocess.run(
            ["wsl.exe", "-e", "sh", "-lc", "echo $WSL_DISTRO_NAME; echo $HOME"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
            **_subprocess_kwargs()
        )
        if r.returncode == 0:
            lines = r.stdout.strip().split("\n")
            if len(lines) >= 2:
                return lines[0].strip(), lines[1].strip()
    except Exception:
        pass

    # Fallback: try to list distros and probe the default
    try:
        r = subprocess.run(
            ["wsl.exe", "-l", "-q"],
            capture_output=True, text=True, encoding="utf-16-le", errors="replace", timeout=5,
            **_subprocess_kwargs()
        )
        if r.returncode == 0:
            for line in r.stdout.strip().split("\n"):
                distro = line.strip().strip("\x00")
                if distro:
                    break
            else:
                distro = "Ubuntu"
        else:
            distro = "Ubuntu"
    except Exception:
        distro = "Ubuntu"
    try:
        r = subprocess.run(
            ["wsl.exe", "-d", distro, "-e", "sh", "-lc", "echo $HOME"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
            **_subprocess_kwargs()
        )
        home = r.stdout.strip() if r.returncode == 0 else "/root"
    except Exception:
        home = "/root"
    return distro, home
```

Also update `apply_backend_env()` to handle empty distro gracefully:

```python
# lib/ccb_config.py:171-188
def apply_backend_env() -> None:
    """Apply BackendEnv=wsl settings (set session root paths for Windows to access WSL)"""
    if sys.platform != "win32" or get_backend_env() != "wsl":
        return
    if os.environ.get("CODEX_SESSION_ROOT") and os.environ.get("GEMINI_ROOT"):
        return
    distro, home = _wsl_probe_distro_and_home()
    if not distro:
        # WSL not available, skip WSL path setup
        return
    # ... rest of existing logic
```

### Why This Fix
The fast check (`wsl.exe --list --quiet` with 2s timeout) runs first. If WSL is not installed, it either returns non-zero or times out in 2 seconds (vs the current 10+ second worst case). The return value `("", "")` signals to `apply_backend_env()` to skip WSL path setup entirely. This eliminates the 10-20s delay for non-WSL users while keeping full WSL probing for users who have it installed.

**Alternatives considered:**
1. Cache the WSL check result in a temp file — adds state management complexity for marginal gain.
2. Check for wsl.exe existence before running — the `FileNotFoundError` catch already handles this.

### Verification
- Test: `python -m pytest tests/windows/test_compat_path.py::TestWSLProbe -x`
- Manual: Set `CCB_BACKEND_ENV=wsl` on a machine without WSL, measure daemon startup time (should be < 2s overhead, not 10-20s)
- Manual: On a machine with WSL, verify `CODEX_SESSION_ROOT` and `GEMINI_ROOT` are still set correctly

---

## Fix: WIN-02-004 — Add os.name != "nt" guard to chmod calls in mail/ modules

**Priority:** 4
**Files:**
- `lib/mail/ask_handler.py:96-98`
- `lib/mail/config.py:335-337`
- `lib/mail/config.py:432-434`
- `lib/mail/daemon.py:94-96`
- `lib/mail/credentials.py:111-113`
- `lib/mail/threads.py:80-82`
- `lib/mail/attachments.py:95-97`
**Risk:** Low (matches existing pattern in askd_server.py:297)

### Current Code (example from each file)

```python
# lib/mail/ask_handler.py:96-98
context_file.chmod(0o600)

# lib/mail/config.py:335-337
config_dir.chmod(0o700)

# lib/mail/config.py:432-434
config_path.chmod(0o600)

# lib/mail/daemon.py:94-96
state_path.chmod(0o600)

# lib/mail/credentials.py:111-113
fallback_path.chmod(0o600)

# lib/mail/threads.py:80-82
self.threads_file.chmod(0o600)

# lib/mail/attachments.py:95-97
local_path.chmod(0o600)
```

### Fixed Code

```python
# lib/mail/ask_handler.py:96-100
if os.name != "nt":
    try:
        context_file.chmod(0o600)
    except OSError:
        pass

# lib/mail/config.py:335-340
if os.name != "nt":
    try:
        config_dir.chmod(0o700)
    except OSError:
        pass

# lib/mail/config.py:432-437
if os.name != "nt":
    try:
        config_path.chmod(0o600)
    except OSError:
        pass

# lib/mail/daemon.py:94-99
if os.name != "nt":
    try:
        state_path.chmod(0o600)
    except OSError:
        pass

# lib/mail/credentials.py:111-116
if os.name != "nt":
    try:
        fallback_path.chmod(0o600)
    except OSError:
        pass

# lib/mail/threads.py:80-85
if os.name != "nt":
    try:
        self.threads_file.chmod(0o600)
    except OSError:
        pass

# lib/mail/attachments.py:95-100
if os.name != "nt":
    try:
        local_path.chmod(0o600)
    except OSError:
        pass
```

Note: Each file needs `import os` at the top if not already present. Check each file first.

### Why This Fix
This follows the exact pattern used in `lib/askd_server.py:297-301`. On Windows NTFS, `os.chmod()` with Unix permission bits has no meaningful effect. The guard prevents the misleading call entirely. The try/except wrapping prevents any edge case failures on unusual filesystems.

### Verification
- Test: `python -m pytest tests/windows/test_security_permission.py::test_mail_modules_missing_nt_guard -x` (should XPASS — xfail becomes pass)
- Test: `python -m pytest tests/windows/test_security_permission.py -v`

---

## Fix: WIN-02-001 — mbcs encoding fallback data loss

**Priority:** 5
**Files:** `lib/compat.py:63-67`
**Risk:** Low

### Current Code

```python
# lib/compat.py:63-67
if sys.platform == "win32":
    try:
        return data.decode("mbcs", errors="strict")
    except Exception:
        pass
```

### Fixed Code

```python
# lib/compat.py:63-67
if sys.platform == "win32":
    try:
        return data.decode("mbcs", errors="replace")
    except Exception:
        pass
```

### Why This Fix
Changing `errors="strict"` to `errors="replace"` in the mbcs fallback makes the behavior predictable. With strict mode, mbcs either succeeds (possibly returning garbled text if the input doesn't match the system code page) or raises an exception (falling through to the next step). With `errors="replace"`, mbcs always succeeds and replaces unknown bytes with the Unicode replacement character (U+FFFD), making the output consistent and never raising an exception.

**Alternatives considered:**
1. Remove mbcs entirely — would skip a potentially valid decode path for users whose input matches their system code page.
2. Use `errors="surrogateescape"` — would preserve bytes as lone surrogates, defeating the docstring's goal of avoiding lone surrogates.

### Verification
- Test: `python -m pytest tests/windows/test_compat_encoding.py::TestEncodingFallback -v`
- Manual: Verify `decode_stdin_bytes(b"\x80\x81\x82")` returns a string (no crash)

---

## Fix: WIN-02-003 — bin/ask PowerShell path escaping incomplete

**Priority:** 6
**Files:** `bin/ask:676-677`
**Risk:** Low (edge case paths)

### Current Code

```python
# bin/ask:676-677
status_file_win = str(status_file).replace('"', '`"')
log_file_win = str(log_file).replace('"', '`"')
```

### Fixed Code

```python
# bin/ask:676-677 (add a helper function or inline)
def _ps_escape_path(p: str) -> str:
    """Escape a file path for embedding in a PowerShell double-quoted string."""
    s = str(p)
    # Escape backtick first (it's the escape char in PS double-quoted strings)
    s = s.replace('`', '``')
    # Escape $ to prevent variable expansion
    s = s.replace('$', '`$')
    # Escape double quotes
    s = s.replace('"', '`"')
    return s

status_file_win = _ps_escape_path(status_file)
log_file_win = _ps_escape_path(log_file)
```

Also search for any other path embedding in PowerShell scripts in bin/ask and apply the same escaping.

### Why This Fix
In PowerShell double-quoted strings, `` ` `` is the escape character, `$` triggers variable expansion, and `"` ends the string. The current code only escapes `"`, leaving `$` and `` ` `` unescaped. This fix escapes all three special characters in the correct order (backtick first, since it's the escape character itself).

### Verification
- Test: `python -m pytest tests/windows/test_compat_powershell.py::TestBinAskPowershellPathEscaping -v`
- Manual: Create a temp directory with `$` in the name (e.g., via `subst X: "C:\temp$test"`), run `bin/ask` and verify no PS errors

---

## Fix: WIN-03-001 — Token plaintext storage in daemon state file

**Priority:** 7
**Files:**
- `lib/askd_runtime.py:111-112` (token generation — no change needed)
- `lib/askd_server.py:293-301` (state file write)
**Risk:** Medium (changes security behavior)

### Current Code

```python
# lib/askd_runtime.py:111-112
def random_token() -> str:
    return os.urandom(16).hex()

# lib/askd_server.py:293-301
payload = {
    "token": self.token,
    # ...
}
self.state_file.parent.mkdir(parents=True, exist_ok=True)
ok, _err = safe_write_session(self.state_file, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
if ok:
    if os.name != "nt":
        try:
            os.chmod(self.state_file, 0o600)
        except Exception:
            pass
```

### Fixed Code

For Windows, use the registry or a Windows ACL approach. For a minimal fix that works cross-platform:

```python
# lib/askd_server.py (after state file write, around line 295-301)
ok, _err = safe_write_session(self.state_file, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
if ok:
    if os.name == "nt":
        # On Windows, restrict file permissions via icacls (ACL)
        # This grants access only to the current user
        try:
            import subprocess
            state_path = str(self.state_file)
            # Remove inherited permissions and grant full control to current user only
            subprocess.run(
                ["icacls", state_path, "/inheritance:r", "/grant:r", f"{os.environ.get('USERNAME', '')}:F"],
                capture_output=True, timeout=5,
            )
        except Exception:
            pass  # Best-effort security hardening
    else:
        try:
            os.chmod(self.state_file, 0o600)
        except Exception:
            pass
```

**Alternative (simpler):** For single-user local daemon, the plaintext token is acceptable since the socket is localhost-only. Document the limitation in a comment and add a TODO for DPAPI integration in a future version:

```python
# lib/askd_server.py:295-301 (minimal fix with documentation)
ok, _err = safe_write_session(self.state_file, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
if ok:
    if os.name != "nt":
        try:
            os.chmod(self.state_file, 0o600)
        except Exception:
            pass
    # TODO: On Windows, consider using DPAPI (win32crypt.CryptProtectData)
    # to encrypt the token in the state file. Current mitigation: localhost-only
    # socket binding means only local processes can reach the daemon.
```

### Why This Fix
The recommended approach is the **minimal documentation fix**. The token is already localhost-only, and the socket has token authentication (WIN-03 confirmed positive). Adding DPAPI encryption would require the `pywin32` dependency and significant refactoring of the token lifecycle (encrypt on write, decrypt on read, decrypt on every request validation). This is better suited for a dedicated security hardening plan. For now, document the limitation and ensure the Windows chmod behavior is clear.

### Verification
- Test: `python -m pytest tests/windows/test_security_token.py -v`
- Manual: Verify state file still works for daemon startup/shutdown

---

## Fix: WIN-03-002 — Timing-unsafe token comparison

**Priority:** 8
**Files:** `lib/askd_server.py:118`
**Risk:** Low (standard library change, no behavioral change)

### Current Code

```python
# lib/askd_server.py:118
if msg.get("token") != self.server.token:
    self._write({"type": response_type, "v": 1, "id": msg.get("id"), "exit_code": 1, "reply": "Unauthorized"})
    return
```

### Fixed Code

```python
# lib/askd_server.py:118
import hmac as _hmac

token_val = msg.get("token") or ""
expected = self.server.token or ""
if not _hmac.compare_digest(token_val, expected):
    self._write({"type": response_type, "v": 1, "id": msg.get("id"), "exit_code": 1, "reply": "Unauthorized"})
    return
```

Note: `import hmac` should be added at the top of the file with other imports.

### Why This Fix
`hmac.compare_digest()` performs a constant-time string comparison, eliminating the timing side-channel. On localhost, the practical risk is near-zero (OS scheduling noise dominates), but this is a one-line fix with zero cost and follows security best practices.

### Verification
- Test: `python -m pytest tests/windows/test_security_socket.py -v`
- Test: `python -m pytest tests/windows/test_e2e_commands.py -v` (after WIN-01-001 fix)

---

## Fix: WIN-03-004 — Missing SO_EXCLUSIVEADDRUSE on Windows

**Priority:** 9
**Files:** `lib/askd_server.py` (server class initialization)
**Risk:** Low

### Current Code

The `AskDaemonServer` inherits from `socketserver.ThreadingTCPServer` which uses default socket options.

### Fixed Code

```python
# In the server class or its __init__:
import sys

if sys.platform == "win32":
    import socket
    # Set SO_EXCLUSIVEADDRUSE to prevent port hijacking on Windows
    socket.SO_EXCLUSIVEADDRUSE = getattr(socket, "SO_EXCLUSIVEADDRUSE", 0)
```

If the server class allows custom `allow_reuse_address` or socket options, add:

```python
class AskDaemonServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    allow_reuse_port = False

    def server_bind(self):
        if sys.platform == "win32":
            self.socket.setsockopt(
                socket.SOL_SOCKET,
                getattr(socket, "SO_EXCLUSIVEADDRUSE", 0),
                1
            )
        super().server_bind()
```

### Why This Fix
`SO_EXCLUSIVEADDRUSE` prevents other processes from binding to the same port during the TIME_WAIT state. This is a Windows-specific socket option that closes a theoretical local attack vector. The fix is additive — it doesn't change existing behavior, only adds an extra layer of protection.

### Verification
- Test: `python -m pytest tests/windows/test_security_socket.py::test_socket_binds_localhost_only -x`
- Manual: Start daemon, try to bind another process to the same port (should fail)

---

## Fix: WIN-03-003 — No TLS/SSL on daemon socket

**Priority:** 10 (lowest — design-level change)
**Files:** `lib/askd_server.py` (entire module)
**Risk:** High (significant refactoring, new dependency possible)

### Assessment
Adding TLS to the localhost daemon socket requires:
1. Generating or loading an SSL certificate (self-signed for localhost)
2. Wrapping the socket with `ssl.wrap_socket()` or using `ssl.SSLContext`
3. Handling certificate errors gracefully
4. Potentially adding `pyOpenSSL` or using Python's built-in `ssl` module

This is a design-level change that significantly increases complexity for marginal security gain on localhost-only binding. **Recommendation: defer to a dedicated security hardening phase.**

### Minimal Mitigation (for now)

Add a comment documenting the design decision:

```python
# lib/askd_server.py (near class definition)
# SECURITY NOTE: The daemon socket uses plain TCP without TLS/SSL.
# This is acceptable because:
# 1. The socket binds to 127.0.0.1 only (localhost)
# 2. All requests require token authentication (128-bit random)
# 3. Local traffic sniffing requires elevated privileges
# Future: Add optional TLS for environments requiring encryption at rest.
```

### Verification
- Documentation-only change, no functional verification needed

---

## Fix: WIN-02-005 — CREATE_NO_WINDOW import path resilience

**Priority:** 11
**Files:** `lib/ccb_config.py:10-13`
**Risk:** Low

### Current Code

```python
# lib/ccb_config.py:10-13
try:
    from terminal import _subprocess_kwargs
except ModuleNotFoundError:
    from lib.terminal import _subprocess_kwargs
```

### Fixed Code

```python
# lib/ccb_config.py:10-13
try:
    from terminal import _subprocess_kwargs
except ModuleNotFoundError:
    try:
        from lib.terminal import _subprocess_kwargs
    except ModuleNotFoundError:
        def _subprocess_kwargs() -> dict:
            """Fallback subprocess kwargs when terminal module is unavailable."""
            import sys
            kwargs = {}
            if sys.platform == "win32":
                # CREATE_NO_WINDOW = 0x08000000 prevents CMD window flash
                CREATE_NO_WINDOW = 0x08000000
                kwargs["creationflags"] = CREATE_NO_WINDOW
            return kwargs
```

### Why This Fix
If both import paths fail (unlikely but possible in unusual deployment scenarios), the code currently crashes. The fallback provides the essential `CREATE_NO_WINDOW` flag directly, which is the only Windows-specific behavior needed from `_subprocess_kwargs()`.

### Verification
- Test: `python -c "from lib.ccb_config import _wsl_probe_distro_and_home; print('import ok')"`
- Manual: Verify no CMD window flash when running `apply_backend_env()` on Windows

---

## Fix: WIN-01-003 — Install psutil for memory measurement

**Priority:** 12
**Files:** None (dependency installation)
**Risk:** None

### Action
```bash
pip install psutil
```

Then re-run the memory test:
```bash
python -m pytest tests/windows/test_perf_daemon.py::TestDaemonMemory -x -v
```

### Why This Fix
psutil is the standard tool for measuring process RSS memory. The test already has `pytest.importorskip("psutil")` guard, so it gracefully skips when not installed. Installing it enables the D-08 verification (<50MB memory).

### Verification
- Test: `python -m pytest tests/windows/test_perf_daemon.py::TestDaemonMemory -x -v`
- Expected: PASS (not SKIPPED)

---

## Fix: WIN-01-004 — WSL probe conditional startup delay

**Priority:** 13 (derived from WIN-02-002)
**Files:** Resolved by WIN-02-002 fix

### Assessment
This issue is a consequence of WIN-02-002. When the fast WSL check is implemented (WIN-02-002 fix), the `apply_backend_env()` function will also short-circuit when `_wsl_probe_distro_and_home()` returns `("", "")`. No separate fix needed.

### Verification
- After WIN-02-002 fix: `python -m pytest tests/windows/ -v` should show no performance regression

---

## Fix Dependency Graph

```
WIN-01-001 (protocol prefix) ──────────────────────┐
WIN-01-002 (import path) ──────────────────────────┤
                                                   ├──> Full test suite passes (0 failures)
WIN-02-002 (WSL timeout) ──> WIN-01-004 (derived) ─┤
                                                   │
WIN-02-004 (chmod guards) ────────────────────────┤
WIN-02-001 (mbcs fallback) ───────────────────────┤
WIN-02-003 (PS escaping) ─────────────────────────┤
WIN-02-005 (import resilience) ───────────────────┤
                                                   │
WIN-03-002 (timing-safe) ─────────────────────────┤
WIN-03-004 (EXCLUSIVEADDRUSE) ────────────────────┤
                                                   │
WIN-03-001 (token plaintext) ─> document only ────┤
WIN-03-003 (TLS/SSL) ────────> defer ─────────────┘
WIN-01-003 (psutil install) ──────────────────────┘
```

**Recommended implementation order for Plan 07-05:**
1. WIN-01-001 + WIN-01-002 (test fixes — gets full suite green)
2. WIN-02-002 (WSL probe — highest user impact)
3. WIN-02-004 (chmod guards — security intent)
4. WIN-03-002 (timing-safe — one-line fix)
5. WIN-02-001 (mbcs — one-line fix)
6. WIN-02-003 (PS escaping — edge case)
7. WIN-02-005 (import resilience — defensive)
8. WIN-03-004 (EXCLUSIVEADDRUSE — defensive)
9. WIN-01-003 (psutil install — test infrastructure)
10. WIN-03-001 (document token limitation)
11. WIN-03-003 (document TLS limitation)
