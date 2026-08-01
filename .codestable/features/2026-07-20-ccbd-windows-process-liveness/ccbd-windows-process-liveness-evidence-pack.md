---
doc_type: feature-evidence-pack
feature: 2026-07-20-ccbd-windows-process-liveness
status: generated
---

# 2026-07-20-ccbd-windows-process-liveness evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml`

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
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-20-ccbd-windows-process-liveness\\ccbd-windows-process-liveness-checklist.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-001",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml\"",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\roadmap\\windows-rmux-native-backend\\windows-rmux-native-backend-items.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-002",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_process_liveness.py test/test_cli_kill_runtime_zombies.py",
      "exit_code": 0,
      "stdout": "......................                                                   [100%]\n22 passed in 0.33s\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_v2_ccbd_mount_ownership.py test/test_cli_daemon_keeper_runtime.py test/test_ccbd_service_graph.py",
      "exit_code": 0,
      "stdout": "........................................ss......                         [100%]\n46 passed, 2 skipped in 1.20s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_v2_kill_service.py test/test_cli_kill_runtime_zombies.py test/test_runtime_accelerator_ownership.py test/test_mobile_host_service.py",
      "exit_code": 0,
      "stdout": "........................................................................ [ 98%]\n.                                                                        [100%]\n73 passed in 2.65s\n",
      "stderr": "",
      "id": "CMD-005",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "rg -n \"from cli\\.kill_runtime\\.processes import is_pid_alive|is_pid_alive\\(\" lib test",
      "exit_code": 0,
      "stdout": "lib\\runtime_accelerator\\ownership.py:11:from cli.kill_runtime.processes import is_pid_alive, terminate_pid_tree\nlib\\runtime_accelerator\\ownership.py:334:    if int(pid) <= 0 or not is_pid_alive(int(pid)):\nlib\\runtime_accelerator\\ownership.py:356:    if not is_pid_alive(owner.pid):\nlib\\provider_core\\runtime_lock.py:19:def _is_pid_alive(pid: int) -> bool:\nlib\\provider_core\\runtime_lock.py:79:                    if not _is_pid_alive(pid):\nlib\\provider_runtime\\helper_cleanup.py:8:from cli.kill_runtime.processes import is_pid_alive as _shared_is_pid_alive\nlib\\provider_runtime\\helper_cleanup.py:91:        if not _is_pid_alive(leader_pid):\nlib\\provider_runtime\\helper_cleanup.py:94:    return not _is_pid_alive(leader_pid)\nlib\\provider_runtime\\helper_cleanup.py:100:    if not _is_pid_alive(pid):\nlib\\provider_runtime\\helper_cleanup.py:113:    return not _is_pid_alive(pid)\nlib\\provider_runtime\\helper_cleanup.py:116:def _is_pid_alive(pid: int) -> bool:\nlib\\provider_runtime\\helper_cleanup.py:117:    return _shared_is_pid_alive(pid)\nlib\\ccbd\\stop_flow_runtime\\pid_cleanup.py:3:from cli.kill_runtime.processes import is_pid_alive, terminate_pid_tree\nlib\\cli\\services\\mobile_host.py:21:from cli.kill_runtime.processes import is_pid_alive, terminate_pid_tree\nlib\\cli\\services\\maintenance.py:22:from cli.kill_runtime.processes import is_pid_alive as _process_pid_alive\nlib\\cli\\kill_runtime\\zombies.py:56:    if is_pid_alive(parent_pid):\nlib\\cli\\kill_runtime\\processes.py:30:def is_pid_alive(pid: int) -> bool:\nlib\\cli\\services\\kill.py:36:from cli.kill_runtime.processes import is_pid_alive, terminate_pid_tree\nlib\\cli\\services\\daemon_runtime\\processes.py:8:from cli.kill_runtime.processes import is_pid_alive, kill_pid\nlib\\cli\\services\\daemon_runtime\\processes.py:86:        if not is_pid_alive(pid):\nlib\\cli\\services\\daemon_runtime\\processes.py:89:    return not is_pid_alive(pid)\nlib\\cli\\services\\daemon_runtime\\keeper.py:23:from cli.kill_runtime.processes import is_pid_alive\nlib\\cli\\services\\daemon_runtime\\facade.py:5:from cli.kill_runtime.processes import is_pid_alive\nlib\\cli\\services\\daemon.py:12:from cli.kill_runtime.processes import is_pid_alive, kill_pid, terminate_pid_tree\ntest\\test_cli_kill_runtime_zombies.py:11:    assert processes.is_pid_alive(123) is False\ntest\\test_cli_kill_runtime_zombies.py:18:    assert processes.is_pid_alive(123) is True\ntest\\test_process_liveness.py:174:    assert kill_processes.is_pid_alive(789) is True\ntest\\test_process_liveness.py:182:    assert runtime_lock._is_pid_alive(321) is False\n",
      "stderr": "",
      "id": "CMD-006",
      "core": true,
      "failure_handling": "inspect-output"
    },
    {
      "command": "rg -n \"os\\.kill\\(pid, 0\\)|os\\.kill\\([^,]+, 0\\)\" lib/ccbd lib/cli/kill_runtime lib/process_liveness.py test/test_process_liveness.py",
      "exit_code": 0,
      "stdout": "lib/process_liveness.py:77:        os.kill(pid, 0)\n",
      "stderr": "",
      "id": "CMD-007",
      "core": true,
      "failure_handling": "inspect-output"
    },
    {
      "command": "git status --porcelain -uall",
      "exit_code": 0,
      "stdout": " M .codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml\n M .codestable/roadmap/windows-rmux-native-backend/goal-state.yaml\n M .codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml\n M .codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md\n M lib/ccbd/system.py\n M lib/cli/kill_runtime/processes.py\n M lib/cli/services/mobile_host.py\n M lib/provider_core/runtime_lock.py\n M lib/provider_core/session_binding_evidence_runtime/fields.py\n M lib/terminal_runtime/tmux.py\n M test/test_cli_kill_runtime_zombies.py\n M test/test_mobile_host_service.py\n M test/test_provider_core_session_binding_fields.py\n M test/test_terminal_runtime_tmux.py\n M test/test_v2_ccbd_mount_ownership.py\n?? .codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-acceptance.md\n?? .codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-evidence-pack.md\n?? .codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-qa.md\n?? .codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-review.md\n?? .codestable/features/2026-07-20-ccbd-windows-process-liveness/evidence-pack-results.json\n?? .codestable/features/2026-07-20-ccbd-windows-process-liveness/scope-gate-results.json\n?? .codestable/features/2026-07-20-ccbd-windows-process-liveness/scope-min.json\n?? lib/process_liveness.py\n?? test/test_process_liveness.py\n",
      "stderr": "",
      "id": "CMD-008",
      "core": true,
      "failure_handling": "inspect-output"
    }
  ],
  "providers": {},
  "feature": "2026-07-20-ccbd-windows-process-liveness",
  "inputs": {
    "checklist": ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml"
  },
  "input_digests": {
    "checklist": "c55c3df97a41d7927ddbb4b06d3db257262212677f695a27766e42127aa1ef88"
  }
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 17189
Checklist bytes: 6803

