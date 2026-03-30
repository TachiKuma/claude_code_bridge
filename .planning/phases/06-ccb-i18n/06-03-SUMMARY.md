---
phase: 06-ccb-i18n
plan: 03
subsystem: i18n
tags: [i18n, language-switching, ci-guards, config, translation-coverage, translation-completeness]

# Dependency graph
requires:
  - phase: 06-ccb-i18n
    provides: "i18n_core with t() API, ccb config lang subcommand, --lang flag, check_protocol_strings.py"
provides:
  - "Unified language priority chain: --lang -> CCB_LANG -> .ccb-config.json -> locale -> en"
  - "i18n_core._detect_language aligned with ccb_config.get_language_setting"
  - "tests/test_i18n_config.py with 28 tests covering config, env, CLI flag and priority"
  - "CI guard scripts verified passing (protocol strings, translation coverage, completeness)"
affects: [06-ccb-i18n]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Language priority chain: --lang/CCB_LANG -> .ccb-config.json -> locale -> en"]

key-files:
  created:
    - tests/test_i18n_config.py
  modified:
    - lib/i18n_core.py

key-decisions:
  - "i18n_core._detect_language now imports ccb_config.get_language_setting for config file fallback"
  - "CCB_LANG='auto' no longer short-circuits; falls through to config file and locale detection"

patterns-established:
  - "Language priority chain: --lang/CCB_LANG -> .ccb-config.json -> locale -> en"

requirements-completed: [I18N-03, I18N-04]

# Metrics
duration: 42min
completed: 2026-03-30
---

# Phase 6 Plan 03: Language Switching & CI Guards Summary

**Unified language priority chain (CCB_LANG -> config -> locale) with 28 config tests and all 3 CI guard scripts passing**

## Performance

- **Duration:** 42 min
- **Started:** 2026-03-30T12:00:33Z
- **Completed:** 2026-03-30T12:42:24Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Unified i18n_core._detect_language with ccb_config.get_language_setting to enforce a single priority chain: --lang/CCB_LANG -> .ccb-config.json Language -> system locale -> default 'en'
- Created comprehensive test suite (28 tests) covering config file Language read/write, CCB_LANG env override, --lang CLI flag priority, and i18n_core integration
- Verified all 3 CI guard scripts pass: check_protocol_strings (300 whitelist items), check_translation_coverage (210 t() calls across 21 files), check_translation_completeness (en/zh/xx key sets consistent)

## Task Commits

1. **Task 1: Unified language switching and CI guards** - `52b7ab4` (feat)

## Files Created/Modified
- `tests/test_i18n_config.py` - 28 tests covering config file Language read/write, CCB_LANG env override, --lang CLI flag priority, i18n_core._detect_language integration
- `lib/i18n_core.py` - Added config file fallback to _detect_language, aligned priority chain with ccb_config

## Decisions Made
- i18n_core._detect_language now imports ccb_config.get_language_setting for config file fallback, ensuring a single unified priority chain
- CCB_LANG='auto' no longer short-circuits at i18n_core level; it falls through to config file and locale detection, matching i18n.py behavior

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_default_en_when_nothing_set failed on Chinese-locale Windows**
- **Found during:** Task 1 (verification)
- **Issue:** Test asserted 'en' but system locale returned 'zh' on this Windows machine
- **Fix:** Used clear=True on mock.patch.dict to fully isolate environment, and mocked ccb_config.get_language_setting to return None
- **Files modified:** tests/test_i18n_config.py
- **Verification:** 28/28 tests pass
- **Committed in:** 52b7ab4 (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test fix for environment isolation. No scope creep.

## Issues Encountered
None beyond the deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Language switching priority chain is unified and tested
- CI guard scripts are in place and passing
- Ready for Plan 04 (Mail/Web/TUI inventory) and Plan 05 (full migration)

---
*Phase: 06-ccb-i18n*
*Completed: 2026-03-30*

## Self-Check: PASSED

- lib/i18n_core.py: FOUND
- tests/test_i18n_config.py: FOUND
- scripts/check_translation_coverage.py: FOUND
- scripts/check_translation_completeness.py: FOUND
- .github/workflows/test.yml: FOUND
- .pre-commit-config.yaml: FOUND
- 06-03-SUMMARY.md: FOUND
- Commit 52b7ab4: FOUND
