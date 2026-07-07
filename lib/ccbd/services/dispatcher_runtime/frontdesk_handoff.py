from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from ccbd.api_models import JobRecord, JobStatus
from completion.models import CompletionConfidence, CompletionDecision, CompletionStatus
from storage.atomic import atomic_write_json, atomic_write_text

from .records import append_event

_PLAN_SLUG_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
_IMPLEMENTATION_VERB_RE = re.compile(
    r'\b('
    r'add|build|change|create|delete|edit|fix|generate|implement|modify|patch|'
    r'run|test|update|verify|write'
    r')\b',
    re.IGNORECASE,
)
_PROJECT_ARTIFACT_RE = re.compile(
    r'(?i)'
    r'('
    r'\b(?:artifact|build|cli|code|config|doc|docs|documentation|file|files|'
    r'implementation|module|package|script|source|test|tests)\b'
    r'|(?:^|[\s`"\'])[\w./-]+/[\w./-]+\.[A-Za-z0-9]{1,12}\b'
    r'|\b(?:README|AGENTS|pyproject\.toml|package\.json|setup\.py)\b'
    r')'
)


def maybe_start_frontdesk_handoff(dispatcher, terminal: JobRecord, decision: CompletionDecision) -> dict[str, object] | None:
    if terminal.agent_name != 'frontdesk':
        return None
    if terminal.status is not JobStatus.COMPLETED or not decision.terminal:
        return None
    if str(getattr(terminal.request, 'message_type', '') or '') != 'ask':
        return None
    reply = decision.reply or ''
    missing = _frontdesk_intake_missing_fields(reply)
    if missing:
        return None

    marker_path = _marker_path(dispatcher, terminal.job_id)
    if marker_path.exists():
        return _load_marker(marker_path)

    plan = _resolve_handoff_plan(dispatcher)
    if plan['status'] != 'ok':
        payload = {
            'schema_version': 1,
            'record_type': 'ccb_frontdesk_auto_handoff',
            'status': 'blocked',
            'job_id': terminal.job_id,
            'agent_name': terminal.agent_name,
            'project_root': str(dispatcher._layout.project_root),
            'reason': 'frontdesk_auto_handoff_requires_plan_slug',
            'plan_resolution': plan['reason'],
            'existing_plan_slugs': plan['existing_plan_slugs'],
            'hint': 'create exactly one docs/plantree/plans/<slug> plan or submit through a plan-aware intake surface',
            'recorded_at': dispatcher._clock(),
        }
        if not _claim_marker(marker_path, payload):
            return _load_marker(marker_path)
        append_event(
            dispatcher,
            terminal,
            'frontdesk_auto_handoff_blocked',
            {
                'reason': payload['reason'],
                'plan_resolution': plan['reason'],
                'existing_plan_slugs': plan['existing_plan_slugs'],
                'marker_path': str(marker_path),
            },
            timestamp=str(payload['recorded_at']),
        )
        return payload

    plan_slug = str(plan['plan_slug'])
    command = _handoff_command(dispatcher, reply, plan_slug=plan_slug)
    log_dir = marker_path.parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / f'{terminal.job_id}.stdout.log'
    stderr_path = log_dir / f'{terminal.job_id}.stderr.log'
    starter = {
        'schema_version': 1,
        'record_type': 'ccb_frontdesk_auto_handoff',
        'status': 'starting',
        'job_id': terminal.job_id,
        'agent_name': terminal.agent_name,
        'project_root': str(dispatcher._layout.project_root),
        'plan_slug': plan_slug,
        'command': command,
        'stdout_path': str(stdout_path),
        'stderr_path': str(stderr_path),
    }
    if not _claim_marker(marker_path, starter):
        return _load_marker(marker_path)

    try:
        env = dict(os.environ)
        env['PYTHONUNBUFFERED'] = '1'
        with open(stdout_path, 'ab') as stdout, open(stderr_path, 'ab') as stderr:
            process = subprocess.Popen(
                command,
                cwd=str(dispatcher._layout.project_root),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
    except Exception as exc:
        payload = {
            **starter,
            'status': 'failed',
            'reason': 'frontdesk_auto_handoff_spawn_failed',
            'error': str(exc),
            'recorded_at': dispatcher._clock(),
        }
        atomic_write_json(marker_path, payload)
        append_event(
            dispatcher,
            terminal,
            'frontdesk_auto_handoff_failed',
            {
                'reason': payload['reason'],
                'marker_path': str(marker_path),
                'error': str(exc),
            },
            timestamp=str(payload['recorded_at']),
        )
        return payload

    payload = {
        **starter,
        'status': 'started',
        'pid': process.pid,
        'recorded_at': dispatcher._clock(),
    }
    atomic_write_json(marker_path, payload)
    append_event(
        dispatcher,
        terminal,
        'frontdesk_auto_handoff_started',
        {
            'marker_path': str(marker_path),
            'pid': process.pid,
            'stdout_path': str(stdout_path),
            'stderr_path': str(stderr_path),
        },
        timestamp=str(payload['recorded_at']),
    )
    return payload


def enforce_frontdesk_boundary(
    dispatcher,
    current: JobRecord,
    decision: CompletionDecision,
    *,
    finished_at: str,
) -> CompletionDecision:
    if current.agent_name != 'frontdesk':
        return decision
    if str(getattr(current.request, 'message_type', '') or '') != 'ask':
        return decision
    if not decision.terminal or decision.status is not CompletionStatus.COMPLETED:
        return decision
    reply = decision.reply or ''
    if not _frontdesk_intake_missing_fields(reply):
        return decision
    request_body = str(getattr(current.request, 'body', '') or '')
    if not _frontdesk_request_requires_planner_handoff(request_body):
        return decision
    reason = 'frontdesk_direct_implementation_boundary_violation'
    marker_path = _boundary_marker_path(dispatcher, current.job_id)
    payload = {
        'schema_version': 1,
        'record_type': 'ccb_frontdesk_boundary_violation',
        'status': 'blocked',
        'job_id': current.job_id,
        'agent_name': current.agent_name,
        'project_root': str(dispatcher._layout.project_root),
        'reason': reason,
        'required_action': 'return_intake_evidence_for_planner_handoff',
        'request_preview': request_body.strip()[:500],
        'reply_preview': reply.strip()[:500],
        'missing_intake_fields': _frontdesk_intake_missing_fields(reply),
        'recorded_at': finished_at,
    }
    atomic_write_json(marker_path, payload)
    append_event(
        dispatcher,
        current,
        'frontdesk_boundary_violation',
        {**payload, 'marker_path': str(marker_path)},
        timestamp=finished_at,
    )
    diagnostics = dict(decision.diagnostics)
    diagnostics.update(
        {
            'frontdesk_boundary_violation': True,
            'boundary_marker_path': str(marker_path),
            'required_action': payload['required_action'],
            'original_status': decision.status.value,
            'missing_intake_fields': payload['missing_intake_fields'],
        }
    )
    return CompletionDecision(
        terminal=True,
        status=CompletionStatus.FAILED,
        reason=reason,
        confidence=CompletionConfidence.EXACT,
        reply=(
            'Frontdesk boundary violation: implementation-like user requests must '
            'be returned as Intake Evidence or Blocked Evidence for controlled '
            'planner handoff; frontdesk must not directly implement project artifacts.'
        ),
        anchor_seen=decision.anchor_seen,
        reply_started=decision.reply_started,
        reply_stable=decision.reply_stable,
        provider_turn_ref=decision.provider_turn_ref,
        source_cursor=decision.source_cursor,
        finished_at=finished_at,
        diagnostics=diagnostics,
    )


def _frontdesk_request_requires_planner_handoff(text: str) -> bool:
    return bool(_IMPLEMENTATION_VERB_RE.search(text or '') and _PROJECT_ARTIFACT_RE.search(text or ''))


def _boundary_marker_path(dispatcher, job_id: str) -> Path:
    path = Path(dispatcher._layout.project_root) / '.ccb' / 'runtime' / 'frontdesk-boundary' / f'{job_id}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _handoff_command(dispatcher, reply: str, *, plan_slug: str) -> list[str]:
    source_root = Path(__file__).resolve().parents[4]
    encoded = base64.b64encode(reply.encode('utf-8')).decode('ascii')
    return [
        sys.executable,
        str(source_root / 'ccb.py'),
        '--project',
        str(dispatcher._layout.project_root),
        'frontdesk',
        'forward-planner',
        '--intake-base64',
        encoded,
        '--plan',
        plan_slug,
        '--json',
    ]


def _resolve_handoff_plan(dispatcher) -> dict[str, object]:
    plans_dir = Path(dispatcher._layout.project_root) / 'docs' / 'plantree' / 'plans'
    slugs = []
    if plans_dir.is_dir():
        slugs = sorted(
            path.name
            for path in plans_dir.iterdir()
            if path.is_dir() and _PLAN_SLUG_RE.match(path.name)
        )
    if len(slugs) == 1:
        return {
            'status': 'ok',
            'plan_slug': slugs[0],
            'reason': 'single_plan_root',
            'existing_plan_slugs': slugs,
        }
    if not slugs:
        slug = _default_plan_slug()
        _bootstrap_plan_root(Path(dispatcher._layout.project_root), slug)
        return {
            'status': 'ok',
            'plan_slug': slug,
            'reason': 'script_bootstrap_default_plan',
            'existing_plan_slugs': [],
            'created_plan_root': str(plans_dir / slug),
        }
    return {
        'status': 'blocked',
        'plan_slug': None,
        'reason': 'multiple_plan_roots',
        'existing_plan_slugs': slugs,
    }


def _default_plan_slug() -> str:
    for env_name in ('CCB_ACTIVE_PLAN', 'CCB_PLAN_SLUG', 'CCB_REAL_PLAN'):
        value = str(os.environ.get(env_name) or '').strip()
        if value and _PLAN_SLUG_RE.match(value):
            return value
    return 'frontdesk-intake'


def _bootstrap_plan_root(project_root: Path, plan_slug: str) -> None:
    plan_root = project_root / 'docs' / 'plantree' / 'plans' / plan_slug
    plan_root.mkdir(parents=True, exist_ok=True)
    readme = plan_root / 'README.md'
    brief = plan_root / 'brief.md'
    if not readme.exists():
        atomic_write_text(readme, f'# {plan_slug}\n\nScript-owned plan root created by frontdesk auto handoff.\n')
    if not brief.exists():
        atomic_write_text(brief, f'# {plan_slug} Brief\n\nCreated for frontdesk-to-planner intake handoff.\n')


def _marker_path(dispatcher, job_id: str) -> Path:
    path = Path(dispatcher._layout.project_root) / '.ccb' / 'runtime' / 'frontdesk-handoff' / f'{job_id}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _claim_marker(path: Path, payload: dict[str, object]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x', encoding='utf-8') as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
        return True
    except FileExistsError:
        return False


