---
doc_type: feature-evidence-pack
feature: 2026-07-06-rmux-capability-gate
status: generated
---

# 2026-07-06-rmux-capability-gate evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-design.md`
- Checklist: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml`

## 2. DoD Results

```json
{
  "gate_id": "dod-runner",
  "stage": "implementation.before_review",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-06-rmux-capability-gate\\rmux-capability-gate-checklist.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-001",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_rmux_capability_probe.py",
      "exit_code": 0,
      "stdout": "..........                                                               [100%]\n10 passed in 1.65s\n",
      "stderr": "",
      "id": "CMD-002",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python \"scripts/probe_rmux_capability.py\" --work-root \".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate\"",
      "exit_code": 0,
      "stdout": "{\"ok\": true, \"report\": \"E:\\\\GitHub\\u5f00\\u6e90\\u9879\\u76ee\\\\TachiKuma\\\\claude_code_bridge\\\\.codestable\\\\roadmap\\\\windows-rmux-native-backend\\\\drafts\\\\rmux-capability-gate\\\\run-20260720T064214Z-14748\\\\capability-report.json\", \"probe_status\": \"completed\", \"reason\": null, \"blocking_gaps\": 5}\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_codex_pane_status_probe.py",
      "exit_code": 0,
      "stdout": ".....................................                                    [100%]\n37 passed in 1.37s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": false,
      "failure_handling": "fix-or-block"
    }
  ],
  "providers": {},
  "feature": "2026-07-06-rmux-capability-gate",
  "inputs": {
    "checklist": ".codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml"
  },
  "input_digests": {
    "checklist": "c1b785e5c0ec01f7c39d21a89cbe32bd739ee480e8aa003ae37773baee6cf220"
  }
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 24127
Checklist bytes: 6213

## 5. Residual Risks

- none

## 6. Provider Signals

```json
{
  "archguard": {
    "status": "unavailable",
    "reason": "archguard binary not found on PATH",
    "warnings": []
  },
  "meta_cc": {
    "status": "unavailable",
    "reason": "meta-cc summary not found; realtime session collection is out of scope",
    "warnings": []
  }
}
```

## 7. Gate Results

```json
{
  "gate_id": "scope-gate",
  "stage": "implementation.before_review",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "changed_files": [
        ".codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-review.md",
        ".codestable/roadmap/windows-rmux-native-backend/goal-state.yaml",
        "scripts/probe_rmux_capability.py",
        "test/test_rmux_capability_probe.py",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/cleanup/kill-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/attach-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/bind-key.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/capture-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/delete-buffer.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/display-message.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/has-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/kill-server.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/kill-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/list-clients.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/list-panes.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/list-windows.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/load-buffer.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/move-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/new-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/new-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/paste-buffer.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/pipe-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/refresh-client.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/rename-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/resize-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/respawn-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/select-layout.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/select-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/send-keys.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/set-hook.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/set-option.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/set-window-option.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/split-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/start-server.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/commands/swap-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/preflight/daemon-pre-state.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/attach_reattach.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/buffer_paste.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/capture_format_fidelity_for_provider_completion.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/capture_last_n_lines.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/ctrl_c_ctrl_d.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/daemon_crash_cleanup_evidence.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/kill_session_cleanup.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/layout_reflow.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/namespace_isolation.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/pane_death.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/pane_id_stability.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/provider_process_distinction_workaround_evidence.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/session_survival.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/user_options_title.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/artifacts/semantics/window_policy.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/capability-report.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063847Z-15112/work/buffer.txt",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/cleanup/kill-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/attach-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/bind-key.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/capture-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/delete-buffer.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/display-message.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/has-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/kill-server.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/kill-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/list-clients.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/list-panes.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/list-windows.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/load-buffer.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/move-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/new-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/new-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/paste-buffer.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/pipe-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/refresh-client.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/rename-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/resize-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/respawn-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/select-layout.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/select-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/send-keys.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/set-hook.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/set-option.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/set-window-option.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/split-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/start-server.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/commands/swap-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/preflight/daemon-pre-state.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/attach_reattach.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/buffer_paste.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/capture_format_fidelity_for_provider_completion.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/capture_last_n_lines.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/ctrl_c_ctrl_d.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/daemon_crash_cleanup_evidence.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/kill_session_cleanup.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/layout_reflow.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/namespace_isolation.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/pane_death.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/pane_id_stability.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/provider_process_distinction_workaround_evidence.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/session_survival.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/user_options_title.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/artifacts/semantics/window_policy.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/capability-report.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T063953Z-13452/work/buffer.txt",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/cleanup/kill-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/attach-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/bind-key.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/capture-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/delete-buffer.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/display-message.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/has-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/kill-server.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/kill-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/list-clients.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/list-panes.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/list-windows.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/load-buffer.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/move-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/new-session.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/new-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/paste-buffer.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/pipe-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/refresh-client.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/rename-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/resize-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/respawn-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/select-layout.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/select-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/send-keys.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/set-hook.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/set-option.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/set-window-option.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/split-window.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/start-server.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/commands/swap-pane.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/preflight/daemon-pre-state.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/attach_reattach.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/buffer_paste.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/capture_format_fidelity_for_provider_completion.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/capture_last_n_lines.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/ctrl_c_ctrl_d.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/daemon_crash_cleanup_evidence.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/kill_session_cleanup.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/layout_reflow.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/namespace_isolation.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/pane_death.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/pane_id_stability.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/provider_process_distinction_workaround_evidence.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/session_survival.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/user_options_title.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/artifacts/semantics/window_policy.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/capability-report.json",
        ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064054Z-10824/work/buffer.txt"
      ],
      "ignored_machine_artifacts": [],
      "allowed_prefixes": [
        ".codestable/features/2026-07-06-rmux-capability-gate",
        "scripts/probe_rmux_capability.py",
        "test/test_rmux_capability_probe.py",
        ".codestable/roadmap/windows-rmux-native-backend"
      ]
    }
  ],
  "providers": {},
  "feature": "2026-07-06-rmux-capability-gate",
  "inputs": {
    "feature_dir": ".codestable/features/2026-07-06-rmux-capability-gate"
  },
  "input_digests": {}
}
```
