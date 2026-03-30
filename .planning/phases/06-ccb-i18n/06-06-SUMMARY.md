---
phase: 06-ccb-i18n
plan: 06
subsystem: installer-and-templates
tags: [i18n, installer, templates, skills, config]

requires:
  - phase: 06-ccb-i18n
    provides: "CLI i18n baseline and shared translation key infrastructure"
provides:
  - "Language-aware skill/config template selection in install.sh/install.ps1"
  - "Chinese config template variants for CLAUDE.md, AGENTS.md, .clinerules, and tmux"
  - "Expanded install script message dictionaries aligned to `install.*` key naming"
  - "Localized argparse/config/template surfaces verified together with phase-level translation checks"
affects: []

key-files:
  created:
    - config/claude-md-ccb.zh.md
    - config/claude-md-ccb-route.zh.md
    - config/agents-md-ccb.zh.md
    - config/clinerules-ccb.zh.md
    - config/tmux-ccb.zh.conf
  modified:
    - install.sh
    - install.ps1
    - ccb
    - lib/i18n/ccb/en.json
    - lib/i18n/ccb/zh.json
    - lib/i18n/ccb/xx.json

key-decisions:
  - "Installer localization was aligned on `install.*` message keys so PowerShell and shell scripts can converge on the same semantic naming scheme"
  - "Chinese config templates were added as parallel artifacts instead of in-place translation to keep English defaults intact and let installers pick by language"
  - "Shared skill/config selector helpers in `install.sh` preserve KISS: choose localized artifact when present, otherwise fall back to existing English template"

requirements-completed: [I18N-02, I18N-06]

duration: session
completed: 2026-03-30
---

# Phase 6 Plan 06: Installer & Template Localization Summary

**补齐 CCB 安装层的中英模板注入和消息体系，新增 5 个中文 config 模板，并把 `install.sh` 的消息字典扩展到 `install.*` 命名空间，与 `install.ps1` 的本地化方向对齐。**

## Accomplishments

- Completed localized template selection in [install.sh](/D:/Python/GitHub/claude_code_bridge/install.sh) and existing [install.ps1](/D:/Python/GitHub/claude_code_bridge/install.ps1) paths so skills/configs prefer `*.zh.*` artifacts under Chinese locale
- Added Chinese config template variants:
  - [claude-md-ccb.zh.md](/D:/Python/GitHub/claude_code_bridge/config/claude-md-ccb.zh.md)
  - [claude-md-ccb-route.zh.md](/D:/Python/GitHub/claude_code_bridge/config/claude-md-ccb-route.zh.md)
  - [agents-md-ccb.zh.md](/D:/Python/GitHub/claude_code_bridge/config/agents-md-ccb.zh.md)
  - [clinerules-ccb.zh.md](/D:/Python/GitHub/claude_code_bridge/config/clinerules-ccb.zh.md)
  - [tmux-ccb.zh.conf](/D:/Python/GitHub/claude_code_bridge/config/tmux-ccb.zh.conf)
- Verified localized skill template inventory is complete for current CCB surfaces: `claude_skills=11`, `codex_skills=6`, `droid_skills=5`
- Expanded [install.sh](/D:/Python/GitHub/claude_code_bridge/install.sh) to `309` `install.*` message-key occurrences and confirmed [install.ps1](/D:/Python/GitHub/claude_code_bridge/install.ps1) is at `89` with `Write-Warning=0`
- Preserved previously landed `ccb` argparse `t(...)` integration and phase-wide translation consistency checks

## Verification

- `python -m pytest tests/test_cli_i18n_smoke.py tests/test_i18n_config.py tests/test_i18n_core.py -q` -> `47 passed`
- `python scripts/check_protocol_strings.py` -> passed
- `python scripts/check_translation_coverage.py` -> passed
- `python scripts/check_translation_completeness.py` -> passed
- `Get-ChildItem ... SKILL.zh.md` counts -> `11 / 6 / 5`
- `rg -o '"install\.' install.sh | Measure-Object` -> `309`
- `rg -o '"install\.' install.ps1 | Measure-Object` -> `89`
- `rg -n 'Write-Warning' install.ps1 | Measure-Object` -> `0`

## Notes

- This Windows environment does not currently expose a runnable `bash` binary or an initialized WSL distribution for `bash -n install.sh`, so installer validation for `install.sh` was limited to static grep/count checks plus phase-wide translation/inventory regressions.
- No commit was created in this session because repository instructions require explicit confirmation before `git commit`.

## Self-Check: PASSED

- FOUND: [install.sh](/D:/Python/GitHub/claude_code_bridge/install.sh)
- FOUND: [install.ps1](/D:/Python/GitHub/claude_code_bridge/install.ps1)
- FOUND: [claude-md-ccb.zh.md](/D:/Python/GitHub/claude_code_bridge/config/claude-md-ccb.zh.md)
- FOUND: [agents-md-ccb.zh.md](/D:/Python/GitHub/claude_code_bridge/config/agents-md-ccb.zh.md)
- FOUND: [tmux-ccb.zh.conf](/D:/Python/GitHub/claude_code_bridge/config/tmux-ccb.zh.conf)
