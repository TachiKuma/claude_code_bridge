# Phase 7: Windows 原生环境专项检查 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 07-windows-native-audit
**Areas discussed:** 检查范围与优先级, 检查深度, 交付形式, 安全深度, 自动化测试形式, 运行环境, 修复范围, 性能基准线, 编码重点

---

## 检查范围与优先级

| Option | Description | Selected |
|--------|-------------|----------|
| 全部三大维度 | 性能、兼容性、安全性全面检查 | ✓ |
| 性能优先 | 重点检查 daemon 启动、内存、通信 | ✓ |
| 兼容性优先 | 重点检查编码、路径、PowerShell | ✓ |
| 安全性优先 | 重点检查权限、泄露、隔离 | ✓ |

**User's choice:** 全部选中 — 最全面的检查范围

---

## 检查深度

| Option | Description | Selected |
|--------|-------------|----------|
| 代码审计 + 实际运行验证 | 静态分析 + 实际运行，输出量化数据 | |
| 仅代码审计 | 只做静态代码分析 | |
| 全面自动化测试 | 建立自动化测试套件覆盖核心场景 | ✓ |

**User's choice:** 全面自动化测试 — 要求建立可回归的自动化测试体系

---

## 交付形式

| Option | Description | Selected |
|--------|-------------|----------|
| 问题清单 + 提升方案文档 | 分类列出问题，附带严重程度和修复建议 | |
| 直接实施修复 | 检查后直接修复代码 | |
| 两者都要 | 先输出报告，再按优先级实施修复 | ✓ |

**User's choice:** 两者都要 — 完整报告 + 全部修复

---

## 安全深度

| Option | Description | Selected |
|--------|-------------|----------|
| 实用安全审计 | 文件权限、泄露、隔离、token | |
| 基础检查 | 仅明显安全问题 | |
| 深入渗透 | 代码注入、socket 安全、daemon 提权 | ✓ |

**User's choice:** 深入渗透 — 最高安全审计标准

---

## 自动化测试形式

| Option | Description | Selected |
|--------|-------------|----------|
| pytest 测试套件 | 集成到现有测试体系 | ✓ |
| 独立检查脚本 | 逐一验证，输出 pass/fail | |
| 两者兼备 | 同时创建 | |

**User's choice:** pytest 测试套件

---

## 运行环境

| Option | Description | Selected |
|--------|-------------|----------|
| 当前原生 Windows | 在当前 Windows 10 Pro 中直接运行 | ✓ |
| 容器化模拟 | Docker 模拟 | |
| 本地 + CI | 本地主 + CI 虚拟环境辅助 | |

**User's choice:** 当前原生 Windows 10 Pro

---

## 修复范围

| Option | Description | Selected |
|--------|-------------|----------|
| 仅 Critical/High | 只修高级别 | |
| 全部修复 | 不区分严重程度 | ✓ |
| Critical/High 修复 + Medium 建议 | 混合方案 | |

**User's choice:** 全部修复

---

## 性能基准线

| Option | Description | Selected |
|--------|-------------|----------|
| 严格指标 | daemon < 3s, 响应 < 500ms, 内存 < 50MB | ✓ |
| 宽松指标 | daemon < 5s, 响应 < 1s, 内存 < 100MB | |
| 仅采集不设限 | 只采集数据 | |

**User's choice:** 严格指标

---

## 编码重点

| Option | Description | Selected |
|--------|-------------|----------|
| 中文场景优先 | 中文路径、内容、PS 5.1 | |
| 全面编码覆盖 | UTF-8/GBK/Windows-1252/Shift-JIS | ✓ |
| 仅 UTF-8 | 只检查 UTF-8 | |

**User's choice:** 全面编码覆盖

---

## Claude's Discretion

以下方面用户未指定偏好，由 Claude 在规划/实施时自行决定：
- 测试文件的组织结构和命名约定
- 性能测试的具体实现方式
- 问题严重程度的分级标准
- 修复的优先级排序策略
- pytest fixture 和 conftest 的组织方式
