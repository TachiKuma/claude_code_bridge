---
doc_type: goal
goal: ccbd-windows-full-chain-smoke
status: active
---

# ccbd-windows-full-chain-smoke

## Objective

在 native Windows 真机通过可解析 transcript 证明 `ccb -> ccbd -> rmux` 的 start、ping、ask、kill 最小全链路跑通，且不经 probe 旁路。

## Starting Point

`ccbd-windows-full-chain-smoke` feature design、design-review 和 checklist 已存在并批准。当前没有对应 goal 目录，本报告作为持久起点。

前置状态：

- `ccbd-rmux-namespace-lifecycle`：accepted。
- `accelerator-transport-windows-guard`：accepted。
- `ccbd-windows-process-liveness`：accepted。
- `ccbd-windows-tcp-loopback-transport`：acceptance report 为 passed，但 roadmap items.yaml 当前显示 in-progress；本 goal 需要用已有 acceptance 证据修正该恢复漂移。
- `rmux-supervision-recovery`：accepted；不是本 full-chain smoke 的必需前置，但当前已完成。

## Acceptance Criteria

- Transcript parser fail closed，强制 `host_kind=native_windows`、`control_plane=ccbd`、`backend_impl=rmux`、`probe_bypass=false`、`backend_selection_source`、`ccbd_transport=tcp_loopback`、`verdict`、`failure_class`、`ask_case_kind`。
- PowerShell runner 记录 start/ping/ask/kill command records、artifact paths、redaction summary，并在 `finally` 中尝试 kill/cleanup。
- Dependency preflight 覆盖四个前置 item；前置未 ready 时 transcript verdict 为 `blocked` 且 `failure_class=dependency_pending`。
- Native Windows transcript 证明 start/ping/doctor 走 ccbd 控制面、Rmux backend、TCP loopback transport。
- `ccb ask` 至少一个 provider 有可接受 evidence；provider auth/credential/quota/CLI failure 分类为 `provider_failure`，不能算 system pass。
- `ccb kill -f` 后 endpoint/token/Rmux namespace/session/owned process residue 有清理证据或 bounded retained reason。
- Probe/fake backend/WSL/direct rmux negative fixtures 不得 pass；scope guard 禁止 production runtime、packaging/docs、provider parser 越界。
- 独立 Task agent code review passed；独立 Task agent 功能验收 passed；feature review/QA/acceptance、roadmap 和 final iteration 回写完成。

## Non-Goals

- 不实现 Rmux backend、ccbd transport、accelerator guard、process liveness 或 provider parser。
- 不覆盖 supervision recovery、multi-project、多 agent 矩阵、restart replay 或 packaging/docs supported 收口。
- 不发布 npm、不 push/tag/release。
- 不把 WSL、probe、fake backend、direct rmux CLI 作为 full-chain pass。

## Decisions And Assumptions

- 本 feature 是本轮 milestone 最小终点，不替代 `rmux-windows-validation-matrix`。
- 无 secret 的 ask case 可以是仓库认可测试入口下的 `fake_provider`，但必须经过 `ccb -> ccbd -> rmux`，不得 fake backend 或 probe bypass。
- 真实 start/ask/kill 会创建和清理本地 runtime 资源；如果执行会触发破坏性或外部 provider 风险，先按 owner-stop 规则处理。

## Current State

Goal active，尚未开始实现。工作区在创建 goal 前是 clean。

## Next Action

实现 transcript parser、PowerShell runner skeleton、fixtures/scope guard，并先运行非破坏性 DoD；真实 start/ask/kill 前按风险规则确认或记录 owner-stop。
