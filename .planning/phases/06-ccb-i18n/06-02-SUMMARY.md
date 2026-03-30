---
phase: 06-ccb-i18n
plan: 02
subsystem: cli-i18n
tags: [i18n, cli, ask, smoke-tests]

requires:
  - phase: 06-ccb-i18n
    provides: "Shared language resolution and translation completeness checks"
provides:
  - "`ccb.ask.*` help and error keys in en/zh/xx"
  - "`tests/test_cli_i18n_smoke.py` covering en/zh/xx help output and missing-key fallback"
  - "CLI help no longer falls back to raw `ccb.ask.*` keys"
affects: [06-04, 06-05, 06-06]

key-files:
  created:
    - tests/test_cli_i18n_smoke.py
  modified:
    - lib/i18n/ccb/en.json
    - lib/i18n/ccb/zh.json
    - lib/i18n/ccb/xx.json

key-decisions:
  - "Existing CLI wrappers already contained most `t()` integration; remaining gap was missing `ccb.ask.*` translation keys and end-to-end smoke coverage"
  - "Smoke tests use subprocess `ask --help` to validate real CLI output instead of mocking translation calls"

requirements-completed: [I18N-02]

duration: session
completed: 2026-03-30
---

# Phase 6 Plan 02: CLI Core Translation Coverage Summary

**补齐 `ask` 入口缺失的翻译 key，并新增 CLI smoke 测试，验证 `en/zh/xx` 帮助输出和缺失 key 回退行为。**

## Accomplishments

- Added missing `ccb.ask.*` keys to [en.json](/D:/Python/GitHub/claude_code_bridge/lib/i18n/ccb/en.json), [zh.json](/D:/Python/GitHub/claude_code_bridge/lib/i18n/ccb/zh.json), and [xx.json](/D:/Python/GitHub/claude_code_bridge/lib/i18n/ccb/xx.json)
- Created [test_cli_i18n_smoke.py](/D:/Python/GitHub/claude_code_bridge/tests/test_cli_i18n_smoke.py) to cover English, Chinese, pseudo-locale help output, plus missing-key fallback
- Verified `ask --help` no longer prints raw `ccb.ask.*` keys or `Translation key not found` warnings

## Verification

- `python -m pytest tests/test_cli_i18n_smoke.py -q` -> passed
- `python scripts/check_protocol_strings.py` -> passed
- `python scripts/check_translation_coverage.py` -> passed
- `python scripts/check_translation_completeness.py` -> passed

## Notes

- No commit was created in this session because the repository instructions require explicit confirmation before `git commit`.

## Self-Check: PASSED

- FOUND: [test_cli_i18n_smoke.py](/D:/Python/GitHub/claude_code_bridge/tests/test_cli_i18n_smoke.py)
- FOUND: [en.json](/D:/Python/GitHub/claude_code_bridge/lib/i18n/ccb/en.json)
- FOUND: [zh.json](/D:/Python/GitHub/claude_code_bridge/lib/i18n/ccb/zh.json)
- FOUND: [xx.json](/D:/Python/GitHub/claude_code_bridge/lib/i18n/ccb/xx.json)
