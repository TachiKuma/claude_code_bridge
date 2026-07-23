from __future__ import annotations

from dataclasses import dataclass
import shutil
import subprocess
import time

from cli.context import CliContext
from ccbd.socket_client import CcbdClient, CcbdClientError
from terminal_runtime import RmuxBackend
from terminal_runtime.mux_backend_contract import MuxCommandError
from terminal_runtime.env import tmux_compatible_env
from terminal_runtime.tmux import tmux_base
from .daemon_runtime.policy import (
    FOREGROUND_ATTACH_RPC_TIMEOUT_S,
    FOREGROUND_ATTACH_TARGET_READY_TIMEOUT_S,
)

_ATTACH_ESTABLISH_TIMEOUT_S = 1.5
_ATTACH_ESTABLISH_POLL_INTERVAL_S = 0.05
_ATTACH_TARGET_READY_TIMEOUT_S = FOREGROUND_ATTACH_TARGET_READY_TIMEOUT_S
_ATTACH_TARGET_READY_POLL_INTERVAL_S = 0.05
_MIN_ATTACH_RPC_TIMEOUT_S = 0.1


@dataclass(frozen=True)
class ForegroundAttachSummary:
    project_id: str
    tmux_socket_path: str | None
    tmux_session_name: str | None
    backend_impl: str = 'tmux'
    namespace_id: str | None = None
    session_name: str | None = None
    ipc_kind: str | None = None
    ipc_ref: str | None = None


class ForegroundAttachError(RuntimeError):
    pass


def attach_started_project_namespace(context: CliContext) -> ForegroundAttachSummary:
    client = _foreground_attach_client(context)
    env = _attach_env()
    payload = _wait_for_attach_target(client, env=env)
    backend_impl = _payload_backend_impl(payload)
    if backend_impl == 'rmux':
        return _attach_rmux_namespace(context, payload, env=env)
    if shutil.which('tmux') is None:
        raise ForegroundAttachError('tmux is required for interactive `ccb`')
    tmux_ipc_kind = _payload_namespace_ipc_kind(payload, default='unix_socket')
    tmux_socket_path = (
        _payload_namespace_ipc_ref(payload)
        if tmux_ipc_kind == 'unix_socket'
        else _payload_namespace_tmux_socket_path(payload)
    )
    tmux_session_name = _payload_namespace_session_name(payload)
    namespace_id = _payload_namespace_id(payload)
    summary = ForegroundAttachSummary(
        project_id=context.project.project_id,
        tmux_socket_path=tmux_socket_path,
        tmux_session_name=tmux_session_name,
        backend_impl='tmux',
        namespace_id=namespace_id or tmux_session_name,
        session_name=tmux_session_name,
        ipc_kind=tmux_ipc_kind,
        ipc_ref=tmux_socket_path,
    )
    attach = subprocess.Popen(
        _tmux_cmd(tmux_socket_path, 'attach-session', '-t', tmux_session_name),
        env=env,
    )
    attached = _wait_for_attach_established(
        attach,
        tmux_socket_path=tmux_socket_path,
        tmux_session_name=tmux_session_name,
        env=env,
    )
    if attached:
        _best_effort_refresh_attached_client(
            tmux_socket_path,
            tmux_session_name,
            client_pid=attach.pid,
            env=env,
        )
    returncode = attach.wait()
    if attached:
        return summary
    if returncode != 0 and not _tmux_has_session(tmux_socket_path, tmux_session_name, env=env):
        raise ForegroundAttachError('project namespace session exited before foreground attach completed')
    raise ForegroundAttachError('failed to attach project namespace after successful `ccb` start')


