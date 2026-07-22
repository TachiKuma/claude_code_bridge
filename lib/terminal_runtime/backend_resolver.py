from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Mapping, TypedDict

MuxBackendName = Literal['tmux', 'rmux', 'auto']
MuxEffectiveBackend = Literal['tmux', 'rmux']
MuxBackendSource = Literal['cli', 'project_config', 'user_config', 'env', 'platform_default']
MuxFailureReason = Literal['route-not-approved', 'rmux-unavailable', 'capability-gap', 'invalid-request']


class MuxBackendSelection(TypedDict):
    backend_family: Literal['tmux-family']
    backend_impl: MuxEffectiveBackend
    requested_backend: MuxBackendName
    effective_backend: MuxEffectiveBackend
    source: MuxBackendSource
    fallback_used: bool
    fallback_reason: str | None
    route_approval_ref: str | None
    capability_report_ref: str | None
    diagnostic: str


class MuxBackendSelectionFailure(TypedDict):
    backend_family: Literal['tmux-family']
    requested_backend: str
    source: MuxBackendSource
    failure_reason: MuxFailureReason
    route_approval_ref: str | None
    capability_report_ref: str | None
    diagnostic: str


@dataclass(frozen=True)
class RmuxRouteApproval:
    approved: bool = False
    ref: str | None = None


@dataclass(frozen=True)
class RmuxCapabilityStatus:
    satisfied: bool = True
    ref: str | None = None


@dataclass(frozen=True)
class RmuxAvailability:
    available: bool = False


class MuxBackendSelectionError(RuntimeError):
    def __init__(self, failure: MuxBackendSelectionFailure) -> None:
        self.failure = failure
        super().__init__(failure['diagnostic'])

    def to_diagnostics(self) -> MuxBackendSelectionFailure:
        return dict(self.failure)  # type: ignore[return-value]


def resolve_mux_backend(
    *,
    cli_backend: object | None = None,
    project_config_backend: object | None = None,
    user_config_backend: object | None = None,
    env: Mapping[str, str] | None = None,
    platform: str | None = None,
    project_root: str | Path | None = None,
    route_approval_reader: Callable[[], RmuxRouteApproval] | None = None,
    rmux_availability_reader: Callable[[], RmuxAvailability] | None = None,
    capability_reader: Callable[[], RmuxCapabilityStatus] | None = None,
) -> MuxBackendSelection:
    env_mapping = os.environ if env is None else env
    requested, source = _requested_backend(
        cli_backend=cli_backend,
        project_config_backend=project_config_backend,
        user_config_backend=user_config_backend,
        env=env_mapping,
    )
    if requested == 'tmux':
        return _selection(
            requested=requested,
            effective='tmux',
            source=source,
            fallback_used=False,
            fallback_reason=None,
            route=RmuxRouteApproval(),
            capability=RmuxCapabilityStatus(),
            diagnostic='mux backend selected: tmux',
        )

    route = (
        route_approval_reader()
        if route_approval_reader is not None
        else default_route_approval_reader(project_root)
    )
    availability = (
        rmux_availability_reader()
        if rmux_availability_reader is not None
        else default_rmux_availability_reader(env_mapping)
    )
    capability = (
        capability_reader()
        if capability_reader is not None
        else default_rmux_capability_reader(project_root)
    )

    if requested == 'rmux':
        failure = _first_rmux_blocker(
            requested=requested,
            source=source,
            route=route,
            availability=availability,
            capability=capability,
        )
        if failure is not None:
            raise MuxBackendSelectionError(failure)
        return _selection(
            requested=requested,
            effective='rmux',
            source=source,
            fallback_used=False,
            fallback_reason=None,
            route=route,
            capability=capability,
            diagnostic='mux backend selected: rmux',
        )

    if _platform_allows_rmux_auto(platform) and route.approved and availability.available and capability.satisfied:
        return _selection(
            requested=requested,
            effective='rmux',
            source=source,
            fallback_used=False,
            fallback_reason=None,
            route=route,
            capability=capability,
            diagnostic='mux backend auto selected rmux',
        )
    reason = _fallback_reason(
        platform=platform,
        route=route,
        availability=availability,
        capability=capability,
    )
    return _selection(
        requested=requested,
        effective='tmux',
        source=source,
        fallback_used=True,
        fallback_reason=reason,
        route=route,
        capability=capability,
        diagnostic=f'mux backend auto fallback to tmux: {reason}',
    )


