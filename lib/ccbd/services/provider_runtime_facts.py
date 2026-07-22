from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from provider_core.instance_resolution import named_agent_instance
from provider_core.session_binding_evidence import (
    session_backend_family,
    session_backend_impl,
    session_ccb_session_id,
    session_file,
    session_id,
    session_namespace_ref,
    session_pane_ref,
    session_pane_title_marker,
    session_ref,
    session_runtime_pid,
    session_runtime_ref,
    session_runtime_root,
    session_terminal,
    session_tmux_socket_name,
    session_tmux_socket_path,
)
from provider_runtime.process_ref import build_process_ref, process_ref_from_record


@dataclass(frozen=True)
class ProviderRuntimeFacts:
    runtime_ref: str | None
    session_ref: str | None
    runtime_root: str | None
    runtime_pid: int | None
    terminal_backend: str | None
    backend_family: str | None
    backend_impl: str | None
    pane_ref: dict | None
    namespace_ref: dict | None
    pane_id: str | None
    pane_title_marker: str | None
    pane_state: str | None
    tmux_socket_name: str | None
    tmux_socket_path: str | None
    session_file: str | None
    session_id: str | None
    ccb_session_id: str | None
    process_ref: dict | None = None


def load_provider_session(binding, workspace_path: Path, agent_name: str):
    instance = named_agent_instance(agent_name, primary_agent=str(getattr(binding, "provider", "") or ""))
    try:
        return binding.load_session(workspace_path, instance)
    except Exception:
        return None


def ensure_provider_pane(session) -> tuple[bool, str]:
    ensure = getattr(session, 'ensure_pane', None)
    if not callable(ensure):
        return False, 'ensure_pane not supported'
    try:
        return ensure()
    except Exception as exc:
        return False, str(exc)


def build_provider_runtime_facts(
    session,
    *,
    binding,
    provider: str,
    pane_id_override: str | None = None,
    runtime=None,
    clock=lambda: None,
) -> ProviderRuntimeFacts:
    pane_ref = session_pane_ref(session)
    pane_id = str(pane_id_override or (pane_ref or {}).get('pane_id') or getattr(session, 'pane_id', '') or '').strip() or None
    runtime_pid = session_runtime_pid(session, provider=provider)
    runtime_root = session_runtime_root(session)
    existing_process_ref = process_ref_from_record(getattr(runtime, 'process_ref', None))
    process_ref = existing_process_ref or build_process_ref(
        runtime=runtime,
        session=session,
        source='health',
        clock=clock,
        runtime_pid=runtime_pid,
        runtime_root=runtime_root,
    )
    return ProviderRuntimeFacts(
        runtime_ref=session_runtime_ref(session, pane_id_override=pane_id),
        session_ref=session_ref(
            session,
            session_id_attr=binding.session_id_attr,
            session_path_attr=binding.session_path_attr,
        ),
        runtime_root=runtime_root,
        runtime_pid=runtime_pid,
        terminal_backend=session_terminal(session),
        backend_family=session_backend_family(session),
        backend_impl=session_backend_impl(session),
        pane_ref=pane_ref,
        namespace_ref=session_namespace_ref(session),
        pane_id=pane_id,
        pane_title_marker=session_pane_title_marker(session),
        pane_state='alive' if pane_id else None,
        tmux_socket_name=session_tmux_socket_name(session),
        tmux_socket_path=session_tmux_socket_path(session),
        session_file=session_file(session),
        session_id=session_id(session, session_id_attr=binding.session_id_attr),
        ccb_session_id=session_ccb_session_id(session),
        process_ref=process_ref,
    )


__all__ = [
    'ProviderRuntimeFacts',
    'build_provider_runtime_facts',
    'ensure_provider_pane',
    'load_provider_session',
]
