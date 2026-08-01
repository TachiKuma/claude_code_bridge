---
doc_type: feature-review
feature: windows-job-object-runtime-evidence
status: passed
reviewer_id: "019f8a72-5013-7fb3-abf6-40dc45c61f6b"
updated_at: "2026-07-22"
---

# windows-job-object-runtime-evidence Review

## Scope

审查 `windows-job-object-runtime-evidence` 的 implementation diff、`process_ref` 契约、runtime/facts/helper roundtrip、health 顺序、Windows kill / cleanup gating、project view diagnostics，以及 checklist / roadmap 状态写回。

## Reviewer

- Review Task agent：`019f8a72-5013-7fb3-abf6-40dc45c61f6b`
- 运行方式：可见只读独立 review；首轮 `changes_requested`，focused closure 后 `verdict: pass`。
- 生命周期：review 结果已消费，agent 已关闭。

## Findings

首轮 review 发现 4 项 blocking：

- runtime record 原样持久化未规范化 `process_ref`，可能写入 handle 字段。
- helper manifest 复用 runtime `process_ref`，runtime pid 与 bridge leader pid 不一致时会导致 Windows stale helper 无法清理。
- destructive cleanup eligibility 未强制 runtime_generation。
- Windows ccbd lease / keeper authority pid 缺少无需 `/proc` / `ps` 的明确 authority-record 放行路径。

## Closure

Focused closure verdict: `pass`。

closure reviewer 确认：

- `AgentRuntime` 序列化与 store load 均通过 `process_ref` normalizer，非 canonical 字段不持久化。
- helper manifest 改为 helper-specific process evidence，只有 existing runtime process_ref 对 `runtime + leader_pid` 可清理时才复用。
- cleanup eligibility 要求正的 `runtime_generation`，并在传入 runtime 时要求 generation 匹配。
- Windows `pid_matches_project()` 增加窄 authority-record matcher；普通 pid file 不放行。
- 未发现新增或未关闭 blocking。

## Residual Risks

- 本 feature 没有真实 Windows Job Object attach / handle lifecycle，当前实现是 evidence contract 与 gating seam；真实 job object 行为仍需后续真机 smoke / supervision feature 验证。
