---
doc_type: feature-evidence-pack
feature: 2026-07-20-ccbd-control-plane-transport-seam
status: generated
---

# 2026-07-20-ccbd-control-plane-transport-seam evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml`

## 2. DoD Results

```json
{
  "gate_id": "dod-runner",
  "stage": "implementation.before_review",
  "status": "passed",
  "blocking": [],
  "warnings": [
    "CMD-005 documented baseline failure: Windows collection imports mobile_gateway.terminal -> fcntl before this feature's ccbd transport seam can be exercised; checklist failure_handling=document-baseline; raw result preserved at ccbd-control-plane-transport-seam-dod-results.raw.json"
  ],
  "evidence": [
    {
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-20-ccbd-control-plane-transport-seam\\ccbd-control-plane-transport-seam-checklist.yaml\n\nAll files valid.\n",
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
      "command": "python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_control_plane_transport_fake.py",
      "exit_code": 0,
      "stdout": "....................                                                     [100%]\n20 passed in 0.55s\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_server.py test/test_ccbd_socket_client.py",
      "exit_code": 0,
      "stdout": "sssss................                                                    [100%]\n16 passed, 5 skipped in 0.19s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_v2_start_service.py test/test_v2_phase2_entrypoint.py -k \"ccbd or socket or endpoint or ping\"",
      "exit_code": 2,
      "stdout": "\n=================================== ERRORS ====================================\n_______________ ERROR collecting test/test_v2_start_service.py ________________\nImportError while importing test module 'D:\\Python\\GitHub\\claude_code_bridge\\test\\test_v2_start_service.py'.\nHint: make sure your test modules/packages have valid Python names.\nTraceback:\nC:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\importlib\\__init__.py:88: in import_module\n    return _bootstrap._gcd_import(name[level:], package, level)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntest\\test_v2_start_service.py:16: in <module>\n    from cli.services.start import _refresh_running_sidebar_helpers, start_agents\nlib\\cli\\services\\start.py:13: in <module>\n    from .daemon import ensure_daemon_started\nlib\\cli\\services\\daemon.py:6: in <module>\n    from ccbd.keeper import KeeperStateStore\nlib\\ccbd\\keeper.py:25: in <module>\n    from mobile_gateway.project_registry import publish_mobile_gateway_project\nlib\\mobile_gateway\\__init__.py:3: in <module>\n    from .service import (\nlib\\mobile_gateway\\service.py:38: in <module>\n    from .terminal import (\nlib\\mobile_gateway\\terminal.py:4: in <module>\n    import fcntl\nE   ModuleNotFoundError: No module named 'fcntl'\n_____________ ERROR collecting test/test_v2_phase2_entrypoint.py ______________\nImportError while importing test module 'D:\\Python\\GitHub\\claude_code_bridge\\test\\test_v2_phase2_entrypoint.py'.\nHint: make sure your test modules/packages have valid Python names.\nTraceback:\nC:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\importlib\\__init__.py:88: in import_module\n    return _bootstrap._gcd_import(name[level:], package, level)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntest\\test_v2_phase2_entrypoint.py:23: in <module>\n    import cli.phase2 as phase2_module\nlib\\cli\\phase2.py:18: in <module>\n    from cli.phase2_services import build_phase2_dispatch_services\nlib\\cli\\phase2_services.py:53: in <module>\n    from cli.services.doctor import doctor_summary\nlib\\cli\\services\\doctor.py:11: in <module>\n    from .doctor_runtime import (\nlib\\cli\\services\\doctor_runtime\\__init__.py:6: in <module>\n    from .system import entrypoint_summary, installation_summary, requirements_summary, runtime_identity_summary\nlib\\cli\\services\\doctor_runtime\\system.py:12: in <module>\n    from cli.management import find_install_dir, get_version_info\nlib\\cli\\management.py:3: in <module>\n    from .management_runtime import (\nlib\\cli\\management_runtime\\__init__.py:2: in <module>\n    from .commands import cmd_install, cmd_reinstall, cmd_uninstall, cmd_update, cmd_version, find_matching_version, is_newer_version, latest_version\nlib\\cli\\management_runtime\\commands.py:5: in <module>\n    from .commands_runtime import cmd_install, cmd_reinstall, cmd_uninstall, cmd_update, cmd_version, find_matching_version, is_newer_version, latest_version\nlib\\cli\\management_runtime\\commands_runtime\\__init__.py:3: in <module>\n    from .install import cmd_install, cmd_reinstall, cmd_uninstall\nlib\\cli\\management_runtime\\commands_runtime\\install.py:6: in <module>\n    from cli.services.mobile import prepare_server_mobile_gateway\nlib\\cli\\services\\mobile.py:10: in <module>\n    from mobile_gateway import (\nlib\\mobile_gateway\\__init__.py:3: in <module>\n    from .service import (\nlib\\mobile_gateway\\service.py:38: in <module>\n    from .terminal import (\nlib\\mobile_gateway\\terminal.py:4: in <module>\n    import fcntl\nE   ModuleNotFoundError: No module named 'fcntl'\n=========================== short test summary info ===========================\nERROR test/test_v2_start_service.py\nERROR test/test_v2_phase2_entrypoint.py\n!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!\n2 errors in 0.85s\n",
      "stderr": "",
      "id": "CMD-005",
      "core": true,
      "failure_handling": "document-baseline"
    },
    {
      "command": "python -m pytest -q test/test_ccbd_control_plane_transport_import_guard.py",
      "exit_code": 0,
      "stdout": ".                                                                        [100%]\n1 passed in 0.07s\n",
      "stderr": "",
      "id": "CMD-006",
      "core": true,
      "failure_handling": "fix-or-block"
    }
  ],
  "providers": {},
  "feature": "2026-07-20-ccbd-control-plane-transport-seam",
  "inputs": {
    "checklist": ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml"
  },
  "input_digests": {
    "checklist": "103576d89c4529f200048372c5115e06082c1493f9f701bf02d0a6a5d982efed"
  }
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 18619
Checklist bytes: 5210

## 5. Residual Risks

- CMD-005 documented baseline failure: Windows collection imports mobile_gateway.terminal -> fcntl before this feature's ccbd transport seam can be exercised; checklist failure_handling=document-baseline; raw result preserved at ccbd-control-plane-transport-seam-dod-results.raw.json

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
        ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml",
        ".codestable/roadmap/windows-rmux-native-backend/goal-state.yaml",
        "lib/ccbd/handlers/ping_runtime/payloads.py",
        "lib/ccbd/models_runtime/mount.py",
        "lib/ccbd/services/lifecycle.py",
        "lib/ccbd/services/mount.py",
        "lib/ccbd/services/ownership.py",
        "lib/ccbd/services/project_inspection.py",
        "lib/ccbd/socket_client_runtime/transport.py",
        "lib/ccbd/socket_server_runtime/bootstrap_probe.py",
        "lib/ccbd/socket_server_runtime/lifecycle.py",
        "lib/ccbd/socket_server_runtime/loop.py",
        "lib/ccbd/socket_server_runtime/server.py",
        "lib/cli/services/doctor_runtime/ccbd.py",
        "test/test_ccbd_bootstrap_probe.py",
        "test/test_ccbd_socket_client.py",
        "test/test_ccbd_socket_lifecycle.py",
        "test/test_ccbd_socket_server_loop.py",
        "test/test_v2_ccbd_socket.py",
        ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-dod-results.raw.json",
        ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-evidence-pack.md",
        ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-review.md",
        ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-scope-gate.json",
        "lib/ccbd/control_plane_transport/__init__.py",
        "lib/ccbd/control_plane_transport/endpoint.py",
        "lib/ccbd/control_plane_transport/factory.py",
        "lib/ccbd/control_plane_transport/fake.py",
        "lib/ccbd/control_plane_transport/interface.py",
        "lib/ccbd/control_plane_transport/unix.py",
        "test/test_ccbd_control_plane_transport_fake.py",
        "test/test_ccbd_control_plane_transport_import_guard.py",
        "test/test_ccbd_control_plane_transport_unix.py",
        "test/test_ccbd_socket_server.py"
      ],
      "ignored_machine_artifacts": [
        ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-dod-results.json",
        ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-evidence-pack-results.json"
      ],
      "allowed_prefixes": [
        ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam",
        ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam",
        ".codestable/roadmap/windows-rmux-native-backend",
        "lib/ccbd/control_plane_transport",
        "lib/ccbd/socket_client_runtime/transport.py",
        "lib/ccbd/socket_server_runtime",
        "lib/ccbd/handlers/ping_runtime/payloads.py",
        "lib/ccbd/models_runtime/mount.py",
        "lib/ccbd/services/lifecycle.py",
        "lib/ccbd/services/mount.py",
        "lib/ccbd/services/project_inspection.py",
        "lib/ccbd/services/ownership.py",
        "lib/cli/services/doctor_runtime/ccbd.py",
        "test/test_ccbd_control_plane_transport_unix.py",
        "test/test_ccbd_control_plane_transport_fake.py",
        "test/test_ccbd_control_plane_transport_import_guard.py",
        "test/test_ccbd_bootstrap_probe.py",
        "test/test_ccbd_socket_server.py",
        "test/test_ccbd_socket_client.py",
        "test/test_ccbd_socket_lifecycle.py",
        "test/test_ccbd_socket_server_loop.py",
        "test/test_v2_ccbd_socket.py"
      ]
    }
  ],
  "providers": {},
  "feature": "2026-07-20-ccbd-control-plane-transport-seam",
  "inputs": {
    "feature_dir": ".codestable/features/2026-07-20-ccbd-control-plane-transport-seam"
  },
  "input_digests": {}
}
```