def selection_diagnostics(
    **kwargs,
) -> MuxBackendSelection | MuxBackendSelectionFailure:
    try:
        return resolve_mux_backend(**kwargs)
    except MuxBackendSelectionError as exc:
        return exc.to_diagnostics()


def default_route_approval_reader(project_root: str | Path | None = None) -> RmuxRouteApproval:
    base = _repo_root(project_root)
    report = (
        base
        / '.codestable'
        / 'features'
        / '2026-07-19-rmux-route-approval'
        / 'approval-report.md'
    )
    try:
        text = report.read_text(encoding='utf-8')
    except OSError:
        return RmuxRouteApproval(False, None)
    data = _load_yaml_mapping(_frontmatter_or_text(text))
    approvals = _mapping(data.get('approvals'))
    approved = _is_approved(approvals.get('rmux-route') or data.get('rmux-route'))
    ref = '.codestable/features/2026-07-19-rmux-route-approval/approval-report.md#rmux-route' if approved else None
    return RmuxRouteApproval(approved, ref)


def default_rmux_availability_reader(env: Mapping[str, str] | None = None) -> RmuxAvailability:
    env_mapping = os.environ if env is None else env
    executable = str(env_mapping.get('CCB_RMUX_BIN') or 'rmux').strip() or 'rmux'
    from shutil import which

    return RmuxAvailability(which(executable) is not None)


def _repo_root(project_root: str | Path | None = None) -> Path:
    current = Path(project_root).expanduser().resolve() if project_root is not None else Path.cwd()
    for path in (current, *current.parents):
        if (path / '.codestable').exists() or (path / '.git').exists():
            return path
    return current


def default_rmux_capability_reader(project_root: str | Path | None = None) -> RmuxCapabilityStatus:
    base = _repo_root(project_root)
    summary = (
        base
        / '.codestable'
        / 'features'
        / '2026-07-19-rmux-route-approval'
        / 'rmux-route-decision-summary.yaml'
    )
    try:
        text = summary.read_text(encoding='utf-8')
    except OSError:
        return RmuxCapabilityStatus(False, None)
    if not _summary_marks_rmux_capable(text):
        return RmuxCapabilityStatus(False, None)
    return RmuxCapabilityStatus(True, _summary_capability_report_ref(text))


def _summary_marks_rmux_capable(text: str) -> bool:
    data = _load_yaml_mapping(text)
    facts = _mapping(data.get('report_facts'))
    parent_handoff = _mapping(data.get('parent_handoff'))
    return bool(
        _is_approved(data.get('decision_status') or data.get('status'))
        and _as_bool(parent_handoff.get('route_approved'))
        and _as_int(facts.get('blocking_gaps_count')) == 0
    )


def _summary_capability_report_ref(text: str) -> str | None:
    data = _load_yaml_mapping(text)
    ref = data.get('capability_report')
    if ref is None:
        return None
    return str(ref).strip() or None


def _frontmatter_or_text(text: str) -> str:
    if not text.startswith('---'):
        return text
    end = text.find('\n---', 3)
    if end == -1:
        return text
    return text[3:end].strip()


def _load_yaml_mapping(text: str) -> dict[str, object]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return _parse_simple_yaml_mapping(text)
    data = yaml.safe_load(text)
    if isinstance(data, dict):
        return data
    return {}


def _parse_simple_yaml_mapping(text: str) -> dict[str, object]:
    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith(('#', '- ')):
            continue
        if ':' not in raw_line:
            continue
        indent = len(raw_line) - len(raw_line.lstrip(' '))
        key, _, raw_value = raw_line.strip().partition(':')
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        value = raw_value.strip()
        if not value:
            child: dict[str, object] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value)
    return root


def _parse_scalar(value: str) -> object:
    text = value.strip().strip('"\'')
    lowered = text.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    try:
        return int(text)
    except ValueError:
        return text


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _is_approved(value: object) -> bool:
    return str(value or '').strip().lower() == 'approved'


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or '').strip().lower() == 'true'


def _as_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    try:
        return int(str(value or '').strip())
    except ValueError:
        return None


