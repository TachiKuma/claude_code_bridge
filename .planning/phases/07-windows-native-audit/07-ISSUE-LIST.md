# Phase 7: Windows Native Audit — Issue List

**Generated:** 2026-03-31T03:39:00Z
**Test results:** 69 tests, 62 passed, 5 failed, 1 skipped, 1 xfailed
**Test run date:** 2026-03-31
**Platform:** Windows 10 Pro 10.0.19045, Python 3.14.2, pytest 9.0.2

## Summary

| Severity | Count | Dimension |
|----------|-------|-----------|
| High | 5 | Performance (1), Compatibility (3), Security (1) |
| Medium | 5 | Security (3), Compatibility (1), Performance (1) |
| Low | 3 | Security (2), Performance (1) |
| **Total Issues** | **13** | |

| Positive Finding | Dimension |
|------------------|-----------|
| No shell=True in codebase | Security |
| No eval/exec in codebase | Security |
| No hardcoded secrets in lib/ | Security |
| Socket has token authentication | Security |
| Token not leaked to log files | Security |
| Token not exposed in error messages | Security |
| Token has sufficient entropy (128-bit) | Security |
| askd_server.py has os.name != "nt" guard for chmod | Security |
| daemon cold start under 3s on native Windows | Performance |
| Python module import time reasonable | Performance |
| Socket connect latency under 100ms | Performance |
| Socket unauthorized rejection under 100ms | Security/Performance |
| Full encode fallback chain works (UTF-8/GBK/1252/Shift-JIS/BOM) | Compatibility |
| Chinese path handling works | Compatibility |
| UNC path handling works | Compatibility |
| File lock mutual exclusion works | Compatibility |
| File lock Chinese paths work | Compatibility |
| Stale lock detection works | Compatibility |
| install.ps1 syntax valid | Compatibility |
| install.ps1 UTF-8 BOM present | Compatibility |
| install.ps1 Get-Msg en/zh/auto-detect work | Compatibility |
| bin/ask PowerShell path escaping verified | Compatibility |

---

## Issues

### WIN-01-001: E2E and perf tests use wrong protocol prefix "askd.ping" instead of "ask.ping"
- **Severity:** High
- **Dimension:** Performance (WIN-01) — causes 4 test failures in perf/e2e suites
- **Location:**
  - `tests/windows/test_e2e_commands.py:110` (`"type": "askd.ping"`)
  - `tests/windows/test_perf_daemon.py:113` (`"type": "askd.ping"`)
  - `tests/windows/test_perf_socket.py:86` (via `_make_ping_request`, uses `"type": "askd.ping"`)
  - `tests/windows/test_perf_socket.py:142` (concurrent test, `"type": "askd.ping"`)
- **Detected by:** `test_e2e_ask_ping_command`, `test_command_response_under_500ms`, `test_socket_request_response_latency`, `test_concurrent_requests_handling`
- **Description:** The unified daemon uses protocol prefix "ask" (from ASKD_SPEC), so requests with `"type": "askd.ping"` are treated as invalid and return `{"reply": "Invalid request", "exit_code": 1}`. Plan 03 already fixed this in security tests but perf/e2e tests were not updated.
- **Impact:** 4 of 5 test failures in the audit suite are caused by this single root issue. Test results cannot be trusted for performance measurement until fixed.
- **Reproduce:** `python -m pytest tests/windows/test_perf_daemon.py::TestCommandResponse -x`

### WIN-01-002: E2E test imports from non-existent module path
- **Severity:** High
- **Dimension:** Performance (WIN-01) — blocks E2E lifecycle test
- **Location:** `tests/windows/test_e2e_commands.py:192` (`from lib.askd.daemon import shutdown_daemon`)
- **Detected by:** `test_e2e_ccb_start_stop_cycle`
- **Description:** The test tries to import `shutdown_daemon` from `lib.askd.daemon`, which then imports from `askd.adapters.base` — a module that doesn't exist in the current codebase (the `askd/` package is installed as a separate package, not as `lib.askd`). This causes `ModuleNotFoundError`.
- **Impact:** The full daemon start/stop lifecycle test cannot run, leaving the E2E test coverage incomplete.
- **Reproduce:** `python -m pytest tests/windows/test_e2e_commands.py::TestE2ECcbStartStop -x`

### WIN-02-001: mbcs encoding fallback may silently produce wrong output
- **Severity:** Medium
- **Dimension:** Compatibility (WIN-02)
- **Location:** `lib/compat.py:63-67`
- **Detected by:** `test_decode_mbcs_windows_data_loss` (passes as expected — test documents the behavior)
- **Description:** When stdin input is not UTF-8 or locale-preferred encoding, the fallback uses `data.decode("mbcs", errors="strict")`. On Windows, mbcs maps to the system ANSI code page (typically cp1252 or cp936). If the actual encoding doesn't match the system code page, strict mode may either succeed with garbled output (wrong decode) or fail and fall through. Either path produces incorrect results for non-matching encodings like Shift-JIS on a cp1252 system.
- **Impact:** Users with non-UTF-8, non-matching-code-page input may see garbled text or replacement characters. Low frequency since most Windows users use UTF-8 or their system code page matches.
- **Reproduce:** Set `locale.getpreferredencoding` to "cp1252", feed Shift-JIS encoded bytes to `decode_stdin_bytes()`.

