---
doc_type: goal
goal: windows-job-object-runtime-evidence
status: complete
---

# windows-job-object-runtime-evidence

## Objective

继续 `windows-rmux-native-backend` epic 中的 `windows-job-object-runtime-evidence`，增加 Windows Job Object 进程树 evidence、runtime authority 字段和 kill / recovery 判定输入，并保持现有 tmux / POSIX 路径不漂移。

## Starting Point

`windows-job-object-runtime-evidence` 的 design / checklist / design-review 已批准。当前代码事实是：

- `AgentRuntime` 没有 `process_ref` 持久字段。
- `ProviderRuntimeFacts` 没有 `process_ref`。
- `ProviderHelperManifest` 只保存 `leader_pid` / `pgid`，不能表达 job object / process tree evidence。
- `runtime_pid_cleanup.matching.pid_matches_project()` 的 Windows 分支仍无条件 `return True`。
- `runtime_health()` 先看 pane，再看 runtime pid，尚未把 pane evidence 与 process evidence 分离。

## Acceptance Criteria

- `AgentRuntime` 和 `ProviderRuntimeFacts` 能承载 `process_ref`，旧 runtime 记录缺失 `process_ref` 时仍可加载。
- 新增 `provider_runtime/process_ref.py` 作为 builder、normalizer、destructive cleanup eligibility 的唯一 seam。
- `process_ref` 区分 `windows_job_object`、`process_tree`、`legacy_pid`，且 `evidence_state` 不退化成单一布尔值。
- `runtime_health()` 在 pane success 短路前读取 `process_ref`；`pane_state == alive` 但 process evidence stale / missing / degraded 时不能返回 `healthy`。
- Windows kill / cleanup 不再把任意 pid 当作项目内 evidence；`taskkill /T` 只作为降级 primitive。
- focused pytest、`rg` guard、checklist 与 roadmap/items 回写通过，并经可见 Task agent 功能验收。

## Non-Goals

- 不把 `ccbd` runtime authority 改成 Job Object authority。
- 不持久化 Job Object handle、socket handle 或进程 handle。
- 不实现 Rmux daemon lifecycle、provider session contract 重写或 Windows `process_exists()` pid probe。
- 不改变 `ccb kill` 的用户语义，只补强 evidence 输入。
- 不执行 `git push`、merge、release、deploy 或生产变更。

## Decisions And Assumptions

- `ccbd` 仍是 authority；Job Object、pid tree、pane 只提供 evidence。
- `process_ref.owner_pid` 是 canonical authority 字段；旧 `job_owner_pid` 只能作为 diagnostics / legacy alias。
- Windows Job Object handle 不能持久化，只记录逻辑 job identity、owner pid、runtime generation、runtime root、source 和 observed_at。
- 非 Windows 路径继续保持当前 tmux / POSIX cleanup 语义，`process_ref` 作为兼容 evidence 字段存在。

## Current State

本 goal 从 design-approved feature 恢复。下一步先实现 `process_ref` contract 与最小 runtime/facts/helper wiring，再推进 health 和 kill gating。

## Next Action

实现 `provider_runtime/process_ref.py`，并接入 `AgentRuntime`、`ProviderRuntimeFacts` 与 helper manifest roundtrip。
