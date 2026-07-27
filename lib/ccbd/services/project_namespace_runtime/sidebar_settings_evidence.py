from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from ccbd.services.project_namespace_pane import ProjectNamespacePaneRecord


def classify_sidebar_settings_pane_evidence(
    pane: ProjectNamespacePaneRecord | None,
    *,
    expected_helper_id: str | None,
    target_pane_id: str | None = None,
) -> dict[str, Any]:
    expected = _clean(expected_helper_id)
    target = _clean(target_pane_id)
    pane_detail = _pane_detail(pane, expected_helper_id=expected)

    if pane is None:
        return _blocked(
            pane_detail,
            'pane_target_missing',
            f'sidebar pane target {target or "<unknown>"} was not found',
        )

    actual_pane_id = _clean(pane.pane_id)
    if target and actual_pane_id != target:
        return _blocked(
            pane_detail,
            'pane_target_mismatch',
            f'sidebar pane target mismatch: expected {target}, got {actual_pane_id or "<missing>"}',
        )

    if not bool(pane.alive):
        return _blocked(
            pane_detail,
            'pane_not_alive',
            f'sidebar pane target {actual_pane_id or target or "<unknown>"} is not alive',
        )

    role = _clean(pane.role)
    if role is None:
        return _blocked(pane_detail, 'pane_role_missing', 'sidebar pane is missing @ccb_role')
    if role != 'sidebar':
        return _blocked(
            pane_detail,
            'pane_role_mismatch',
            f'sidebar pane target has @ccb_role={role}, expected sidebar',
        )

    if expected is None:
        return _blocked(
            pane_detail,
            'expected_helper_missing',
            'expected sidebar helper fingerprint is unavailable',
        )

    current = _clean(pane.sidebar_helper_id)
    if current is None:
        return _blocked(
            pane_detail,
            'sidebar_helper_missing',
            'sidebar pane is missing @ccb_sidebar_helper_id',
        )
    if current != expected:
        return _blocked(
            pane_detail,
            'sidebar_helper_mismatch',
            f'sidebar helper fingerprint mismatch: pane has {current}, expected {expected}',
        )

    return {
        'status': 'pass',
        'failure_kind': None,
        'failure_detail': None,
        'pane': pane_detail,
    }


def classify_sidebar_settings_pane_mapping(
    pane: dict[str, Any] | None,
    *,
    expected_helper_id: str | None,
    target_pane_id: str | None = None,
) -> dict[str, Any]:
    return classify_sidebar_settings_pane_evidence(
        _pane_from_mapping(pane),
        expected_helper_id=expected_helper_id,
        target_pane_id=target_pane_id,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Classify sidebar settings pane identity evidence.',
    )
    parser.add_argument(
        '--pane-json',
        type=Path,
        help='JSON file containing a ProjectNamespacePaneRecord-shaped object; stdin is used when omitted.',
    )
    parser.add_argument('--expected-helper-id', required=True)
    parser.add_argument('--target-pane-id')
    parser.add_argument('--output', type=Path, help='Write result JSON to this path.')
    args = parser.parse_args(argv)

    pane = _read_pane_json(args.pane_json)
    result = classify_sidebar_settings_pane_mapping(
        pane,
        expected_helper_id=args.expected_helper_id,
        target_pane_id=args.target_pane_id,
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output is None:
        sys.stdout.write(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding='utf-8')
    return 0


def _blocked(pane: dict[str, Any], failure_kind: str, failure_detail: str) -> dict[str, Any]:
    return {
        'status': 'blocked',
        'failure_kind': failure_kind,
        'failure_detail': failure_detail,
        'pane': pane,
    }


def _pane_detail(
    pane: ProjectNamespacePaneRecord | None,
    *,
    expected_helper_id: str | None,
) -> dict[str, Any]:
    return {
        'pane_id': _clean(getattr(pane, 'pane_id', None)),
        'role': _clean(getattr(pane, 'role', None)),
        'sidebar_helper_id': _clean(getattr(pane, 'sidebar_helper_id', None)),
        'expected_helper_id': expected_helper_id,
        'session_name': _clean(getattr(pane, 'session_name', None)),
        'window_name': _clean(getattr(pane, 'window_name', None)),
        'project_id': _clean(getattr(pane, 'project_id', None)),
        'managed_by': _clean(getattr(pane, 'managed_by', None)),
        'alive': bool(getattr(pane, 'alive', False)) if pane is not None else None,
    }


def _clean(value: object) -> str | None:
    text = str(value or '').strip()
    return text or None


def _read_pane_json(path: Path | None) -> dict[str, Any] | None:
    raw = sys.stdin.read() if path is None else path.read_text(encoding='utf-8')
    data = json.loads(raw)
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError('pane JSON must be an object or null')
    return data


def _pane_from_mapping(data: dict[str, Any] | None) -> ProjectNamespacePaneRecord | None:
    if data is None:
        return None
    fields = ProjectNamespacePaneRecord.__dataclass_fields__.keys()
    values = {'pane_id': ''}
    values.update({field: data[field] for field in fields if field in data})
    return ProjectNamespacePaneRecord(
        **values,
    )


__all__ = [
    'classify_sidebar_settings_pane_evidence',
    'classify_sidebar_settings_pane_mapping',
    'main',
]


if __name__ == '__main__':
    raise SystemExit(main())