def _attach_rmux_namespace(
    context: CliContext,
    payload: dict[str, object],
    *,
    env: dict[str, str],
) -> ForegroundAttachSummary:
    del env
    namespace_id = _payload_namespace_id(payload)
    session_name = _payload_namespace_session_name(payload) or namespace_id
    ipc_kind = _payload_namespace_ipc_kind(payload, default='named_pipe')
    ipc_ref = _payload_namespace_ipc_ref(payload)
    workspace_window_name = str(payload.get('namespace_workspace_window_name') or '').strip() or None
    if not namespace_id or not session_name:
        raise ForegroundAttachError('rmux foreground attach failed: namespace_id/session_name missing')
    if ipc_kind not in {'named_pipe', 'socket_name'}:
        raise ForegroundAttachError(f'rmux foreground attach failed: unsupported ipc_kind={ipc_kind!r}')
    backend = _build_rmux_attach_backend(
        namespace_id=namespace_id,
        session_name=session_name,
        ipc_kind=ipc_kind,
        ipc_ref=ipc_ref,
    )
    namespace_ref = {
        'backend_family': 'tmux-family',
        'backend_impl': 'rmux',
        'namespace_id': namespace_id,
        'session_name': session_name,
        'ipc_kind': ipc_kind,
        'ipc_ref': ipc_ref or namespace_id,
    }
    try:
        returncode = backend.attach_namespace(namespace_ref, window_name=workspace_window_name)
    except MuxCommandError as exc:
        raise ForegroundAttachError(
            'rmux foreground attach failed: '
            f'namespace_id={namespace_id!r} session_name={session_name!r} detail={exc.detail}'
        ) from exc
    if returncode != 0:
        raise ForegroundAttachError(
            'rmux foreground attach failed: '
            f'namespace_id={namespace_id!r} session_name={session_name!r} returncode={returncode}'
        )
    return ForegroundAttachSummary(
        project_id=context.project.project_id,
        tmux_socket_path=None,
        tmux_session_name=None,
        backend_impl='rmux',
        namespace_id=namespace_id,
        session_name=session_name,
        ipc_kind=ipc_kind,
        ipc_ref=ipc_ref or namespace_id,
    )


def _wait_for_attach_established(
    attach: subprocess.Popen[bytes] | subprocess.Popen[str],
    *,
    tmux_socket_path: str,
    tmux_session_name: str,
    env: dict[str, str],
) -> bool:
    deadline = time.monotonic() + _ATTACH_ESTABLISH_TIMEOUT_S
    while True:
        if _tmux_client_pid_attached(
            tmux_socket_path,
            tmux_session_name,
            client_pid=attach.pid,
            env=env,
        ):
            return True
        if attach.poll() is not None:
            return False
        if time.monotonic() >= deadline:
            return True
        time.sleep(_ATTACH_ESTABLISH_POLL_INTERVAL_S)


def _tmux_client_pid_attached(
    tmux_socket_path: str,
    tmux_session_name: str,
    *,
    client_pid: int,
    env: dict[str, str],
) -> bool:
    return client_pid in _tmux_list_client_pids(
        tmux_socket_path,
        tmux_session_name,
        env=env,
    )


def _wait_for_attach_target(client, *, env: dict[str, str]) -> dict[str, object]:
    deadline = time.monotonic() + _ATTACH_TARGET_READY_TIMEOUT_S
    attempts = 0
    ping_successes = 0
    last_error = _attach_target_unavailable_error(
        attempts=attempts,
        timeout_s=_ATTACH_TARGET_READY_TIMEOUT_S,
    )
    while True:
        remaining_s = deadline - time.monotonic()
        if remaining_s < _MIN_ATTACH_RPC_TIMEOUT_S:
            raise ForegroundAttachError(last_error)
        attempt_timeout_s = min(FOREGROUND_ATTACH_RPC_TIMEOUT_S, remaining_s)
        try:
            attempts += 1
            payload = _client_for_attach_attempt(client, timeout_s=attempt_timeout_s).ping('ccbd')
        except CcbdClientError as exc:
            last_error = _attach_ping_timeout_error(
                exc,
                attempts=attempts,
                timeout_s=_ATTACH_TARGET_READY_TIMEOUT_S,
                rpc_timeout_s=attempt_timeout_s,
            )
        else:
            ping_successes += 1
            ready, error = _attach_target_ready(payload, env=env)
            if ready:
                return payload
            last_error = _attach_namespace_timeout_error(
                error,
                attempts=attempts,
                ping_successes=ping_successes,
                timeout_s=_ATTACH_TARGET_READY_TIMEOUT_S,
            )
        if time.monotonic() >= deadline:
            raise ForegroundAttachError(last_error)
        time.sleep(min(_ATTACH_TARGET_READY_POLL_INTERVAL_S, max(0.0, deadline - time.monotonic())))


