---
phase: 07-windows-native-audit
plan: 04
subsystem: audit
tags: [pytest, windows, audit, issue-list, fix-plan, performance, compatibility, security]

# Dependency graph
requires:
  - phase: 07-01
    provides: "pytest test infrastructure, performance baseline tests (15 tests)"
  - phase: 07-02
    provides: "compatibility audit tests (35 tests), encoding/path/PowerShell coverage"
  - phase: 07-03
    provides: "security audit tests (19 tests), token/permission/process/socket coverage"
provides:
  - "Complete categorized issue list: 13 issues across 3 dimensions (5 High, 5 Medium, 3 Low)"
  - "Detailed fix plan with copy-paste-ready code changes for every issue"
  - "Root cause analysis: 4 of 5 test failures share same cause (wrong protocol prefix)"
  - "Cross-reference of RESEARCH.md known issues vs test findings"
  - "Implementation order recommendation for Plan 07-05"
affects: [07-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Issue severity classification: Critical/High/Medium/Low with clear criteria"
    - "Fix plan template: Current Code / Fixed Code / Why / Verification / Risk"
    - "Root cause consolidation: multiple test failures mapped to single issue"

key-files:
  created:
    - .planning/phases/07-windows-native-audit/07-ISSUE-LIST.md
    - .planning/phases/07-windows-native-audit/07-FIX-PLAN.md
  modified: []

key-decisions:
  - "Classified WIN-03-001 (token plaintext) as documentation-only fix: DPAPI too complex for audit phase, localhost binding is adequate mitigation"
  - "Classified WIN-03-003 (TLS/SSL) as deferred: significant refactoring with marginal localhost security gain"
  - "Ordered fixes by dependency: protocol prefix first (unblocks 4 tests), then WSL probe (user impact), then security hardening"
  - "Recommended WIN-01-004 (WSL conditional delay) as derived from WIN-02-002 fix, no separate implementation needed"

patterns-established:
  - "Audit issue list format: severity/dimension/location/test-reference/description/impact/reproduce"
  - "Fix plan format: priority/files/risk + current-code/fixed-code/why/verification per issue"

requirements-completed: [WIN-01, WIN-02, WIN-03]

# Metrics
duration: 7min
completed: 2026-03-31
---

# Phase 07 Plan 04: Issue List and Fix Plan Summary

**13 Windows audit issues categorized across performance (3), compatibility (5), and security (5) dimensions, with copy-paste-ready fix instructions ordered by dependency and user impact for Plan 07-05 implementation.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-31T03:39:04Z
- **Completed:** 2026-03-31T03:46:36Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Ran full audit test suite (69 tests: 62 passed, 5 failed, 1 skipped, 1 xfailed)
- Created comprehensive issue list with 13 issues: 5 High, 5 Medium, 3 Low
- Created detailed fix plan with current/fixed code snippets for every issue
- Identified single root cause for 80% of test failures (wrong protocol prefix "askd.ping")
- Cross-referenced all RESEARCH.md known issues against actual test findings
- Produced implementation order recommendation for Plan 07-05

## Task Commits

Each task was committed atomically:

1. **Task 1: Compile Windows audit issue list from test results** - `f117ec6` (docs)
2. **Task 2: Create detailed fix plan for all 13 issues** - `b8d70cb` (docs)

## Files Created/Modified
- `.planning/phases/07-windows-native-audit/07-ISSUE-LIST.md` - 13 categorized issues with severity, location, test reference, description, impact, and reproduce steps; test status by module; RESEARCH.md cross-reference
- `.planning/phases/07-windows-native-audit/07-FIX-PLAN.md` - Copy-paste-ready code changes for all 13 issues, ordered by priority with dependency awareness and risk assessment

## Decisions Made
- **Token plaintext (WIN-03-001) as documentation-only:** Adding DPAPI encryption requires pywin32 dependency and significant refactoring. Localhost-only binding with token auth is adequate mitigation for the audit phase. Document limitation for future hardening.
- **TLS/SSL (WIN-03-003) deferred:** Significant complexity (certificate generation, socket wrapping, error handling) with marginal security gain on localhost. Defer to dedicated security hardening phase.
- **WIN-01-004 derived from WIN-02-002:** The WSL conditional startup delay is a consequence of the WSL probe timeout. The fast WSL check in WIN-02-002's fix eliminates both issues simultaneously.
- **Fix ordering:** Protocol prefix fix first (unblocks 4/5 test failures, minimal risk), then WSL probe (highest user impact), then chmod guards (security intent), then one-line fixes, then documentation-only items.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Worktree was behind main repo (Phase 07 test files from Plans 01-03 not present). Resolved by merging main into worktree (fast-forward).
- psutil not installed: memory test (D-08) skipped. Documented as WIN-01-003 in issue list with pip install fix.

## Audit Findings Summary

| ID | Finding | Severity | Dimension | Test Status |
|----|---------|----------|-----------|-------------|
| WIN-01-001 | Wrong protocol prefix "askd.ping" in 4 test files | High | Performance | 4 test failures |
| WIN-01-002 | Import path error in E2E lifecycle test | High | Performance | 1 test failure |
| WIN-01-003 | psutil not installed for memory test | Low | Performance | 1 test skipped |
| WIN-01-004 | WSL probe conditional startup delay | Low | Performance | Documented |
| WIN-02-001 | mbcs encoding strict mode may produce wrong output | Medium | Compatibility | Documented by test |
| WIN-02-002 | WSL probe 10s timeout without WSL installed | High | Compatibility | Documented by test |
| WIN-02-003 | PowerShell path escaping incomplete ($/backtick) | Medium | Compatibility | Partially tested |
| WIN-02-004 | 7 chmod calls in mail/ without NT guard | Medium | Compat/Security | xfail |
| WIN-02-005 | CREATE_NO_WINDOW import path could fail | Medium | Compatibility | Code review |
| WIN-03-001 | Token plaintext in daemon state file | Medium | Security | Documented |
| WIN-03-002 | Timing-unsafe token comparison (!=) | Low | Security | Documented |
| WIN-03-003 | No TLS/SSL on daemon socket | Low | Security | Documented |
| WIN-03-004 | No SO_EXCLUSIVEADDRUSE on Windows socket | Medium | Security | Code review |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Complete issue list and fix plan ready for Plan 07-05 implementation
- Fix plan provides exact implementation order: protocol prefix -> WSL probe -> chmod guards -> one-line fixes -> documentation
- WIN-01-001 + WIN-01-002 fixes will bring test suite to 0 failures
- 22 positive findings documented (tests passing, no security issues in several areas)

## Known Stubs

None - all issues have fix instructions. Two issues (WIN-03-001, WIN-03-003) are recommended as documentation-only/deferred rather than implemented in the fix phase.

## Self-Check: PASSED

- 07-ISSUE-LIST.md exists at `.planning/phases/07-windows-native-audit/07-ISSUE-LIST.md`
- 07-FIX-PLAN.md exists at `.planning/phases/07-windows-native-audit/07-FIX-PLAN.md`
- Task 1 commit `f117ec6` verified
- Task 2 commit `b8d70cb` verified

---
*Phase: 07-windows-native-audit*
*Completed: 2026-03-31*
