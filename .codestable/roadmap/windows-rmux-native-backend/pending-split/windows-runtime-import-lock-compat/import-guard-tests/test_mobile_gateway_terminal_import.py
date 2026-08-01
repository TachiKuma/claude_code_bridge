from __future__ import annotations

import builtins
import importlib
import sys


def test_mobile_gateway_terminal_import_does_not_require_unix_ioctl_modules(monkeypatch) -> None:
    original_module = sys.modules.pop('mobile_gateway.terminal', None)
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in {'fcntl', 'termios', 'pty'}:
            raise ModuleNotFoundError(f"No module named '{name}'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', guarded_import)
    try:
        module = importlib.import_module('mobile_gateway.terminal')
        target = module.TerminalAttachTarget(
            terminal_id='term-test',
            socket_path='/tmp/ccb-test/tmux.sock',
            session_name='ccb-test',
            pane_id='%42',
            geometry=module.TerminalGeometry(),
            target_summary={'project_id': 'proj-test'},
        )

        assert target.command[:5] == [
            'tmux',
            '-S',
            '/tmp/ccb-test/tmux.sock',
            'capture-pane',
            '-p',
        ]
    finally:
        sys.modules.pop('mobile_gateway.terminal', None)
        if original_module is not None:
            sys.modules['mobile_gateway.terminal'] = original_module
