from __future__ import annotations

from agents.config_loader import CONFIG_SOURCE_PROJECT, CONFIG_SOURCE_USER, load_project_config
from terminal_runtime.backend_resolver import selection_diagnostics


def backend_selection_summary(context) -> dict[str, object]:
    try:
        loaded = load_project_config(context.project.project_root)
    except Exception as exc:
        return {
            'backend_family': 'tmux-family',
            'requested_backend': None,
            'source': None,
            'failure_reason': 'config-invalid',
            'route_approval_ref': None,
            'capability_report_ref': None,
            'diagnostic': f'backend selection config load failed: {exc}',
        }
    project_backend = None
    user_backend = None
    backend = loaded.config.runtime_mux.backend if loaded.config.runtime_mux.explicit_backend else None
    if loaded.source_kind == CONFIG_SOURCE_PROJECT:
        project_backend = backend
    elif loaded.source_kind == CONFIG_SOURCE_USER:
        user_backend = backend
    return dict(
        selection_diagnostics(
            project_config_backend=project_backend,
            user_config_backend=user_backend,
            project_root=context.project.project_root,
        )
    )


__all__ = ['backend_selection_summary']