def _load_marker(path: Path) -> dict[str, object] | None:
    try:
        payload: Any = json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _has_heading(text: str, heading: str) -> bool:
    escaped = re.escape(heading)
    return bool(re.search(rf'(?mi)^\s*(?:#+\s*)?(?:\*\*)?\s*{escaped}\s*(?:\*\*)?\s*$', text))


def _has_label(text: str, label: str) -> bool:
    escaped = re.escape(label)
    return bool(re.search(rf'(?mi)^\s*(?:[-*]\s*)?(?:\*\*)?\s*{escaped}\s*(?:\*\*)?\s*:', text))


def _has_structured_blocked_evidence(reply: str) -> bool:
    return (
        _has_heading(reply, 'Blocked Evidence')
        and _has_label(reply, 'Requested validation')
        and _has_label(reply, 'Blocker')
        and _has_label(reply, 'Routing recommendation')
        and (
            _has_label(reply, 'Prohibited actions')
            or _has_label(reply, 'Constraints')
            or _has_label(reply, 'Required behavior')
        )
    )


def _frontdesk_intake_missing_fields(reply: str) -> list[str]:
    has_blocked_evidence = _has_structured_blocked_evidence(reply)
    has_request_detail = any(
        (
            _has_heading(reply, 'Macro Task Request'),
            _has_heading(reply, 'User Request'),
            _has_heading(reply, 'User Intent'),
            _has_label(reply, 'Requested validation'),
            _has_label(reply, 'Macro request'),
            _has_label(reply, 'User request'),
            _has_label(reply, 'User intent'),
        )
    )
    has_legacy_contract = _has_heading(reply, 'Execution Contract') or _has_heading(reply, 'Acceptance Criteria')
    has_intake_contract = _has_label(reply, 'Required behavior') and (
        _has_label(reply, 'Scope') or _has_label(reply, 'Constraints')
    )
    has_request_anchor = any(
        (
            _has_heading(reply, 'Macro Task Request'),
            _has_heading(reply, 'User Request'),
            _has_heading(reply, 'Intake Evidence'),
            has_blocked_evidence,
            has_request_detail and (has_legacy_contract or has_intake_contract),
        )
    )
    missing = []
    if not has_request_anchor:
        missing.append('Macro Task Request, User Request, or Intake Evidence')
    if not has_request_detail:
        missing.append('Macro request or User request detail')
    if not has_legacy_contract and not has_intake_contract and not has_blocked_evidence:
        missing.append('Execution Contract, Acceptance Criteria, or Required behavior with Scope/Constraints')
    return missing


__all__ = ['enforce_frontdesk_boundary', 'maybe_start_frontdesk_handoff']
