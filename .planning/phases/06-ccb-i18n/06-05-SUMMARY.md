---
phase: 06-ccb-i18n
plan: 05
subsystem: mail-web-tui
tags: [i18n, mail, web, tui, regression]

requires:
  - phase: 06-ccb-i18n
    provides: "Residual hardcoded surface inventory from plan 04"
provides:
  - "Mail/Web/TUI remaining hardcoded surfaces migrated to translation keys"
  - "Updated inventory showing 158 translated / 0 hardcoded surfaces"
  - "Regression coverage for mail sender error path and wizard provider list pseudo locale"
affects: [06-06]

key-files:
  modified:
    - lib/mail/sender.py
    - lib/mail_tui/wizard.py
    - lib/web/templates/dashboard.html
    - lib/web/templates/mail.html
    - lib/i18n/ccb/en.json
    - lib/i18n/ccb/zh.json
    - lib/i18n/ccb/xx.json
    - tests/test_mail_i18n.py
    - .planning/phases/06-ccb-i18n/reports/i18n_surface_inventory.md

key-decisions:
  - "Mail sender hardcoded exceptions/retry logs were moved to translation keys so pseudo locale can cover failure paths, not only success copy"
  - "Provider labels were normalized through shared `ccb.provider.*` keys to avoid repeating brand strings across TUI and Web config surfaces"
  - "Template-side `console.error(...)` strings were routed through pre-rendered translation values to keep HTML/JS behavior aligned with server-side i18n"

requirements-completed: [I18N-06]

duration: session
completed: 2026-03-30
---

# Phase 6 Plan 05: Mail/Web/TUI Migration Summary

**按 inventory 收口剩余 16 个硬编码 surface，把 Mail/Web/TUI 用户可见文案全部迁到统一翻译系统，并重新生成盘点结果为 0 个硬编码。**

## Accomplishments

- Migrated [sender.py](/D:/Python/GitHub/claude_code_bridge/lib/mail/sender.py) connection failures, missing-password errors, and SMTP retry logs to `t(...)` keys
- Replaced hardcoded default-provider labels in [wizard.py](/D:/Python/GitHub/claude_code_bridge/lib/mail_tui/wizard.py) with shared `ccb.provider.*` translation keys
- Routed template-side fetch error messages in [dashboard.html](/D:/Python/GitHub/claude_code_bridge/lib/web/templates/dashboard.html) and [mail.html](/D:/Python/GitHub/claude_code_bridge/lib/web/templates/mail.html) through translated UI state instead of raw English literals
- Added targeted regression coverage in [test_mail_i18n.py](/D:/Python/GitHub/claude_code_bridge/tests/test_mail_i18n.py) for pseudo-locale sender failures and wizard provider labels
- Regenerated [i18n_surface_inventory.md](/D:/Python/GitHub/claude_code_bridge/.planning/phases/06-ccb-i18n/reports/i18n_surface_inventory.md) to `158 translated / 0 hardcoded`

## Verification

- `python -m pytest tests/test_mail_i18n.py tests/test_web_i18n.py -q` -> `5 passed, 3 skipped`
- `python scripts/check_translation_coverage.py` -> passed
- `python scripts/check_translation_completeness.py` -> passed
- `python scripts/audit_ccb_i18n_surface.py` -> `158 translated / 0 hardcoded`

## Notes

- `tests/test_web_i18n.py` remains skipped in this environment because `fastapi` is not installed; this is an environment gap, not a failing regression.
- No commit was created in this session because repository instructions require explicit confirmation before `git commit`.

## Self-Check: PASSED

- FOUND: [sender.py](/D:/Python/GitHub/claude_code_bridge/lib/mail/sender.py)
- FOUND: [wizard.py](/D:/Python/GitHub/claude_code_bridge/lib/mail_tui/wizard.py)
- FOUND: [dashboard.html](/D:/Python/GitHub/claude_code_bridge/lib/web/templates/dashboard.html)
- FOUND: [mail.html](/D:/Python/GitHub/claude_code_bridge/lib/web/templates/mail.html)
- FOUND: [i18n_surface_inventory.md](/D:/Python/GitHub/claude_code_bridge/.planning/phases/06-ccb-i18n/reports/i18n_surface_inventory.md)
