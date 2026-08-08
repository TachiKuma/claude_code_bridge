---
status: observed
scope: Native Windows / Herdr / provider-session 续用诊断
date: 2026-08-08
---
规则：当 `.\\ccb8.cmd` 在 Native Windows + Herdr 场景下启动后，`startup-report.json` / `agent-*-runtime.json` 显示 `restore_requested=true` 且 `binding_source="provider-session"` 时，不能直接把当前 pane 状态解释为“系统配置未被复用”；这通常表示运行时优先续用了既有 provider session，先把旧 session、lease 和 restart 路径隔离干净，再判断配置 materialize 是否生效。
适用 / 不适用：适用于外部项目通过 `ccb8` 启动 Herdr 后的运行态诊断、配置复用排障和 session 恢复路径分析；不适用于已经明确 fresh materialize 且无 session 续用痕迹的场景。
证据：
- [.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260808-120250/ccb-live-diag/startup-report.json](../.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260808-120250/ccb-live-diag/startup-report.json)
- [.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260808-120250/ccb-live-diag/agent-agent_1-runtime.json](../.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260808-120250/ccb-live-diag/agent-agent_1-runtime.json)
- [.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260808-120250/pane-evidence/pane-verification.md](../.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260808-120250/pane-evidence/pane-verification.md)
候选归宿：project-doc
