from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from provider_backends.pane_log_support.session import session_tmux_identity_lookup
from provider_runtime.session_payload import project_session_payload
from terminal_runtime import get_backend_for_session

from ..home_layout import claude_layout_from_session_data
from .normalization import normalize_session_data
from .lifecycle import attach_pane_log, ensure_pane, update_claude_binding, write_back


@dataclass
class ClaudeProjectSession:
    session_file: Path
    data: dict

    @property
    def terminal(self) -> str:
        return project_session_payload(self.data).terminal

    @property
    def pane_id(self) -> str:
        return project_session_payload(self.data).pane_id or ""

    @property
    def backend_family(self) -> str:
        return project_session_payload(self.data).backend_family or ""

    @property
    def backend_impl(self) -> str:
        return project_session_payload(self.data).backend_impl or ""

    @property
    def pane_ref(self) -> dict[str, object]:
        return dict(project_session_payload(self.data).pane_ref)

    @property
    def namespace_ref(self) -> dict[str, object]:
        return dict(project_session_payload(self.data).namespace_ref)

    @property
    def pane_title_marker(self) -> str:
        return str(self.data.get("pane_title_marker") or "").strip()

    @property
    def claude_session_id(self) -> str:
        return str(self.data.get("claude_session_id") or "").strip()

    @property
    def claude_session_path(self) -> str:
        return str(self.data.get("claude_session_path") or "").strip()

    @property
    def claude_home(self) -> str:
        return str(self.data.get("claude_home") or "").strip()

    @property
    def claude_home_path(self) -> Path | None:
        layout = claude_layout_from_session_data(self.data)
        return layout.home_root if layout is not None else None

    @property
    def claude_projects_root(self) -> str:
        layout = claude_layout_from_session_data(self.data)
        if layout is not None:
            return str(layout.projects_root)
        return str(self.data.get("claude_projects_root") or "").strip()

    @property
    def work_dir(self) -> str:
        return str(self.data.get("work_dir") or self.session_file.parent)

    @property
    def runtime_dir(self) -> Path:
        return Path(self.data.get("runtime_dir") or self.session_file.parent)

    @property
    def start_cmd(self) -> str:
        return str(self.data.get("start_cmd") or "").strip()

    def user_option_lookup(self) -> dict[str, str]:
        return session_tmux_identity_lookup(self.data)

    def backend(self):
        return get_backend_for_session(self.data)

    def _attach_pane_log(self, backend: object, pane_id: str) -> None:
        attach_pane_log(self, backend, pane_id)

    def ensure_pane(self) -> Tuple[bool, str]:
        return ensure_pane(self)

    def update_claude_binding(self, *, session_path: Optional[Path], session_id: Optional[str]) -> None:
        update_claude_binding(self, session_path=session_path, session_id=session_id)

    def _write_back(self) -> None:
        normalize_session_data(self.data)
        write_back(self)


__all__ = ["ClaudeProjectSession"]
