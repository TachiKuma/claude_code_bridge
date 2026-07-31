---
doc_type: feature-evidence-pack
feature: 2026-07-31-windows-x64-v852-baseline-gate
status: generated
---

# 2026-07-31-windows-x64-v852-baseline-gate evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-checklist.yaml`

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
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-31-windows-x64-v852-baseline-gate\\windows-x64-v852-baseline-gate-checklist.yaml\n\nAll files valid.\n",
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
      "command": "python -m pytest -q test/test_windows_x64_platform_gate.py",
      "exit_code": 0,
      "stdout": ".................                                                        [100%]\n17 passed in 0.18s\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_cli_doctor_windows_x64_platform_gate.py",
      "exit_code": 0,
      "stdout": "...                                                                      [100%]\n3 passed in 0.32s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_doctor_startup_baseline_windows_x64_platform_gate.py",
      "exit_code": 0,
      "stdout": "..                                                                       [100%]\n2 passed in 0.08s\n",
      "stderr": "",
      "id": "CMD-005",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_windows_x64_package_no_change_guard.py",
      "exit_code": 0,
      "stdout": "..                                                                       [100%]\n2 passed in 0.07s\n",
      "stderr": "",
      "id": "CMD-006",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_doctor_runtime_system_windows_x64_platform_gate.py test/test_cli_versioning_local.py",
      "exit_code": 0,
      "stdout": ".......                                                                  [100%]\n7 passed in 0.38s\n",
      "stderr": "",
      "id": "CMD-008",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "npm run pack:check",
      "exit_code": 0,
      "stdout": "\n> @seemseam/ccb@8.2.1 pack:check\n> npm pack --dry-run\n\nseemseam-ccb-8.2.1.tgz\n",
      "stderr": "npm notice\nnpm notice package: @seemseam/ccb@8.2.1\nnpm notice Tarball Contents\nnpm notice 2.5kB LICENSE\nnpm notice 23.2kB README.md\nnpm notice 18.2kB README/ar.md\nnpm notice 16.1kB README/de.md\nnpm notice 16.1kB README/es.md\nnpm notice 16.7kB README/fr.md\nnpm notice 17.4kB README/ja.md\nnpm notice 16.4kB README/ko.md\nnpm notice 16.0kB README/pt.md\nnpm notice 20.7kB README/ru.md\nnpm notice 21.7kB README/zh.md\nnpm notice 7B VERSION\nnpm notice 75B bin/ask.js\nnpm notice 79B bin/autonew.js\nnpm notice 5.1kB bin/ccb-npm-install.js\nnpm notice 641B bin/ccb-npm-runner.js\nnpm notice 75B bin/ccb.js\nnpm notice 84B bin/ctx-transfer.js\nnpm notice 1.5kB package.json\nnpm notice Tarball Details\nnpm notice name: @seemseam/ccb\nnpm notice version: 8.2.1\nnpm notice filename: seemseam-ccb-8.2.1.tgz\nnpm notice package size: 55.7 kB\nnpm notice unpacked size: 192.5 kB\nnpm notice shasum: 2549a7cd87933694711c7a1728767e9b0277673f\nnpm notice integrity: sha512-G4vQrLbKIW8TL[...]BbvCIm6QPgomA==\nnpm notice total files: 19\nnpm notice\n",
      "id": "CMD-007",
      "core": false,
      "failure_handling": "fix-or-block-if-package-touched"
    }
  ],
  "providers": {}
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 21989
Checklist bytes: 7000

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
        ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/dod-results.json",
        ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/evidence-pack-gate.json",
        ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/platform-gate-summary.json",
        ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/scope-gate.json",
        ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-checklist.yaml",
        ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/windows-x64-v852-baseline-gate-evidence-pack.md",
        ".codestable/roadmap/windows-native-herdr-ccb/approval-report.md",
        ".codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml",
        "install.sh",
        "lib/cli/management_runtime/versioning_runtime/local.py",
        "lib/cli/render_runtime/ops_views_doctor.py",
        "lib/cli/services/doctor.py",
        "lib/cli/services/doctor_runtime/system.py",
        "lib/terminal_runtime/windows_x64_platform_gate.py",
        "test/test_cli_doctor_windows_x64_platform_gate.py",
        "test/test_cli_versioning_local.py",
        "test/test_doctor_runtime_system_windows_x64_platform_gate.py",
        "test/test_doctor_startup_baseline_windows_x64_platform_gate.py",
        "test/test_windows_x64_package_no_change_guard.py",
        "test/test_windows_x64_platform_gate.py"
      ],
      "ignored_machine_artifacts": [],
      "allowed_prefixes": [
        ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate",
        ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/",
        ".codestable/roadmap/windows-native-herdr-ccb/",
        "install.sh",
        "lib/cli/management_runtime/versioning_runtime/local.py",
        "lib/terminal_runtime/windows_x64_platform_gate.py",
        "lib/cli/services/doctor.py",
        "lib/cli/services/doctor_runtime/system.py",
        "lib/cli/render_runtime/ops_views_doctor.py",
        "test/test_windows_x64_platform_gate.py",
        "test/test_cli_doctor_windows_x64_platform_gate.py",
        "test/test_cli_versioning_local.py",
        "test/test_doctor_runtime_system_windows_x64_platform_gate.py",
        "test/test_doctor_startup_baseline_windows_x64_platform_gate.py",
        "test/test_windows_x64_package_no_change_guard.py"
      ]
    }
  ],
  "providers": {}
}
```
