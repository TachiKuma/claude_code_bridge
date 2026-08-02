---
doc_type: feature-implementation
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
status: implemented
implemented: 2026-08-02
---

# ccbd-herdr-namespace-lifecycle 实现记录

## 当前结论

S0-S7 已完成。最新 CMD-013 的 Native Windows x64 transcript 已通过，证明 CCB
control-plane、Herdr project namespace、foreground attach、reload apply、restart deferred
boundary 和 kill 均有可观察证据。

本轮修复了 Herdr namespace ref/session scope、pane topology 映射、reload namespace patch
边界和 provider runtime 延迟语义。Herdr namespace 的 reload 不启动 provider runtime，
而是发布 namespace patch/config graph，并返回明确的
`reason=provider_runtime_deferred_on_herdr` / `runtime_mount_deferred=true` 诊断。

## 主要改动

- `lib/terminal_runtime/herdr_backend.py`
  - pane 查询/描述使用当前项目 Herdr namespace。
  - reload 新建 backend 后可从 `_ccb_project_namespace_ref` 恢复 pane namespace。
  - `set_pane_identity()` 会重建 pane cache。
- `lib/terminal_runtime/herdr_backend_runtime/cli.py`
  - pane metadata 前等待 pane 可见。
  - 非 root pane 不能作为 split parent 时回退同 workspace 的 `ccb_root_pane=1`。
- `lib/ccbd/reload_apply_runtime.py`、`reload_runtime_mount_models.py`
  - Herdr namespace reload 不启动 provider runtime，返回显式 noop/deferred 语义。
  - 允许 namespace patch/config graph 发布，避免 tmux socket 依赖阻塞。
- `lib/ccbd/services/project_namespace_runtime/additive_patch_apply.py`、
  `lib/ccbd/reload_apply_stages.py`、`lib/cli/render_runtime/reload_view.py`
  - 增强 namespace patch 失败的 operation/category/evidence 诊断。
- 新增 Herdr backend、adapter、reload runtime mount、additive patch 回归测试。

## Step 状态

| Step | 状态 | 证据 |
|---|---|---|
| S0-S6 | done | 前置 V2 contract、state projection、helper path、ensure/reflow、foreground seam、kill/restart/reload boundary 与 scope/content guard 已覆盖。 |
| S7 | done | focused regression 与 Native Windows CMD-013 transcript 均通过。 |

## 最新验证证据

- S7 聚焦：`200 passed, 75 deselected`。
- reload 聚焦：`36 passed`。
- Herdr namespace/backend 聚焦：`171 passed, 32 deselected`。
- CMD-013：`evidence/cmd-013-native-windows-herdr-transcript.md`，最终 `Verdict: passed`。
  - Native Windows x64 / Python 64-bit / Herdr version 已记录。
  - namespace durable state 与 project namespace title 对齐。
  - `ccbd ping`、foreground attach、reload apply、kill 均 exit 0。
  - `restart agent1` 返回 exit 1，但输出预期的
    `deferred_to_provider_runtime_on_herdr`，属于该 feature 的显式 deferred boundary。
- YAML 校验、scope/content guard 与 `git diff --check` 已通过。

## 清洁度

- 未修改 provider runtime、recovery owner、Mobile/Config UI、doctor/support、
  package/release/update/installer 或 public validation matrix。
- public payload 只记录 `namespace_restore_token_present`；CMD-013 transcript 不输出 raw
  restore token。
- 本 feature 只完成 implementation gate；后续 review、QA、acceptance 不在本轮范围内。

## 下一步

将实现状态交给既有 feature gate，保持后续 `provider-runtime-on-herdr` 等 roadmap item
不提前启动。后续 review/QA/acceptance 应按项目流程单独执行。
