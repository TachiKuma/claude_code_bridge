---
doc_type: refactor-design
refactor: 2026-08-07-herdr-ui-integration-spike-collector
status: draft
summary: 在保持采集脚本外部行为和 evidence 契约不变的前提下，拆分执行、上下文、维度、解析、分类和 cleanup 责任
source_scan: .codestable/refactors/2026-08-07-herdr-ui-integration-spike-collector/herdr-ui-integration-spike-collector-scan.md
behavior_contract: behavior-equivalent
decision_confirm:
  default_mutating_dimensions: owner-decision-required
  output_schema: preserve
  classification_strings: preserve
tech_validation:
  powershell_ast_parse: passed
  self_test: passed
  git_diff_check: passed
tags:
  - herdr
  - ccb
  - native-windows
  - collector
  - powershell
  - evidence
---

# Herdr UI Integration Spike 采集脚本重构方案

## 1. 目标

在不改变外部可观察行为的前提下，降低 `run_spike.ps1` 的认知复杂度和失败传播范围：

- 保持现有 CLI 参数、维度名称、默认输出目录、summary 字段和 classification 字符串。
- 让每个维度拥有显式输入、依赖、输出和失败状态。
- 让 evidence 结论来自结构化校验，而不是变量时序和文本正则的偶然结果。
- 让 cleanup 只操作本次采集拥有的进程。
- 为后续 Windows/Herdr 定向验证提供可重复的 fixture 和 baseline。

## 2. 行为不变边界

### 必须保持不变

- `OnlyDimension` 和 `SkipDimension` 的参数语义
- 现有维度名称和执行顺序
- `raw-command-refs`、`report.md`、`summary.json` 的主要路径契约
- `classification` 中已有字符串的含义
- CCB 仍是 provider runtime、completion、queue/cancellation 和 recovery authority
- Herdr panel 观察仍只能作为 diagnostics evidence

### 不属于本次纯重构

- 默认禁用 `ccb-lifecycle`、`ccb-ask-smoke`、`ccb-reload-smoke`
- 改变默认 API 请求策略
- 改变 summary schema 的公开字段语义
- 引入新的 Herdr runtime 能力
- 改变 CCB/Herdr 生命周期 ownership

默认 destructive probe 策略必须由 owner 另行确认，并通过 `cs-feat` 或 `cs-issue` 实施。

## 3. 现状分层

当前脚本将以下职责集中在单文件和共享变量中：

1. 参数和路径解析
2. Windows 进程启动、超时、stdout/stderr 采集
3. Herdr/CCB 命令执行
4. runtime/config/session 文件复制
5. snapshot、ping、layout 解析
6. lifecycle、ask、reload 等主动 probe
7. classification 和 summary 写入
8. 全局残留进程 cleanup

主要结构性问题是：维度之间通过 `$commands`、`$pingAllText`、`$runtimeStateRoot`、`$effectiveHerdrSession` 等隐式共享状态通信。

## 4. 目标结构

### 4.1 CollectorContext

在执行任何维度前构造一次上下文对象，至少包含：

- `ProjectRoot`
- `RepoRoot`
- `Ccb8Path`
- `HerdrExe`
- `EffectiveHerdrSession`
- `CcbHerdrSession`
- `RuntimeStateRoot`
- `RuntimeProjectId`
- `OutputRoot`
- `RawDir`
- `RunId`
- `ExpectedAgents`
- redaction policy

`RuntimeStateRoot` 和 session 解析不再依赖某个维度是否启用。

### 4.2 DimensionRegistry

每个维度注册以下元数据：

```text
name
requires
mutates
outputs
runner
failure_policy
```

例如：

```text
provider-logs:
  requires: [ccb-ping]
  mutates: false
  outputs: [provider-logs]

ccb-lifecycle:
  requires: [ccb-start, ccb-ping, ccb-layout]
  mutates: true
  outputs: [lifecycle-evidence]
```

依赖缺失时必须记录 `blocked` 或 `dependency-missing`，不能静默跳过。

### 4.3 CommandExecutor

抽取共享 PowerShell module，集中实现：

- Windows argv quoting
- captured command
- detached command
- stdout/stderr 读取和脱敏
- timeout 和 process tree
- command evidence record

`run_spike.ps1` 和 `ccb8.ps1` 共用 quoting/redaction 实现，避免重复逻辑漂移。

### 4.4 EvidenceCollector

将证据采集分成职责明确的 probe：

- `DiagnosticsProbe`
- `SnapshotAndPaneProbe`
- `RuntimeStateProbe`
- `ProviderProbe`
- `LifecycleProbe`
- `ConfigProbe`
- `CleanupAdapter`

probe 返回结果对象，由 orchestrator 统一写入命令记录和维度记录；probe 不直接修改全局 `$commands`。

## 5. 分阶段实施

### 阶段 0：冻结等价基线

建立 golden fixtures，覆盖：

- full run 的命令顺序和 summary
- `OnlyDimension` / `SkipDimension`
- wrapper session 与 CCB namespace session 不一致
- runtime root relocation
- ping/layout/snapshot 成功、失败和超时
- provider logs、lifecycle、ask、reload 的失败路径
- 当前 classification 字符串

验收：fixture 能复现当前输出契约；未建立基线前不修改生产脚本。

### 阶段 1：抽离执行核心

先只移动纯执行逻辑，不改变调用顺序：

- `Quote-WindowsProcessArgument`
- `Join-WindowsProcessArguments`
- `Redact-Text`
- `Invoke-CapturedCommand`
- `Invoke-DetachedCommand`
- `New-CommandRef`

