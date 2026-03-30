---
phase: 06-ccb-i18n
plan: 04
subsystem: inventory-and-strategy
tags: [i18n, inventory, estimate, migration-strategy]

requires:
  - phase: 06-ccb-i18n
    provides: "CLI i18n baseline and shared translation infrastructure"
provides:
  - "Executable Mail/Web/TUI surface audit script"
  - "Structured inventory with translated-vs-hardcoded breakdown"
  - "Second estimate focused on remaining hardcoded surfaces"
  - "Phase 05 migration strategy ordered by actual residual work"
affects: [06-05]

key-files:
  modified:
    - scripts/audit_ccb_i18n_surface.py
    - .planning/phases/06-ccb-i18n/reports/i18n_surface_inventory.md
    - .planning/phases/06-ccb-i18n/reports/i18n_second_estimate.md
    - .planning/phases/06-ccb-i18n/reports/i18n_migration_strategy.md

key-decisions:
  - "Inventory should distinguish translated keys from remaining hardcoded strings; raw grep output was too noisy to guide migration"
  - "Phase 05 should focus on `mail/sender.py`, `mail_tui/wizard.py`, and template-side JS errors instead of rewriting already-translated API routes"

requirements-completed: [I18N-05]

duration: session
completed: 2026-03-30
---

# Phase 6 Plan 04: Surface Inventory & Strategy Summary

**重写盘点脚本并生成第二版估算/迁移策略，把 Mail/Web/TUI 的剩余工作从“模糊范围”收敛到 16 个真实硬编码 surface。**

## Accomplishments

- Reworked [audit_ccb_i18n_surface.py](/D:/Python/GitHub/claude_code_bridge/scripts/audit_ccb_i18n_surface.py) to emit translated keys and residual hardcoded surfaces separately
- Generated [i18n_surface_inventory.md](/D:/Python/GitHub/claude_code_bridge/.planning/phases/06-ccb-i18n/reports/i18n_surface_inventory.md) with 153 total surfaces: 137 translated, 16 hardcoded
- Updated [i18n_second_estimate.md](/D:/Python/GitHub/claude_code_bridge/.planning/phases/06-ccb-i18n/reports/i18n_second_estimate.md) to reflect that Phase 05 is now primarily hardcoded cleanup plus regression work
- Updated [i18n_migration_strategy.md](/D:/Python/GitHub/claude_code_bridge/.planning/phases/06-ccb-i18n/reports/i18n_migration_strategy.md) with a targeted execution order based on remaining hardcoded hotspots

## Key Findings

- `lib/mail/sender.py` has 6 remaining hardcoded surfaces and is the highest-risk file for Phase 05
- `lib/mail_tui/wizard.py` still hardcodes the provider selection list
- `lib/web/templates/dashboard.html` and `lib/web/templates/mail.html` are mostly translated; the main leftovers are `console.error(...)` strings
- `lib/web/routes/daemons.py` and `lib/web/routes/mail.py` already route user-visible messages through `t()`

## Verification

- `python scripts/audit_ccb_i18n_surface.py` -> passed

## Notes

- No commit was created in this session because the repository instructions require explicit confirmation before `git commit`.

## Self-Check: PASSED

- FOUND: [audit_ccb_i18n_surface.py](/D:/Python/GitHub/claude_code_bridge/scripts/audit_ccb_i18n_surface.py)
- FOUND: [i18n_surface_inventory.md](/D:/Python/GitHub/claude_code_bridge/.planning/phases/06-ccb-i18n/reports/i18n_surface_inventory.md)
- FOUND: [i18n_second_estimate.md](/D:/Python/GitHub/claude_code_bridge/.planning/phases/06-ccb-i18n/reports/i18n_second_estimate.md)
- FOUND: [i18n_migration_strategy.md](/D:/Python/GitHub/claude_code_bridge/.planning/phases/06-ccb-i18n/reports/i18n_migration_strategy.md)