### WIN-02-002: WSL probe causes 10s timeout on native Windows without WSL
- **Severity:** High
- **Dimension:** Compatibility (WIN-02)
- **Location:** `lib/ccb_config.py:128-168` (`_wsl_probe_distro_and_home()`)
- **Detected by:** `test_wsl_probe_timeout_on_native_windows` (passes as expected — test documents behavior with 20s timeout)
- **Description:** When `apply_backend_env()` is called on native Windows (no WSL installed), the first `subprocess.run(["wsl.exe", ...])` call in `_wsl_probe_distro_and_home()` waits up to 10 seconds before timing out. This is called during daemon startup if BackendEnv is "wsl" (auto-detected on Windows via `get_backend_env()` defaulting to "windows" on win32).
- **Impact:** Users with BackendEnv explicitly set to "wsl" but no WSL installed experience 10s daemon startup delay. Impact is mitigated because `get_backend_env()` defaults to "windows" on win32, so `apply_backend_env()` returns early unless WSL mode is explicitly configured.
- **Reproduce:** Set `CCB_BACKEND_ENV=wsl` on a Windows machine without WSL, start daemon.
- **Note:** The fallback path (`wsl.exe -l -q` with 5s timeout) may also add delay. Total worst case: 10s + 5s + 5s = 20s.

