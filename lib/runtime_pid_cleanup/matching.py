from __future__ import annotations

import os
import json
from pathlib import Path

from provider_runtime.process_ref import process_ref_allows_destructive_cleanup, process_ref_from_record


def pid_matches_project(
    pid: int,
    *,
    project_root: Path,
    hint_paths: tuple[Path, ...],
    read_proc_path_fn,
    read_proc_cmdline_fn,
    path_within_fn,
    os_name: str = os.name,
) -> bool:
    accelerator_hints = tuple(
        path for path in hint_paths if path.name in {'runtime-accelerator.json', 'runtime-accelerator.legacy'}
    )
    if accelerator_hints:
        from runtime_accelerator.ownership import (
            runtime_accelerator_pid_matches_legacy,
            runtime_accelerator_pid_matches_owner,
        )

        return all(
            runtime_accelerator_pid_matches_owner(
                pid,
                project_root=project_root,
                manifest_path=path,
            )
            if path.name == 'runtime-accelerator.json'
            else runtime_accelerator_pid_matches_legacy(pid, project_root=project_root)
            for path in accelerator_hints
        )
    if os_name == 'nt':
        return _process_ref_matches_project_pid(
            pid,
            project_root=project_root,
            hint_paths=hint_paths,
        ) or _authority_record_matches_project_pid(
            pid,
            project_root=project_root,
            hint_paths=hint_paths,
        ) or (
            _has_control_plane_authority_hint(hint_paths)
            and _pid_matches_hint_paths(
                pid,
                project_root=project_root,
                hint_paths=hint_paths,
                read_proc_path_fn=read_proc_path_fn,
                read_proc_cmdline_fn=read_proc_cmdline_fn,
                path_within_fn=path_within_fn,
            )
        )
    return _pid_matches_hint_paths(
        pid,
        project_root=project_root,
        hint_paths=hint_paths,
        read_proc_path_fn=read_proc_path_fn,
        read_proc_cmdline_fn=read_proc_cmdline_fn,
        path_within_fn=path_within_fn,
    )


def _pid_matches_hint_paths(
    pid: int,
    *,
    project_root: Path,
    hint_paths: tuple[Path, ...],
    read_proc_path_fn,
    read_proc_cmdline_fn,
    path_within_fn,
) -> bool:
    normalized_hints = normalize_hint_roots(project_root, hint_paths=hint_paths)
    cwd_path = read_proc_path_fn(pid, 'cwd')
    if cwd_path is not None:
        for root in normalized_hints:
            if path_within_fn(cwd_path, root):
                return True
    cmdline = read_proc_cmdline_fn(pid)
    if cmdline:
        for candidate in (*normalized_hints, *hint_paths):
            text = str(candidate).strip()
            if text and text in cmdline:
                return True
    return False


def normalize_hint_roots(project_root: Path, *, hint_paths: tuple[Path, ...]) -> list[Path]:
    normalized: list[Path] = []
    for candidate in (project_root, *(path.parent for path in hint_paths)):
        try:
            resolved = candidate.expanduser().resolve()
        except Exception:
            resolved = candidate.expanduser().absolute()
        if resolved not in normalized:
            normalized.append(resolved)
    return normalized


def path_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except Exception:
        return False
    return True


__all__ = ['normalize_hint_roots', 'path_within', 'pid_matches_project']


def _process_ref_matches_project_pid(pid: int, *, project_root: Path, hint_paths: tuple[Path, ...]) -> bool:
    for path in hint_paths:
        record = _load_json_object(path)
        if record is None:
            continue
        process_ref = process_ref_from_record(record.get('process_ref'))
        if process_ref_allows_destructive_cleanup(process_ref, project_root=project_root, pid=pid):
            return True
    return False


def _has_control_plane_authority_hint(hint_paths: tuple[Path, ...]) -> bool:
    authority_names = {'lease.json', 'keeper.json', 'lifecycle.json'}
    for path in hint_paths:
        if path.name in authority_names:
            return True
        if path.parent.name == 'ccbd':
            return True
    return False


def _authority_record_matches_project_pid(pid: int, *, project_root: Path, hint_paths: tuple[Path, ...]) -> bool:
    expected_keys = {
        'lease.json': ('ccbd_pid', 'keeper_pid'),
        'keeper.json': ('keeper_pid',),
        'lifecycle.json': ('owner_pid', 'keeper_pid'),
    }
    for path in hint_paths:
        keys = expected_keys.get(path.name)
        if keys is None or not _path_within_project_ccbd(path, project_root):
            continue
        record = _load_json_object(path)
        if record is None:
            continue
        for key in keys:
            try:
                if int(record.get(key)) == int(pid):
                    return True
            except Exception:
                continue
    return False


def _path_within_project_ccbd(path: Path, project_root: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to((project_root / '.ccb' / 'ccbd').expanduser().resolve())
        return True
    except Exception:
        return False


def _load_json_object(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None
