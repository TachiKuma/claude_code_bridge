---
phase: 07-windows-native-audit
plan: 03
subsystem: security
tags: [pytest, windows, security, audit, token, chmod, process, socket, tls, authentication]

# Dependency graph
requires:
  - phase: 07-windows-native-audit
    provides: "pytest.ini, conftest.py, daemon_proc fixture, test infrastructure"
provides:
  - "19 security audit tests (18 passed, 1 xfailed) covering token handling, file permissions, process security, and socket authentication"
  - "Documented Pitfall 1: 7 unguarded chmod calls in mail/ modules on NTFS"
  - "Documented Pitfall 3: token stored as plaintext in daemon state file"
  - "Documented D-11: timing-unsafe token comparison (!= not hmac.compare_digest)"
  - "Documented D-11: no TLS/SSL on localhost-only daemon socket"
  - "daemon_proc fixture promoted to conftest.py for cross-module sharing"
affects: [07-04, 07-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AST-based static analysis for security audit (eval/exec/token-in-response)"
    - "xfail pattern for documenting known audit gaps without failing test suite"
    - "shared daemon_proc fixture in conftest.py for socket test reuse"

key-files:
  created:
    - tests/windows/test_security_token.py
    - tests/windows/test_security_permission.py
    - tests/windows/test_security_process.py
    - tests/windows/test_security_socket.py
  modified:
    - tests/windows/conftest.py
    - tests/windows/test_perf_daemon.py

key-decisions:
  - "Moved daemon_proc fixture to conftest.py for cross-module availability"
  - "Used xfail (not fail) for mail/ chmod audit finding to document gap without blocking"
  - "Used AST parsing for token-in-error-response check to avoid false positives"
  - "Correct protocol prefix is 'ask' not 'askd' for unified daemon ping messages"

patterns-established:
  - "Security audit test pattern: static code analysis + runtime verification"
  - "Audit finding documentation via xfail with descriptive reason strings"

requirements-completed: [WIN-03]

# Metrics
duration: 14min
completed: 2026-03-31
---

# Phase 07 Plan 03: Security Audit Tests Summary

**19 security audit tests covering token handling (D-11/D-12), NTFS chmod ineffectiveness (Pitfall 1), process security (eval/exec/shell=True), and socket authentication with timing/TLS findings.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-31T03:18:17Z
- **Completed:** 2026-03-31T03:31:56Z
- **Tasks:** 4
- **Files modified:** 6 (4 created, 2 modified)

## Accomplishments
- 5 token handling tests: entropy (128-bit), uniqueness, plaintext state file storage, log leakage prevention, error message safety
- 4 file permission tests: NTFS chmod(0o600) ineffectiveness, chmod(0o400) read-only, askd_server NT guard, mail/ unguarded chmod audit (xfail)
- 4 process security tests: zero eval(), zero exec(), zero shell=True, zero hardcoded secrets -- full codebase scan confirmed
- 6 socket security tests: token rejection (missing + wrong), correct token acceptance, timing-unsafe comparison documented, no TLS documented, localhost binding verified
- Shared daemon_proc fixture promoted to conftest.py for cross-module availability

## Task Commits

Each task was committed atomically:

1. **Task 1: Token handling and leakage tests** - `6afbef1` (test)
2. **Task 2a: File permission tests** - `a077370` (test)
3. **Task 2b: Process security audit tests** - `7b33b5f` (test)
4. **Task 3: Socket security audit tests** - `7485807` (test)

## Files Created/Modified
- `tests/windows/test_security_token.py` - 5 tests: token entropy, uniqueness, plaintext storage, log leakage, error exposure
- `tests/windows/test_security_permission.py` - 4 tests: NTFS chmod, read-only flag, askd guard, mail/ gap (xfail)
- `tests/windows/test_security_process.py` - 4 tests: eval/exec/shell=True/hardcoded secrets scan
- `tests/windows/test_security_socket.py` - 6 tests: token auth, timing safety, TLS, binding
- `tests/windows/conftest.py` - Added daemon_proc shared fixture
- `tests/windows/test_perf_daemon.py` - Removed duplicate daemon_proc (moved to conftest)

## Decisions Made
- Moved daemon_proc from test_perf_daemon.py to conftest.py (Rule 3: blocking issue -- cross-module fixture availability)
- Used xfail for mail/ chmod audit finding: test documents the gap, won't block CI, will XPASS when fixed
- Used AST parsing for token-in-error-response check to avoid false positives from string literals
- Used "ask" not "askd" as protocol prefix for unified daemon ping messages (daemon uses ASKD_SPEC with prefix "ask")

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Moved daemon_proc fixture to conftest.py**
- **Found during:** Task 3 (Write socket security audit tests)
- **Issue:** daemon_proc fixture defined in test_perf_daemon.py was not available to test_security_socket.py (pytest doesn't share fixtures across test_*.py files)
- **Fix:** Moved daemon_proc from test_perf_daemon.py to conftest.py, removed duplicate
- **Files modified:** tests/windows/conftest.py, tests/windows/test_perf_daemon.py
- **Verification:** test_security_socket.py finds daemon_proc fixture, all tests pass

**2. [Rule 1 - Bug] Fixed protocol prefix in socket security tests**
- **Found during:** Task 3 (test_socket_accepts_correct_token failed)
- **Issue:** Tests used "askd.ping" but the unified daemon protocol prefix is "ask" (from ASKD_SPEC), so "askd.ping" was treated as an invalid request type
- **Fix:** Changed all request types from "askd.ping" to "ask.ping"
- **Files modified:** tests/windows/test_security_socket.py
- **Verification:** test_socket_accepts_correct_token passes with correct pong response

**3. [Rule 2 - Missing Critical] Used xfail instead of pytest.fail for mail/ chmod audit**
- **Found during:** Task 2a (test_mail_modules_missing_nt_guard failed on Windows)
- **Issue:** Plan suggested using pytest.mark.xfail or pytest.fail, but pytest.fail would always fail the suite on Windows (where the issue is live)
- **Fix:** Used pytest.xfail() call to document the finding without failing the test suite; will XPASS when fixed
- **Files modified:** tests/windows/test_security_permission.py
- **Verification:** 3 passed, 1 xfailed

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 bug, 1 missing critical)
**Impact on plan:** All auto-fixes necessary for test correctness and cross-module fixture sharing. No scope creep.

## Issues Encountered
- Pre-existing issue: test_perf_socket.py uses "askd.ping" (wrong protocol prefix), causing TestSocketRequestResponseLatency to fail. This is out of scope for this plan but noted for future fix.

## Audit Findings Summary

| ID | Finding | Severity | Test |
|----|---------|----------|------|
| Pitfall 1 | 7 chmod(0o600) calls in mail/ without NT guard | Medium | test_mail_modules_missing_nt_guard (xfail) |
| Pitfall 3 | Token stored as plaintext in askd.json | Medium | test_token_in_state_file_is_plaintext |
| D-11 | Token comparison uses != (not timing-safe) | Low (localhost) | test_socket_token_comparison_not_timing_safe |
| D-11 | No TLS/SSL on daemon socket | Low (localhost) | test_socket_no_tls_encryption |
| D-12 | Zero eval/exec/shell=True in codebase | Clean | test_no_eval_in_lib, test_no_exec_in_lib, test_no_shell_true_in_lib_and_bin |
| D-12 | Zero hardcoded secrets in lib/ | Clean | test_no_hardcoded_secrets_in_lib |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Security audit test suite complete (19 tests covering all D-11/D-12 items)
- daemon_proc fixture now shared via conftest.py, available for plans 04 and 05
- Pitfall 1 (mail/ chmod) documented as xfail -- needs fix in a future plan
- Perf socket test protocol prefix mismatch is a known pre-existing issue

## Known Stubs

None -- all tests are fully functional and verified against the live codebase.

## Self-Check: PASSED

- All 4 test files exist
- SUMMARY.md exists
- All 4 commits verified: 6afbef1, a077370, 7b33b5f, 7485807

---
*Phase: 07-windows-native-audit*
*Completed: 2026-03-31*
