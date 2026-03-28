---
phase: 01
slug: 代码库分析
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/test_i18n_analysis.py -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_i18n_analysis.py -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 0 | ANALYSIS-01 | unit | `pytest tests/test_ccb_scanner.py -v` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | ANALYSIS-01 | unit | `pytest tests/test_ccb_scanner.py::test_protocol_detection -v` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 0 | ANALYSIS-02 | unit | `pytest tests/test_gsd_scanner.py -v` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | ANALYSIS-02 | unit | `pytest tests/test_gsd_scanner.py::test_template_extraction -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_ccb_scanner.py` — stubs for ANALYSIS-01, ANALYSIS-03
- [ ] `tests/test_gsd_scanner.py` — stubs for ANALYSIS-02
- [ ] `tests/test_i18n_evaluation.py` — stubs for ANALYSIS-04
- [ ] `tests/conftest.py` — shared fixtures for AST parsing
- [ ] `pytest` — install if not present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 协议字符串分类准确性 | ANALYSIS-03 | 需要人工判断边界情况 | 抽查 10 个协议字符串,确认未被标记为可翻译文本 |
| i18n.py 可复用性评估 | ANALYSIS-04 | 架构决策需要人工审查 | 审查评估报告,确认结论有充分证据支持 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
