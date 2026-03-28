---
phase: 02-架构设计
plan: 02
subsystem: multi-ai-collaboration
tags: [interface-design, data-structures, ccb-integration]
dependency_graph:
  requires: [02-01]
  provides: [ccb-cli-backend-spec, task-models-spec]
  affects: [phase-04-prototype]
tech_stack:
  added: [subprocess, dataclasses, typing]
  patterns: [structured-task-passing, error-as-value]
key_files:
  created:
    - .planning/phases/02-架构设计/designs/task_models_design.md
    - .planning/phases/02-架构设计/designs/ccb_cli_backend_design.md
  modified: []
decisions:
  - id: D-08
    summary: "CCBCLIBackend 提供 4 个核心方法"
  - id: D-09
    summary: "使用结构化对象 TaskHandle/TaskResult"
  - id: D-10
    summary: "错误处理返回 TaskResult(status='error')，不抛出异常"
  - id: D-11
    summary: "通过 subprocess 包装 ask/pend 命令实现"
metrics:
  duration_seconds: 144
  tasks_completed: 2
  files_created: 2
  commits: 2
  completed_date: "2026-03-28"
---

# Phase 02 Plan 02: CCBCLIBackend 接口与任务数据结构设计 Summary

**一句话总结:** 设计了结构化的多 AI 协作接口（CCBCLIBackend）和任务数据模型（TaskHandle/TaskResult），通过 subprocess 包装 CCB CLI 命令，避免解析控制台文本。

## 执行概览

**计划:** 02-02-PLAN.md
**状态:** ✅ 完成
**时长:** 144 秒 (~2.4 分钟)
**任务:** 2/2 完成

## 交付成果

### 1. TaskHandle 和 TaskResult 数据结构设计

**文件:** `.planning/phases/02-架构设计/designs/task_models_design.md` (256 行)

**核心内容:**
- TaskHandle 数据结构：task_id, provider, timestamp 三个字段
- TaskResult 数据结构：task_id, status, output, error 四个字段
- 状态转换图：pending → completed/error
- 错误处理策略：不抛出异常，通过 status 字段返回错误
- 使用示例和序列化支持

**关键设计决策:**
- task_id 格式：`{provider}_{timestamp_ms}`（可读性 + 包含提供商信息）
- status 使用字符串而非枚举（简单、易于序列化）
- 使用 dataclass（类型安全、IDE 支持、可扩展）

### 2. CCBCLIBackend 接口设计

**文件:** `.planning/phases/02-架构设计/designs/ccb_cli_backend_design.md` (404 行)

**核心内容:**
- submit() 方法：提交任务返回 TaskHandle
- poll() 方法：轮询结果返回 TaskResult
- ping() 方法：检查提供商连接
- list_providers() 方法：列出可用 AI
- subprocess 包装实现模式
- 与 CCB 命令的映射表

**关键设计决策:**
- 后台提交：submit() 不等待命令完成
- 命令映射：codex → cpend, droid → dpend, gemini → gpend
- 超时设置：poll() 5秒，ping() 2秒
- 错误处理：所有方法不抛出异常，通过返回值报告错误

## 提交记录

| Task | Commit | 文件 |
|------|--------|------|
| 1 | 1eedf01 | task_models_design.md |
| 2 | de95d3c | ccb_cli_backend_design.md |

## 偏差说明

**无偏差** — 计划按原定设计执行。

## 需求覆盖

- ✅ **ARCH-02:** CCBCLIBackend 接口已设计（submit/poll/ping/list_providers）
- ✅ **ARCH-03:** TaskHandle/TaskResult 数据结构已设计

## 关键洞察

1. **结构化优于文本解析:** 使用 TaskHandle/TaskResult 对象传递状态，避免解析控制台输出，语言切换时不会破坏功能

2. **错误即值模式:** 所有方法不抛出异常，通过返回值报告错误（TaskResult.status="error"），简化调用者的错误处理逻辑

3. **subprocess 包装简单可靠:** 直接包装 CCB 现有命令（ask/pend/ping），无需修改 CCB 代码，实现成本低

4. **预留扩展点:** context 参数、metadata 字段等预留扩展点，未来添加功能不破坏兼容性

## 下游影响

**Phase 04 原型验证:**
- 可直接基于这两份设计文档实现 Python 原型
- 接口定义清晰，实现路径明确
- 测试用例可基于使用示例编写

**Phase 03 风险评估:**
- 需评估 subprocess 包装的性能开销
- 需评估并发场景下的竞态条件风险

## 已知限制

1. **非线程安全:** 当前设计未考虑锁机制，同一提供商的 poll() 应串行调用
2. **单任务限制:** 每个提供商同一时刻只能有一个活跃任务
3. **无流式输出:** 当前设计不支持部分结果返回

这些限制在可行性研究阶段可接受，生产实现时需要解决。

## 自检结果

✅ **PASSED**

检查项：
- [x] task_models_design.md 存在且包含 TaskHandle/TaskResult 定义
- [x] ccb_cli_backend_design.md 存在且包含 4 个方法设计
- [x] 两份文档引用用户决策 D-08, D-09, D-10, D-11
- [x] 提交 1eedf01 存在
- [x] 提交 de95d3c 存在
- [x] 文档行数满足要求（256 行 > 40 行，404 行 > 80 行）

---

**完成时间:** 2026-03-28
**下一步:** 继续执行 Phase 02 其他计划（i18n_core 设计、协议字符串保护机制）
