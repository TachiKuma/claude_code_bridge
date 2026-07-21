---
doc_type: feature-evidence-pack
feature: 2026-07-19-rmux-route-approval
status: generated
---

# 2026-07-19-rmux-route-approval evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-design.md`
- Checklist: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml`

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
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-19-rmux-route-approval\\rmux-route-approval-checklist.yaml\n\nAll files valid.\n",
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
      "command": "manual capability report and artifacts review",
      "exit_code": 0,
      "stdout": "CMD-003 passed; see .codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-cmd003-results.json",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block",
      "evidence": ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-cmd003-results.json"
    }
  ],
  "providers": {},
  "feature": "2026-07-19-rmux-route-approval",
  "inputs": {
    "checklist": ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml"
  },
  "input_digests": {
    "checklist": "d9a76c7bf147860a3a9914d350e41bea37f283cbd045ceb5a77ce67632d1800e"
  }
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 12917
Checklist bytes: 3847

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
      "changed_files": [
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-design.md",
        ".codestable/roadmap/windows-rmux-native-backend/goal-state.yaml",
        ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml",
        ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md",
        ".codestable/features/2026-07-19-rmux-route-approval/approval-report.md",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-acceptance.md",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-cmd003-results.json",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-evidence-pack.md",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-qa.md",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-review.md",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-decision-summary.yaml"
      ],
      "ignored_machine_artifacts": [
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-acceptance-dod-gate-results.json",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-dod-results.json",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-evidence-pack-results.json",
        ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-scope-gate-results.json"
      ],
      "allowed_prefixes": [
        ".codestable/features/2026-07-19-rmux-route-approval",
        ".codestable/roadmap/windows-rmux-native-backend"
      ]
    }
  ],
  "providers": {},
  "feature": "2026-07-19-rmux-route-approval",
  "inputs": {
    "feature_dir": ".codestable/features/2026-07-19-rmux-route-approval"
  },
  "input_digests": {}
}
```