## 5. Residual Risks

- none

## 6. Provider Signals

```json
{
  "archguard": {
    "status": "skipped",
    "reason": "archguard collection disabled",
    "warnings": []
  },
  "meta_cc": {
    "status": "skipped",
    "reason": "meta-cc collection disabled",
    "warnings": []
  }
}
```

## 7. Gate Results

```json
{
  "gate_id": "scope-gate",
  "stage": "acceptance",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "changed_files": [
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-checklist.yaml",
        ".codestable/roadmap/windows-rmux-native-backend/goal-state.yaml",
        ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml",
        ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md",
        "lib/ccbd/system.py",
        "lib/cli/kill_runtime/processes.py",
        "lib/cli/services/mobile_host.py",
        "lib/provider_core/runtime_lock.py",
        "lib/provider_core/session_binding_evidence_runtime/fields.py",
        "lib/terminal_runtime/tmux.py",
        "test/test_cli_kill_runtime_zombies.py",
        "test/test_mobile_host_service.py",
        "test/test_provider_core_session_binding_fields.py",
        "test/test_terminal_runtime_tmux.py",
        "test/test_v2_ccbd_mount_ownership.py",
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-acceptance.md",
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-evidence-pack.md",
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-qa.md",
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-review.md",
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness/dod-results.json",
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness/evidence-pack-results.json",
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness/scope-min.json",
        "lib/process_liveness.py",
        "test/test_process_liveness.py"
      ],
      "ignored_machine_artifacts": [
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness/scope-gate-results.json"
      ],
      "allowed_prefixes": [
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness",
        ".codestable/features/2026-07-20-ccbd-windows-process-liveness",
        ".codestable/roadmap/windows-rmux-native-backend/goal-state.yaml",
        ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml",
        ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md",
        "lib/ccbd",
        "lib/cli/kill_runtime",
        "lib/cli/services/mobile_host.py",
        "lib/provider_core/runtime_lock.py",
        "lib/provider_core/session_binding_evidence_runtime/fields.py",
        "lib/terminal_runtime/tmux.py",
        "lib/process_liveness.py",
        "test"
      ]
    }
  ],
  "providers": {},
  "feature": "2026-07-20-ccbd-windows-process-liveness",
  "inputs": {
    "feature_dir": ".codestable/features/2026-07-20-ccbd-windows-process-liveness"
  },
  "input_digests": {}
}
```
