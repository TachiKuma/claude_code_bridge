from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

from agents.models import AgentSpec
from cli.context import CliContext
from cli.models import ParsedStartCommand
from provider_core.contracts import ProviderRuntimeLauncher
from provider_core.runtime_shared import (
    provider_executable as resolve_provider_executable,
    provider_start_parts as resolve_provider_start_parts,
)
from runtime_observability import record_startup_operation, startup_operation_scope
from terminal_runtime import RmuxBackend, TmuxBackend
from terminal_runtime.rmux_backend_runtime.targets import canonical_pane_id as _canonical_rmux_pane_id
from workspace.models import WorkspacePlan

from .provider_hooks import prepare_provider_workspace, provider_workspace_path_for_prepare
from .provider_binding import AgentBinding, resolve_agent_binding
from .role_command_policy import role_command_policy_for_spec, role_command_policy_requires_enforcement
from .runtime_launch_runtime import (
    best_effort_kill_tmux_pane as _best_effort_kill_tmux_pane_impl,
    binding_runtime_alive as _binding_runtime_alive_impl,
    cleanup_stale_tmux_binding as _cleanup_stale_tmux_binding_impl,
    create_detached_tmux_pane as _create_detached_tmux_pane_impl,
    ensure_agent_runtime as _ensure_agent_runtime_impl,
    launch_session_id as _launch_session_id_impl,
    launch_tmux_runtime as _launch_tmux_runtime_impl,
    pane_meets_minimum_size as _pane_meets_minimum_size_impl,
    pane_title_marker as _pane_title_marker_impl,
    runtime_launcher as _runtime_launcher_impl,
    session_filename as _session_filename_impl,
    write_session_file as _write_session_file_impl,
)


@dataclass(frozen=True)
class RuntimeLaunchResult:
    launched: bool
    binding: AgentBinding | None
    timings_ms: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if self.timings_ms is None:
            return
        object.__setattr__(self, 'timings_ms', _clean_runtime_launch_timings(self.timings_ms))


def _runtime_launcher(provider: str) -> ProviderRuntimeLauncher | None:
    return _runtime_launcher_impl(provider)


def ensure_agent_runtime(
    context: CliContext,
    command: ParsedStartCommand,
    spec: AgentSpec,
    plan: WorkspacePlan,
    binding: AgentBinding | None,
    *,
    assigned_pane_id: str | None = None,
    style_index: int = 0,
    tmux_socket_path: str | None = None,
    provider_prepared: bool = False,
    effective_command: ParsedStartCommand | None = None,
    namespace_backend_impl: str | None = None,
    namespace_session_name: str | None = None,
    namespace_window_name: str | None = None,
) -> RuntimeLaunchResult:
    launcher = _runtime_launcher(spec.provider)
    runtime_dir = context.paths.agent_provider_runtime_dir(spec.name, spec.provider)
    launch_command = (
        effective_command
        if effective_command is not None
        else effective_start_command(command, spec)
    )
    if not provider_prepared:
        provider_workspace_path = provider_workspace_path_for_prepare(
            command=launch_command,
            spec=spec,
            plan=plan,
            runtime_dir=runtime_dir,
            launcher=launcher,
        )
        record_startup_operation('provider_prepare_attempt_count')
        with startup_operation_scope('provider_prepare'):
            prepare_provider_workspace(
                layout=context.paths,
                spec=spec,
                workspace_path=provider_workspace_path,
                completion_dir=runtime_dir / 'completion',
                agent_name=spec.name,
                auto_permission=launch_command.auto_permission,
            )
        record_startup_operation('provider_prepare_count')
    return _ensure_agent_runtime_impl(
        context,
        launch_command,
        spec,
        plan,
        binding,
        runtime_launch_result_cls=RuntimeLaunchResult,
        binding_runtime_alive_fn=_binding_runtime_alive,
        provider_executable_fn=_provider_executable,
        cleanup_stale_tmux_binding_fn=_cleanup_stale_tmux_binding,
        launch_tmux_runtime_fn=_launch_tmux_runtime,
        resolve_agent_binding_fn=resolve_agent_binding,
        assigned_pane_id=assigned_pane_id,
        style_index=style_index,
        tmux_socket_path=tmux_socket_path,
        namespace_backend_impl=namespace_backend_impl,
        namespace_session_name=namespace_session_name,
        namespace_window_name=namespace_window_name,
    )


def effective_start_command(command: ParsedStartCommand, spec: AgentSpec) -> ParsedStartCommand:
    """Resolve the single command used for provider preparation and launch."""
    policy = role_command_policy_for_spec(spec)
    if role_command_policy_requires_enforcement(policy) and command.auto_permission:
        return replace(command, auto_permission=False)
    return command


