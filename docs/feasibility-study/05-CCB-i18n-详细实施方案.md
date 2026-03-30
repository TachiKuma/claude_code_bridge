# CCB i18n 国际化详细实施方案（修订版）

**基于:** GSD 5 阶段可行性研究 + Codex 代码级审计
**日期:** 2026-03-30
**范围:** 仅限 CCB（Claude Code Bridge）项目
**状态:** 待审批

---

## 一、Codex 审计发现的 4 项关键偏差

以下问题来源于 Codex 对代码和文档的源码级交叉验证，是修订方案的核心输入：

### 偏差 1: 逐 key 英文回退未实现

| 项目 | 详情 |
|------|------|
| **文档声称** | 回退链："当前语言 → 英文 → 键名"（01-技术方案文档.md:48） |
| **实际代码** | `i18n_core.py:38/50` 仅在整份语言文件不存在时回退英文；单个 key 缺失时直接返回 key 名（`i18n_core.py:113/116`） |
| **影响** | 渐进迁移时部分翻译缺失的鲁棒性未经验证 |
| **修复优先级** | **P0-阻断** — 必须在正式立项前修复并重新验证 |

### 偏差 2: 协议运行时保护弱于文档描述

| 项目 | 详情 |
|------|------|
| **文档声称** | "发现外部翻译命中白名单时拒绝加载并回退到内置翻译"（02-风险评估报告.md:118） |
| **实际代码** | `i18n_core.py:62` 先合并外部翻译，`i18n_core.py:70/151` 只做告警，不剔除违规值 |
| **影响** | 运行时层偏"告警"而非"防护"，与"Critical 风险已被双层机制兜住"的结论不符 |
| **修复优先级** | **P0-阻断** — 运行时保护必须从 warn 升级为 reject |

### 偏差 3: i18n 覆盖面被低估

| 项目 | 详情 |
|------|------|
| **文档估算** | 643h（CCB 全量） |
| **实际情况** | `t()` 仅在 7 个入口文件、69 个调用点；Mail/Web/TUI 仍有大量硬编码 |
| **遗漏范围** | `wizard.py`、`dashboard.html`、`mail.html`、`daemons.py`、`mail.py`、`sender.py` 等 |
| **修复优先级** | **P1** — 需重新盘点 Mail/Web/TUI 后出第二版估算 |

### 偏差 4: 原型工程化成熟度不足

| 项目 | 详情 |
|------|------|
| **问题** | `locale.getdefaultlocale()` 弃用告警（`i18n_core.py:97`、`i18n.py:271`） |
| **影响** | P0 之前需一轮"原型→稳定基础设施"清理 |
| **修复优先级** | **P0** — 使用 `locale.getlocale()` 替代 |

---

## 二、修订后实施路径

### 总体判断（综合 GSD 结论 + Codex 审计）

- **技术可行性:** 高 — 核心代码和 57 个测试存在且可运行
- **架构成熟度:** **中** — 回退链和运行时保护语义未完全闭环
- **风险控制完备度:** **中偏低** — CI 层可靠，运行时层需升级
- **工作量确定性:** **中低** — CLI 主链可估，Mail/Web/TUI 面被低估
- **立项建议:** **有条件 Go** — 先补齐 P0 缺口，再扩大样本

### 修订后阶段划分

```
Phase R0: 原型缺陷修复（~8h）  ← 新增，Codex 审计驱动
  ↓
Phase P0: CLI 核心 i18n 基础设施（~40h）
  ↓
Phase P1: Mail/Web/TUI 盘点 + CLI 全量迁移（待第二版估算）
  ↓
Phase P2: 多 AI 协作增强（~52h）
```

---

## 三、Phase R0: 原型缺陷修复（~8h）

**前置条件:** 无
**目标:** 消除 Codex 审计发现的 4 项偏差，使原型从"演示级"升级为"可立项级"

### R0-01: 修复逐 key 英文回退（3h）

**当前行为:**
```python
# i18n_core.py:113 — key 缺失时直接返回 key 名
if key not in translations:
    logger.warning(f"Missing key: {key}")
    return key  # ← 应该先尝试英文回退
```

**目标行为:**
```python
# 修复后的回退链
1. 当前语言翻译文件中查找 key
2. 如果缺失 → 查找 en.json（英文回退）
3. 如果英文也缺失 → 返回 key 本身
```