def _requested_backend(
    *,
    cli_backend: object | None,
    project_config_backend: object | None,
    user_config_backend: object | None,
    env: Mapping[str, str] | None,
) -> tuple[MuxBackendName, MuxBackendSource]:
    env_mapping = os.environ if env is None else env
    candidates: tuple[tuple[object | None, MuxBackendSource], ...] = (
        (cli_backend, 'cli'),
        (project_config_backend, 'project_config'),
        (user_config_backend, 'user_config'),
        (env_mapping.get('CCB_MUX_BACKEND'), 'env'),
    )
    for raw, source in candidates:
        value = _normalize_backend(raw, source=source)
        if value is not None:
            return value, source
    return 'tmux', 'platform_default'


def _normalize_backend(value: object | None, *, source: MuxBackendSource) -> MuxBackendName | None:
    text = str(value or '').strip().lower()
    if not text:
        return None
    if text not in {'tmux', 'rmux', 'auto'}:
        raise MuxBackendSelectionError(
            _failure(
                requested=text,
                source=source,
                reason='invalid-request',
                route=RmuxRouteApproval(),
                capability=RmuxCapabilityStatus(),
                diagnostic=f'invalid mux backend request: {text}',
            )
        )
    return text  # type: ignore[return-value]


def _first_rmux_blocker(
    *,
    requested: MuxBackendName,
    source: MuxBackendSource,
    route: RmuxRouteApproval,
    availability: RmuxAvailability,
    capability: RmuxCapabilityStatus,
) -> MuxBackendSelectionFailure | None:
    if not route.approved:
        return _failure(
            requested=requested,
            source=source,
            reason='route-not-approved',
            route=route,
            capability=capability,
            diagnostic='rmux backend requested but route approval is missing',
        )
    if not availability.available:
        return _failure(
            requested=requested,
            source=source,
            reason='rmux-unavailable',
            route=route,
            capability=capability,
            diagnostic='rmux backend requested but rmux executable is unavailable',
        )
    if not capability.satisfied:
        return _failure(
            requested=requested,
            source=source,
            reason='capability-gap',
            route=route,
            capability=capability,
            diagnostic='rmux backend requested but required capability is missing',
        )
    return None


def _fallback_reason(
    *,
    platform: str | None,
    route: RmuxRouteApproval,
    availability: RmuxAvailability,
    capability: RmuxCapabilityStatus,
) -> str:
    if not _platform_allows_rmux_auto(platform):
        return 'platform default keeps tmux'
    if not route.approved:
        return 'rmux route approval is missing'
    if not availability.available:
        return 'rmux executable is unavailable'
    if not capability.satisfied:
        return 'required rmux capability is missing'
    return 'rmux auto prerequisites are incomplete'


def _platform_allows_rmux_auto(platform: str | None) -> bool:
    value = (platform or sys.platform or '').strip().lower()
    return value.startswith('win')


def _selection(
    *,
    requested: MuxBackendName,
    effective: MuxEffectiveBackend,
    source: MuxBackendSource,
    fallback_used: bool,
    fallback_reason: str | None,
    route: RmuxRouteApproval,
    capability: RmuxCapabilityStatus,
    diagnostic: str,
) -> MuxBackendSelection:
    return {
        'backend_family': 'tmux-family',
        'backend_impl': effective,
        'requested_backend': requested,
        'effective_backend': effective,
        'source': source,
        'fallback_used': fallback_used,
        'fallback_reason': fallback_reason,
        'route_approval_ref': route.ref,
        'capability_report_ref': capability.ref,
        'diagnostic': diagnostic,
    }


def _failure(
    *,
    requested: str,
    source: MuxBackendSource,
    reason: MuxFailureReason,
    route: RmuxRouteApproval,
    capability: RmuxCapabilityStatus,
    diagnostic: str,
) -> MuxBackendSelectionFailure:
    return {
        'backend_family': 'tmux-family',
        'requested_backend': requested,
        'source': source,
        'failure_reason': reason,
        'route_approval_ref': route.ref,
        'capability_report_ref': capability.ref,
        'diagnostic': diagnostic,
    }


__all__ = [
    'MuxBackendSelection',
    'MuxBackendSelectionError',
    'MuxBackendSelectionFailure',
    'RmuxAvailability',
    'RmuxCapabilityStatus',
    'RmuxRouteApproval',
    'resolve_mux_backend',
    'selection_diagnostics',
]
