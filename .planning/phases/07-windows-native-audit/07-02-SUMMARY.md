---
phase: 07-windows-native-audit
plan: 02
subsystem: testing
tags: [pytest, windows, encoding, compat, file-lock, powershell, path-handling]

# Dependency graph
requires:
  - phase: 07-01
    provides: "pytest.ini, tests/windows/ infrastructure, conftest.py shared fixtures"
provides:
  - 35 automated compatibility tests covering encoding fallback chains, Windows path handling, PowerShell compatibility, and file lock correctness
  - Bug fix in lib/compat.py: CCB_STDIN_ENCODING with invalid encoding name no longer raises LookupError
  - is_acquired property added to ProviderLock for interface consistency with FileLock
affects: [07-03, 07-04, 07-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "unittest.mock.patch for encoding environment isolation in tests"
    - "test classes grouping related test scenarios (TestUTF8Strict, TestBOMDetection, etc.)"
    - "force-add for gitignored tests/ directory (inherited from 07-01 pattern)"

key-files:
  created:
    - tests/windows/test_compat_encoding.py
    - tests/windows/test_compat_path.py
    - tests/windows/test_compat_file_lock.py
    - tests/windows/test_compat_powershell.py
  modified:
    - lib/compat.py
    - lib/process_lock.py

key-decisions:
  - "Grouped tests into classes by subsystem (encoding/BOM/fallback/edge) for clear test organization"
  - "Fixed LookupError bug in decode_stdin_bytes: invalid CCB_STDIN_ENCODING now falls through to standard chain instead of crashing"
  - "Added is_acquired property to ProviderLock for symmetry with FileLock interface"

patterns-established:
  - "Encoding test pattern: mock.patch locale.getpreferredencoding and sys.platform to simulate Windows encoding environments"
  - "File lock test pattern: create temp lock files, verify acquire/release/mutual exclusion, test stale PID detection"
  - "PowerShell test pattern: _run_ps helper using _subprocess_kwargs() for Windows subprocess flags"

requirements-completed: [WIN-02]

# Metrics
duration: 7min
completed: 2026-03-31
---

# Phase 7 Plan 02: Compatibility Audit Tests Summary

**35 compatibility audit tests covering encoding fallback chains (UTF-8/GBK/Windows-1252/Shift-JIS), Chinese path handling, PowerShell 5.1 compatibility, and file lock correctness (D-09/D-10/D-16)**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-31T03:04:28Z
- **Completed:** 2026-03-31T03:11:15Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- 13 encoding tests exercising the full decode_stdin_bytes() fallback chain: BOM detection, CCB_STDIN_ENCODING override, GBK/Windows-1252/Shift-JIS fallback, surrogate-free guarantee
- 7 path tests validating Chinese directory paths, UNC paths, paths with spaces, WSL probe timeout (<20s), and run_dir behavior on Windows
- 9 file lock tests covering FileLock acquire/release/context manager/mutual exclusion/Chinese paths/timeout, ProviderLock basic/different-dirs, and stale lock detection via dead PID
- 6 PowerShell tests: install.ps1 syntax validation, UTF-8 BOM encoding check, Get-Msg en/zh/auto-detect locale, bin/ask path escaping verification
- Bug fix: decode_stdin_bytes() no longer crashes with LookupError when CCB_STDIN_ENCODING is set to an invalid encoding name
- Interface fix: ProviderLock now exposes is_acquired property matching FileLock interface

## Task Commits

Each task was committed atomically:

1. **Task 1: Write encoding fallback chain tests (WIN-02 D-09)** - `465c9e5` (test)
2. **Task 2: Write Windows path handling and file lock tests (WIN-02 D-10 D-16)** - `a83cb88` (test)
3. **Task 3: Write PowerShell compatibility and install.ps1 tests (WIN-02 D-10)** - `01811af` (test)

## Files Created/Modified
- `tests/windows/test_compat_encoding.py` - 13 encoding fallback chain tests (UTF-8, GBK, Windows-1252, Shift-JIS, BOM, env override, surrogate-free)
- `tests/windows/test_compat_path.py` - 7 path handling tests (Chinese dirs, spaces, UNC, separators, WSL probe, run_dir)
- `tests/windows/test_compat_file_lock.py` - 9 file lock tests (acquire/release, context manager, mutual exclusion, Chinese paths, timeout, ProviderLock, stale detection)
- `tests/windows/test_compat_powershell.py` - 6 PowerShell tests (syntax, BOM, Get-Msg en/zh/auto, path escaping)
- `lib/compat.py` - Fixed LookupError when CCB_STDIN_ENCODING contains invalid encoding name
- `lib/process_lock.py` - Added is_acquired property to ProviderLock class

## Decisions Made
- **Class-based test organization**: Tests grouped into classes by subsystem (TestUTF8Strict, TestBOMDetection, TestEncodingFallback, etc.) for clear navigation and selective execution
- **LookupError fix falls through to standard chain**: Instead of just using errors="replace" for invalid CCB_STDIN_ENCODING, the fix allows the standard UTF-8/locale/mbcs chain to attempt decoding, which is more robust
- **ProviderLock is_acquired property**: Added for interface consistency with FileLock -- both lock classes now expose the same acquired state query API

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed LookupError in decode_stdin_bytes() with invalid CCB_STDIN_ENCODING**
- **Found during:** Task 1 (encoding fallback chain tests)
- **Issue:** When CCB_STDIN_ENCODING is set to a nonexistent encoding name, `data.decode(forced, errors="replace")` on line 45 of lib/compat.py also raises `LookupError` because Python does not recognize the encoding name at all. The replace fallback was outside the try/except, so the LookupError propagated to the caller.
- **Fix:** Wrapped the replace fallback in the except clause. Now `UnicodeDecodeError` triggers the replace path, while `LookupError` (and any other exception) falls through to the standard decode chain (UTF-8 -> locale -> mbcs -> utf-8 with replace).
- **Files modified:** lib/compat.py
- **Verification:** test_decode_env_override_invalid_encoding now passes -- "hello" encoded as UTF-8 is decoded successfully via the standard chain
- **Committed in:** `465c9e5` (Task 1 commit)

**2. [Rule 2 - Missing Critical] Added is_acquired property to ProviderLock**
- **Found during:** Task 2 (file lock tests)
- **Issue:** ProviderLock class has `_acquired` internal attribute but no public `is_acquired` property, while FileLock exposes it. Tests expecting the consistent interface failed with `AttributeError`.
- **Fix:** Added `@property is_acquired` to ProviderLock returning `self._acquired`, matching FileLock's interface.
- **Files modified:** lib/process_lock.py
- **Verification:** test_provider_lock_basic and test_provider_lock_different_dirs now pass
- **Committed in:** `a83cb88` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug fix, 1 missing critical functionality)
**Impact on plan:** Both auto-fixes are necessary for correctness. The LookupError fix prevents crashes with misconfigured environment variables. The ProviderLock property fix ensures API consistency across lock implementations.

## Issues Encountered
- None beyond the two deviations documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 35 compatibility tests pass on Windows 10 Pro (Python 3.14.2)
- Test infrastructure from 07-01 (conftest.py, pytest.ini) used successfully by 07-02
- Phase 07-03 (security audit tests) can build on these compatibility tests
- Phase 07-04 and 07-05 can extend the same test patterns

## Self-Check: PASSED

- All 4 test files exist: test_compat_encoding.py, test_compat_path.py, test_compat_file_lock.py, test_compat_powershell.py
- All 3 task commits verified: 465c9e5, a83cb88, 01811af
- All 35 tests pass: `python -m pytest tests/windows/test_compat_*.py -v` -> 35 passed in 4.37s
- No stubs found in created test files
- No untracked files remaining

---
*Phase: 07-windows-native-audit*
*Completed: 2026-03-31*
