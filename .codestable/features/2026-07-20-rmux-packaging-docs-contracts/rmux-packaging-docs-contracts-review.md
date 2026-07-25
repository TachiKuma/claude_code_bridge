---
doc_type: feature-review
feature: 2026-07-20-rmux-packaging-docs-contracts
status: passed
reviewer_id: 019f9768-b255-7292-895d-0245bb7d3daf
updated_at: 2026-07-25
---

# rmux-packaging-docs-contracts 代码审查

## Scope

审查范围覆盖本 feature 的实现与文档收口：support projection owner、doctor/diagnostics 输出、`install.ps1` rmux prerequisite 行为、Windows npm no-change rationale、README/docs consistency、release guard、测试与 evidence artifacts。

## 独立审查结论

初轮独立 reviewer `019f975e-d585-7f40-afad-fc8b3261326d` 发现两个问题：

- `doctor_summary()` 使用用户项目根目录读取 projection，安装位置与用户项目位置不一致时会读错。
- `install.ps1` 将 beta support tier 文案硬编码，未消费同一 projection owner。

两项均已修复：

- `lib/cli/services/doctor.py` 优先使用 install root 调用 `rmux_packaging_support_summary()`。
- `install.ps1` 新增 `Get-RmuxPackagingSupportProjection`，从 `lib/terminal_runtime/rmux_packaging_support_projection.json` 读取 support projection。

聚焦 closure reviewer `019f9768-b255-7292-895d-0245bb7d3daf` 返回：

- `verdict: passed`
- original findings: closed
- new findings: none
- spec compliance: pass
- code quality: pass

## Reviewer Evidence

Reviewer 确认：

- projection 当前为 `support_tier=beta`、`install_entry=install_ps1`、`windows_npm_enabled=false`。
- `package.json.os` 未加入 `win32`。
- `install.ps1` 只探测/提示 rmux，不包含 rmux 下载逻辑。
- doctor 渲染包含 support、install、validation、fallback 字段。
- Python owner 负责 live evidence 与 packaged projection fallback；PowerShell 只消费 JSON 并做本机 prerequisite probe。

## Residual Risks

- 工作区存在多个与本 feature 无关或无法语义审查的脏项，其中 `bin/ccb-agent-sidebar.exe` 是二进制变更，不属于本 feature 核心路径。
- bundle 测试验证 raw doctor JSON 的核心 projection 字段；fallback/validation 全字段主要由 render 与 projection 测试覆盖。

## Verdict

`passed`。无 unresolved blocking findings。
