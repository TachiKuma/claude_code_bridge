from __future__ import annotations

from pathlib import Path
from typing import Any


def provider_launch_config_signature(spec) -> dict[str, object]:
    return {
        'provider': str(getattr(spec, 'provider', '') or '').strip().lower(),
        'provider_command_template': str(getattr(spec, 'provider_command_template', '') or ''),
        'runtime_mode': _enum_value(getattr(spec, 'runtime_mode', None)),
        'permission_default': _enum_value(getattr(spec, 'permission_default', None)),
        'model': str(getattr(spec, 'model', '') or ''),
        'thinking': str(getattr(spec, 'thinking', '') or ''),
        'startup_args': tuple(str(value) for value in tuple(getattr(spec, 'startup_args', ()) or ())),
        'env': {str(key): str(value) for key, value in dict(getattr(spec, 'env', {}) or {}).items()},
        'api': _to_record(getattr(spec, 'api', None)),
    }


def restart_bound_config_signature(spec, *, paths=None) -> dict[str, object]:
    return {
        **provider_launch_config_signature(spec),
        'provider_profile': _provider_profile_signature(
            getattr(spec, 'provider_profile', None),
            paths=paths,
        ),
    }


def restart_bound_config_changed_agents(current_config, candidate_config, *, paths=None) -> tuple[str, ...]:
    if candidate_config is None:
        return ()
    current_agents = dict(getattr(current_config, 'agents', {}) or {})
    candidate_agents = dict(getattr(candidate_config, 'agents', {}) or {})
    names: list[str] = []
    for agent_name in sorted(set(current_agents) & set(candidate_agents)):
        current = current_agents[agent_name]
        candidate = candidate_agents[agent_name]
        if restart_bound_config_signature(
            current,
            paths=paths,
        ) != restart_bound_config_signature(candidate, paths=paths):
            names.append(str(agent_name))
    return tuple(names)


def changed_signature_paths(prefix: str, desired: object, actual: object) -> tuple[str, ...]:
    if isinstance(desired, dict) and isinstance(actual, dict):
        changed: list[str] = []
        for key in sorted(set(desired) | set(actual)):
            child_prefix = f'{prefix}.{key}'
            if key not in desired or key not in actual:
                changed.append(child_prefix)
                continue
            changed.extend(changed_signature_paths(child_prefix, desired[key], actual[key]))
        return tuple(changed)
    return () if desired == actual else (prefix,)


def _provider_profile_signature(profile, *, paths) -> dict[str, object]:
    record = _to_record(profile)
    home = record.get('home')
    if home:
        record['home'] = _normalized_profile_home(home, paths=paths)
    return record


def _normalized_profile_home(value: object, *, paths) -> str | None:
    raw = str(value or '').strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute() and paths is not None:
        path = Path(paths.project_root) / path
    try:
        return str(path.resolve())
    except Exception:
        return str(path)


def _to_record(value) -> dict[str, Any]:
    to_record = getattr(value, 'to_record', None)
    if callable(to_record):
        return dict(to_record())
    return dict(value or {}) if isinstance(value, dict) else {}


def _enum_value(value) -> str:
    enum_value = getattr(value, 'value', value)
    return str(enum_value or '')


__all__ = [
    'changed_signature_paths',
    'provider_launch_config_signature',
    'restart_bound_config_changed_agents',
    'restart_bound_config_signature',
]
