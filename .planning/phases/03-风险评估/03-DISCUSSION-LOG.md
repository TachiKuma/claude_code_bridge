# Phase 3: 风险评估 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 03-风险评估
**Areas discussed:** 协议字符串误翻译风险, 多 AI 并发风险, 实施工作量估算, 技术债务风险

---

## 协议字符串误翻译风险

### 影响评估
| Option | Selected |
|--------|----------|
| 完全破坏 — CCB 守护进程无法识别命令，系统崩溃 | ✓ |
| 部分破坏 — 某些功能失效，但系统仍可运行 | |
| 静默失败 — 错误不明显，难以调试 | |

**User's choice:** 完全破坏

### 最高风险漏洞
| Option | Selected |
|--------|----------|
| 运行时检测 — CI 只检查静态文件，运行时动态生成的字符串无法检测 | |
| 白名单维护 — 新增协议字符串时，开发者可能忘记更新白名单 | |
| 外部翻译 — 用户自定义翻译（~/.ccb/i18n/）绕过 CI 检查 | ✓ |

**User's choice:** 外部翻译

### 缓解方案
| Option | Selected |
|--------|----------|
| 运行时验证 — i18n_core 加载外部翻译时检查白名单，拒绝协议字符串覆盖 | ✓ |
| 文档警告 — 在用户文档中明确说明不要翻译协议字符串 | |
| 仅允许 ccb.* 命名空间 — 外部翻译只能覆盖 ccb.* 开头的键 | |

**User's choice:** 运行时验证

---

## 多 AI 并发风险

### 文件锁方案
| Option | Selected |
|--------|----------|
| 操作系统级文件锁 — 使用 fcntl (Unix) / msvcrt (Windows)，跨进程可靠 | ✓ |
| 应用级锁文件 — 创建 .lock 文件标记占用，简单但不够健壮 | |
| 无锁设计 — 每个 AI 使用独立会话文件，避免共享 | |

**User's choice:** 操作系统级文件锁

### 超时策略
| Option | Selected |
|--------|----------|
| 立即失败 — 返回错误，让调用者重试 | |
| 等待重试 — 循环尝试 N 次，每次等待 T 秒 | ✓ |
| 队列机制 — 将请求加入队列，按顺序处理 | |

**User's choice:** 等待重试（统一接口 + 等待重试）
**Notes:** FileLock 类封装平台差异，默认重试 3 次，每次等待 0.5 秒

---

## 实施工作量估算

### 最耗时部分
**User's choice:** 翻译文件创建 > 代码修改 > 测试覆盖

### 时间估算确认
**User's choice:** 合理
**Notes:** 完整实施约 536 小时（13.4 周），原型阶段约 26 小时（3-4 天）

---

## 技术债务风险

### 主要担忧
**User's choice:** 字符串提取不完整，键命名不一致

### 缓解策略选择
| Option | Selected |
|--------|----------|
| 自动化扫描工具 — 使用 AST 分析确保覆盖所有字符串 | ✓ |
| 代码审查清单 — PR 必须检查是否有遗漏的硬编码文本 | |
| 运行时检测 — 开发模式下记录所有未翻译的键 | |
| 命名规范文档 — 定义清晰的键命名约定 | ✓ |
| 自动化检查 — CI 验证键名符合规范 | |
| 代码生成工具 — 提供脚本自动生成标准键名 | |

**User's choice:** 命名规范文档 + 自动化扫描工具

---

## Claude's Discretion

无 — 所有关键决策已由用户确认

## Deferred Ideas

- 性能回归风险评估 — Phase 1 已测试性能，当前不是主要风险
- 测试覆盖下降风险 — 属于 Phase 4 原型验证阶段
- MCP Backend 的并发风险 — CLI Backend 优先
