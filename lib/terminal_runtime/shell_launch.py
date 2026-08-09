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

    Resolution order:
    1. ``CCB_SH_EXECUTABLE`` environment variable (explicit override).
    2. ``shutil.which('sh')`` (PATH lookup).
    3. Fixed paths covering standard Git Bash install locations.
    """
    explicit = str(os.environ.get('CCB_SH_EXECUTABLE') or '').strip()
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.is_file():
            return str(candidate)
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
    ``['cmd', '/d', '/c', <sh.exe>, <script>]`` so ``cmd.exe`` invokes sh.exe
    directly.  This avoids the PowerShell ``&`` call operator which Herdr's
    ``pane run`` may not handle reliably (2026-08-09 实测：手动在 pane 中键入
    ``& <sh.exe> <script>`` 可执行，但经 ``herdr pane run`` 注入后 agent2
    报 ``sh : 无法识别``).  Without Git Bash, falls back to ``['sh', '-lc',
    command]`` (the historical tmux behavior).
    """
    sh_exe = resolve_sh_executable()
    if not sh_exe:
        import sys
        print(
            f'[shell_launch] WARNING: resolve_sh_executable() returned None '
            f'for agent={name}; fallback to bare "sh". '
            f'CCB_SH_EXECUTABLE={os.environ.get("CCB_SH_EXECUTABLE", "")!r} '
            f'PATH={os.environ.get("PATH", "")[:200]!r}',
            file=sys.stderr,
            flush=True,
        )
        return ['sh', '-lc', command]
    script_dir = Path(tempfile.gettempdir()) / 'ccb-agent-launch'
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path = script_dir / f'start-{name}-{os.getpid()}.sh'
    script_path.write_text(f'cd {sh_quote(str(cwd))} && {command}\n', encoding='utf-8')
    import sys
    print(
        f'[shell_launch] herdr_respawn: name={name} sh_exe={sh_exe!r} '
        f'script={script_path.as_posix()!r}',
        file=sys.stderr,
        flush=True,
    )
    return ['cmd', '/d', '/c', sh_exe, str(script_path)]
