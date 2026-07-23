from __future__ import annotations

import json
import time
from pathlib import Path

from provider_backends.codex.session_authority import resume_authority_matches
from provider_core.pathing import session_filename_for_agent
from project.identity import normalize_work_dir
from provider_core.runtime_shared import pane_title_marker as build_pane_title_marker
from provider_runtime.session_payload import build_mux_session_payload, merge_provider_payload
from provider_sessions.files import safe_write_session
from rolepacks.runtime_lookup import load_installed_role, tree_digest
from rolepacks.sources import installed_role_metadata


def write_session_file(
    *,
    context,
    spec,
    plan,
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
    session_path = context.paths.ccb_dir / session_filename(spec)
    existing_payload = _read_existing_session_payload(session_path)
    payload = {
        "ccb_session_id": launch_session_id,
        "agent_name": spec.name,
        "ccb_project_id": context.project.project_id,
        "project_root": str(context.project.project_root),
        "project_anchor_path": str(context.paths.ccb_dir),
        "runtime_state_root": str(getattr(context.paths, "runtime_state_root", context.paths.ccb_dir)),
        "runtime_dir": str(runtime_dir),
        "completion_artifact_dir": str(runtime_dir / "completion"),
        "pane_title_marker": pane_title_marker,
        "workspace_path": str(plan.workspace_path),
        "work_dir": str(run_cwd),
        "work_dir_norm": normalize_work_dir(run_cwd),
        "start_dir": str(context.project.project_root),
        **_project_role_launch_evidence(spec),
        "active": True,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "start_cmd": start_cmd,
    }
    payload.update(
        build_mux_session_payload(
            backend_family=backend_family,
            backend_impl=backend_impl,
            pane_id=pane_id,
            session_name=_session_name(context),
            window_name=window_name or _window_name(context),
            namespace_id=_namespace_id(context),
            tmux_socket_name=tmux_socket_name,
            tmux_socket_path=tmux_socket_path,
        )
    )
    payload = merge_provider_payload(payload, provider_payload)
    _merge_existing_session_binding(payload, existing_payload, provider=str(spec.provider or '').strip().lower())
    ok, error = safe_write_session(session_path, json.dumps(payload, ensure_ascii=False, indent=2))
    if not ok:
        raise RuntimeError(error or f"failed to write session file: {session_path}")
    return session_path


def launch_session_id(agent_name: str) -> str:
    import uuid

    return f"ccb-{agent_name}-{uuid.uuid4().hex[:12]}"


def session_filename(spec) -> str:
    return session_filename_for_agent(spec.provider, spec.name)


def pane_title_marker(context, spec) -> str:
    return build_pane_title_marker(
        project_id=str(getattr(context.project, "project_id", "") or ""),
        agent_name=spec.name,
    )


def _read_existing_session_payload(session_path: Path) -> dict[str, object]:
    if not session_path.is_file():
        return {}
    try:
        data = json.loads(session_path.read_text(encoding='utf-8-sig'))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _merge_existing_session_binding(
    payload: dict[str, object],
    existing_payload: dict[str, object],
    *,
    provider: str,
) -> None:
    if provider == 'codex':
        _merge_codex_session_binding(payload, existing_payload)
    elif provider == 'claude':
        _merge_keys(
            payload,
            existing_payload,
            keys=(
                'claude_home',
                'claude_projects_root',
                'claude_session_env_root',
                'claude_session_id',
                'claude_session_path',
                'old_claude_session_id',
                'old_claude_session_path',
            ),
        )


def _merge_codex_session_binding(payload: dict[str, object], existing_payload: dict[str, object]) -> None:
    _merge_keys(
        payload,
        existing_payload,
        keys=(
            'codex_home',
            'codex_session_root',
            'old_codex_session_id',
            'old_codex_session_path',
            'old_updated_at',
        ),
    )
    current_fingerprint = str(payload.get('codex_provider_authority_fingerprint') or '').strip()
    if not resume_authority_matches(existing_payload, current_fingerprint=current_fingerprint):
        return
    _merge_keys(
        payload,
        existing_payload,
        keys=(
            'codex_session_id',
            'codex_session_path',
            'codex_session_authority_fingerprint',
            'updated_at',
        ),
    )


def _merge_keys(payload: dict[str, object], existing_payload: dict[str, object], *, keys: tuple[str, ...]) -> None:
    for key in keys:
        value = existing_payload.get(key)
        if value is None:
            continue
        if key in payload and str(payload.get(key) or '').strip():
            continue
        payload[key] = value


def _session_name(context) -> str | None:
    return _context_path_text(context, 'ccbd_tmux_session_name')


def _window_name(context) -> str | None:
    return _context_path_text(context, 'ccbd_tmux_workspace_window_name')


def _namespace_id(context) -> str | None:
    return _context_path_text(context, 'ccbd_namespace_id') or _session_name(context)


def _context_path_text(context, attr_name: str) -> str | None:
    value = getattr(getattr(context, 'paths', None), attr_name, None)
    text = str(value or '').strip()
    return text or None


def _project_role_launch_evidence(spec) -> dict[str, str]:
    role_id = str(getattr(spec, 'role', '') or '').strip()
    if not role_id:
        return {}
    try:
        role = load_installed_role(role_id)
    except Exception:
        return {'ccb_role_id': role_id}
    if role is None:
        return {'ccb_role_id': role_id}
    metadata = installed_role_metadata(role.id)
    digest = str(metadata.get('digest') or '').strip() or f'sha256:{tree_digest(role.root)}'
    return {
        'ccb_role_id': role.id,
        'ccb_role_version': str(role.version),
        'ccb_role_digest': digest,
    }


__all__ = [
    "launch_session_id",
    "pane_title_marker",
    "session_filename",
    "write_session_file",
]