def _launch_tmux_runtime(
    context: CliContext,
    command: ParsedStartCommand,
    spec: AgentSpec,
    plan: WorkspacePlan,
    launcher: ProviderRuntimeLauncher,
    *,
    assigned_pane_id: str | None = None,
    style_index: int = 0,
    tmux_socket_path: str | None = None,
    namespace_backend_impl: str | None = None,
    namespace_session_name: str | None = None,
    namespace_window_name: str | None = None,
) -> dict[str, float]:
    return _launch_tmux_runtime_impl(
        context,
        command,
        spec,
        plan,
        launcher,
        backend_factory=_launch_backend_factory(
            context=context,
            namespace_backend_impl=namespace_backend_impl,
            namespace_session_name=namespace_session_name,
            namespace_window_name=namespace_window_name,
        ),
        pane_title_marker_fn=_pane_title_marker,
        launch_session_id_fn=_launch_session_id,
        create_detached_tmux_pane_fn=_create_detached_tmux_pane,
        pane_meets_minimum_size_fn=_pane_meets_minimum_size,
        best_effort_kill_tmux_pane_fn=_best_effort_kill_tmux_pane,
        write_session_file_fn=_write_session_file,
        assigned_pane_id=assigned_pane_id,
        style_index=style_index,
        tmux_socket_path=tmux_socket_path,
        allow_detached_fallback=tmux_socket_path is None,
    )