### WIN-02-003: bin/ask PowerShell path escaping incomplete
- **Severity:** Medium
- **Dimension:** Compatibility (WIN-02)
- **Location:** `bin/ask:676-677`
- **Detected by:** `test_bin_ask_powershell_path_escaping` (passes — test verifies basic double-quote escaping only)
- **Description:** Path escaping in the PowerShell script generation only handles double-quote characters (`replace('"', '`"')`). PowerShell has additional special characters that should be escaped in double-quoted strings: `$` (variable expansion), backtick `` ` `` (escape character), and potentially others like `'` and `()` in certain contexts. If a user's temp directory or project path contains these characters, the generated PowerShell script may behave unexpectedly.
- **Impact:** Users with `$` in their path (unlikely but possible, e.g. `C:\Users\dev$\project`) could have PowerShell interpret it as a variable. Backtick in paths would be interpreted as an escape sequence.
- **Reproduce:** Create a project in a path containing `$` (e.g., via `subst` or symlink), run `bin/ask`.

### WIN-02-004: 7 os.chmod(0o600/0o700) calls in mail/ modules without Windows guard
- **Severity:** Medium
- **Dimension:** Compatibility (WIN-02) / Security (WIN-03)
- **Location:**
  - `lib/mail/ask_handler.py:98` (`.chmod(0o600)`)
  - `lib/mail/config.py:337` (`.chmod(0o700)`)
  - `lib/mail/config.py:434` (`.chmod(0o600)`)
  - `lib/mail/daemon.py:96` (`.chmod(0o600)`)
  - `lib/mail/credentials.py:113` (`.chmod(0o600)`)
  - `lib/mail/threads.py:82` (`.chmod(0o600)`)
  - `lib/mail/attachments.py:97` (`.chmod(0o600)`)
- **Detected by:** `test_mail_modules_missing_nt_guard` (xfail — test documents the gap)
- **Description:** All 7 chmod calls in the mail/ modules lack the `if os.name != "nt":` guard that `lib/askd_server.py:297` correctly uses. On Windows NTFS, `os.chmod(0o600)` has no meaningful effect (NTFS uses ACLs, not Unix permission bits). The calls silently succeed without actually restricting access.
- **Impact:** Sensitive files (credentials, config, attachments) are not access-restricted on Windows. Any user on the same machine can read these files. Low practical risk for single-user machines but violates the security intent of chmod calls.
- **Reproduce:** Run any mail module that writes sensitive files on Windows, then check file permissions via `icacls`.

### WIN-03-001: Token stored as plaintext in daemon state file
- **Severity:** Medium
- **Dimension:** Security (WIN-03)
- **Location:** `lib/askd_runtime.py:111-112` (`random_token()`), `lib/askd_server.py:293-301` (state file write)
- **Detected by:** `test_token_in_state_file_is_plaintext`
- **Description:** The daemon generates a 128-bit random token via `secrets.token_hex(16)` and writes it as plaintext JSON to `askd.json`. On Windows NTFS, combined with WIN-02-004, the state file permissions are not restricted. Any process running under the same user account can read the token and send authenticated requests to the daemon.
- **Impact:** Local privilege escalation within the same user session. An attacker with user-level access can impersonate the daemon client. Risk is low for single-user machines but non-trivial for shared workstation scenarios.
- **Reproduce:** Read `~/.cache/ccb/askd/askd.json` and extract the "token" field.

### WIN-03-002: Token comparison uses timing-unsafe string comparison
- **Severity:** Low
- **Dimension:** Security (WIN-03)
- **Location:** `lib/askd_server.py:118` (`msg.get("token") != self.server.token`)
- **Detected by:** `test_socket_token_comparison_not_timing_safe`
- **Description:** Token validation uses Python's standard string comparison (`!=`), which is timing-dependent. A sophisticated attacker on the local network could theoretically measure response times to incrementally guess the correct token character by character.
- **Impact:** Very low on localhost-only daemon (timing variations dominated by OS scheduling). Would be Medium if the daemon were exposed on a network interface. Documented as design-level finding, not a bug.
- **Reproduce:** Not practically exploitable on localhost. This is a defense-in-depth improvement.

### WIN-03-003: No TLS/SSL encryption on daemon socket
- **Severity:** Low
- **Dimension:** Security (WIN-03)
- **Location:** `lib/askd_server.py` (entire module, uses plain `socketserver.TCPServer`)
- **Detected by:** `test_socket_no_tls_encryption`
- **Description:** The daemon listens on a plain TCP socket without TLS/SSL encryption. All communication (including token, prompts, and responses) is transmitted in cleartext. The daemon binds to 127.0.0.1 only, which mitigates remote access, but local processes can sniff localhost traffic.
- **Impact:** Low for localhost-only binding. Any process on the same machine can sniff daemon traffic using raw sockets or packet capture. Documented as design-level finding — adding TLS to localhost daemon is significant complexity for marginal security gain.
- **Reproduce:** Use Wireshark or netcat to observe localhost traffic on the daemon port.

### WIN-01-003: daemon memory measurement skipped (psutil not installed)
- **Severity:** Low
- **Dimension:** Performance (WIN-01)
- **Location:** `tests/windows/test_perf_daemon.py` (`test_daemon_memory_under_50mb` — uses `pytest.importorskip("psutil")`)
- **Detected by:** Test skipped due to missing psutil dependency
- **Description:** The D-08 memory baseline (<50MB) cannot be verified because psutil is not installed in the test environment. The test was designed to skip gracefully, but the D-08 requirement remains unverified.
- **Impact:** No data point for daemon memory consumption. D-08 compliance is unverified.
- **Reproduce:** `python -m pytest tests/windows/test_perf_daemon.py::TestDaemonMemory -v` → SKIPPED

### WIN-02-005: No CREATE_NO_WINDOW flags on ccb_config.py subprocess calls for WSL probe fallback
- **Severity:** Medium
- **Dimension:** Compatibility (WIN-02)
- **Location:** `lib/ccb_config.py:143-146`, `lib/ccb_config.py:160-164` (fallback subprocess calls in `_wsl_probe_distro_and_home`)
- **Detected by:** Code review (not directly tested)
- **Description:** The fallback subprocess calls in `_wsl_probe_distro_and_home` use `_subprocess_kwargs()` which should include `CREATE_NO_WINDOW` on Windows. However, the first call (line 131) and fallback calls (lines 143, 160) could potentially flash a CMD window if `_subprocess_kwargs()` fails or the import is bypassed. The import at line 11-13 has a fallback from `terminal` to `lib.terminal`, but if both fail, the function crashes rather than falling back.
- **Impact:** Potential CMD window flash during WSL probe on native Windows. Low frequency since the import fallback covers standard usage.
- **Reproduce:** Unlikely to trigger in normal operation. Would need import path corruption.

### WIN-03-004: Daemon socket lacks SO_EXCLUSIVEADDRUSE on Windows
- **Severity:** Medium
- **Dimension:** Security (WIN-03)
- **Location:** `lib/askd_server.py` (server initialization, `socketserver.TCPServer` usage)
- **Detected by:** Code review (not directly tested)
- **Description:** On Windows, without `SO_EXCLUSIVEADDRUSE`, another process could potentially bind to the same port during a brief window between the daemon's listen and accept calls. This is a known Windows socket behavior where ports in TIME_WAIT can be hijacked.
- **Impact:** Local port hijacking is theoretically possible but requires precise timing. Combined with the token authentication, an attacker would also need to guess the token. Low practical risk but a defense-in-depth gap.
- **Reproduce:** Difficult to reproduce — requires racing the daemon's bind during startup.

### WIN-01-004: WSL probe timeout affects daemon startup performance (conditional)
- **Severity:** Low
- **Dimension:** Performance (WIN-01)
- **Location:** `lib/ccb_config.py:171-188` (`apply_backend_env()`)
- **Detected by:** `test_wsl_probe_timeout_on_native_windows`
- **Description:** When BackendEnv is "wsl" on a machine without WSL, `_wsl_probe_distro_and_home()` adds up to 20s of delay to daemon startup. This is a dependency on WIN-02-002. On native Windows with default "windows" backend, this is not triggered.
- **Impact:** Only affects users who explicitly set `CCB_BACKEND_ENV=wsl` or have it in `.ccb-config.json` without having WSL installed. daemon cold start test passes (<3s) because default backend is "windows".
- **Reproduce:** Set `CCB_BACKEND_ENV=wsl` and start daemon without WSL installed.

---

## Test Failure Analysis

### Root Cause Breakdown of 5 Failures

| Failure | Root Cause | Issue ID |
|---------|-----------|----------|
| `test_e2e_ask_ping_command` | Wrong protocol prefix "askd.ping" | WIN-01-001 |
| `test_e2e_ccb_start_stop_cycle` | Import path error (lib.askd.daemon) | WIN-01-002 |
| `test_command_response_under_500ms` | Wrong protocol prefix "askd.ping" | WIN-01-001 |
| `test_socket_request_response_latency` | Wrong protocol prefix "askd.ping" | WIN-01-001 |
| `test_concurrent_requests_handling` | Wrong protocol prefix "askd.ping" | WIN-01-001 |

**4 of 5 test failures share the same root cause (WIN-01-001).** Fixing the protocol prefix in test files would resolve 80% of test failures.

### Test Status by Module

| Module | Total | Passed | Failed | Skipped | Xfailed |
|--------|-------|--------|--------|---------|---------|
| test_compat_encoding.py | 13 | 13 | 0 | 0 | 0 |
| test_compat_file_lock.py | 10 | 10 | 0 | 0 | 0 |
| test_compat_path.py | 7 | 7 | 0 | 0 | 0 |
| test_compat_powershell.py | 6 | 6 | 0 | 0 | 0 |
| test_e2e_commands.py | 4 | 2 | 2 | 0 | 0 |
| test_perf_daemon.py | 6 | 4 | 1 | 1 | 0 |
| test_perf_socket.py | 4 | 1 | 2 | 0 | 0 |
| test_security_permission.py | 4 | 3 | 0 | 0 | 1 |
| test_security_process.py | 4 | 4 | 0 | 0 | 0 |
| test_security_socket.py | 6 | 6 | 0 | 0 | 0 |
| test_security_token.py | 5 | 5 | 0 | 0 | 0 |
| **Total** | **69** | **62** | **5** | **1** | **1** |

---

## Cross-Reference: RESEARCH.md Known Issues vs Test Findings

| RESEARCH.md Issue | Confirmed by Tests? | Issue ID | Notes |
|-------------------|---------------------|----------|-------|
| os.chmod(0o600) silent on NTFS (7 locations in mail/) | Yes (xfail) | WIN-02-004 | 7 chmod calls confirmed, all lack NT guard |
| mbcs encoding fallback data loss | Yes (documented by test) | WIN-02-001 | Test passes showing expected behavior |
| daemon state token plaintext storage | Yes | WIN-03-001 | Token visible in askd.json |
| bin/ask PowerShell path escaping incomplete | Partially | WIN-02-003 | Basic double-quote escaping works, but $/backtick not covered |
| WSL probe 10s timeout on native Windows | Yes (documented by test) | WIN-02-002 | Test uses 20s timeout to verify the behavior |
| Missing CREATE_NO_WINDOW flags | Partially | WIN-02-005 | Uses _subprocess_kwargs() but import path could fail |
| No shell=True in codebase | Confirmed positive | — | No issues |
| No eval/exec in codebase | Confirmed positive | — | No issues |
| Socket has token auth | Confirmed positive | — | No issues |
| Tokens not in log paths | Confirmed positive | — | No issues |

### New Issues Not in RESEARCH.md

| Issue ID | Description | Discovery Source |
|----------|-------------|------------------|
| WIN-01-001 | Wrong protocol prefix in perf/e2e tests | Test failures |
| WIN-01-002 | Import path error in E2E test | Test failure |
| WIN-03-002 | Timing-unsafe token comparison | Code review (not in RESEARCH.md pitfalls) |
| WIN-03-003 | No TLS/SSL on daemon socket | Code review (not in RESEARCH.md pitfalls) |
| WIN-01-003 | psutil not installed for memory test | Test skip |
| WIN-03-004 | No SO_EXCLUSIVEADDRUSE on Windows socket | Code review |
| WIN-02-005 | CREATE_NO_WINDOW import path risk | Code review |
| WIN-01-004 | WSL probe conditional startup delay | Derived from WIN-02-002 |
