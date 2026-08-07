---
doc_type: refactor-scan
refactor: 2026-08-07-herdr-ui-integration-spike-collector
status: changes-requested
summary: 对 Herdr UI integration spike 采集脚本进行全维度只读审核，结论为建议先改再合
reviewed: 2026-08-07
target: .codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1
target_sha256: B9618470229CD44162104FA35DE10312F2577EAACC7D9B0113B26DCEF44C28D1
review_mode: audit
tags:
  - herdr
  - ccb
  - native-windows
  - collector
  - evidence
  - powershell
---

# Herdr UI Integration Spike 采集脚本审核结论

## 1. 审查范围

本次审查目标是当前工作树中的完整采集脚本，而不是只审新增 diff：

- 目标文件：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1`
- 文件规模：2142 行，约 109 KB
- 工作树状态：目标文件存在未提交修改，当前 diff 为 `99 additions / 15 deletions`
- 目标 SHA-256：`B9618470229CD44162104FA35DE10312F2577EAACC7D9B0113B26DCEF44C28D1`
- 相关上下文：现有 follow-up、旧版 spike review、`.codestable/audits/2026-08-05-herdr-ccb-recent-changes/`

本轮没有修改业务代码，没有创建 Git commit，也没有重新运行会触发 CCB 生命周期、provider 请求或 reload 的完整 spike。

## 2. 验证结果

- PowerShell AST parse：通过，14,646 tokens，0 个语法错误
- `run_spike.ps1 -SelfTest`：通过
- `git diff --check`：通过
- 最近一次已有 evidence：`evidence/run-20260807-164232/`
- 最近一次 evidence 的 `classification` 为 `mounted-with-herdr-panel-observation`
- 最近一次 evidence 的 `command_failure_count` 为 `1`
- 最近一次 evidence 的 `provider-logs` 仅生成 `ccbd.stderr.log` 和 `keeper.stderr.log`，没有按 agent 生成 provider log
- 最近一次 evidence 的 `herdr-config/config-probe.json` 中 `auto_restore_mode` 为 `unknown`

AST、自测和已有 evidence 不能替代隔离环境中的真实 Windows/Herdr 定向验证。

## 3. 总体结论

**建议先改再合。**

当前脚本已经具备较完整的采集维度和 evidence 输出能力，但仍存在两个阻断性问题：

1. cleanup 通过模糊命令行匹配和全局 `herdr.exe` sweep 终止进程，无法证明只清理本次运行拥有的进程。
2. 默认维度包含 `ccb kill`、`ccb restart`、`ccb ask` 和 `ccb reload` 等外部副作用，默认采集不再是 observe-only。

此外，维度之间存在隐式变量依赖，provider/lifecycle/config 证据存在正确性缺口，失败状态和敏感文件处理也不完整。

## 4. Findings

### Blocking

#### B1. cleanup 可能终止无关进程

- 位置：`run_spike.ps1:904`、`:983`、`:1003`、`:1024`、`:1059`
- 事实：cleanup 根据 ProjectRoot/RepoRoot 出现在命令行中进行广域扫描；非 Herdr UI 环境下额外收集所有 `herdr.exe`；随后使用 `taskkill /F /T`。
- 风险：可能终止其他 CCB 项目、IDE、测试进程或用户自己的 Herdr server。当前仅依赖 PID 快照和字符串匹配，未验证启动时间、可执行文件路径、父子关系或本次运行 owner token。`Ccb8Path` 传入 cleanup 但未实际参与归属判定。
- 处理要求：重构 cleanup 为 ownership-based 清理；在无法证明归属时只报告不终止。

#### B2. 默认运行包含破坏性和有成本的 probe

- 位置：默认维度 `run_spike.ps1:26-46`；生命周期 `:1687`；ask smoke `:1863`；reload smoke `:1902`
- 事实：默认执行 kill/restart/ask/reload，会改变 runtime、创建或销毁 pane，并可能产生 provider API 成本。
- 风险：这与“采集脚本”的 observe-only 语义不一致，直接运行脚本可能影响用户现有环境。
- 处理要求：是否从默认集合移除这些维度属于 `cs-feat`/`cs-issue` 决策，不能作为行为等价重构的一部分擅自改变。

### Important

#### I1. provider-logs 使用尚未初始化的 `$pingAllText`

- 位置：`run_spike.ps1:1654-1658`；变量实际在 `:1954-1957` 初始化
- 影响：通常无法解析 agent 名称，不执行 `ccb logs <agent>`。最近一次 evidence 已验证该问题。

#### I2. provider-logs 和 provider-session-files 隐式依赖 startup-state-files

- 位置：`runtimeStateRoot` 在 `run_spike.ps1:1375` 初始化；在 `:1672` 和 `:1846` 使用
- 影响：单独运行相关维度时会静默跳过 runtime 证据，但输出目录仍然存在，形成假完整证据。

#### I3. 生命周期 snapshot 使用错误的 Herdr session

- 位置：实际 CCB session 在 `run_spike.ps1:1319-1334` 提取；kill/restart snapshot 在 `:1711-1717`、`:1763-1769` 仍使用 `$effectiveHerdrSession`
- 影响：当 CCB namespace session 与 wrapper session 不一致时，生命周期 evidence 可能来自错误 session。

#### I4. Herdr config probe 匹配旧字段

- 位置：`run_spike.ps1:1816-1825`
- 事实：只匹配 `auto_restore`，没有按项目 supportability 契约解析 `herdr_auto_restore_mode` 或当前 Herdr 配置字段。
- 影响：当前 evidence 为 `unknown`，无法支撑“Herdr auto restore disabled”的 gate。

#### I5. 采集失败被吞掉且不进入统一失败统计

- 位置：`run_spike.ps1:1251-1255`、`:1554-1555`、`:1678`、`:1801`、`:1810`、`:1842`、`:1853`
- 影响：维度可能报告已执行，但实际 evidence 缺失；`command_failure_count` 不能代表完整失败。

#### I6. partial classification 覆盖具体失败原因

- 位置：`run_spike.ps1:1997-2019`
- 影响：`partial-dimension-failed` 会隐藏未挂载、session 错误、pane 缺失或 provider 失败等根因。

#### I7. 结构化 evidence 校验过弱

- 位置：`run_spike.ps1:198-265`、`:1959-1990`
- 影响：snapshot 只验证 JSON 和 snapshot 对象；ping 依赖文本正则；layout 未验证 agent identity、provider、project id、session、backend 归属，存在假阳性。

#### I8. runtime/config/session 文件原样复制，未统一脱敏

- 位置：`run_spike.ps1:727-780`、`:1799-1810`、`:1837-1853`
- 影响：`Redact-Text` 不覆盖这些文件，产物可能包含 prompt、provider session、内部 payload 或认证信息。

#### I9. timeout 只终止直接进程

- 位置：`run_spike.ps1:486-489`
- 影响：子进程可能残留，后续依赖高风险广域 cleanup 扫尾。

#### I10. detached launch 的 `running` 被当作成功

- 位置：`run_spike.ps1:553-594`
- 影响：launch probe 到期只能证明进程仍存活，不能证明 bootstrap/CCB 启动成功；`exit_code=0` 会造成状态弱化。

#### I11. ask smoke 没有验证 provider 响应语义

- 位置：`run_spike.ps1:1883-1897`
- 影响：只检查进程退出码和后续 ping，没有验证目标 provider 实际消费请求并返回预期响应。

### Nit

#### N1. evidence run id 只有秒级

- 位置：`run_spike.ps1:1110`
- 影响：同一秒并发运行可能写入同一 evidence 目录。

#### N2. 路径解析和复用边界硬编码

- 位置：默认 `RepoRoot` 为 `run_spike.ps1:4`；Herdr 默认路径为 `:330`；repo root 解析固定向上五层为 `:280-300`
- 影响：脚本难以迁移到其他用户、机器和安装布局。

#### N3. 共享逻辑重复

- 位置：`run_spike.ps1:119-152` 与 `ccb8.ps1:591-623` 重复 Windows argv quoting；`run_spike.ps1:637` 另有局部 redaction 实现
- 影响：修复和行为验证需要维护多个实现。

## 5. 已核实的旧问题状态

- 旧审计中 pane capture session 错误当前已有 `$captureSession` 选择逻辑，未重复列为当前 finding。
- 旧审计中 runtime root 重复追加 project id 的问题当前已改为直接使用 `$runtimeStateRoot\ccbd`，未重复列为当前 finding。

## 6. 非自动动作

- 不自动修改默认 destructive probe 集合。
- 不自动改变 summary schema、classification 字符串或 evidence 路径契约。
- 不自动修改现有 v1 roadmap、audit 或 follow-up 文档。
- 不执行 Git commit、push、reset 或回滚。

## 7. 后续归属

- 本审核结论归档于本 refactor 单元的 `*-scan.md`。
- 行为等价重构方案见同目录的 `*-refactor-design.md`。
- destructive probe 默认策略若需改变，另行进入 `cs-feat` 或 `cs-issue`。
- 当前没有足够证据新建或更新 lesson；不执行 `cs-keep`。