def _attach_target_ready(payload: dict[str, object], *, env: dict[str, str]) -> tuple[bool, str]:
    backend_impl = _payload_backend_impl(payload)
    if backend_impl == 'rmux':
        namespace_id = _payload_namespace_id(payload)
        session_name = _payload_namespace_session_name(payload) or namespace_id
        ipc_kind = _payload_namespace_ipc_kind(payload, default='named_pipe')
        ui_attachable = bool(payload.get('namespace_ui_attachable'))
        if not namespace_id or not session_name or not ui_attachable:
            return False, _attach_error_with_selection(
                'project namespace is not attachable after successful `ccb` start',
                payload,
            )
        if ipc_kind not in {'named_pipe', 'socket_name'}:
            return False, _attach_error_with_selection(
                f'rmux project namespace uses unsupported ipc_kind={ipc_kind!r}',
                payload,
            )
        return True, ''
    tmux_ipc_kind = _payload_namespace_ipc_kind(payload, default='unix_socket')
    tmux_socket_path = (
        _payload_namespace_ipc_ref(payload)
        if tmux_ipc_kind == 'unix_socket'
        else _payload_namespace_tmux_socket_path(payload)
    )
    tmux_session_name = _payload_namespace_session_name(payload)
    workspace_window_name = str(payload.get('namespace_workspace_window_name') or '').strip()
    ui_attachable = bool(payload.get('namespace_ui_attachable'))
    if not tmux_socket_path or not tmux_session_name or not ui_attachable:
        return False, _attach_error_with_selection(
            'project namespace is not attachable after successful `ccb` start',
            payload,
        )
    if not _tmux_has_session(tmux_socket_path, tmux_session_name, env=env):
        return False, _attach_error_with_selection(
            'project namespace session is missing after successful `ccb` start',
            payload,
        )
    if workspace_window_name and not _tmux_select_window(
        tmux_socket_path,
        f'{tmux_session_name}:{workspace_window_name}',
        env=env,
    ):
        return False, _attach_error_with_selection(
            'project namespace workspace window is missing after successful `ccb` start',
            payload,
        )
    return True, ''


def _attach_error_with_selection(message: str, payload: dict[str, object]) -> str:
    summary = _selection_summary_from_payload(payload)
    return f'{message}; {summary}' if summary else message


def _selection_summary_from_payload(payload: dict[str, object]) -> str:
    selection = payload.get('backend_selection')
    if isinstance(selection, dict):
        requested = selection.get('requested_backend')
        effective = selection.get('effective_backend') or selection.get('backend_impl')
        source = selection.get('source')
        fallback = selection.get('fallback_used')
        failure = selection.get('failure_reason')
        diagnostic = selection.get('diagnostic')
    else:
        requested = payload.get('backend_selection_requested')
        effective = payload.get('backend_selection_effective')
        source = payload.get('backend_selection_source')
        fallback = payload.get('backend_selection_fallback_used')
        failure = payload.get('backend_selection_failure_reason')
        diagnostic = payload.get('backend_selection_diagnostic')
    if all(value is None for value in (requested, effective, source, fallback, failure, diagnostic)):
        return ''
    parts = []
    if requested is not None:
        parts.append(f'backend_requested={requested}')
    if effective is not None:
        parts.append(f'backend_effective={effective}')
    if source is not None:
        parts.append(f'backend_source={source}')
    if fallback is not None:
        parts.append(f'backend_fallback={fallback}')
    if failure is not None:
        parts.append(f'backend_failure={failure}')
    if diagnostic is not None:
        parts.append(f'backend_diagnostic={diagnostic}')
    return 'selection: ' + ' '.join(parts)


