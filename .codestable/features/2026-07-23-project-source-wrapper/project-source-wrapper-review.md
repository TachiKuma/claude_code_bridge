---
doc_type: feature-review
feature: 2026-07-23-project-source-wrapper
status: passed
reviewer: subagent
reviewed: 2026-07-23
round: 2
lane_a_state: completed
lane_a_ref: "019f8e55-11a4-7640-b557-fe14d011e400"
lane_a_reason: "二次独立复审完成；首轮 ref 019f8e4f-cd1f-7b30-bc49-8db0df952474 提出 blocking，已修复并 focused closure。"
lane_b_state: unavailable
lane_b_ref: ""
lane_b_reason: "ocr llm test 返回 403 Forbidden。"
---

# project-source-wrapper 代码审查报告

## 1. Scope And Inputs

- Design: none
- Checklist: none
- Evidence pack: none
- Gate results: none
- DoD results: none
- Implementation evidence: `.codestable/features/2026-07-23-project-source-wrapper/project-source-wrapper-ff-note.md`
- Diff basis: 当前仓库新增 ff-note；外部 `CodeStable` 项目新增 `.codestable/tools/ccb-src.ps1` 与 `.codestable/tools/ccb-src.cmd`；本机忽略的 `.ccb/ccb.config` 做旧格式迁移
- Review mode: initial + focused-closure
- Baseline dirty files: 外部 `CodeStable` 项目已有多项无关 dirty 文件，本审查只覆盖新增 `ccb-src` 两个 wrapper

### Independent Review

- Detection: sub-agent 可用；OCR CLI 存在但 `ocr llm test` 返回 403
- 环节 A 独立隔离 Task agent: independent-agent completed
- 环节 B OCR CLI: unavailable
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion, Low->discarded
- Merge policy: 两轮 sub-agent findings 已本地核验；blocking 修复后用 focused closure 关闭
- Gate effect: reviewer=subagent，允许 Quick gate 放行

## 2. Diff Summary

- 新增：`D:/C#Project/GitHub/CodeStable/.codestable/tools/ccb-src.ps1`
- 新增：`D:/C#Project/GitHub/CodeStable/.codestable/tools/ccb-src.cmd`
- 新增：`.codestable/features/2026-07-23-project-source-wrapper/project-source-wrapper-ff-note.md`
- 修改：`D:/C#Project/GitHub/CodeStable/.ccb/ccb.config`（被外部项目 `.gitignore` 忽略）
- 删除：none
- 未跟踪 / staged：上述文件未暂存
- 风险热点：PowerShell 参数转发、环境变量恢复、源码 guard allowlist、全局 `ccb` 隔离

## 3. Adversarial Pass

- 假设的生产 bug：用户传入第二个 `--project` 让源码版 CCB 作用到非绑定项目。
- 主动攻击过的反例：`--project <当前项目>`、`--project=<当前项目>`、正常 `--help`、`.cmd` 失败退出码传播、全局 `ccb` 解析不变、临时环境变量不泄漏。
- 结果：首轮和二轮 sub-agent 都命中 `--project` 覆盖风险；最终已由 wrapper 层拒绝覆盖并验证拒绝信息。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] REV-001 `D:/C#Project/GitHub/CodeStable/.codestable/tools/ccb-src.ps1:63` 后续若要把 wrapper 用于更复杂的自动化，可补 argv 保真 smoke，覆盖嵌入引号、空字符串、JSON 文本。

### learning

- PowerShell 变量名大小写不敏感，避免用 `$Args` 这类 automatic variable 近名作为函数参数。
- Windows PowerShell 5.1 下 `.ps1` 保持 ASCII，并用 `[char]` 拼接中文路径，可避免无 BOM UTF-8 解码问题。

### praise

- `try/finally` 恢复 `CCB_SOURCE_ALLOWED_ROOTS`，并区分原变量存在与否，避免污染调用 shell。
- `.cmd` 用 `setlocal` 包住 `CCB_SRC_EXIT_PROCESS=1`，进程退出控制未泄漏到父 shell。

## 5. Test And QA Focus

- QA 必须重点复核：在 WezTerm 中从 `D:/C#Project/GitHub/CodeStable` 手动运行 `.codestable/tools/ccb-src.ps1 --help` 与 `.codestable/tools/ccb-src.cmd --help`。
- Evidence pack residual risks / gate warnings：OCR 不可用；已用本地行级审查和独立 sub-agent 补足。
- 建议新增或加强的测试：若该 wrapper 未来入库为通用模板，再补 PowerShell 参数转发单测。
- 不能靠 review 完全确认的点：真实 `ccb start/ask` 的长生命周期行为未跑，本轮只验证入口隔离和轻量命令。

## 6. Residual Risk

- 复杂 argv 在 Windows PowerShell 5.1 native command 调用下仍有历史边界；当前需求的普通 WezTerm 命令和常规参数已覆盖，复杂 JSON/空字符串参数留待后续模板化时补测试。

## 7. Verdict

- Status: passed
- Next: Quick feature 可收尾；是否 commit 需用户另行确认。

## 8. Focused Closure

- Closed findings: 首轮 `--project` 覆盖 blocking；二轮 `$Args` automatic variable blocking。
- Attributed delta: `ccb-src.ps1` 的 override 检查改为 `ForwardedArgs`，`.cmd` 改用 `CCB_SRC_EXIT_PROCESS` 环境开关，ff-note 追加验证记录。
- Targeted verification: `ccb-src.ps1 --help` 返回 0；`ccb-src.cmd --help` 返回 0；`ccb-src.cmd --project "<当前项目>" --help` 和 `ccb-src.cmd --project="<当前项目>" --help` 返回非 0 且输出 wrapper 拒绝信息；`ccb-src.cmd config validate --json` 在配置修复前返回 1、配置修复后 `ccb-src.ps1 config validate --json` 返回 `config_status: valid`；全局 `ccb` 和临时环境变量调用前后不变。
- Classification: 只修复 wrapper 参数校验、项目本机配置格式和元数据记录，未改变公开安装、PATH、全局命令或源码 CCB 行为。
