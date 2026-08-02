---
doc_type: feature-evidence-pack
feature: 2026-08-02-ccbd-windows-control-plane-transport
status: generated
---

# 2026-08-02-ccbd-windows-control-plane-transport evidence pack

## 1. Scope

- Design: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md`
- Checklist: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-checklist.yaml`

## 2. DoD Results

```json
{
  "gate_id": "dod-runner",
  "stage": "implementation.before_review",
  "status": "passed",
  "blocking": [],
  "warnings": [
    "CMD-006: documented baseline failed with exit 2"
  ],
  "evidence": [
    {
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-08-02-ccbd-windows-control-plane-transport\\ccbd-windows-control-plane-transport-checklist.yaml\n\nAll files valid.\n",
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
      "command": "python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_control_plane_transport_fake.py",
      "exit_code": 0,
      "stdout": "..............                                                           [100%]\n============================== warnings summary ===============================\nC:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475\n  C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475: PytestCacheWarning: could not create cache path D:\\Python\\GitHub\\claude_code_bridge\\.pytest_cache\\v\\cache\\nodeids: [WinError 183] ���ļ��Ѵ���ʱ���޷��������ļ���: 'D:\\\\Python\\\\GitHub\\\\claude_code_bridge\\\\.pytest_cache\\\\v\\\\cache'\n    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n14 passed, 1 warning in 0.35s\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_ccbd_windows_tcp_loopback_transport.py",
      "exit_code": 0,
      "stdout": "...............                                                          [100%]\n============================== warnings summary ===============================\nC:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475\n  C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475: PytestCacheWarning: could not create cache path D:\\Python\\GitHub\\claude_code_bridge\\.pytest_cache\\v\\cache\\nodeids: [WinError 183] ���ļ��Ѵ���ʱ���޷��������ļ���: 'D:\\\\Python\\\\GitHub\\\\claude_code_bridge\\\\.pytest_cache\\\\v\\\\cache'\n    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n15 passed, 1 warning in 0.66s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_socket_server_loop.py test/test_ccbd_socket_client.py",
      "exit_code": 0,
      "stdout": "....s................................................                    [100%]\n============================== warnings summary ===============================\nC:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475\n  C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475: PytestCacheWarning: could not create cache path D:\\Python\\GitHub\\claude_code_bridge\\.pytest_cache\\v\\cache\\nodeids: [WinError 183] ���ļ��Ѵ���ʱ���޷��������ļ���: 'D:\\\\Python\\\\GitHub\\\\claude_code_bridge\\\\.pytest_cache\\\\v\\\\cache'\n    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n52 passed, 1 skipped, 1 warning in 0.58s\n",
      "stderr": "",
      "id": "CMD-005",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_v2_start_service.py -k \"ccbd or endpoint or ping or socket\"",
      "exit_code": 2,
      "stdout": "\n=================================== ERRORS ====================================\n_______________ ERROR collecting test/test_v2_start_service.py ________________\nImportError while importing test module 'D:\\Python\\GitHub\\claude_code_bridge\\test\\test_v2_start_service.py'.\nHint: make sure your test modules/packages have valid Python names.\nTraceback:\nC:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\importlib\\__init__.py:88: in import_module\n    return _bootstrap._gcd_import(name[level:], package, level)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntest\\test_v2_start_service.py:16: in <module>\n    from cli.services.start import _refresh_running_sidebar_helpers, start_agents\nlib\\cli\\services\\start.py:13: in <module>\n    from .daemon import ensure_daemon_started\nlib\\cli\\services\\daemon.py:6: in <module>\n    from ccbd.keeper import KeeperStateStore\nlib\\ccbd\\keeper.py:24: in <module>\n    from mobile_gateway.project_registry import publish_mobile_gateway_project\nlib\\mobile_gateway\\__init__.py:3: in <module>\n    from .service import (\nlib\\mobile_gateway\\service.py:32: in <module>\n    from .activity_watch import (\nlib\\mobile_gateway\\activity_watch.py:22: in <module>\n    from .terminal import TerminalHistoryTarget, capture_tmux_pane_text\nlib\\mobile_gateway\\terminal.py:4: in <module>\n    import fcntl\nE   ModuleNotFoundError: No module named 'fcntl'\n============================== warnings summary ===============================\nC:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475\n  C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475: PytestCacheWarning: could not create cache path D:\\Python\\GitHub\\claude_code_bridge\\.pytest_cache\\v\\cache\\nodeids: [WinError 183] ���ļ��Ѵ���ʱ���޷��������ļ���: 'D:\\\\Python\\\\GitHub\\\\claude_code_bridge\\\\.pytest_cache\\\\v\\\\cache'\n    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))\n\nC:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:429\n  C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:429: PytestCacheWarning: could not create cache path D:\\Python\\GitHub\\claude_code_bridge\\.pytest_cache\\v\\cache\\lastfailed: [WinError 183] ���ļ��Ѵ���ʱ���޷��������ļ���: 'D:\\\\Python\\\\GitHub\\\\claude_code_bridge\\\\.pytest_cache\\\\v\\\\cache'\n    config.cache.set(\"cache/lastfailed\", self.lastfailed)\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n=========================== short test summary info ===========================\nERROR test/test_v2_start_service.py\n!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!\n2 warnings, 1 error in 0.46s\n",
      "stderr": "",
      "id": "CMD-006",
      "core": true,
      "failure_handling": "document-baseline"
    },
    {
      "command": "python -m pytest -q test/test_ccbd_windows_tcp_loopback_import_guard.py",
      "exit_code": 0,
      "stdout": "..                                                                       [100%]\n============================== warnings summary ===============================\nC:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475\n  C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\_pytest\\cacheprovider.py:475: PytestCacheWarning: could not create cache path D:\\Python\\GitHub\\claude_code_bridge\\.pytest_cache\\v\\cache\\nodeids: [WinError 183] ���ļ��Ѵ���ʱ���޷��������ļ���: 'D:\\\\Python\\\\GitHub\\\\claude_code_bridge\\\\.pytest_cache\\\\v\\\\cache'\n    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n2 passed, 1 warning in 0.10s\n",
      "stderr": "",
      "id": "CMD-007",
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

Design bytes: 17608
Checklist bytes: 7081

## 5. Residual Risks

- CMD-006: documented baseline failed with exit 2
- cleanliness marker TODO in .codestable/tools/codestable-scope-gate.py
- cleanliness marker FIXME in .codestable/tools/codestable-scope-gate.py
- cleanliness marker XXX in .codestable/tools/codestable-scope-gate.py
- cleanliness marker TODO in .codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md
- cleanliness marker FIXME in .codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md

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
  "warnings": [
    "cleanliness marker TODO in .codestable/tools/codestable-scope-gate.py",
    "cleanliness marker FIXME in .codestable/tools/codestable-scope-gate.py",
    "cleanliness marker XXX in .codestable/tools/codestable-scope-gate.py",
    "cleanliness marker TODO in .codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md",
    "cleanliness marker FIXME in .codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md"
  ],
  "evidence": [
    {
      "changed_files": [
        ".codestable/tools/codestable-dod-runner.py",
        ".codestable/tools/codestable-scope-gate.py",
        ".codestable/tools/codestable_gate_common.py",
        "lib/ccbd/app_runtime/lifecycle.py",
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
        "test/test_ccbd_bootstrap_probe.py",
        "test/test_ccbd_socket_client.py",
        "test/test_ccbd_socket_server_loop.py",
        ".codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/evidence/cmd-013-native-windows-herdr-transcript.md",
        ".codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-checklist.yaml",
        ".codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design-review.md",
        ".codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md",
        ".codestable/roadmap/windows-native-herdr-ccb/goal-features/ccbd-windows-control-plane-transport.md",
        "lib/ccbd/control_plane_transport/__init__.py",
        "lib/ccbd/control_plane_transport/endpoint.py",
        "lib/ccbd/control_plane_transport/endpoint_store.py",
        "lib/ccbd/control_plane_transport/factory.py",
        "lib/ccbd/control_plane_transport/fake.py",
        "lib/ccbd/control_plane_transport/interface.py",
        "lib/ccbd/control_plane_transport/token_auth.py",
        "lib/ccbd/control_plane_transport/unix.py",
        "lib/ccbd/control_plane_transport/windows_tcp.py",
        "test/test_ccbd_control_plane_transport_fake.py",
        "test/test_ccbd_control_plane_transport_unix.py",
        "test/test_ccbd_windows_tcp_loopback_import_guard.py",
        "test/test_ccbd_windows_tcp_loopback_transport.py"
      ],
      "ignored_machine_artifacts": [
        ".codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-scope-gate-results.json"
      ],
      "allowed_prefixes": [
        ".codestable/features/2026-08-02-ccbd-windows-control-plane-transport",
        "lib/ccbd/control_plane_transport",
        "lib/ccbd/socket_client_runtime",
        "lib/ccbd/socket_server_runtime",
        "lib/ccbd/app_runtime/lifecycle.py",
        "lib/ccbd/handlers/ping_runtime/payloads.py",
        "lib/ccbd/models_runtime/mount.py",
        "lib/ccbd/services/lifecycle.py",
        "lib/ccbd/services/mount.py",
        "lib/ccbd/services/ownership.py",
        "lib/ccbd/services/project_inspection.py",
        "test/test_ccbd_control_plane_transport_unix.py",
        "test/test_ccbd_control_plane_transport_fake.py",
        "test/test_ccbd_windows_tcp_loopback_transport.py",
        "test/test_ccbd_windows_tcp_loopback_import_guard.py",
        "test/test_ccbd_bootstrap_probe.py",
        "test/test_ccbd_socket_server_loop.py",
        "test/test_ccbd_socket_client.py",
        ".codestable/roadmap/windows-native-herdr-ccb/goal-features/ccbd-windows-control-plane-transport.md",
        ".codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/evidence/cmd-013-native-windows-herdr-transcript.md",
        ".codestable/tools/codestable_gate_common.py",
        ".codestable/tools/codestable-scope-gate.py",
        ".codestable/tools/codestable-dod-runner.py"
      ]
    }
  ],
  "providers": {}
}
```
