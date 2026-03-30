# Phase 4: 原型验证 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 04-原型验证
**Areas discussed:** 原型范围和优先级, i18n_core 原型实现方式, CCBCLIBackend 和文件锁验证, 验证方式和验收标准

---

## 原型范围和优先级

| Option | Description | Selected |
|--------|-------------|----------|
| 全部 5 个 PROTO | PROTO-01~05 全部实现，26 小时上限 | |
| 核心优先 | PROTO-01+03 完整，其他概念验证 | ✓ |
| 最小验证 | 仅 PROTO-01+03，其他仅文档 | |

**User's choice:** 核心优先

---

## i18n_core 原型实现方式

### 实现深度

| Option | Description | Selected |
|--------|-------------|----------|
| 完整实现设计文档 | 按 Phase 2 文档完整实现 I18nCore | ✓ |
| 简化实现核心逻辑 | 仅 t() API 和基础加载 | |

**User's choice:** 完整实现设计文档

### 验证方式

| Option | Description | Selected |
|--------|-------------|----------|
| 纯单元测试 | 不启动 CCB，仅单元测试 | |
| 单元测试 + Demo 脚本 | 额外写 demo 展示效果 | ✓ |

**User's choice:** 单元测试 + Demo 脚本

### 翻译文件数量

| Option | Description | Selected |
|--------|-------------|----------|
| 中英文 | en.json + zh.json | |
| 中英文 + 伪翻译 | 额外 xx.json 伪翻译文件 | ✓ |

**User's choice:** 中英文 + 伪翻译

### i18n.py 兼容性

| Option | Description | Selected |
|--------|-------------|----------|
| 独立验证 | i18n_core 完全独立 | |
| i18n.py 接入 i18n_core | 修改 i18n.py 调用 i18n_core | ✓ |

**User's choice:** i18n.py 接入 i18n_core

### 消息迁移数量

| Option | Description | Selected |
|--------|-------------|----------|
| 50 条关键消息 | 最小验证 | |
| 全部现有消息 | 迁移 i18n.py 全部 56 条 | ✓ |

**User's choice:** 全部现有消息

### 伪翻译策略

| Option | Description | Selected |
|--------|-------------|----------|
| 标记 + 拉长 | [«text»] + x 填充 | ✓ |
| 仅标记 | [«text»] | |

**User's choice:** 标记 + 拉长

### 代码位置

| Option | Description | Selected |
|--------|-------------|----------|
| 放入项目 lib/ | 与生产代码结构一致 | ✓ |
| 放在 Phase 目录下 | 与项目代码隔离 | |

**User's choice:** 放入项目 lib/

---

## CCBCLIBackend 和文件锁验证

### CCBCLIBackend 验证方式

| Option | Description | Selected |
|--------|-------------|----------|
| Mock 测试 | 不依赖真实 CCB 环境 | ✓ |
| 真实环境验证 | 需要 CCB 守护进程 | |

**User's choice:** Mock 测试

### 文件锁验证深度

| Option | Description | Selected |
|--------|-------------|----------|
| 单元测试验证 | 验证当前系统 | ✓ |
| 单元 + 并发测试 | 多进程竞争测试 | |

**User's choice:** 单元测试验证

### CCBCLIBackend 实现范围

| Option | Description | Selected |
|--------|-------------|----------|
| 完整实现 | 4 个方法全部实现 | ✓ |
| 仅核心方法 | submit + poll | |

**User's choice:** 完整实现

### TaskHandle 模块组织

| Option | Description | Selected |
|--------|-------------|----------|
| 独立模块实现 | lib/task_models.py | ✓ |
| 内嵌在 Backend 中 | 同一文件 | |

**User's choice:** 独立模块实现

---

## 验证方式和验收标准

### 验收标准

| Option | Description | Selected |
|--------|-------------|----------|
| 测试通过 + 报告 | 单元测试 + Demo + 验证报告 | ✓ |
| 仅测试通过 | 最小验证 | |

**User's choice:** 测试通过 + 报告

### 报告组织

| Option | Description | Selected |
|--------|-------------|----------|
| 分 PROTO 报告 + 汇总 | 每个 PROTO 单独报告 + 汇总 | ✓ |
| 单一汇总报告 | 一个文档 | |

**User's choice:** 分 PROTO 报告 + 汇总

### 报告内容

| Option | Description | Selected |
|--------|-------------|----------|
| 测试结果 + 发现 + 建议 | 完整报告 | ✓ |
| 测试结果 + 发现 | 简要报告 | |

**User's choice:** 测试结果 + 发现 + 建议

### 测试框架

| Option | Description | Selected |
|--------|-------------|----------|
| unittest | Python 内置，无额外依赖 | ✓ |
| pytest | 功能强大但需新依赖 | |

**User's choice:** unittest

---

## Claude's Discretion

- FileLock 类的具体实现细节
- 运行时验证的错误消息格式和日志级别
- Demo 脚本的具体展示内容和格式
- 伪翻译文件中字符串拉长的倍数
- 协议检查脚本的具体命令行参数

## Deferred Ideas

- 真实 CCB 环境中的 CCBCLIBackend 集成测试
- 跨平台文件锁的多平台实际验证
- MCP Backend 实现
- 并发文件锁的多进程竞争测试
