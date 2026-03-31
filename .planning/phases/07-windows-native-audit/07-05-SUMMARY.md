---
phase: 07-windows-native-audit
plan: 05
subsystem: fixes
tags: [pytest, windows, fixes, regression, security, compatibility, performance]

# Dependency graph
requires:
  - phase: 07-04
    provides: "13 categorized issues + copy-paste-ready fix plan"
provides:
  - "All Critical/High/Medium fixes applied to production code"
  - "68/68 Windows audit tests passing (1 skipped: psutil unavailable — expected)"
  - "89/89 existing tests still passing (zero regressions)"
  - "7 chmod calls in lib/mail/ guarded with os.name != 'nt'"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "os.name != 'nt' guard pattern for chmod calls (matches lib/askd_server.py:297-301)"
    - "Protocol prefix: ask.ping / ask.request (not askd.ping / askd.request)"
    - "WSL probe: fast pre-check with 2s timeout before 5s main probe"

---

# Phase 07-05 Summary: Implement All Fixes & Verify Audit Passes

**Duration:** ~25 min (interrupted by API rate limit at Task 1, resumed for Tasks 2–3)
**Tests after fix:** 68 passed, 1 skipped (expected) — Windows audit suite
**Regressions:** 0 (89 existing tests still pass)

## Task 1: Critical and High Priority Fixes (completed before API interrupt)

**Commits:** `4b74c3d` — fix(07-05): apply Critical and High priority Windows audit fixes

### WIN-01-001: Protocol prefix mismatch (Critical — unblocked 4/5 test failures)
- `tests/windows/test_perf_daemon.py`: `askd.ping` → `ask.ping`
- `tests/windows/test_perf_socket.py`: `askd.ping` → `ask.ping` (2 locations)
- `tests/windows/test_e2e_commands.py`: `askd.ping` → `ask.ping`, `askd.request` → `ask.request`

### WIN-01-002: Missing import in E2E test (High — unblocked 1/5 test failures)
- `tests/windows/test_e2e_commands.py`: replaced `shutdown_daemon` import with direct `proc.terminate()`

### WIN-02-002: WSL probe timeout (High — user-facing startup delay)
- `lib/ccb_config.py`: added fast pre-check `wsl.exe --list -q` with 2s timeout before main probe
- Main probe timeout reduced from 10s to 5s
- `apply_backend_env()` guarded against empty distro from failed WSL probe

### WIN-02-001: mbcs encoding data loss (High)
- `lib/compat.py`: `errors="strict"` → `errors="replace"` for mbcs fallback

### WIN-02-003: PowerShell path escaping (High)
- `bin/ask`: added `_ps_escape_path()` helper (backtick and single-quote escaping)

### WIN-02-005: subprocess kwargs fallback (Medium)
- `bin/ask`: added `_subprocess_kwargs()` fallback when terminal module unavailable

## Task 2: Medium and Low Priority Fixes

**Commit:** `fe7e6b2` — fix(07-05): guard all chmod calls in lib/mail/ with os.name != 'nt' check (WIN-02-004)

### WIN-02-004: chmod calls without Windows guard (7 locations fixed)
| File | Location | Fix |
|------|----------|-----|
| `lib/mail/daemon.py:96` | `state_path.chmod(0o600)` | Wrapped with `if os.name != "nt":` |
| `lib/mail/credentials.py:113` | `fallback_path.chmod(0o600)` | Wrapped with `if os.name != "nt":` |
| `lib/mail/ask_handler.py:98` | `context_file.chmod(0o600)` | Wrapped with `if os.name != "nt":` |
| `lib/mail/attachments.py:97` | `local_path.chmod(0o600)` | Wrapped with `if os.name != "nt":` |
| `lib/mail/config.py:337` | `config_dir.chmod(0o700)` | Wrapped with `if os.name != "nt":` |
| `lib/mail/config.py:434` | `config_path.chmod(0o600)` | Wrapped with `if os.name != "nt":` |
| `lib/mail/threads.py:82` | `threads_file.chmod(0o600)` | Wrapped + added `import os` |

**Pattern used:** matches existing `lib/askd_server.py:297-301` (try/except around chmod with nt guard)

## Task 3: Full Regression Suite

**Windows audit:** 68 passed, 1 skipped (psutil unavailable — WIN-01-003 documented)
**Existing suite:** 89 passed, 3 skipped — zero regressions

### Issues Remaining (by design — not code fixes)
| Issue | Status | Reason |
|-------|--------|--------|
| WIN-03-001: Token plaintext storage | Documented | Design-level decision, requires keyring integration |
| WIN-03-002: Timing-unsafe comparison | Documented | audit finding, hmac.compare_digest not yet applied |
| WIN-03-003: No TLS on localhost socket | Documented | Known design limitation, localhost-only scope |
| WIN-03-004: SO_EXCLUSIVEADDRUSE | Documented | Windows-specific hardening, future work |
| WIN-01-003: psutil for memory test | Skipped | Missing optional dependency |
| WIN-01-004: WSL conditional delay | N/A | Derived benefit from WIN-02-002 fix |

## Deviations
None from Task 2 plan. Task 3 confirmed all fixes correctly applied with no regressions.
