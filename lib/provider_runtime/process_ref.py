from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal, TypedDict

ProcessRefKind = Literal['windows_job_object', 'process_tree', 'legacy_pid']
ProcessRefEvidenceState = Literal['attached', 'observed', 'degraded', 'missing', 'unsupported', 'stale']
ProcessRefSource = Literal['launch', 'health', 'kill', 'recovery', 'diagnostic']


class ProcessRef(TypedDict):
    kind: ProcessRefKind
    evidence_state: ProcessRefEvidenceState
    job_id: str | None
    owner_pid: int | None
    root_pid: int | None
    runtime_pid: int | None
    runtime_generation: int | None
    runtime_root: str | None
    source: ProcessRefSource
    observed_at: str | None


_VALID_KINDS = {'windows_job_object', 'process_tree', 'legacy_pid'}
_VALID_STATES = {'attached', 'observed', 'degraded', 'missing', 'unsupported', 'stale'}
_VALID_SOURCES = {'launch', 'health', 'kill', 'recovery', 'diagnostic'}
_DESTRUCTIVE_STATES = {'attached', 'observed', 'degraded'}


def build_process_ref(
    *,
    runtime=None,
    session=None,
    source: str,
    clock,
    job_id: str | None = None,
    owner_pid: int | None = None,
    root_pid: int | None = None,
    runtime_pid: int | None = None,
    runtime_generation: int | None = None,
    runtime_root: str | None = None,
    os_name: str = os.name,
) -> ProcessRef | None:
    del session
    runtime_pid = _coerce_pid(runtime_pid)
    owner_pid = _coerce_pid(owner_pid)
    root_pid = _coerce_pid(root_pid)
    if runtime is not None:
        runtime_pid = runtime_pid or _coerce_pid(getattr(runtime, 'runtime_pid', None) or getattr(runtime, 'pid', None))
        owner_pid = owner_pid or _coerce_pid(getattr(runtime, 'pid', None) or getattr(runtime, 'runtime_pid', None))
        root_pid = root_pid or runtime_pid
        runtime_generation = _coerce_generation(runtime_generation) or _coerce_generation(
            getattr(runtime, 'runtime_generation', None)
        )
        runtime_root = _normalize_text(runtime_root) or _normalize_text(getattr(runtime, 'runtime_root', None))
    if runtime_pid is None and owner_pid is None and root_pid is None and not _normalize_text(runtime_root):
        return None
    normalized_job_id = _normalize_text(job_id)
    if os_name == 'nt':
        kind: ProcessRefKind = 'windows_job_object' if normalized_job_id else 'process_tree'
        state: ProcessRefEvidenceState = 'attached' if normalized_job_id else 'degraded'
    else:
        kind = 'legacy_pid'
        state = 'observed' if (runtime_pid or owner_pid or root_pid) else 'missing'
    return {
        'kind': kind,
        'evidence_state': state,
        'job_id': normalized_job_id,
        'owner_pid': owner_pid,
        'root_pid': root_pid,
        'runtime_pid': runtime_pid,
        'runtime_generation': _coerce_generation(runtime_generation),
        'runtime_root': _normalize_text(runtime_root),
        'source': _normalize_source(source),
        'observed_at': _normalize_text(clock()),
    }


def process_ref_from_record(value) -> ProcessRef | None:
    if not isinstance(value, dict):
        return None
    kind = str(value.get('kind') or '').strip()
    evidence_state = str(value.get('evidence_state') or '').strip()
    source = str(value.get('source') or '').strip()
    if kind not in _VALID_KINDS:
        return None
    if evidence_state not in _VALID_STATES:
        return None
    if source not in _VALID_SOURCES:
        source = 'diagnostic'
    return {
        'kind': kind,  # type: ignore[typeddict-item]
        'evidence_state': evidence_state,  # type: ignore[typeddict-item]
        'job_id': _normalize_text(value.get('job_id')),
        'owner_pid': _coerce_pid(value.get('owner_pid')),
        'root_pid': _coerce_pid(value.get('root_pid')),
        'runtime_pid': _coerce_pid(value.get('runtime_pid')),
        'runtime_generation': _coerce_generation(value.get('runtime_generation')),
        'runtime_root': _normalize_text(value.get('runtime_root')),
        'source': source,  # type: ignore[typeddict-item]
        'observed_at': _normalize_text(value.get('observed_at')),
    }


