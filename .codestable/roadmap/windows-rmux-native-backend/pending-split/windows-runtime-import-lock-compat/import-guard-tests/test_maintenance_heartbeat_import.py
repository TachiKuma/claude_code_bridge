from __future__ import annotations

import builtins
import importlib
import sys


def test_maintenance_heartbeat_import_does_not_require_fcntl(monkeypatch) -> None:
    original_lock = sys.modules.pop('maintenance_heartbeat.lock', None)
    original_package = sys.modules.pop('maintenance_heartbeat', None)
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'fcntl':
            raise ModuleNotFoundError("No module named 'fcntl'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', guarded_import)
    try:
        module = importlib.import_module('maintenance_heartbeat')

        assert module.MaintenanceHeartbeatLock.__name__ == 'MaintenanceHeartbeatLock'
        assert module.MaintenanceHeartbeatLockBusy.__name__ == 'MaintenanceHeartbeatLockBusy'
    finally:
        sys.modules.pop('maintenance_heartbeat.lock', None)
        sys.modules.pop('maintenance_heartbeat', None)
        if original_lock is not None:
            sys.modules['maintenance_heartbeat.lock'] = original_lock
        if original_package is not None:
            sys.modules['maintenance_heartbeat'] = original_package