**验收标准:**
- [ ] `test_i18n_core_fallback_to_english` 测试通过
- [ ] `test_i18n_core_missing_key_in_all_locales_returns_key` 测试通过
- [ ] `test_partial_translation_fallback` — 部分翻译场景鲁棒性验证

**文件变更:**
- `lib/i18n_core.py` — 修改 `_get_translation()` 方法
- `tests/test_i18n_core.py` — 新增 3 个回退链测试

### R0-02: 升级协议运行时保护（3h）

**当前行为:**
```python
# i18n_core.py:62 — 先合并
merged.update(external)
# i18n_core.py:70 — 只告警
logger.warning(f"Protocol key found in external: {key}")
```

**目标行为:**
```python
# 修改后 — 拒绝合并违规值
for key, value in external.items():
    if self._is_protocol_key(key):
        logger.error(f"BLOCKED: Protocol key '{key}' in external translation")
        continue  # 不合并
    merged[key] = value
```

**验收标准:**
- [ ] `test_protocol_key_rejected_from_external` — 运行时拒绝测试
- [ ] `test_protocol_key_falls_back_to_builtin` — 拒绝后回退内置测试
- [ ] `test_non_protocol_keys_still_merged` — 合规 key 正常合并测试
- [ ] CI 脚本 `scripts/check_protocol_strings.py` 仍然通过

**文件变更:**
- `lib/i18n_core.py` — 修改 `_load_translations()` 方法
- `tests/test_i18n_core.py` — 新增 3 个运行时保护测试

### R0-03: 修复弃用告警 + 原型清理（2h）

**变更内容:**
- `i18n_core.py:97` — `locale.getdefaultlocale()` → `locale.getlocale()`
- `i18n.py:271` — 同上
- 清理所有测试运行时的弃用告警

**验收标准:**
- [ ] `python -W error -m pytest tests/ -q` 全部通过，无 DeprecationWarning
- [ ] 原有 57 个测试不受影响

---

## 四、Phase P0: CLI 核心 i18n 基础设施（~40h）

**前置条件:** R0 全部完成并通过验证
**目标:** 将 i18n 基础设施从原型升级为生产级，覆盖 CLI 全链路

### P0-01: 翻译文件完善（12h）

**当前状态:** 56 条消息已迁移（en.json/zh.json/xx.json）

**任务清单:**
1. 扫描 `lib/` 下所有 `print()`、`logger.info/warning/error()`、`raise` 调用
2. 识别 CLI 核心模块中未覆盖的用户可见消息
3. 补充翻译条目，目标覆盖率 > 95%（CLI 核心）
4. 建立翻译条目命名规范文档

**CLI 核心模块范围（基于 Codex 审计确认的 69 个调用点）:**
- `ccb` — 主入口
- `lib/codex_comm.py` — Codex 通信
- `lib/gemini_comm.py` — Gemini 通信
- `lib/opencode_comm.py` — OpenCode 通信
- `lib/droid_comm.py` — Droid 通信
- `bin/ask`、`bin/cask`、`bin/gask` — CLI 包装脚本

**验收标准:**
- [ ] CLI 核心 `t()` 调用点覆盖率 ≥ 95%
- [ ] en.json 条目 ≥ 200 条
- [ ] zh.json 与 en.json 1:1 对应
- [ ] `scripts/check_protocol_strings.py` CI 通过

### P0-02: 错误消息标准化（8h）

**任务清单:**
1. 统一错误消息格式：`{action} failed: {reason}`
2. 为所有 `TaskResult(status='error')` 场景添加翻译
3. 建立错误码体系（`E001`-`E050`）
4. 错误消息支持变量插值 `t('error.file_not_found', path=xxx)`

**验收标准:**
- [ ] 错误消息 100% 走翻译系统
- [ ] 错误码与翻译 key 1:1 映射
- [ ] 变量插值在 en/zh 两语言下均正常渲染

### P0-03: CI/CD 集成（6h）

**任务清单:**
1. 将 `scripts/check_protocol_strings.py` 集成到 CI pipeline
2. 新增翻译覆盖率检查（`t()` 调用必须全部有对应翻译 key）
3. 新增翻译完整性检查（en.json 与 zh.json 条目数一致）
4. 添加 pre-commit hook

**验收标准:**
- [ ] CI 中 3 个检查全部通过：协议保护、翻译覆盖率、翻译完整性
- [ ] pre-commit hook 在本地生效
- [ ] 违规时 CI 明确报告缺失的翻译 key