将 `$commands +=` 改为 `List[object]` 或统一 `Add-CommandRecord`。

额外保障：针对 timeout 子进程、重定向管道和 Windows argv 建立定向 fixture。

### 阶段 2：集中路径和运行上下文

统一：

- 显式参数优先
- 环境变量其次
- `Get-Command` 和脚本相对路径作为 fallback
- run id 改为 GUID 或毫秒级独占目录

路径策略变更会影响 evidence 目录契约，因此必须先增加兼容验证；若必须保留秒级路径格式，则使用独占创建失败重试。

### 阶段 3：接入维度注册表和依赖图

将现有 if-block 转为 registry 驱动的 orchestrator：

1. 解析 enabled dimensions
2. 校验依赖
3. 构造 DimensionContext
4. 执行 runner
5. 记录 success/failed/blocked/skipped
6. 汇总 evidence refs

先保持当前执行顺序，避免改变生命周期时序。

### 阶段 4：结构化解析和安全复制

- ping、layout、snapshot 采用 JSON 优先。
- 增加最小 schema 和 session/project/provider/pane 归属校验。
- config probe 解析 canonical supportability 字段，并保留原始字段名和标准化字段。
- runtime/config/session 文件改为字段级脱敏或 allowlist。
- 复制失败写入 manifest，不再使用空 catch。

额外保障：敏感字段 fixture、JSON schema fixture、损坏 JSON fixture。

### 阶段 5：集中分类和失败投影

新增纯函数分类器，保留现有分类字符串，同时新增内部诊断字段：

- `failed_dimensions`
- `blocked_dimensions`
- `evidence_gaps`
- `blocking_reasons`

`partial-dimension-failed` 只能作为 scope 标记，不能覆盖具体根因。

### 阶段 6：ownership-based cleanup

清理流程改为：

1. 记录本次启动的 PID、启动时间、可执行路径、命令行和 parent PID。
2. 优先 graceful shutdown，并持续读取 stdout/stderr。
3. 只对 owner 证明成立的进程树执行终止。
4. 没有 owner 证明时记录 warning 并跳过。
5. 删除全局 `herdr.exe` sweep。

该阶段属于高风险信任边界变更，需要独立 review 和隔离 Windows 验证。

### 阶段 7：定向回归和真实验证

最小验证集：

- PowerShell AST parse
- `-SelfTest`
- golden fixture 对照
- full/partial dimension matrix
- provider logs 单独运行
- CCB namespace session 不一致
- cleanup ownership fixture
- run id 并发创建
- redaction fixture
- 隔离 Herdr session 定向 smoke

完整 spike 仅在 destructive probe 策略获得 owner 决策后执行。

## 6. 影响面

### 必须修改

- `run_spike.ps1` 的执行核心、上下文、维度编排、解析、分类和 cleanup
- 共享 PowerShell quoting/redaction 所属模块
- 与新执行记录契约直接相关的 fixture/self-test

### 需要验证

- evidence 目录和 summary schema 兼容性
- full run 的命令顺序
- partial run 的分类和 failure count
- CCB namespace session 与 wrapper session 的选择
- Herdr config supportability 字段
- Windows 进程树终止语义

### 仍待调查

- Herdr 当前配置字段的 canonical 名称和版本差异
- `ccb logs <agent>` 的结构化输出格式
- Herdr API snapshot 的稳定 schema
- provider ask smoke 的最小 completion 判据
- 是否需要 Job Object，或可接受 `taskkill /T`

## 7. 风险与取舍

| 风险事实 | 增加的保障 |
|---|---|
| cleanup 可能误杀无关进程 | ownership fixture、进程树验证、独立 review |
| 默认 probe 有外部副作用 | 将 mutating 维度显式建模，默认策略另行审批 |
| 维度变量时序错误 | Context 初始化 + 依赖图 + partial matrix |
| evidence 假阳性 | JSON schema、归属校验、golden fixtures |
| runtime 产物包含敏感信息 | allowlist/字段级脱敏 fixture |
| run id 并发覆盖 | 独占目录创建和并发测试 |

## 8. 验收标准

- full run 的 CLI 参数、维度名称、主要输出路径、summary 字段和 classification 字符串保持兼容。
- 单独运行任意维度不依赖其他维度的局部变量。
- 所有失败和 blocked 维度均进入结构化记录。
- provider logs 能按 agent 采集，runtime logs 缺失时明确报告。
- lifecycle snapshot 使用实际 CCB namespace session。
- layout/snapshot/ping 校验 agent、provider、project、session 和 backend 归属。
- evidence 中的 runtime/config/session 文件经过统一脱敏。
- cleanup 不依据模糊路径终止无关进程。
- 并发运行不会覆盖 evidence 目录。
- destructive probe 默认策略没有在纯重构中被擅自改变。

## 9. 状态与未决

- 当前状态：`draft`
- 审核结论：`changes-requested`
- blocking findings：B1、B2
- important findings：I1-I11
- 尚未开始代码实施
- 尚未创建 checklist，因为 owner 尚未确认 destructive probe 默认策略和 cleanup ownership 契约

## 10. 毕业去向

- 审核事实保留在同目录 `herdr-ui-integration-spike-collector-scan.md`。
- 重构设计保留在本文件，作为后续实现和 review 的输入。
- 可复用经验暂不进入 `.codestable/compound/` 或 lessons，当前已有审计资料足以承载事实。
- destructive probe 默认策略如获得决策，应转入独立 feature/issue 单元，不在本 refactor 单元内隐式改变。
