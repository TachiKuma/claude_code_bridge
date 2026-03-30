---
phase: 06-ccb-i18n
plan: 01
subsystem: i18n
tags: [i18n, fallback-chain, protocol-protection, locale-detection]

# Dependency graph
requires:
  - phase: 04-原型验证
    provides: i18n_core prototype with basic translations and test suite
provides:
  - Verified fallback chain: current-lang -> en.json -> key itself
  - Protocol string BLOCKED reject from external translations
  - locale.getlocale() replacing deprecated locale.getdefaultlocale()
  - 15 passing tests covering fallback, protocol reject, and locale detection
affects: [06-02, 06-03, 06-04, 06-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [fallback-chain, protocol-reject, whitelist-guard]

key-files:
  created: []
  modified:
    - tests/test_i18n_core.py

key-decisions:
  - "i18n_core code was already correct from Phase 04 prototype; only test gap for protocol reject fallback needed closing"
  - "tests/ directory is in .gitignore but must be force-added for i18n tests"

patterns-established:
  - "Fallback chain: translations.get(key) -> fallback_translations.get(key) -> key itself"
  - "Protocol reject: _merge_external_translations skips whitelist values with BLOCKED log"
  - "Language detection: CCB_LANG -> LANG/LC_ALL/LC_MESSAGES -> locale.getlocale() -> default en"

requirements-completed: [I18N-01]

# Metrics
duration: 9min
completed: 2026-03-30
---

# Phase 6 Plan 01: i18n_core 阻断项修复 Summary

**验证 i18n_core 的回退链、协议 reject 和 locale 检测已满足 R0 要求，补齐协议 reject 后回退内置翻译的测试覆盖**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-30T11:45:45Z
- **Completed:** 2026-03-30T11:54:35Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Confirmed i18n_core fallback chain (current-lang -> en.json -> key) is correctly implemented
- Confirmed protocol string BLOCKED reject mechanism works in _merge_external_translations
- Confirmed locale.getdefaultlocale() has been replaced with locale.getlocale() in both files
- Added test_protocol_reject_falls_back_to_builtin to close the test coverage gap
- All 15 i18n_core tests pass with python -W error (zero DeprecationWarning)

## Task Commits

Each task was committed atomically:

1. **Task 1: 修复回退链、协议 reject 和 locale 检测** - `ea32ac7` (test)

**Plan metadata:** pending (docs commit)

_Note: Code changes (i18n_core.py, i18n.py) were already correct from Phase 04. Only test gap was closed._

## Files Created/Modified
- `tests/test_i18n_core.py` - Added test_protocol_reject_falls_back_to_builtin (33 lines added)

## Decisions Made
- Code was already correct from Phase 04 prototype; no code changes to i18n_core.py or i18n.py needed
- Only added one test to verify protocol reject -> builtin fallback behavior explicitly
- Force-added tests/ directory to git despite .gitignore exclusion (i18n tests must be tracked)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Force-added gitignored tests/ directory**
- **Found during:** Task 1 (commit)
- **Issue:** tests/ directory is in .gitignore, preventing `git add tests/test_i18n_core.py`
- **Fix:** Used `git add -f` to force-add the test file
- **Files modified:** tests/test_i18n_core.py
- **Verification:** Commit succeeded, file tracked in git
- **Committed in:** ea32ac7 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking - gitignore)
**Impact on plan:** Minimal - only needed force-add for gitignored test directory.

## Issues Encountered
- pytest was not installed in the environment; installed with `pip install pytest`
- tests/ directory in .gitignore required force-add

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- i18n_core R0 blocking items all verified and passing
- Ready for Plan 06-02 (CLI core translation coverage expansion)
- Fallback chain and protocol reject form the foundation for all subsequent i18n work

## Self-Check: PASSED

- FOUND: .planning/phases/06-ccb-i18n/06-01-SUMMARY.md
- FOUND: tests/test_i18n_core.py
- FOUND: ea32ac7 (task commit)

---
*Phase: 06-ccb-i18n*
*Completed: 2026-03-30*
