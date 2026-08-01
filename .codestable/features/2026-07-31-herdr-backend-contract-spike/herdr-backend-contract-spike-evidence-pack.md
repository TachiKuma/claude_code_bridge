---
doc_type: feature-evidence-pack
feature: 2026-07-31-herdr-backend-contract-spike
status: generated
---

# 2026-07-31-herdr-backend-contract-spike evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml`

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
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-31-herdr-backend-contract-spike\\herdr-backend-contract-spike-checklist.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-001",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml\"",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\roadmap\\windows-native-herdr-ccb\\windows-native-herdr-ccb-items.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-002",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_herdr_contract_spike_evidence.py",
      "exit_code": 0,
      "stdout": "..........................                                               [100%]\n26 passed in 0.99s\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py test/test_herdr_spike_no_production_route.py",
      "exit_code": 0,
      "stdout": ".........                                                                [100%]\n9 passed in 1.70s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python \".codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-backend-contract-spike/run_spike.py\" --platform-gate-ref \".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/platform-gate-summary.json\" --session ccb-herdr-spike --isolated-server --isolation-created-by-spike --isolated-socket-ref \".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/isolated-herdr.sock\" --out \".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/herdr-contract-spike-evidence.json\"",
      "exit_code": 0,
      "stdout": "wrote .codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/herdr-contract-spike-evidence.json verdict=blocked failure_class=platform-gate-blocked\n",
      "stderr": "",
      "id": "CMD-005",
      "core": true,
      "failure_handling": "blocked-evidence-if-host-missing-or-restart-not-isolated"
    },
    {
      "command": "python -m pytest -q test/test_herdr_contract_spike_evidence.py -k \"minimal_machine_check or truth_table\"",
      "exit_code": 0,
      "stdout": ".........                                                                [100%]\n9 passed, 17 deselected in 0.75s\n",
      "stderr": "",
      "id": "CMD-006",
      "core": true,
      "failure_handling": "fix-or-block"
    }
  ],
  "providers": {}
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 25588
Checklist bytes: 7404

## 5. Residual Risks

- Machine evidence verdict: `blocked`
- Failure class: `platform-gate-blocked`
- Adapter recommendation: `stop`
- Residual risk: `ccb-version-mismatch`
- Blocking gaps: `schema`, `server_status`, `session_attach`, `pane_spawn`, `send_input`, `read_output`, `kill_pane`, `detach_reattach`, `server_restart_restore`

This evidence pack passed implementation gates because the runner produced valid fail-closed blocked evidence. It does not prove Herdr backend capability support.

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
      "changed_files": [
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml",
        ".codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml",
        ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml",
        ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md",
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/dod-results.json",
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/evidence-pack-gate.json",
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/herdr-contract-spike-evidence.json",
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/manual-native-windows-runbook.md",
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/scope-gate.json",
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-acceptance.md",
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-evidence-pack.md",
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-qa.md",
        ".codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-review.md",
        ".codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-backend-contract-spike/run_spike.py",
        "test/test_herdr_contract_spike_evidence.py",
        "test/test_herdr_spike_no_production_route.py",
        "test/test_mux_backend_contract.py"
      ],
      "ignored_machine_artifacts": [],
      "allowed_prefixes": [
        ".codestable/features/2026-07-31-herdr-backend-contract-spike",
        ".codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-backend-contract-spike",
        ".codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml",
        ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml",
        ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md",
        "test/test_herdr_contract_spike_evidence.py",
        "test/test_herdr_spike_no_production_route.py",
        "test/test_mux_backend_contract.py"
      ]
    }
  ],
  "providers": {},
  "feature": "2026-07-31-herdr-backend-contract-spike",
  "inputs": {
    "feature_dir": ".codestable/features/2026-07-31-herdr-backend-contract-spike"
  },
  "input_digests": {}
}
```
