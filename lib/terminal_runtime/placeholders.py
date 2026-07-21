from __future__ import annotations

import os

_PANE_PLACEHOLDER_BODY = 'while :; do sleep 3600; done'
_WINDOWS_PANE_PLACEHOLDER_BODY = 'while ($true) { Start-Sleep -Seconds 3600 }'


def pane_placeholder_cmd() -> str:
    if os.name == 'nt':
        return _WINDOWS_PANE_PLACEHOLDER_BODY
    return _PANE_PLACEHOLDER_BODY


def pane_placeholder_argv() -> tuple[str, ...]:
    if os.name == 'nt':
        return ('powershell.exe', '-NoProfile', '-Command', _WINDOWS_PANE_PLACEHOLDER_BODY)
    return ('sh', '-lc', _PANE_PLACEHOLDER_BODY)


__all__ = ['pane_placeholder_argv', 'pane_placeholder_cmd']