def _clean_runtime_launch_timings(value: object) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    timings: dict[str, float] = {}
    for key, raw_value in value.items():
        try:
            parsed = float(raw_value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(parsed) or parsed < 0:
            continue
        timings[str(key)] = parsed
    return timings


def _write_session_file(
    *,
    context: CliContext,
    spec: AgentSpec,
    plan: WorkspacePlan,
    runtime_dir: Path,
    run_cwd: Path,
    pane_id: str,
    tmux_socket_name: str | None,
    tmux_socket_path: str | None,
    pane_title_marker: str,
    start_cmd: str,
    launch_session_id: str,
    provider_payload: dict[str, object],
    backend_family: str = 'tmux-family',
    backend_impl: str = 'tmux',
    window_name: str | None = None,
) -> Path:
    return _write_session_file_impl(
        context=context,
        spec=spec,
        plan=plan,
        runtime_dir=runtime_dir,
        run_cwd=run_cwd,
        pane_id=pane_id,
        tmux_socket_name=tmux_socket_name,
        tmux_socket_path=tmux_socket_path,
        pane_title_marker=pane_title_marker,
        start_cmd=start_cmd,
        launch_session_id=launch_session_id,
        provider_payload=provider_payload,
        backend_family=backend_family,
        backend_impl=backend_impl,
        window_name=window_name,
    )


def _launch_backend_factory(
    *,
    context: CliContext,
    namespace_backend_impl: str | None,
    namespace_session_name: str | None,
    namespace_window_name: str | None,
):
    if str(namespace_backend_impl or '').strip().lower() != 'rmux':
        return TmuxBackend
    namespace = str(namespace_session_name or '').strip() or _namespace_session_from_state(context)
    window = str(namespace_window_name or '').strip() or None

    def factory(*, socket_path: str | None = None):
        return _StringPaneRmuxBackend(namespace=namespace, window_name=window, socket_path=socket_path)

    return factory


def _namespace_session_from_state(context: CliContext) -> str | None:
    path = getattr(getattr(context, 'paths', None), 'ccbd_state_path', None)
    if path is None:
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    for key in ('namespace_session_name', 'tmux_session_name'):
        value = str(payload.get(key) or '').strip()
        if value:
            return value
    namespace_ref = payload.get('namespace_ref')
    if isinstance(namespace_ref, dict):
        value = str(namespace_ref.get('session_name') or '').strip()
        if value:
            return value
    return None


class _StringPaneRmuxBackend:
    backend_family = 'tmux-family'
    backend_impl = 'rmux'

    def __init__(
        self,
        *,
        namespace: str | None = None,
        window_name: str | None = None,
        socket_path: str | None = None,
    ) -> None:
        self._backend = RmuxBackend(namespace=namespace, socket_path=socket_path)
        self.namespace = self._backend.namespace
        self.window_name = str(window_name or '').strip() or None
        self.socket_path = self._backend.socket_path
        self._socket_name = self.namespace
        self._socket_path = self.socket_path

    def respawn_pane(
        self,
        pane_id: str,
        *,
        cmd: str,
        cwd: str | None = None,
        remain_on_exit: bool = True,
    ) -> str | None:
        target = self._pane_ref(pane_id)
        replacement = self._backend.respawn_pane(
            target,
            cmd=cmd,
            cwd=cwd,
            remain_on_exit=remain_on_exit,
        )
        replacement_pane_id = str(replacement or '').strip()
        if replacement_pane_id.startswith('%'):
            return replacement_pane_id
        return str(target.get('pane_id') or pane_id).strip()

    def set_pane_identity(
        self,
        pane_id: str,
        *,
        title: str,
        user_options: dict[str, str],
        border_style: str | None = None,
        active_border_style: str | None = None,
    ) -> None:
        self._backend.set_pane_identity(
            self._pane_ref(pane_id),
            title=title,
            user_options=user_options,
            border_style=border_style,
            active_border_style=active_border_style,
        )

    def set_pane_title(self, pane_id: str, title: str) -> None:
        self._backend.set_pane_title(self._pane_ref(pane_id), title)

    def set_pane_user_option(self, pane_id: str, name: str, value: str) -> None:
        self._backend.set_pane_user_option(self._pane_ref(pane_id), name, value)

    def set_pane_style(
        self,
        pane_id: str,
        *,
        border_style: str | None = None,
        active_border_style: str | None = None,
    ) -> None:
        self._backend.set_pane_style(
            self._pane_ref(pane_id),
            border_style=border_style,
            active_border_style=active_border_style,
        )

    def _pane_ref(self, pane_id: str, *, canonicalize: bool = True) -> dict[str, str | None]:
        pane_text = str(pane_id or '').strip()
        if canonicalize:
            pane_text = self._canonical_pane_id(pane_text)
        window_name = self.window_name
        if pane_text.startswith('%'):
            window_name = None
        return {
            'backend_impl': 'rmux',
            'pane_id': pane_text,
            'session_name': self.namespace,
            'window_name': window_name,
        }

    def _canonical_pane_id(self, pane_id: str) -> str:
        pane_text = str(pane_id or '').strip()
        if not pane_text.startswith('%') or not self.namespace:
            return pane_text
        if self.window_name:
            return pane_text
        pane_ref = self._pane_ref(pane_text, canonicalize=False)
        try:
            resolved = _canonical_rmux_pane_id(self._backend, pane_ref)
        except Exception:
            resolved = pane_text
        if resolved.startswith('%') and resolved != pane_text:
            return resolved
        if not self.window_name:
            return pane_text
        try:
            result = self._backend._run_checked(
                [
                    'display-message',
                    '-p',
                    '-t',
                    f'{self.namespace}:{self.window_name}.{pane_text}',
                    '#{pane_id}',
                ],
                operation='canonicalize_pane',
            )
        except Exception:
            return pane_text
        resolved = ((str(getattr(result, 'stdout', '') or '').splitlines() or [''])[0]).strip()
        return resolved if resolved.startswith('%') else pane_text


def _launch_session_id(agent_name: str) -> str:
    return _launch_session_id_impl(agent_name)


def _session_filename(spec: AgentSpec) -> str:
    return _session_filename_impl(spec)


def _provider_executable(provider: str) -> str:
    return resolve_provider_executable(provider)


def _provider_start_parts(provider: str) -> list[str]:
    return resolve_provider_start_parts(provider)


def _pane_title_marker(context: CliContext, spec: AgentSpec) -> str:
    return _pane_title_marker_impl(context, spec)


def _binding_runtime_alive(binding: AgentBinding) -> bool:
    return _binding_runtime_alive_impl(binding, tmux_backend_cls=TmuxBackend, rmux_backend_cls=RmuxBackend)


def _cleanup_stale_tmux_binding(
    binding: AgentBinding | None,
    *,
    protected_pane_id: str | None = None,
) -> None:
    _cleanup_stale_tmux_binding_impl(
        binding,
        tmux_backend_cls=TmuxBackend,
        rmux_backend_cls=RmuxBackend,
        kill_tmux_pane_fn=_best_effort_kill_tmux_pane,
        protected_pane_id=protected_pane_id,
    )


def _inside_tmux() -> bool:
    return bool((os.environ.get('TMUX') or os.environ.get('TMUX_PANE') or '').strip())


def _prepare_detached_tmux_server(backend: TmuxBackend) -> None:
    from .runtime_launch_runtime import prepare_detached_tmux_server as _prepare_detached_tmux_server_impl

    _prepare_detached_tmux_server_impl(backend)


def _create_detached_tmux_pane(backend: TmuxBackend, *, cmd: str, cwd: Path, session_name: str) -> str:
    return _create_detached_tmux_pane_impl(backend, cmd=cmd, cwd=cwd, session_name=session_name)


def _pane_meets_minimum_size(backend: TmuxBackend, pane_id: str, *, min_width: int = 20, min_height: int = 8) -> bool:
    return _pane_meets_minimum_size_impl(
        backend,
        pane_id,
        min_width=min_width,
        min_height=min_height,
    )


def _best_effort_kill_tmux_pane(backend: TmuxBackend, pane_id: str) -> None:
    _best_effort_kill_tmux_pane_impl(backend, pane_id)
