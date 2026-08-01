---
doc_type: feature-evidence-pack
feature: 2026-07-20-ccbd-windows-tcp-loopback-transport
status: generated
---

# 2026-07-20-ccbd-windows-tcp-loopback-transport evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml`

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
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-20-ccbd-windows-tcp-loopback-transport\\ccbd-windows-tcp-loopback-transport-checklist.yaml\n\nAll files valid.\n",
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
      "command": "python -m pytest -q test/test_ccbd_windows_tcp_loopback_transport.py",
      "exit_code": 0,
      "stdout": ".......                                                                  [100%]\n7 passed in 0.30s\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_control_plane_transport_fake.py",
      "exit_code": 0,
      "stdout": "sssss......                                                              [100%]\n6 passed, 5 skipped in 0.51s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_v2_start_service.py -k \"ccbd or endpoint or ping or socket\"",
      "exit_code": 0,
      "stdout": "..                                                                       [100%]\n2 passed, 18 deselected in 0.28s\n",
      "stderr": "",
      "id": "CMD-005",
      "core": true,
      "failure_handling": "document-baseline"
    },
    {
      "command": "python -m pytest -q test/test_ccbd_windows_tcp_loopback_import_guard.py",
      "exit_code": 0,
      "stdout": "..                                                                       [100%]\n2 passed in 0.07s\n",
      "stderr": "",
      "id": "CMD-006",
      "core": true,
      "failure_handling": "fix-or-block"
    }
  ],
  "providers": {},
  "feature": "2026-07-20-ccbd-windows-tcp-loopback-transport",
  "inputs": {
    "checklist": ".codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml"
  },
  "input_digests": {
    "checklist": "f39ae64dc7f982bffa7398c69c83406e79070168377d70a85743779bb7d962e0"
  }
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 14910
Checklist bytes: 4986

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
  "stage": "implementation.before_review",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "changed_files": [],
      "ignored_machine_artifacts": [],
      "allowed_prefixes": [
        ".codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport",
        ".codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport",
        "lib/ccbd",
        "test/test_ccbd_windows_tcp_loopback_transport.py",
        "test/test_ccbd_windows_tcp_loopback_import_guard.py",
        ".codestable/roadmap/windows-rmux-native-backend/goal-state.yaml",
        ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"
      ]
    }
  ],
  "providers": {}
}
```
