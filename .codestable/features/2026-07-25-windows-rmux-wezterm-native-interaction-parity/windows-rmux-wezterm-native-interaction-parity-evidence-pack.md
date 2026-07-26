---
doc_type: feature-evidence-pack
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: generated
---

# 2026-07-25-windows-rmux-wezterm-native-interaction-parity evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml`

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
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-25-windows-rmux-wezterm-native-interaction-parity\\windows-rmux-wezterm-native-interaction-parity-checklist.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-001",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_v2_tmux_ui.py",
      "exit_code": 0,
      "stdout": "............ss.                                                          [100%]\n13 passed, 2 skipped in 0.85s\n",
      "stderr": "",
      "id": "CMD-002",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "cargo test --manifest-path \"tools/ccb-agent-sidebar/Cargo.toml\" shifted_q_is_project_kill_across_terminal_key_encodings --quiet",
      "exit_code": 0,
      "stdout": "\nrunning 1 test\n.\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 53 filtered out; finished in 0.00s\n\n\nrunning 0 tests\n\ntest result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s\n\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "cargo test --manifest-path \"tools/ccb-agent-sidebar/Cargo.toml\" --quiet",
      "exit_code": 0,
      "stdout": "\nrunning 54 tests\n......................................................\ntest result: ok. 54 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s\n\n\nrunning 0 tests\n\ntest result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s\n\n\nrunning 0 tests\n\ntest result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s\n\n",
      "stderr": "",
      "id": "CMD-004",
      "core": false,
      "failure_handling": "fix-or-block-if-touched"
    },
    {
      "command": "python -m py_compile \"lib/cli/services/tmux_ui_runtime/service.py\" \"test/test_v2_tmux_ui.py\"",
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "id": "CMD-005",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings",
      "exit_code": 0,
      "stdout": ".                                                                        [100%]\n1 passed, 14 deselected in 0.49s\n",
      "stderr": "",
      "id": "CMD-006",
      "core": true,
      "failure_handling": "attach-transcript-or-block-pass"
    }
  ],
  "providers": {}
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 15458
Checklist bytes: 3812

## 5. Residual Risks

- AC-007 manual WezTerm GUI foreground interaction remains partial: `evidence/manual-wezterm-runbook.md` records that the agent could not directly observe single-click focus, drag selection, right-click behavior, ordinary pane wheel behavior, sidebar settings click, or sidebar `x` KillProject click. Human foreground verification is required before final acceptance can claim full manual GUI pass.
- Ordinary pane wheel fallback now avoids `copy-mode -e`, `send-keys -X scroll-up/down`, and the old no-target `select-pane -M` placeholder. It uses `select-pane -t =` only, so WezTerm-native content scrolling is still not proven in this v1 and remains a design residual for manual QA/acceptance.

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
        ".codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity",
        ".codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity",
        "lib/cli/services/tmux_ui_runtime/service.py",
        "test/test_v2_tmux_ui.py"
      ]
    }
  ],
  "providers": {}
}
```