def _client_for_attach_attempt(client, *, timeout_s: float):
    with_timeout = getattr(client, 'with_timeout', None)
    if callable(with_timeout):
        return with_timeout(timeout_s)
    return client


def _attach_target_unavailable_error(*, attempts: int, timeout_s: float) -> str:
    return (
        'foreground attach timed out: project namespace did not become '
        f'attachable within {timeout_s:.1f}s after successful `ccb` start '
        f'(attempts={attempts})'
    )


def _attach_ping_timeout_error(
    exc: Exception,
    *,
    attempts: int,
    timeout_s: float,
    rpc_timeout_s: float,
) -> str:
    detail = str(exc or '').strip() or type(exc).__name__
    return (
        'foreground attach timed out: ccbd did not respond to ping '
        f'within {timeout_s:.1f}s after successful `ccb` start '
        f'(rpc_timeout={rpc_timeout_s:.1f}s, attempts={attempts}, last_error={detail})'
    )


def _attach_namespace_timeout_error(
    error: str,
    *,
    attempts: int,
    ping_successes: int,
    timeout_s: float,
) -> str:
    detail = str(error or '').strip() or 'project namespace is not attachable'
    return (
        'foreground attach timed out: ccbd is responsive but project namespace '
        f'was not attachable within {timeout_s:.1f}s after successful `ccb` start '
        f'(attempts={attempts}, ping_successes={ping_successes}, last_error={detail})'
    )


