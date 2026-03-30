# Roadmap: GSD & CCB 国际化与多 AI 协作可行性研究

**项目:** GSD & CCB 国际化与多 AI 协作可行性研究
**创建日期:** 2026-03-28
**粒度:** fine
**总阶段数:** 6

## 核心价值

通过国际化和多 AI 协作，让 GSD 和 CCB 能够服务更广泛的用户群体，并显著提升复杂任务的执行质量。

## Phases

- [x] **Phase 1: 代码库分析** - 识别所有需要国际化的文本位置 (completed 2026-03-28)
- [x] **Phase 2: 架构设计** - 设计共享 i18n 和多 AI 协作架构 (completed 2026-03-28)
- [x] **Phase 3: 风险评估** - 评估实施风险和工作量 (completed 2026-03-30)
- [x] **Phase 4: 原型验证** - 验证关键技术点可行性 (completed 2026-03-30)
- [x] **Phase 5: 文档交付** - 编写完整技术方案和建议 (completed 2026-03-30)
- [ ] **Phase 6: CCB i18n 实施** - 按修订实施方案完成 CCB 国际化落地

## Phase Details

### Phase 1: 代码库分析
**Goal**: 识别 CCB 和 GSD 代码库中所有需要国际化的文本，区分人类可读文本和协议字符串
**Depends on**: 无（起点阶段）
**Requirements**: ANALYSIS-01, ANALYSIS-02, ANALYSIS-03, ANALYSIS-04
**Success Criteria** (what must be TRUE):
  1. CCB 代码库中所有硬编码文本位置已被识别和分类
  2. GSD 代码库中所有硬编码文本位置已被识别和分类
  3. 人类可读文本和协议字符串（命令名、环境变量、完成标记）已明确区分
  4. 现有 CCB i18n.py 的可复用性评估报告已完成
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — 扫描 CCB 代码库提取所有字符串
- [x] 01-02-PLAN.md — 扫描 GSD 代码库并实现分类器
- [x] 01-03-PLAN.md — 评估 i18n.py 并生成分析报告

### Phase 2: 架构设计
**Goal**: 设计共享 i18n_core 模块和 CCBCLIBackend 接口，建立协议字符串保护机制
**Depends on**: Phase 1
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05
**Success Criteria** (what must be TRUE):
  1. 共享 i18n_core 模块架构已设计（命名空间、回退机制、t() API）
  2. CCBCLIBackend 接口已设计（submit/poll/ping/list_providers 方法）
  3. TaskHandle/TaskResult 数据结构已定义（避免文本解析）
  4. 协议字符串保护机制已设计（CI 检查、白名单）
  5. 翻译文件组织结构已确定（ccb/, gsd/, common/ 目录）
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — 设计 i18n_core 模块和翻译文件结构
- [x] 02-02-PLAN.md — 设计 CCBCLIBackend 接口和数据结构
- [x] 02-03-PLAN.md — 设计协议字符串保护机制

### Phase 3: 风险评估
**Goal**: 评估协议误翻译、上下文崩溃、竞态条件等风险，估算实施工作量
**Depends on**: Phase 2
**Requirements**: RISK-01, RISK-02, RISK-03, RISK-04, RISK-05
**Success Criteria** (what must be TRUE):
  1. 协议字符串误翻译的影响已评估，缓解策略已制定
  2. 多 AI 上下文崩溃的风险已评估，解决方案已确定
  3. 会话文件竞态条件的风险已评估，文件锁方案已确定
  4. i18n 改造的工作量已估算（代码行数、文件数、时间）
  5. 多 AI 集成的工作量和技术复杂度已估算
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — 协议字符串保护风险评估
- [x] 03-02-PLAN.md — 多 AI 并发风险评估
- [x] 03-03-PLAN.md — 工作量估算报告

### Phase 4: 原型验证
**Goal**: 验证关键技术点可行性（i18n_core、CCBCLIBackend、协议保护、FileLock）
**Depends on**: Phase 2, Phase 3
**Requirements**: PROTO-01, PROTO-02, PROTO-03, PROTO-04, PROTO-05
**Success Criteria** (what must be TRUE):
  1. i18n_core 最小原型已实现并验证（命名空间、t() API 工作正常）
  2. CCBCLIBackend 最小原型已实现并验证（能包装 ask/pend 命令）
  3. 协议字符串保护机制已验证（CI 检查脚本能检测误翻译）
  4. TaskHandle 结构化传递已验证（避免文本解析）
  5. 跨平台文件锁机制已验证（Windows/Linux/macOS 均可工作）
**Plans**: 4 plans

Plans:
- [x] 04-01-PLAN.md — I18nCore 原型验证
- [x] 04-02-PLAN.md — CCBCLIBackend 原型验证
- [x] 04-03-PLAN.md — 协议字符串保护验证
- [x] 04-04-PLAN.md — FileLock 跨平台验证

