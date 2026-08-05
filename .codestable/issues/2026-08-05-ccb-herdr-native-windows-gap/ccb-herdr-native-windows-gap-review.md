---
doc_type: issue-review
issue: 2026-08-05-ccb-herdr-native-windows-gap
status: passed
reviewer: subagent+ocr
reviewed: 2026-08-05
round: 1
closed: 2026-08-05
residual_issue: 2026-08-05-herdr-residual-gaps
lane_a_state: completed
lane_a_ref: "native-agent (sonnet)"
lane_b_state: completed
lane_b_ref: "ocr"
---

# CCB Native Windows Herdr 集成 gap 代码审查报告

## 1. Scope And Inputs

- Report: `.codestable/issues/2026-08-05-ccb-herdr-native-windows-gap/ccb-herdr-native-windows-gap-report.md`
- Analysis: `.codestable/issues/2026-08-05-ccb-herdr-native-windows-gap/ccb-herdr-native-windows-gap-analysis.md`
- Fix note: `.codestable/issues/2026-08-05-ccb-herdr-native-windows-gap/ccb-herdr-native-windows-gap-fix-note.md`
- Implementation evidence: 当前工作区 diff
- Diff basis: `git diff`
- Review mode: focused-closure

### Independent Review

- Detection: OCR CLI 可用，独立 Task agent 可用
- 环节 A 独立隔离 Task agent (sonnet): completed
- 环节 B OCR: completed
- Merge policy: 已逐条本地核验并合并
- Gate effect: none

## 2. Diff Summary