def _tmux_list_client_pids(
    tmux_socket_path: str,
    tmux_session_name: str,
    *,
    env: dict[str, str],
) -> tuple[int, ...]:
    probe = subprocess.run(
        _tmux_cmd(tmux_socket_path, 'list-clients', '-t', tmux_session_name, '-F', '#{client_pid}'),
        check=False,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if probe.returncode != 0:
        return ()
    client_pids: list[int] = []
    for line in (probe.stdout or '').splitlines():
        value = line.strip()
        if not value:
            continue
        try:
            client_pids.append(int(value))
        except ValueError:
            continue
    return tuple(client_pids)


def _tmux_client_tty(
    tmux_socket_path: str,
    tmux_session_name: str,
    *,
    client_pid: int,
    env: dict[str, str],
) -> str | None:
    probe = subprocess.run(
        _tmux_cmd(tmux_socket_path, 'list-clients', '-t', tmux_session_name, '-F', '#{client_pid}\t#{client_tty}'),
        check=False,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if probe.returncode != 0:
        return None
    for line in (probe.stdout or '').splitlines():
        pid_text, _sep, tty_text = line.partition('\t')
        try:
            listed_pid = int(pid_text.strip())
        except ValueError:
            continue
        if listed_pid != client_pid:
            continue
        tty = tty_text.strip()
        return tty or None
    return None


def _best_effort_refresh_attached_client(
    tmux_socket_path: str,
    tmux_session_name: str,
    *,
    client_pid: int,
    env: dict[str, str],
) -> None:
    client_tty = _tmux_client_tty(
        tmux_socket_path,
        tmux_session_name,
        client_pid=client_pid,
        env=env,
    )
    if not client_tty:
        return
    try:
        subprocess.run(
            _tmux_cmd(tmux_socket_path, 'refresh-client', '-t', client_tty),
            check=False,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return


def _foreground_attach_client(context: CliContext):
    try:
        return _build_foreground_attach_client(context.paths.ccbd_socket_path)
    except CcbdClientError as exc:
        raise ForegroundAttachError(
            'foreground attach failed: ccbd client is unavailable '
            f'after successful `ccb` start: {exc}'
        ) from exc


def _build_foreground_attach_client(socket_path):
    return CcbdClient(socket_path, timeout_s=FOREGROUND_ATTACH_RPC_TIMEOUT_S)


def _attach_env() -> dict[str, str]:
    env = tmux_compatible_env()
    env.pop('TMUX', None)
    env.pop('TMUX_PANE', None)
    return env


def _tmux_cmd(tmux_socket_path: str, *args: str) -> list[str]:
    return [*tmux_base(socket_path=tmux_socket_path), *args]


def _build_rmux_attach_backend(
    *,
    namespace_id: str,
    session_name: str | None = None,
    ipc_kind: str = 'named_pipe',
    ipc_ref: str | None,
):
    socket_path = ipc_ref if ipc_ref and _looks_like_path_ref(ipc_ref) else None
    namespace = str(ipc_ref or '').strip() if ipc_kind == 'socket_name' else ''
    return RmuxBackend(namespace=namespace or session_name or namespace_id, socket_path=socket_path)


def _payload_backend_impl(payload: dict[str, object]) -> str:
    namespace_ref = _payload_namespace_ref(payload)
    return str(
        payload.get('namespace_backend_impl')
        or namespace_ref.get('backend_impl')
        or 'tmux'
    ).strip().lower() or 'tmux'


def _payload_namespace_id(payload: dict[str, object]) -> str:
    namespace_ref = _payload_namespace_ref(payload)
    return str(
        payload.get('namespace_id')
        or namespace_ref.get('namespace_id')
        or payload.get('project_id')
        or payload.get('namespace_session_name')
        or namespace_ref.get('session_name')
        or payload.get('namespace_tmux_session_name')
        or ''
    ).strip()


def _payload_namespace_session_name(payload: dict[str, object]) -> str:
    namespace_ref = _payload_namespace_ref(payload)
    return str(
        payload.get('namespace_session_name')
        or namespace_ref.get('session_name')
        or payload.get('namespace_tmux_session_name')
        or ''
    ).strip()


def _payload_namespace_ipc_kind(payload: dict[str, object], *, default: str = 'unix_socket') -> str:
    namespace_ref = _payload_namespace_ref(payload)
    return str(payload.get('namespace_ipc_kind') or namespace_ref.get('ipc_kind') or default).strip() or default


def _payload_namespace_ipc_ref(payload: dict[str, object]) -> str:
    namespace_ref = _payload_namespace_ref(payload)
    ref = str(payload.get('namespace_ipc_ref') or namespace_ref.get('ipc_ref') or '').strip()
    if ref:
        return ref
    if _payload_namespace_ipc_kind(payload, default='unix_socket') == 'named_pipe':
        return _payload_namespace_id(payload)
    return _payload_namespace_tmux_socket_path(payload)


def _payload_namespace_tmux_socket_path(payload: dict[str, object]) -> str:
    return str(payload.get('namespace_tmux_socket_path') or '').strip()


def _payload_namespace_ref(payload: dict[str, object]) -> dict[str, object]:
    namespace_ref = payload.get('namespace_ref')
    return dict(namespace_ref) if isinstance(namespace_ref, dict) else {}


def _looks_like_path_ref(value: str) -> bool:
    return '/' in value or '\\' in value


def _tmux_has_session(tmux_socket_path: str, tmux_session_name: str, *, env: dict[str, str]) -> bool:
    probe = subprocess.run(
        _tmux_cmd(tmux_socket_path, 'has-session', '-t', tmux_session_name),
        check=False,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return probe.returncode == 0


def _tmux_select_window(tmux_socket_path: str, target: str, *, env: dict[str, str]) -> bool:
    probe = subprocess.run(
        _tmux_cmd(tmux_socket_path, 'select-window', '-t', target),
        check=False,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return probe.returncode == 0


__all__ = [
    'ForegroundAttachError',
    'ForegroundAttachSummary',
    'attach_started_project_namespace',
]