### Phase 5: 文档交付
**Goal**: 编写完整的技术方案文档、风险评估报告、原型验证报告和实施建议
**Depends on**: Phase 3, Phase 4
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04
**Success Criteria** (what must be TRUE):
  1. 技术方案文档已完成（架构设计、实施路径清晰）
  2. 风险评估报告已完成（工作量、技术风险、缓解策略明确）
  3. 原型验证报告已完成（关键技术点验证结果记录）
  4. 实施建议已完成（阶段划分、优先级、资源需求明确）
**Plans**: 3 plans

Plans:
- [x] 05-01-PLAN.md — 执行摘要 + 技术方案文档
- [x] 05-02-PLAN.md — 风险评估报告 + 原型验证报告
- [x] 05-03-PLAN.md — 实施建议 + 最终审查

### Phase 6: CCB i18n 实施
**Goal**: 基于 `docs/feasibility-study/05-CCB-i18n-详细实施方案.md` 完成 CCB i18n 的阻断项修复、CLI 核心生产化、覆盖盘点和全量迁移准备
**Depends on**: Phase 5
**Requirements**: I18N-01, I18N-02, I18N-03, I18N-04, I18N-05, I18N-06
**Success Criteria** (what must be TRUE):
  1. `lib/i18n_core.py` 的逐 key 英文回退、外部翻译协议拒绝、locale 检测行为与修订方案一致
  2. CLI 核心用户可见消息完成翻译迁移，目标范围内 `t()` 覆盖率达到 >= 95%
  3. 翻译 CI 守卫、完整性检查和语言切换机制具备可执行落地方案
  4. Mail/Web/TUI 的文案盘点和第二版工时估算已形成书面产物
  5. CCB 全量 i18n 迁移的执行顺序、回归门禁和验证命令已明确
**Plans**: 6 plans

Plans:
- [x] 06-01-PLAN.md — 修复 i18n_core 阻断项与弃用告警
- [ ] 06-02-PLAN.md — 扩展 CLI 核心翻译覆盖并标准化错误消息
- [x] 06-03-PLAN.md — 建立语言切换、CI 守卫与测试补全
- [ ] 06-04-PLAN.md — 盘点 Mail/Web/TUI 文案并更新估算
- [ ] 06-05-PLAN.md — 执行全量迁移与回归验证
- [ ] 06-06-PLAN.md — Skill 模板双语化 + Install 脚本全量迁移 + argparse help t() 包裹 + Config 模板混合翻译

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 代码库分析 | 3/3 | Complete   | 2026-03-28 |
| 2. 架构设计 | 3/3 | Complete   | 2026-03-28 |
| 3. 风险评估 | 3/3 | Complete   | 2026-03-30 |
| 4. 原型验证 | 4/4 | Complete   | 2026-03-30 |
| 5. 文档交付 | 3/3 | Complete   | 2026-03-30 |
| 6. CCB i18n 实施 | 0/6 | Not Started | - |

## Coverage

**Total requirements:** 29
**Mapped to phases:** 29
**Unmapped:** 0

### Requirement Mapping

| Requirement | Phase | Category |
|-------------|-------|----------|
| ANALYSIS-01 | 1 | 代码分析 |
| ANALYSIS-02 | 1 | 代码分析 |
| ANALYSIS-03 | 1 | 代码分析 |
| ANALYSIS-04 | 1 | 代码分析 |
| ARCH-01 | 2 | 架构设计 |
| ARCH-02 | 2 | 架构设计 |
| ARCH-03 | 2 | 架构设计 |
| ARCH-04 | 2 | 架构设计 |
| ARCH-05 | 2 | 架构设计 |
| RISK-01 | 3 | 风险评估 |
| RISK-02 | 3 | 风险评估 |
| RISK-03 | 3 | 风险评估 |
| RISK-04 | 3 | 风险评估 |
| RISK-05 | 3 | 风险评估 |
| PROTO-01 | 4 | 原型验证 |
| PROTO-02 | 4 | 原型验证 |
| PROTO-03 | 4 | 原型验证 |
| PROTO-04 | 4 | 原型验证 |
| PROTO-05 | 4 | 原型验证 |
| DOC-01 | 5 | 文档交付 |
| DOC-02 | 5 | 文档交付 |
| DOC-03 | 5 | 文档交付 |
| DOC-04 | 5 | 文档交付 |
| I18N-01 | 6 | 原型修复 |
| I18N-02 | 6 | CLI 核心生产化 |
| I18N-03 | 6 | CI 与完整性保护 |
| I18N-04 | 6 | 语言切换 |
| I18N-05 | 6 | 文案盘点 |
| I18N-06 | 6 | 全量迁移与回归 |

---
*Roadmap created: 2026-03-28*
*Last updated: 2026-03-30*
