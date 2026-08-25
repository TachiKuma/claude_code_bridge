from __future__ import annotations

import json
from pathlib import Path

from storage.atomic import atomic_write_text

HERDR_HOOK_DIAGNOSTICS_FILENAME = '.ccb-herdr-hook-diagnostics.json'


def filter_herdr_agent_hooks(payload: object) -> tuple[dict[str, object], dict[str, object]]:
    hooks = dict(payload) if isinstance(payload, dict) else {}
    filtered: dict[str, object] = {}
    removed: list[dict[str, object]] = []
    for event_name, raw_groups in hooks.items():
        if not isinstance(raw_groups, list):
            filtered[str(event_name)] = _clone_jsonish(raw_groups)
            continue
        groups: list[object] = []
        for group_index, raw_group in enumerate(raw_groups):
            group, group_removed = _filter_group(
                raw_group,
                event_name=str(event_name),
                group_index=group_index,
            )
            removed.extend(group_removed)
            if group is not None:
                groups.append(group)
        if groups:
            filtered[str(event_name)] = groups
    return filtered, herdr_hook_diagnostics(removed)


def write_herdr_hook_diagnostics(home_root: Path, diagnostics: dict[str, object]) -> Path:
    path = Path(home_root).expanduser() / HERDR_HOOK_DIAGNOSTICS_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, json.dumps(diagnostics, ensure_ascii=False, indent=2) + '\n')
    return path


def herdr_hook_diagnostics(removed: list[dict[str, object]]) -> dict[str, object]:
    return {
        'schema_version': 1,
        'status': 'risk_detected' if removed else 'clear',
        'reason': 'herdr_native_agent_hook_competes_with_ccb_authority' if removed else None,
        'authority': 'source=ccb',
        'seq_policy': 'ccb_monotonic_seq_not_hook_time_ns',
        'removed_hook_count': len(removed),
        'removed_hooks': removed,
    }


def herdr_agent_hook_command(command: object) -> bool:
    normalized = str(command or '').strip().replace('\\', '/').lower()
    if not normalized:
        return False
    if 'herdr-agent-state' in normalized:
        return True
    if 'report_agent_session' in normalized or 'report-agent-session' in normalized:
        return True
    return 'herdr' in normalized and 'agent-state' in normalized


def _filter_group(
    raw_group: object,
    *,
    event_name: str,
    group_index: int,
) -> tuple[object | None, list[dict[str, object]]]:
    if not isinstance(raw_group, dict):
        return _clone_jsonish(raw_group), []
    raw_hooks = raw_group.get('hooks')
    if not isinstance(raw_hooks, list):
        return _clone_jsonish(raw_group), []
    hooks: list[object] = []
    removed: list[dict[str, object]] = []
    for hook_index, raw_hook in enumerate(raw_hooks):
        if _is_herdr_agent_hook(raw_hook):
            removed.append(
                {
                    'event_name': event_name,
                    'group_index': group_index,
                    'hook_index': hook_index,
                    'command_preview': _command_preview(raw_hook),
                }
            )
            continue
        hooks.append(_clone_jsonish(raw_hook))
    if not hooks:
        return None, removed
    group = {key: _clone_jsonish(value) for key, value in raw_group.items() if key != 'hooks'}
    group['hooks'] = hooks
    return group, removed


def _is_herdr_agent_hook(raw_hook: object) -> bool:
    if not isinstance(raw_hook, dict):
        return False
    if str(raw_hook.get('type') or '').strip().lower() != 'command':
        return False
    return herdr_agent_hook_command(raw_hook.get('command'))


def _command_preview(raw_hook: object) -> str:
    command = str(raw_hook.get('command') or '') if isinstance(raw_hook, dict) else ''
    command = ' '.join(command.split())
    return command[:160]


def _clone_jsonish(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _clone_jsonish(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clone_jsonish(item) for item in value]
    return value


__all__ = [
    'HERDR_HOOK_DIAGNOSTICS_FILENAME',
    'filter_herdr_agent_hooks',
    'herdr_agent_hook_command',
    'herdr_hook_diagnostics',
    'write_herdr_hook_diagnostics',
]
