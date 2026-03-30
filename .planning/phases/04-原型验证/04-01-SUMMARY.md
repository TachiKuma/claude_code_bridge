---
phase: 04-原型验证
plan: 01
subsystem: i18n
tags: [i18n-core, namespace, fallback, translation-json, backward-compat]

# Dependency graph
requires:
  - phase: 02-架构设计
    provides: i18n_core_design.md, translation_structure.md
provides:
  - I18nCore class with namespace isolation, fallback chain, external override
  - en.json, zh.json, xx.json with 56 namespaced translation keys
  - Backward-compatible lib/i18n.py wrapper with _key_mapping
  - Protocol string runtime validation in i18n_core
affects: [04-03, 05-文档编写, future-i18n-rollout]

# Tech tracking
tech-stack:
  added: []
  patterns: [namespace-translation, fallback-chain, external-override, lazy-init]

key-files:
  created:
    - lib/i18n_core.py
    - lib/i18n/ccb/en.json
    - lib/i18n/ccb/zh.json
    - lib/i18n/ccb/xx.json
    - tests/test_i18n_core.py
    - tests/demo_i18n_core.py
  modified:
    - lib/i18n.py

key-decisions:
  - "Added 'xx' language code support in _detect_language() for pseudo-translation"
  - "_load_json_file() returns empty dict on error instead of raising"
  - "lib/i18n.py imports I18nCore at module level, wraps via _key_mapping"

patterns-established:
  - "Namespace prefix: ccb.{category}.{specific} for all translation keys"
  - "Fallback: current_lang -> en -> key_name (for debugging)"

requirements-completed: [PROTO-01]

# Metrics
duration: 8min
completed: 2026-03-30
---

# Phase 04 Plan 01: I18nCore + Translation Files Summary

**I18nCore 命名空间翻译框架，56 条消息迁移至 JSON，支持中英伪翻译、回退链、外部覆盖和向后兼容**

## Performance

- **Duration:** 8 min
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- I18nCore 类实现命名空间隔离、语言检测、回退链、外部覆盖
- 56 条消息完整迁移至 en.json/zh.json/xx.json，0 数据丢失
- lib/i18n.py 向后兼容层确保旧代码无需修改
- 运行时协议字符串验证集成到 load_translations()

## Task Commits

1. **Task 1: 创建翻译文件和 I18nCore 类** - `4fa67b1` (feat)
2. **Task 2: 单元测试 + 兼容层改造 + Demo 脚本** - `4fa67b1` (feat)

## Files Created/Modified
- `lib/i18n_core.py` - I18nCore: namespace, load_translations, t(), fallback, protocol validation
- `lib/i18n/ccb/en.json` - 56 English translations with ccb.* namespace
- `lib/i18n/ccb/zh.json` - 56 Chinese translations with ccb.* namespace
- `lib/i18n/ccb/xx.json` - 56 pseudo-translations with [«»] markers
- `lib/i18n.py` - Backward-compatible wrapper with _key_mapping (56 entries)
- `tests/test_i18n_core.py` - 11 unit tests
- `tests/demo_i18n_core.py` - Demo script for 4 scenarios

## Decisions Made
- XX 语言码作为特殊伪翻译语言处理，不走 locale 回退
- _load_json_file 添加 FileNotFoundError 处理，返回空 dict
- MESSAGES 字典保留不删除，确保最大向后兼容

## Deviations from Plan
None - plan executed as written with minor auto-fixes.

## Issues Encountered
- tests/ 目录在 .gitignore 中，需 git add -f 强制添加
- Windows GBK 控制台无法打印 Unicode 伪翻译标记（数据本身正确）
- Path.home monkey-patch 在 Python 3.14 需使用 staticmethod

## Next Phase Readiness
- i18n_core 架构已验证，可供 Phase 5 实施全面集成
- 协议字符串运行时验证已就绪，与 04-03 CI 检查形成双层保护

---
*Phase: 04-原型验证*
*Completed: 2026-03-30*