def process_ref_allows_destructive_cleanup(
    process_ref,
    *,
    runtime=None,
    project_root=None,
    pid: int | None = None,
) -> bool:
    ref = process_ref_from_record(process_ref)
    if ref is None:
        return False
    if ref['evidence_state'] not in _DESTRUCTIVE_STATES:
        return False
    if ref['runtime_generation'] is None:
        return False
    if pid is not None and not _pid_matches_ref(pid, ref):
        return False
    if runtime is not None and not _runtime_matches_ref(runtime, ref):
        return False
    if project_root is not None and not _project_matches_ref(project_root, ref):
        return False
    return any(ref.get(name) is not None for name in ('owner_pid', 'root_pid', 'runtime_pid'))


def process_ref_health(process_ref) -> str | None:
    ref = process_ref_from_record(process_ref)
    if ref is None:
        return None
    state = ref['evidence_state']
    if state in {'missing', 'stale'}:
        return 'process-evidence-missing'
    if state in {'degraded', 'unsupported'}:
        return 'process-evidence-degraded'
    return None


def process_ref_to_record(process_ref) -> dict[str, Any] | None:
    ref = process_ref_from_record(process_ref)
    return dict(ref) if ref is not None else None


def _runtime_matches_ref(runtime, ref: ProcessRef) -> bool:
    runtime_generation = _coerce_generation(getattr(runtime, 'runtime_generation', None))
    if runtime_generation is None or ref['runtime_generation'] is None:
        return False
    if runtime_generation != ref['runtime_generation']:
        return False
    runtime_root = _normalize_text(getattr(runtime, 'runtime_root', None))
    if runtime_root and ref['runtime_root']:
        if _resolve_path(runtime_root) != _resolve_path(ref['runtime_root']):
            return False
    runtime_pid = _coerce_pid(getattr(runtime, 'runtime_pid', None) or getattr(runtime, 'pid', None))
    return runtime_pid is None or _pid_matches_ref(runtime_pid, ref)


def _pid_matches_ref(pid: int, ref: ProcessRef) -> bool:
    try:
        candidate = int(pid)
    except Exception:
        return False
    return candidate in {
        value
        for value in (ref['owner_pid'], ref['root_pid'], ref['runtime_pid'])
        if value is not None
    }


def _project_matches_ref(project_root, ref: ProcessRef) -> bool:
    runtime_root = _normalize_text(ref.get('runtime_root'))
    if not runtime_root:
        return False
    try:
        _resolve_path(runtime_root).relative_to(_resolve_path(project_root))
        return True
    except Exception:
        return False


def _normalize_source(value: str) -> ProcessRefSource:
    text = str(value or '').strip()
    if text in _VALID_SOURCES:
        return text  # type: ignore[return-value]
    return 'diagnostic'


def _normalize_text(value) -> str | None:
    text = str(value or '').strip()
    return text or None


def _coerce_pid(value) -> int | None:
    try:
        pid = int(value)
    except Exception:
        return None
    return pid if pid > 0 else None


def _coerce_generation(value) -> int | None:
    try:
        generation = int(value)
    except Exception:
        return None
    return generation if generation > 0 else None


def _resolve_path(value) -> Path:
    try:
        return Path(value).expanduser().resolve()
    except Exception:
        return Path(value).expanduser().absolute()


__all__ = [
    'ProcessRef',
    'build_process_ref',
    'process_ref_allows_destructive_cleanup',
    'process_ref_from_record',
    'process_ref_health',
    'process_ref_to_record',
]
