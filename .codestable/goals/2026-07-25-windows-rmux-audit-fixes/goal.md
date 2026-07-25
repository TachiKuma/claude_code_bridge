---
doc_type: goal
goal: windows-rmux-audit-fixes
status: active
---

# Windows Rmux 审计修复 Goal

## Objective

根据 Windows Rmux Native Backend 审计报告修复 4 条发现问题，补充回归测试并完成功能验收。

## Starting Point

审计报告位于 `.codestable/audits/2026-07-25-windows-rmux-native-backend/index.md`，当前包含 4 条 open finding：

- `finding-01.md`：Windows additive patch 忽略 rmux respawn replacement pane id。
- `finding-02.md`：ccbd 客户端响应读取缺少最大字节上限。
- `finding-03.md`：terminal API 的全局 backend cache 实际无法命中。
- `finding-04.md`：PowerShell export 转译用裸分号切分，边界条件会破坏 provider 命令。

## Acceptance Criteria

- `finding-01`：Windows additive patch 的 rmux respawn replacement pane id 被正确传播，并有回归测试覆盖。
- `finding-02`：ccbd 客户端响应读取存在最大字节上限，并有回归测试覆盖。
- `finding-03`：terminal API backend cache 能跨 `get_backend()` 调用命中，或移除误导缓存状态，并有回归测试覆盖。
- `finding-04`：PowerShell export/unset 转译不再按裸分号切坏 quoted semicolon，并有回归测试覆盖。
- 相关 pytest 子集通过。
- `functional-acceptance.md` 记录可见 Task agent 功能验收 `pass`。

## Non-Goals

- 不处理 `arch-drift` 审计维度。
- 不发布包、不执行 `git commit` / `git push`。
- 不重构与 4 条 finding 无关的 Windows Rmux 模块。

## Decisions And Assumptions

- 用户已明确要求根据审计报告修复发现的问题；无需再拆分为独立 issue/refactor 流。
- 采用最小可验证修复：优先修改被审计证据指向的函数，并补贴近回归测试。
- 当前工作区已有大量无关改动；本 goal 只改与 4 条 finding 和 goal 产物直接相关的文件。

## Current State

Goal 已创建，尚未开始实现。

## Next Action

阅读相关实现和现有测试，按 finding 顺序完成最小修复与回归测试。