### P0-04: 文档和测试补全（8h）

**任务清单:**
1. 编写 `lib/i18n_core.py` 模块文档（docstring + 使用示例）
2. 编写迁移指南（如何将现有 `print()` 改为 `t()` 调用）
3. 补全边界条件测试（空文件、损坏 JSON、编码异常）
4. 性能基准测试（翻译查找延迟 < 1μs）

**验收标准:**
- [ ] 模块文档覆盖率 100%
- [ ] 测试覆盖率达到 ≥ 90%（`lib/i18n_core.py`）
- [ ] 性能基准通过

### P0-05: 语言切换机制（6h）

**任务清单:**
1. 实现 `CCB_LANG` 环境变量支持
2. 实现 `ccb config lang` 命令
3. 实现运行时语言检测（`locale.getlocale()`）
4. 添加 `--lang` 命令行参数支持

**验收标准:**
- [ ] `CCB_LANG=zh` 切换中文
- [ ] `CCB_LANG=en` 切换英文
- [ ] `CCB_LANG=xx` 使用占位符模式（调试用）
- [ ] 缺少翻译时按 R0 修复后的回退链处理

---

## 五、Phase P1: Mail/Web/TUI 盘点 + CLI 全量迁移（待第二版估算）

**前置条件:** P0 完成
**目标:** 扩大 i18n 覆盖范围，补全 Mail/Web/TUI

### P1-01: Mail/Web/TUI 文案盘点（8h）

**Codex 审计识别的遗漏范围:**

| 模块 | 文件 | 问题 |
|------|------|------|
| Mail TUI | `lib/mail_tui/wizard.py:113/196` | 硬编码中文 UI 文本 |
| Web 模板 | `lib/web/templates/dashboard.html:17` | 硬编码英文 |
| Web 模板 | `lib/web/templates/mail.html:23` | 硬编码英文 |
| Web API | `lib/web/routes/daemons.py:96` | 硬编码消息 |
| Web API | `lib/web/routes/mail.py:238` | 硬编码消息 |
| Mail 发送 | `lib/mail/sender.py:273/281` | 硬编码邮件正文 |

**任务清单:**
1. 逐一扫描上述文件中的硬编码文本
2. 分类为"用户可见"和"系统内部"
3. 评估翻译复杂度（纯文本 vs HTML 模板 vs 动态生成）
4. 输出第二版工作量估算

**验收标准:**
- [ ] 完整的文案盘点清单（含文件、行号、文本内容、分类）
- [ ] 修订后工作量估算（更新 643h → 实际值）
- [ ] Mail/Web/TUI 翻译策略文档

### P1-02: CLI 全量迁移（预估 200-300h，待 P1-01 后确认）

**任务清单:**
1. 将所有剩余 CLI 模块的硬编码文本迁移到翻译系统
2. 逐模块验证功能不受影响
3. 更新协议白名单（如有新增协议字符串）

**验收标准:**
- [ ] `rg -c 't\(' lib/` 调用点数与文案盘点一致
- [ ] 全部 CI 检查通过
- [ ] 功能回归测试通过

### P1-03: Mail/Web/TUI i18n 实施（预估 150-250h，待 P1-01 后确认）

**任务清单:**
1. HTML 模板国际化（dashboard、mail 等）
2. 邮件正文模板国际化
3. Web API 返回消息国际化
4. Mail TUI 向导国际化

---

## 六、Phase P2: 多 AI 协作增强（~52h）

**前置条件:** P0 完成（可与 P1 并行）
**目标:** 让 CCB 在 CCB 多 AI 环境中更好地利用协作能力

### P2-01: CCBCLIBackend 生产化（20h）

**当前状态:** 177 行原型，25 个 mock 测试

**任务清单:**
1. 集成真实终端后端（替换 mock）
2. 添加超时和重试机制
3. 实现多 provider 并发安全（ProviderLock）
4. 错误处理完善

**验收标准:**
- [ ] `ccb submit codex "hello"` 真实执行成功
- [ ] `ccb poll <handle>` 正确返回结果
- [ ] 并发 submit 同一 provider 时正确排队
- [ ] 网络超时时优雅降级

### P2-02: 多 AI 任务编排（20h）

**任务清单:**
1. 实现并行任务提交（多 provider 同时执行）
2. 实现任务依赖图（DAG）
3. 结果聚合和冲突解决
4. 任务状态持久化

