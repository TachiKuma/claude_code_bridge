from __future__ import annotations

from dataclasses import dataclass
from storage.paths import PathLayout
from terminal_runtime import PsmuxBackend, RmuxBackend, TmuxBackend, TmuxMuxBackendAdapter
from terminal_runtime.backend_selection import TerminalBackendSelection
from terminal_runtime.backend_resolver import RmuxAvailability, RmuxCapabilityStatus, RmuxRouteApproval
from typing import Callable

from ccbd.system import utc_now

from .backend import build_backend, session_root_pane, session_window_target, window_root_pane
from .controller_state import ProjectNamespaceControllerState, ProjectNamespaceControllerStateMixin
from .destroy import destroy_project_namespace
from .ensure import ensure_project_namespace
from .additive_patch import apply_additive_patch, apply_reload_patch
from .models import ProjectNamespace
from .reflow import reflow_project_workspace
from .records import namespace_from_state
from ..project_namespace_state import ProjectNamespaceEventStore, ProjectNamespaceStateStore
from ..project_namespace_pane import snapshot_project_namespace_panes


@dataclass
class ProjectNamespaceBackendSelectionConfig:
    project_config_backend: str | None = None
    user_config_backend: str | None = None
    project_root: str | None = None


class ProjectNamespaceController(ProjectNamespaceControllerStateMixin):
    def __init__(
        self,
        layout: PathLayout,
        project_id: str,
        *,
        clock=utc_now,
        backend_factory=None,
        project_config_backend: str | None = None,
        user_config_backend: str | None = None,
        project_root: str | None = None,
        state_store: ProjectNamespaceStateStore | None = None,
        event_store: ProjectNamespaceEventStore | None = None,
        layout_version: int = 3,
    ) -> None:
        resolved_project_id = str(project_id or '').strip()
        if not resolved_project_id:
            raise ValueError('project_id cannot be empty')
        resolved_layout_version = int(layout_version)
        if resolved_layout_version <= 0:
            raise ValueError('layout_version must be positive')
        self._backend_selection_config = ProjectNamespaceBackendSelectionConfig(
            project_config_backend=project_config_backend,
            user_config_backend=user_config_backend,
            project_root=project_root,
        )
        self._runtime_state = ProjectNamespaceControllerState(
            layout=layout,
            project_id=resolved_project_id,
            clock=clock,
            backend_factory=backend_factory
            or (
                lambda namespace=None, socket_path=None: default_project_namespace_backend(
                    namespace=namespace,
                    socket_path=socket_path,
                    project_config_backend=self._backend_selection_config.project_config_backend,
                    user_config_backend=self._backend_selection_config.user_config_backend,
                    project_root=self._backend_selection_config.project_root,
                )
            ),
            state_store=state_store or ProjectNamespaceStateStore(layout),
            event_store=event_store or ProjectNamespaceEventStore(layout),
            layout_version=resolved_layout_version,
        )

    def configure_backend_selection(
        self,
        *,
        project_config_backend: str | None = None,
        user_config_backend: str | None = None,
        project_root: str | None = None,
    ) -> None:
        self._backend_selection_config.project_config_backend = project_config_backend
        self._backend_selection_config.user_config_backend = user_config_backend
        if project_root is not None:
            self._backend_selection_config.project_root = str(project_root)

    def load(self) -> ProjectNamespace | None:
        state = self._state_store.load()
        if state is None:
            return None
        return namespace_from_state(state)

    def ensure(
        self,
        *,
        layout_signature: str | None = None,
        topology_plan=None,
        force_recreate: bool = False,
        recreate_reason: str | None = None,
        session_probe_timeout_s: float | None = None,
        terminal_size: tuple[int, int] | None = None,
    ) -> ProjectNamespace:
        return ensure_project_namespace(
            self,
            layout_signature=layout_signature,
            topology_plan=topology_plan,
            force_recreate=force_recreate,
            recreate_reason=recreate_reason,
            session_probe_timeout_s=session_probe_timeout_s,
            terminal_size=terminal_size,
        )

    def destroy(self, *, reason: str, force: bool = False):
        del force
        return destroy_project_namespace(self, reason=reason)

    def reflow_workspace(
        self,
        *,
        layout_signature: str | None = None,
        reason: str | None = None,
        session_probe_timeout_s: float | None = None,
    ) -> ProjectNamespace:
        return reflow_project_workspace(
            self,
            layout_signature=layout_signature,
            reason=reason,
            session_probe_timeout_s=session_probe_timeout_s,
        )

    def apply_additive_patch(
        self,
        *,
        patch_plan: dict[str, object],
        old_topology,
        new_topology,
        timeout_s: float | None = None,
    ):
        return apply_additive_patch(
            self,
            patch_plan=patch_plan,
            old_topology=old_topology,
            new_topology=new_topology,
            timeout_s=timeout_s,
        )

    def apply_reload_patch(
        self,
        *,
        patch_plan: dict[str, object],
        old_topology,
        new_topology,
        timeout_s: float | None = None,
    ):
        return apply_reload_patch(
            self,
            patch_plan=patch_plan,
            old_topology=old_topology,
            new_topology=new_topology,
            timeout_s=timeout_s,
        )

    def root_pane_id(
        self,
        namespace: ProjectNamespace | None = None,
        *,
        timeout_s: float | None = None,
    ) -> str:
        current = namespace or self.load()
        if current is None:
            raise RuntimeError('project namespace is not available')
        backend = build_backend(
            self._backend_factory,
            socket_path=current.tmux_socket_path,
            namespace=current.tmux_session_name,
        )
        workspace_window_name = str(current.workspace_window_name or '').strip()
        pane_records = snapshot_project_namespace_panes(backend)
        if pane_records is not None:
            cmd_panes = [
                pane_id
                for pane_id, record in pane_records.items()
                if record.matches_authoritative_topology(
                    tmux_session_name=current.tmux_session_name,
                    project_id=self._project_id,
                    role='cmd',
                    slot_key='cmd',
                    window_name=workspace_window_name or None,
                    managed_by='ccbd',
                    namespace_epoch=current.namespace_epoch,
                )
            ]
            if len(cmd_panes) == 1:
                return cmd_panes[0]
            if len(cmd_panes) > 1:
                raise RuntimeError('project namespace has multiple authoritative cmd panes')
        if workspace_window_name:
            return window_root_pane(
                backend,
                target_window=session_window_target(current.tmux_session_name, workspace_window_name),
                timeout_s=timeout_s,
            )
        return session_root_pane(backend, current.tmux_session_name, timeout_s=timeout_s)


def default_project_namespace_backend(
    *,
    namespace: str | None = None,
    socket_path: str | None = None,
    project_config_backend: str | None = None,
    user_config_backend: str | None = None,
    project_root: str | None = None,
    route_approval_reader: Callable[[], RmuxRouteApproval] | None = None,
    rmux_availability_reader: Callable[[], RmuxAvailability] | None = None,
    capability_reader: Callable[[], RmuxCapabilityStatus] | None = None,
):
    return TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: TmuxMuxBackendAdapter(TmuxBackend(socket_name=namespace, socket_path=socket_path)),
        psmux_backend_factory=lambda: PsmuxBackend(namespace=namespace, socket_path=socket_path),
        rmux_backend_factory=lambda: RmuxBackend(namespace=namespace, socket_path=socket_path),
        project_config_backend=project_config_backend,
        user_config_backend=user_config_backend,
        project_root=project_root,
        route_approval_reader=route_approval_reader,
        rmux_availability_reader=rmux_availability_reader,
        capability_reader=capability_reader,
    ).get_backend()


__all__ = ['ProjectNamespaceController']
