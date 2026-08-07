"""``ccb herdr open`` — WezTerm-launched Herdr managed startup bootstrap.

Locates the Herdr runtime, verifies its server is running, probes read-only
capabilities, and injects the ``CCB_HERDR_*`` env the CCB herdr backend
consumes (executable, session, and a runtime capability report). Herdr stays
the physical pane owner; CCB remains the agent/provider/recovery authority
(managed mode, never an attached-mode degradation).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

from terminal_runtime.herdr_backend_runtime.capabilities import _KNOWN_CAPABILITIES

from .herdr_common import herdr_command_env, query_herdr_server_status, resolve_herdr_executable

_DEFAULT_HERDR_SESSION = 'ccb-herdr'

_READ_PROBES = (
    ('session_attach', ('api', 'snapshot')),
    ('workspace_list', ('workspace', 'list')),
    ('pane_list', ('pane', 'list')),
)


def ensure_herdr_bootstrap_env(
    *,
    herdr_exe: str | None = None,
    herdr_session: str | None = None,
) -> dict[str, object]:
    """Locate herdr, verify the server, probe capabilities, inject runtime env.

    Args:
        herdr_exe: Explicit herdr executable path (``--herdr-exe``).
        herdr_session: Explicit Herdr session name (``--herdr-session``).

    Returns:
        A dict with ``ok``; on failure ``reason`` carries actionable guidance.
        On success also returns ``herdr_exe``, ``herdr_session``, ``warnings``
        and ``capability_report``. Successful calls set ``CCB_HERDR_EXE``,
        ``CCB_HERDR_SESSION`` and ``CCB_HERDR_CAPABILITY_REPORT`` in the process
        environment so downstream CCB startup picks the herdr backend.
    """
    exe = resolve_herdr_executable(explicit=herdr_exe)
    if not exe:
        return {
            'ok': False,
            'reason': (
                'Herdr executable not found. Install Herdr '
                '(AppData/Local/Programs/Herdr) or set CCB_HERDR_EXE.'
            ),
        }
    status = query_herdr_server_status(exe)
    if status is None:
        return {
            'ok': False,
            'reason': 'Failed to query Herdr server status.',
        }
    # Unwrap nested server shape when Herdr returns
    # {"result": {"server": {"running": true, ...}}} rather than a flat dict.
    server = status
    inner = status.get('result')
    if isinstance(inner, dict):
        nested = inner.get('server')
        server = nested if isinstance(nested, dict) else inner
    if server.get('running') is not True:
        return {
            'ok': False,
            'reason': (
                'Herdr server is not running. Start Herdr first — run `herdr` '
                'to attach the persistent session, then retry `ccb herdr open`.'
            ),
        }
    if server.get('compatible') is not True:
        return {
            'ok': False,
            'reason': (
                f'Herdr protocol is not compatible with CCB '
                f'(server protocol={server.get("protocol")!r}). Upgrade Herdr.'
            ),
        }
    probe = _probe_herdr_read_capabilities(exe)
    failed_probes = [name for name, ok in probe.items() if not ok]
    if failed_probes:
        return {
            'ok': False,
            'reason': (
                'Herdr read-only capability probes failed: '
                + ', '.join(sorted(failed_probes))
                + '. Herdr server may be degraded.'
            ),
        }
    capability_report = _build_capability_report(probe)
    report_path = _write_capability_report(capability_report)
    warnings: list[str] = []
    live_session = str(server.get('session') or '').strip() or None
    session = (
        str(herdr_session or '').strip()
        or os.environ.get('CCB_HERDR_SESSION', '').strip()
        or live_session
        or _DEFAULT_HERDR_SESSION
    )
    if not herdr_session and not os.environ.get('CCB_HERDR_SESSION', '').strip():
        warnings.append(
            f'Using Herdr session {session!r}; pass --herdr-session to override.'
        )
    os.environ['CCB_HERDR_EXE'] = exe
    os.environ['CCB_HERDR_SESSION'] = session
    os.environ['CCB_HERDR_CAPABILITY_REPORT'] = report_path
    return {
        'ok': True,
        'herdr_exe': exe,
        'herdr_session': session,
        'capability_report': report_path,
        'warnings': warnings,
    }


def _probe_herdr_read_capabilities(exe: str) -> dict[str, bool]:
    """Probe read-only herdr commands; returns ``{capability: ok}``."""
    result: dict[str, bool] = {}
    for capability, args in _READ_PROBES:
        try:
            run = subprocess.run(
                [exe, *args],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10,
                env=herdr_command_env(),
                check=False,
            )
            result[capability] = run.returncode == 0 and bool((run.stdout or '').strip())
        except (OSError, subprocess.SubprocessError):
            result[capability] = False
    return result


def _build_capability_report(probe: dict[str, bool]) -> dict[str, object]:
    """Build a capability report covering all known capabilities.

    Probed capabilities reflect the live probe result; unprobed capabilities
    are marked ``supported`` because the server is reachable, protocol is
    compatible, and the read-only probes passed. Failure would surface at the
    operation gate at runtime rather than at bootstrap.
    """
    command_status: dict[str, str] = {}
    for name in sorted(_KNOWN_CAPABILITIES):
        ok = probe.get(name, True)
        command_status[name] = 'supported' if ok else 'unsupported'
    return {
        'backend_impl': 'herdr',
        'adapter_recommendation': 'continue',
        'verdict': 'pass',
        'failure_class': 'none',
        'command_status': command_status,
        'semantic_status': dict(command_status),
        'blocking_gaps': [],
        'windows_beta_gaps': [],
        'source_ref': 'ccb-herdr-open-runtime-probe',
    }


def _write_capability_report(report: dict[str, object]) -> str:
    fd, path = tempfile.mkstemp(prefix='ccb-herdr-capability-', suffix='.json')
    with os.fdopen(fd, 'w', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, sort_keys=True)
    return path


__all__ = ['ensure_herdr_bootstrap_env']