**验收标准:**
- [ ] 同时向 3 个 provider 提交任务并收集结果
- [ ] 依赖任务按正确顺序执行
- [ ] 进程重启后恢复任务状态

### P2-03: 质量保证机制（12h）

**任务清单:**
1. 实现回复质量评分（自动）
2. 实现多 AI 交叉验证
3. 实现结果缓存和去重

---

## 七、资源估算总览

### 修订后估算

| 阶段 | 工时 | 依赖 | 里程碑 |
|------|------|------|--------|
| **R0: 原型缺陷修复** | **8h** | 无 | 可立项门槛 |
| **P0: CLI 核心 i18n** | **40h** | R0 | CLI i18n 生产可用 |
| **P1-01: 盘点** | **8h** | P0 | 第二版估算输入 |
| **P1-02/03: 全量实施** | **TBD** | P1-01 | 全量 i18n 覆盖 |
| **P2: 多 AI 增强** | **52h** | P0 | 多 AI 协作可用 |
| **合计（已知部分）** | **108h** | | |
| **合计（含全量估算）** | **~643h+** | | 原始估算可能偏低 |

### 与原始估算对比

| 维度 | 原始 GSD 结论 | 修订后（含 Codex 审计） |
|------|--------------|----------------------|
| 立项门槛 | 原型验证通过即可 | 需先完成 R0（8h 修复） |
| CLI i18n | 60h (P0) | 40h (P0，不含 R0) |
| 全量 i18n | 536h | 待 P1-01 盘点后修订（可能上调） |
| 多 AI | 40-60h | 52h（不变） |
| 风险评级 | Critical 风险已缓解 | 运行时保护需从 warn→reject |

---

## 八、Go/No-Go 决策框架

### Go 条件（全部满足）

- [ ] R0 的 3 项修复全部完成
- [ ] 修复后 57+ 测试全部通过
- [ ] Codex 复审通过（可请 Codex 二次审计 R0 修复后的代码）

### 有条件 Go（满足 Go 条件后可启动 P0）

- [ ] P0 预算 40h 获批
- [ ] P1-01 盘点工作（8h）纳入 P0 后续计划

### No-Go 信号

- R0 修复引发新的测试失败
- 修复后发现架构根本性问题需要重新设计

---

## 九、Codex 建议的下一步行动

1. 修正文档与实现偏差（本方案已覆盖）
2. 补齐逐 key 英文回退和外部翻译违规回退，重新跑原型验证（R0-01, R0-02）
3. 单独盘点 Mail/Web/TUI 文案面，形成第二版工作量估算（P1-01）
4. 对 GSD 部分做源码级复核后再接受总量结论（建议纳入 R0 验收）

---

## 附录: 验证清单

### R0 完成标准（8h 修复后）

| 检查项 | 命令 | 预期 |
|--------|------|------|
| 逐 key 英文回退 | `python -m pytest tests/test_i18n_core.py -k fallback -v` | 3 个新测试通过 |
| 运行时协议拒绝 | `python -m pytest tests/test_i18n_core.py -k protocol -v` | 3 个新测试通过 |
| 无弃用告警 | `python -W error -m pytest tests/ -q` | 60+ 测试通过，0 告警 |
| CI 脚本仍通过 | `python scripts/check_protocol_strings.py` | 检测 3 个已知违规 |
| Codex 复审 | `ask codex "审计 lib/i18n_core.py 的 R0 修复"` | 确认偏差已消除 |

### P0 完成标准

| 检查项 | 命令 | 预期 |
|--------|------|------|
| 翻译覆盖率 | `python scripts/check_translation_coverage.py` | CLI 核心 ≥ 95% |
| 翻译完整性 | `diff <(jq keys en.json) <(jq keys zh.json)` | 完全一致 |
| CI 全通过 | `python scripts/check_protocol_strings.py` | 0 新违规 |
| 测试通过 | `python -m pytest tests/ -q` | 80+ 测试通过 |
| 语言切换 | `CCB_LANG=zh ccb help` | 中文输出 |

---

*方案基于 GSD 5 阶段可行性研究 + Codex 代码级审计综合生成*
*核心数据: 57 测试, 300 白名单, 9029 文本, 5 PROTO 全 SATISFIED*
*关键修正: R0 阶段（8h）为新增，解决文档-实现偏差*
