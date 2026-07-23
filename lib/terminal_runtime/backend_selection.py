from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable, Mapping

from terminal_runtime.backend_resolver import (
    RmuxAvailability,
    RmuxCapabilityStatus,
    RmuxRouteApproval,
    resolve_mux_backend,
)
from terminal_runtime.layouts import LayoutResult, create_tmux_auto_layout


@dataclass
class TerminalBackendSelection:
    detect_terminal_fn: Callable[[], object | None]
    tmux_backend_factory: Callable[[], object]
    psmux_backend_factory: Callable[[], object] | None = None
    rmux_backend_factory: Callable[[], object] | None = None
    project_config_backend: str | None = None
    user_config_backend: str | None = None
    env: Mapping[str, str] | None = None
    platform: str | None = None
    project_root: str | None = None
    route_approval_reader: Callable[[], RmuxRouteApproval] | None = None
    rmux_availability_reader: Callable[[], RmuxAvailability] | None = None
    capability_reader: Callable[[], RmuxCapabilityStatus] | None = None
    cached_backend: object | None = None
    cached_selection: dict[str, object] | None = None
    cached_selection_key: tuple[object, ...] | None = None
    cached_backend_impl: str | None = None

    def get_backend(self, terminal_type: str | None = None) -> object | None:
        selected = self.select_backend(terminal_type)
        effective_backend = str(selected['effective_backend'])
        if self.cached_backend is not None and self.cached_backend_impl == effective_backend:
            return self.cached_backend
        if selected['effective_backend'] == 'tmux':
            self.cached_backend = self.tmux_backend_factory()
        elif selected['effective_backend'] == 'rmux':
            factory = self.rmux_backend_factory or self.psmux_backend_factory
            if factory is not None:
                self.cached_backend = factory()
        self.cached_backend_impl = effective_backend if self.cached_backend is not None else None
        return self.cached_backend

    def select_backend(self, terminal_type: str | None = None) -> dict[str, object]:
        detected_terminal = terminal_type
        if (
            detected_terminal is None
            and self.project_config_backend is None
            and self.user_config_backend is None
            and not _has_mux_env_override(self.env)
        ):
            detected_terminal = self.detect_terminal_fn()
        cache_key = self._selection_cache_key(detected_terminal)
        if self.cached_selection is not None and self.cached_selection_key == cache_key:
            return dict(self.cached_selection)
        selected = resolve_mux_backend(
            cli_backend=_normalize_legacy_backend_name(detected_terminal),
            project_config_backend=self.project_config_backend,
            user_config_backend=self.user_config_backend,
            env=self.env,
            platform=self.platform,
            project_root=self.project_root,
            route_approval_reader=self.route_approval_reader,
            rmux_availability_reader=self.rmux_availability_reader,
            capability_reader=self.capability_reader,
        )
        self.cached_selection = dict(selected)
        self.cached_selection_key = cache_key
        return dict(self.cached_selection)

    def _selection_cache_key(self, terminal_type: object | None) -> tuple[object, ...]:
        env_mapping = os.environ if self.env is None else self.env
        return (
            _normalize_legacy_backend_name(terminal_type),
            self.project_config_backend,
            self.user_config_backend,
            str(env_mapping.get('CCB_MUX_BACKEND') or '').strip(),
            self.platform,
            self.project_root,
        )

    def get_backend_for_session(self, session_data: dict) -> object:
        socket_name = str(session_data.get('tmux_socket_name') or '').strip() or None
        socket_path = str(session_data.get('tmux_socket_path') or '').strip() or None
        selected = _normalize_backend_name(
            session_data.get('backend_impl')
            or session_data.get('mux_backend')
            or session_data.get('terminal_backend')
            or session_data.get('terminal')
        )
        if selected == 'rmux':
            factory = self.rmux_backend_factory or self.psmux_backend_factory
            if factory is not None:
                namespace = str(
                    session_data.get('rmux_namespace')
                    or session_data.get('namespace_id')
                    or socket_name
                    or ''
                ).strip() or None
                try:
                    return factory(namespace=namespace, socket_path=socket_path)
                except TypeError:
                    return factory()
        if selected == 'psmux' and self.psmux_backend_factory is not None:
            namespace = str(
                session_data.get('rmux_namespace')
                or session_data.get('psmux_namespace')
                or socket_name
                or ''
            ).strip() or None
            try:
                return self.psmux_backend_factory(namespace=namespace, socket_path=socket_path)
            except TypeError:
                return self.psmux_backend_factory()
        try:
            return self.tmux_backend_factory(socket_name=socket_name, socket_path=socket_path)
        except TypeError:
            return self.tmux_backend_factory()

    @staticmethod
    def get_pane_id_from_session(session_data: dict) -> str | None:
        return session_data.get('pane_id') or session_data.get('tmux_session')


@dataclass
class TerminalLayoutService:
    tmux_backend_factory: Callable[[], object]
    detached_session_name_fn: Callable[..., str]
    os_getpid_fn: Callable[[], int] = os.getpid
    time_fn: Callable[[], float] = time.time
    env: dict[str, str] | None = None

    def create_auto_layout(
        self,
        providers: list[str],
        *,
        cwd: str,
        root_pane_id: str | None = None,
        tmux_session_name: str | None = None,
        percent: int = 50,
        set_markers: bool = True,
        marker_prefix: str = 'CCB',
    ) -> LayoutResult:
        env = self.env if self.env is not None else os.environ
        return create_tmux_auto_layout(
            providers,
            cwd=cwd,
            backend=self.tmux_backend_factory(),
            root_pane_id=root_pane_id,
            tmux_session_name=tmux_session_name,
            percent=percent,
            set_markers=set_markers,
            marker_prefix=marker_prefix,
            detached_session_name=self.detached_session_name_fn(
                cwd=cwd,
                pid=self.os_getpid_fn(),
                now_ts=self.time_fn(),
            ),
            inside_tmux=bool((env.get('TMUX') or '').strip()),
        )


def _normalize_backend_name(value: object | None) -> str | None:
    text = str(value or '').strip().lower()
    return text or None


def _normalize_legacy_backend_name(value: object | None) -> str | None:
    text = _normalize_backend_name(value)
    if text == 'psmux':
        return 'rmux'
    return text


def _has_mux_env_override(env: Mapping[str, str] | None) -> bool:
    env_mapping = os.environ if env is None else env
    text = str(env_mapping.get('CCB_MUX_BACKEND') or '').strip()
    return bool(text)
