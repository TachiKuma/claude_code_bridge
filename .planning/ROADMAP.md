# Roadmap: GSD & CCB 国际化与多 AI 协作可行性研究

**项目:** GSD & CCB 国际化与多 AI 协作可行性研究  
**创建日期:** 2026-03-28  
**粒度:** fine  
**总阶段数:** 5

## 核心价值

通过国际化和多 AI 协作，让 GSD 和 CCB 能够服务更广泛的用户群体，并显著提升复杂任务的执行质量。

## Phases

- [x] **Phase 1: 代码库分析** - 识别所有需要国际化的文本位置 (completed 2026-03-28)
- [ ] **Phase 2: 架构设计** - 设计共享 i18n 和多 AI 协作架构
- [ ] **Phase 3: 风险评估** - 评估实施风险和工作量
- [ ] **Phase 4: 原型验证** - 验证关键技术点可行性
- [ ] **Phase 5: 文档交付** - 编写完整技术方案和建议

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
- [ ] 02-03-PLAN.md — 设计协议字符串保护机制

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
**Plans**: TBD

### Phase 4: 原型验证
**Goal**: 实现最小原型验证 i18n_core、CCBCLIBackend、协议保护、文件锁等关键技术点
**Depends on**: Phase 2
**Requirements**: PROTO-01, PROTO-02, PROTO-03, PROTO-04, PROTO-05
**Success Criteria** (what must be TRUE):
  1. i18n_core 最小原型已实现并验证（命名空间、t() API 工作正常）
  2. CCBCLIBackend 最小原型已实现并验证（能包装 ask/pend 命令）
  3. 协议字符串保护机制已验证（CI 检查脚本能检测误翻译）
  4. TaskHandle 结构化传递已验证（避免文本解析）
  5. 跨平台文件锁机制已验证（Windows/Linux/macOS 均可工作）
**Plans**: TBD

### Phase 5: 文档交付
**Goal**: 编写完整的技术方案文档、风险评估报告、原型验证报告和实施建议
**Depends on**: Phase 3, Phase 4
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04
**Success Criteria** (what must be TRUE):
  1. 技术方案文档已完成（架构设计、实施路径清晰）
  2. 风险评估报告已完成（工作量、技术风险、缓解策略明确）
  3. 原型验证报告已完成（关键技术点验证结果记录）
  4. 实施建议已完成（阶段划分、优先级、资源需求明确）
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 代码库分析 | 3/3 | Complete   | 2026-03-28 |
| 2. 架构设计 | 2/3 | In Progress|  |
| 3. 风险评估 | 0/0 | Not started | - |
| 4. 原型验证 | 0/0 | Not started | - |
| 5. 文档交付 | 0/0 | Not started | - |

## Coverage

**Total v1 requirements:** 23
**Mapped to phases:** 23
**Unmapped:** 0 ✓

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

---
*Roadmap created: 2026-03-28*
*Last updated: 2026-03-28*