- 修改：`lib/terminal_runtime/herdr_backend_runtime/cli.py`（3 处 `--session` 参数顺序 + 1 处 redaction 逻辑）
- 修改：`lib/terminal_runtime/api.py`（新增 `_deduce_herdr_verdict()`）
- 修改：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1`（新增 3 个采集维度，约 170 行）
- 修改：`test/test_herdr_backend_client.py`（约 15 处断言更新，适配新参数位置）
- 风险热点：`--session` 参数顺序与 Herdr 0.7.5 CLI 解析兼容性；capability evidence verdict auto-derive 范围；spike 脚本 pane capture 文件覆盖

## 3. Adversarial Pass

- 假设的生产 bug：`_redacted_argv` 错将 session 名而非秘密文本脱敏；`_deduce_herdr_verdict` 仅匹配 `continue-with-gaps` + `windows-beta-gap` 一种组合；spike 脚本 flat name 导致文件覆盖
- 主动攻击过的反例：send_text secret 位置偏移、verdict 缺失 + 不同 failure_class 组合、同文件名覆盖
- 结果：OCR 和 Agent 各发现 3 条，本地核验后确认为 2 条 important + 3 条 nit/suggestion + 3 条 residual-risk

## 4. Findings

### blocking

none

### important

**I1. `_redacted_argv` 测试断言过弱（native-agent）**

- 文件: `test/test_herdr_backend_client.py:3778-3780`
- 当前测试只验证 `len(redacted) >= 1`，不验证被脱敏的确实是文本参数（第 3 个参数）而非 session 名（第 5 个参数）
- 修复边界: 增加 `assert secret not in " ".join(argv)` 和 `assert "ccb-demo" in argv` 验证 session 名未被误脱敏

**I2. `_deduce_herdr_verdict` 仅覆盖精确匹配的一种组合（native-agent）**

- 文件: `lib/terminal_runtime/api.py:324-330`
- 仅处理 `continue-with-gaps` + `windows-beta-gap`，不处理 `continue` + `none/failure_class=""` 等其他合法组合
- 修复边界: 将条件放宽为 `adapter_recommendation in {"continue", "continue-with-gaps"} and failure_class in {"", "none", "windows-beta-gap"}`

### nit

**N1. `Get-HerdrArgs` 函数已无调用点但未移除（本地核验确认）**

- 文件: `run_spike.ps1:518-524`
- grep 确认：`Get-HerdrArgs` 仅定义未调用。继续保留有被误用风险（旧参数顺序）
- 修复边界: 移除该函数或添加废弃注释

**N2. `_redacted_argv` else 分支回退语义与当前参数顺序不匹配（native-agent + 本地核验确认）**

- 文件: `lib/terminal_runtime/herdr_backend_runtime/cli.py:1376-1378`
- `redacted[-1] = "<redacted>"` 在新参数顺序下会脱敏 `--session` 的值而非文本
- 修复边界: 改为轮询 args 中非 flag 的最后一个参数

**N3. spike 脚本 pane capture `tail` 标签名误导（OCR + 本地核验部分采纳）**

- 文件: `run_spike.ps1:772`
- 字段名为 `tail` 但实际取的是前 80 字符（`Substring(0, ...)` 而非从末尾取）
- 修复边界: 改为 `head=` 或改为 `Substring(Math.Max(0, length - 80))` 真正取末尾

### suggestion

**S1. 新增 `_server_status_running` 命令格式直接断言测试（native-agent）**

- `_server_status_running` (`cli.py:1141`) 绕过 `_command` 层直接调 `_run_fn`，当前无测试直接验证其生成的完整命令格式

**S2. 新增 capability evidence verdict auto-derive 端到端测试（native-agent）**

- 用 fixture JSON（缺失 `verdict`）验证 `_herdr_capability_gate` 最终返回非 blocked

**S3. spike self-test 扩展 `Add-HerdrSessionArgs` 多参数变体验证（native-agent）**

- 当前仅测 `status server --json`，可增加 `pane read X --lines 3 --format text`

### learning

**L1. `--session` 参数顺序是"风险集中型改动"（代码层 4 处必须全部一致）**

- `_command()` / `_start_server()` / `_server_status_running()` / `_redacted_argv()` 4 个位置全部依赖相同的 `--session` 位置约定

**L2. `_redacted_argv` 新实现比旧实现更精确**

- 旧版 `redacted[-1]` 依赖文本恰好是最后一个参数；新版通过 `--session` 锚点定位，语义更准确

### praise

**P1. 4 处代码改动与 spike 脚本已验证的 `--session` 放置约定完全一致**

- `cli.py` 3 处参数顺序 + `_redacted_argv` 的 redaction anchor 全部与 `Add-HerdrSessionArgs` 约定匹配

**P2. spike 脚本新采集维度均有 try/catch 保护**

- 所有 3 个新维度的采集路径都有异常保护，不会因某维度失败而阻断脚本其他部分

### residual-risk

**R1. `herdr server --session X` 未在真实 Herdr 0.7.5 中直接验证（native-agent）**

- spike 脚本验证过 `status server --json --session X` 和 `api snapshot --session X`，但从未验证过 `server --session X`。若 Herdr `server` 子命令的参数解析规则不同，后台服务可能启动失败

**R2. capability evidence JSON 的 `windows_beta_gaps` 非空与 `failure_class="windows-beta-gap"` 的语义矛盾无防护（native-agent）**

- `_deduce_herdr_verdict` 设置 `verdict="partial"` 后，`herdr_capability_report_supported()` 中 `not windows_beta_gaps` 仍可能 block。两者在当前 evidence JSON 中一致（`windows_beta_gaps: []`），但无代码级防护

**R3. spike 脚本 `Invoke-DetachedCommand` 的 stdout buffer 饱和理论风险（native-agent）**

- `ReadToEndAsync()` 仅在进程退出后 wait 获取结果；若 daemon 启动期产生大量输出，存在子进程写阻塞风险。当前 CCB daemon 不会产生大量 stdout，且仅影响采集

## 5. Test And QA Focus

- QA 必须重点复核：真实 Herdr 0.7.5 UI 环境中运行 `run_spike.ps1`，确认所有 Herdr CLI 命令（`status server`、`workspace create`、`pane split/run/read/close`）的 `--session` 参数顺序正确
- 建议新增或加强的测试：已在上方 S1/S2/S3 列出
- 不能靠 review 完全确认的点：Herder CLI 不同子命令的 `--session` 解析规则是否完全统一（code review 只能分析代码约定，不能验证 Herdr 程序的真实行为）

## 6. Residual Risk

- 当前依赖一次真实 Herdr 0.7.5 环境下重跑 spike 来消除 R1（`server --session` 参数格式）；本 review 中的 R1/R2/R3 均为已知未消除风险

## 7. Verdict

- Status: passed
- Next: 按 issue 收尾（沉淀 + attention note + commit）

## 8. Focused Closure

- Closed findings: 无（本轮为首轮审查）
- Attributed delta: 见上方 Diff Summary
- Targeted verification:
  - `python -m pytest test/test_herdr_backend_client.py -q` → `169 passed`
  - `python -m pytest test/test_ccbd_bootstrap_probe.py test/test_ccbd_windows_tcp_loopback_transport.py -q` → `26 passed, 1 skipped`
  - `python -m pytest test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py -q` → `43 passed`
  - `python -m pytest test/test_v2_project_namespace_backend.py -q` → `23 passed`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File "run_spike.ps1" -SelfTest` → `passed`
  - `ocr review --audience agent` → `3 finding(s)`（全部核验后驳回为 blocking）
- Classification: 逻辑修复（参数顺序）+ 容错增强（verdict auto-derive）+ 测试适配（断言更新）+ 采集扩展（spike 脚本）；未改变公开协议、安全边界、并发或架构
