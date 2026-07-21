from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable

from terminal_runtime.layouts import LayoutResult, create_tmux_auto_layout


@dataclass
class TerminalBackendSelection:
    detect_terminal_fn: Callable[[], object | None]
    tmux_backend_factory: Callable[[], object]
    psmux_backend_factory: Callable[[], object] | None = None
    cached_backend: object | None = None

    def get_backend(self, terminal_type: str | None = None) -> object | None:
        if self.cached_backend is not None:
            return self.cached_backend
        selected = _normalize_backend_name(terminal_type or self.detect_terminal_fn())
        if selected == 'tmux':
            self.cached_backend = self.tmux_backend_factory()
        elif selected in {'psmux', 'rmux'} and self.psmux_backend_factory is not None:
            self.cached_backend = self.psmux_backend_factory()
        return self.cached_backend

    def get_backend_for_session(self, session_data: dict) -> object:
        socket_name = str(session_data.get('tmux_socket_name') or '').strip() or None
        socket_path = str(session_data.get('tmux_socket_path') or '').strip() or None
        selected = _normalize_backend_name(
            session_data.get('terminal_backend')
            or session_data.get('terminal')
            or session_data.get('backend_impl')
            or session_data.get('mux_backend')
        )
        if selected in {'psmux', 'rmux'} and self.psmux_backend_factory is not None:
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
