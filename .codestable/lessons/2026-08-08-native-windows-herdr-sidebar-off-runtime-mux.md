---
status: observed
scope: Native Windows / Herdr / 外部项目 CCB 启动
date: 2026-08-08
---
规则：外部项目通过 `.\ccb8.cmd` 走 Herdr 时，若不希望出现 CCB 自己的 sidebar 占位 pane，`ccb.config` 应显式写 `[runtime.mux] backend = "herdr"`，并在 `[ui.sidebar]` 下写 `mode = "off"`。这样禁用的是 CCB 侧 sidebar materialization，不是 Herdr 自己的 UI。
补充：如果 `ccb8 ping ccbd` 看到 `binding_source = "provider-session"`、`restore_mode = "provider_resume"`，同时 `ccbd.stderr.log` 里还在报 `lease.json` 原子写失败，当前 pane 很可能是在续用旧 provider session，而不是重新 materialize 新配置；这时先修复 lease / restart 路径，再判断“系统配置没复用”。
证据：
- [docs/ccb-config-layout-contract.md](../docs/ccb-config-layout-contract.md)
- [docs/native-windows-herdr-managed-launch.md](../docs/native-windows-herdr-managed-launch.md)
- [.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260807-164232/ccb-live-diag/agent-agent_1-runtime.json](../.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260807-164232/ccb-live-diag/agent-agent_1-runtime.json)
- [.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260807-164232/provider-logs/ccbd.stderr.log](../.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260807-164232/provider-logs/ccbd.stderr.log)
候选归宿：project-doc
