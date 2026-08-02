---
doc_type: approval-report
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
status: approved
reason: ScopeBoundaryChange
blocker_signature: missing-windows-ccbd-tcp-loopback-control-plane
updated_at: 2026-08-02
---

# ccbd-herdr-namespace-lifecycle Owner Stop

## Decision Needed

需要 owner 决定是否把旧 `windows-rmux-native-backend` 路线中已验收的
`ccbd-windows-tcp-loopback-transport` / control-plane transport seam 移植或重开到当前
`windows-native-herdr-ccb` roadmap。

Resolution: owner selected **CreateRoadmapItem** on 2026-08-02. A new child feature
`.codestable/features/2026-08-02-ccbd-windows-control-plane-transport` now owns the
control-plane transport seam + Windows TCP loopback/token work before this namespace
feature resumes.

## Why Now

S7 / CMD-013 已在真实 Native Windows x64 上运行：

- Herdr 可执行存在：`C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`
  -> `herdr 0.7.5-preview.2026-07-29-44b3adb12552`。
- transcript 已落盘：
  `evidence/cmd-013-native-windows-herdr-transcript.md`。
- 失败发生在 Herdr namespace 创建之前：`ccbd` 启动时崩溃，
  `ccbd.stderr.log` 记录 `RuntimeError: unix domain sockets are not supported on this platform`。

这证明新阻断不是缺 Herdr，而是当前 Herdr 分支的 `ccbd` control-plane RPC 仍为
AF_UNIX-only。`ccb` public workflow 在 Native Windows 下无法启动到 Herdr lifecycle。

## Scope Boundary

当前 feature 的 approved design 负责 Herdr project namespace lifecycle、foreground attach、
kill/restart/reload，不包含 `ccbd` control-plane transport。直接在本 feature 中实现或移植
Windows TCP loopback 会改变已批准 scope，并引入新的 control-plane capability。

同时，旧 rmux roadmap 已有可复用的 accepted 前置：

- `2026-07-20-ccbd-control-plane-transport-seam`
- `2026-07-20-ccbd-windows-tcp-loopback-transport`
- 关键提交：`83897b79`、`f98432e3`、`a633adf9`

当前分支只保留相关 `.codestable` 文档，生产代码没有
`lib/ccbd/control_plane_transport/`，`socket_server_runtime/lifecycle.py` 仍直接使用
`socket.AF_UNIX`。

## Options

- **ApproveTransportImport**：批准把已验收的 control-plane transport seam 与 Windows TCP
  loopback adapter 移植到当前 Herdr roadmap，作为 CMD-013 前置修复；完成后重跑 focused
  transport tests，再重跑 CMD-013。
- **CreateRoadmapItem**：新增独立 child feature，放在 `ccbd-herdr-namespace-lifecycle` 之前，
  专门恢复 Windows ccbd control-plane transport，并重新 review/QA/acceptance。
- **KeepHandoff**：暂不继续，保持 roadmap handoff。

## Recommendation

选择 **ApproveTransportImport**。这是已验收能力在当前 `v8.5.2` Herdr 分支的缺失前置，
不是新的产品方向；移植后才能用真实 public workflow 验证 Herdr namespace lifecycle。

## After Owner Decision

- 若批准：按旧 accepted feature 的实现边界移植 control-plane seam/TCP adapter，保留 Unix
  AF_UNIX 行为；运行 focused transport tests 与 CMD-013。
- 若新增 roadmap item：先更新 roadmap/items/goal-state，再按 child feature loop 实现。**已选择并落盘**。
- 若保持 handoff：不进入 code review、QA 或 acceptance。
