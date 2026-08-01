---
doc_type: feature-evidence-pack
feature: 2026-07-19-backend-resolver-opt-in-contract
status: generated
---

# 2026-07-19-backend-resolver-opt-in-contract evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-design.md`
- Checklist: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-checklist.yaml`

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
      "command": "python \"C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/validate-yaml.py\" --file \".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-19-backend-resolver-opt-in-contract\\backend-resolver-opt-in-contract-checklist.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-001",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python \"C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/validate-yaml.py\" --file \".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml\"",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\roadmap\\windows-rmux-native-backend\\windows-rmux-native-backend-items.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-002",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_terminal_runtime_backend_selection.py",
      "exit_code": 0,
      "stdout": "............................                                             [100%]\n28 passed in 1.35s\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_v2_config_loader.py test/test_v3_config_loader.py test/test_v2_start_foreground.py test/test_backend_selection_diagnostics.py -k \"runtime_mux or foreground or backend_selection\"",
      "exit_code": 0,
      "stdout": ".......................                                                  [100%]\n23 passed, 168 deselected in 2.91s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": true,
      "failure_handling": "fix-or-block"
    }
  ],
  "providers": {},
  "feature": "2026-07-19-backend-resolver-opt-in-contract",
  "inputs": {
    "checklist": ".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-checklist.yaml"
  },
  "input_digests": {
    "checklist": "8e2acb10259d3ac82562863a458b2c1209dd426fa03e12047e34f68da9bd623d"
  }
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 13820
Checklist bytes: 4774

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
        ".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-checklist.yaml",
        ".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-design.md",
        ".codestable/reference/agent-conventions.md",
        ".codestable/roadmap/windows-rmux-native-backend/goal-state.yaml",
        "lib/agents/config_loader_runtime/common.py",
        "lib/agents/config_loader_runtime/dynamic_agent_overlays.py",
        "lib/agents/config_loader_runtime/io_runtime/documents.py",
        "lib/agents/config_loader_runtime/loop_overlays.py",
        "lib/agents/config_loader_runtime/parsing_runtime/validation.py",
        "lib/agents/config_loader_runtime/parsing_runtime/workflow_v3.py",
        "lib/agents/models.py",
        "lib/agents/models_runtime/__init__.py",
        "lib/agents/models_runtime/config.py",
        "lib/agents/models_runtime/config_runtime/__init__.py",
        "lib/agents/models_runtime/config_runtime/project.py",
        "lib/ccbd/app_runtime/bootstrap.py",
        "lib/ccbd/app_runtime/handlers.py",
        "lib/ccbd/app_runtime/service_graph.py",
        "lib/ccbd/handlers/ping_runtime/handler.py",
        "lib/ccbd/handlers/ping_runtime/payloads.py",
        "lib/ccbd/handlers/project_reload.py",
        "lib/ccbd/reload_apply_service.py",
        "lib/ccbd/services/project_namespace_runtime/controller.py",
        "lib/cli/render_runtime/ops_views_doctor.py",
        "lib/cli/services/doctor.py",
        "lib/cli/services/ping.py",
        "lib/cli/services/start_foreground.py",
        "lib/storage/path_helpers.py",
        "lib/terminal_runtime/api.py",
        "lib/terminal_runtime/api_selection.py",
        "lib/terminal_runtime/backend_selection.py",
        "test/test_ccbd_reload_apply.py",
        "test/test_ccbd_reload_dry_run.py",
        "test/test_ccbd_service_graph.py",
        "test/test_terminal_runtime_backend_selection.py",
        "test/test_v2_ccbd_ping_runtime.py",
        "test/test_v2_ccbd_start_flow.py",
        "test/test_v2_config_loader.py",
        "test/test_v2_storage_paths.py",
        "test/test_v3_config_loader.py",
        ".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-dod-contract-results.json",
        ".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-evidence-pack.md",
        ".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-review-packet.md",
        ".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-review.md",
        "lib/agents/config_loader_runtime/parsing_runtime/runtime_mux.py",
        "lib/cli/services/backend_selection_diagnostics.py",
        "lib/terminal_runtime/backend_resolver.py",
        "test/test_backend_selection_diagnostics.py"
      ],
      "ignored_machine_artifacts": [
        ".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-evidence-pack-results.json",
        ".codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-scope-gate-results.json"
      ],
      "allowed_prefixes": [
        ".codestable/features/2026-07-19-backend-resolver-opt-in-contract",
        "lib",
        "test",
        ".codestable/roadmap/windows-rmux-native-backend",
        ".codestable/reference"
      ]
    }
  ],
  "providers": {},
  "feature": "2026-07-19-backend-resolver-opt-in-contract",
  "inputs": {
    "feature_dir": ".codestable/features/2026-07-19-backend-resolver-opt-in-contract"
  },
  "input_digests": {}
}
```
