"""Windows-safe shell command construction for herdr pane respawn.

Herdr panes run PowerShell on Windows; bash-style ``export VAR=...; cmd``
payloads cannot be injected directly.  When Git Bash is installed, the payload
is written to a ``.sh`` script and respawned as ``& <sh.exe> <script>`` so the
PowerShell pane calls the full sh.exe path (bare ``sh`` is not a PowerShell
command).  Shared by the runtime-launch path
(``cli/services/runtime_launch_runtime/pane_runtime.py``) and the ccbd
namespace materialization path
(``ccbd/services/project_namespace_runtime/backend.py``) so both respawn
agent/sidebar panes with the same command shape.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


def resolve_sh_executable() -> str | None:
    """Resolve Git Bash's sh.exe on Windows; None when unavailable.

    ``shutil.which('sh')`` covers PATH; the fixed candidates cover the
    standard Git Bash install locations when PATH does not include them.
    """
    found = shutil.which('sh')
    if found:
        return str(found)
    for candidate in (
        r'C:\Program Files\Git\bin\sh.exe',
        r'C:\Program Files\Git\usr\bin\sh.exe',
        r'C:\Program Files\Git\cmd\sh.exe',
    ):
        if Path(candidate).exists():
            return candidate
    return None


def sh_quote(value: str) -> str:
    """Quote a path for a POSIX shell single-quote literal."""
    escaped = value.replace("'", "'\\''")
    return f"'{escaped}'"


def herdr_respawn_command(command: str, cwd: Path, name: str) -> list[str]:
    """Build the herdr respawn argv for a bash-style command payload.

    With Git Bash present, writes the payload to a ``.sh`` script and returns
    ``['&', <sh.exe>, <script>]`` so the PowerShell pane invokes the full sh
    executable (bare ``sh`` is not a PowerShell command).  Without Git Bash,
    falls back to ``['sh', '-lc', command]`` (the historical tmux behavior).
    """
    sh_exe = resolve_sh_executable()
    if not sh_exe:
        return ['sh', '-lc', command]
    script_dir = Path(tempfile.gettempdir()) / 'ccb-agent-launch'
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path = script_dir / f'start-{name}-{os.getpid()}.sh'
    script_path.write_text(f'cd {sh_quote(str(cwd))} && {command}\n', encoding='utf-8')
    return ['&', sh_exe, script_path.as_posix()]
