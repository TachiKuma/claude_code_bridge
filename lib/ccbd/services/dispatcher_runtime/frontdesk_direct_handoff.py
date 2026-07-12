from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Callable

from ccbd.api_models import AcceptedJobReceipt, DeliveryScope, JobStatus, MessageEnvelope, SubmitReceipt
from storage.atomic import atomic_write_json
from storage.locks import file_lock


_ACTIVATION_TASK_RE = re.compile(r'^act-frontdesk-([A-Za-z0-9][A-Za-z0-9_-]{0,79})$')
_REQUEST_ID_RE = re.compile(r'(?mi)^\s*CCB_REQ_ID\s*:\s*`?([^`\n]+?)`?\s*$')


@dataclass(frozen=True)
class _DirectHandoff:
    context: object
    activation_id: str
    activation_path: Path
    activation: dict[str, object]
    intake_sha256: str


def is_frontdesk_submission(request: MessageEnvelope) -> bool:
    return str(request.from_actor or '').strip().lower() == 'frontdesk'


def submit_frontdesk_direct_handoff(
    dispatcher,
    request: MessageEnvelope,
    *,
    accepted_at: str,
    submit: Callable[[], SubmitReceipt],
) -> SubmitReceipt:
    """Admit the one Frontdesk effect and attach mechanical loop authority.

    Frontdesk owns the Planner message.  This function validates and records
    that message without rewriting it, then wakes the existing loop runner.
    """

    _validate_shape(dispatcher, request)
    lock_path = _direct_activation_path(dispatcher, str(request.task_id)).with_suffix('.lock')
    with file_lock(lock_path):
        handoff = _prepare(dispatcher, request)
        existing = _existing_planner_job(dispatcher, request)
        if existing is not None:
            _finalize(dispatcher, handoff, existing)
            return _existing_receipt(existing, accepted_at=accepted_at)

        receipt = submit()
        if len(receipt.jobs) != 1:
            raise dispatcher._dispatch_error('frontdesk planner handoff must create exactly one job')
        job = dispatcher.get(receipt.jobs[0].job_id)
        if job is None:
            raise dispatcher._dispatch_error('frontdesk planner handoff job was not persisted')
        _finalize(dispatcher, handoff, job)
        return receipt


def recover_frontdesk_direct_handoffs(dispatcher) -> tuple[str, ...]:
    recovered: list[str] = []
    latest = {}
    for job in dispatcher._job_store.list_agent('planner'):
        latest[job.job_id] = job
    for job in latest.values():
        request = job.request
        if not _looks_like_direct_handoff(request):
            continue
        try:
            _validate_shape(dispatcher, request)
            with file_lock(_direct_activation_path(dispatcher, str(request.task_id)).with_suffix('.lock')):
                handoff = _prepare(dispatcher, request)
                if _job_import_settled(handoff.context, job.job_id):
                    continue
                _finalize(dispatcher, handoff, job)
            recovered.append(job.job_id)
        except Exception:
            # Startup recovery is conservative. The original ask and intent
            # remain durable, so a later exact retry can recover visibly.
            continue
    return tuple(recovered)


def _prepare(dispatcher, request: MessageEnvelope) -> _DirectHandoff:
    from cli.services.frontdesk_intake import (
        _activation_path,
        _load_existing_activation,
        _new_activation,
        _resolve_plan_slug,
    )

    _validate_shape(dispatcher, request)
    context = _context(dispatcher)
    plan = _resolve_plan_slug(context, SimpleNamespace(plan_slug=None))
    if str(plan.get('status') or '') != 'ok':
        raise dispatcher._dispatch_error(str(plan.get('reason') or 'frontdesk handoff plan resolution failed'))
    plan_slug = str(plan['plan_slug'])
    activation_id = str(request.task_id)
    request_id = activation_id.removeprefix('act-frontdesk-')
    intake_sha256 = hashlib.sha256(request.body.encode('utf-8')).hexdigest()
    intake_bytes = len(request.body.encode('utf-8'))
    activation_path = _activation_path(context, activation_id)
    activation = _load_existing_activation(activation_path)
    if activation is not None:
        if str(activation.get('plan_slug') or '') != plan_slug:
            raise dispatcher._dispatch_error('frontdesk activation plan conflict')
        if str(activation.get('intake_sha256') or '') != intake_sha256:
            raise dispatcher._dispatch_error('frontdesk activation request id conflict')
    else:
        activation = _new_activation(
            context,
            activation_id=activation_id,
            plan_slug=plan_slug,
            request_id=request_id,
            intake_text=request.body,
            intake_sha256=intake_sha256,
            source_request={
                'status': 'ok',
                'source_job_id': request_id,
                'agent_name': 'frontdesk',
                'project_id': request.project_id,
                'to_agent': 'planner',
                'from_actor': 'frontdesk',
                'message_type': 'ask',
                'text': request.body,
                'bytes': intake_bytes,
                'sha256': intake_sha256,
            },
        )
        if activation.get('planner_contract') == 'task_set':
            activation['source_task_id'] = _ensure_source_task(
                context,
                plan_slug=plan_slug,
                request_id=request_id,
            )
        activation['source'] = 'frontdesk_direct_silence_ask'
        activation['status'] = 'direct_ask_pending'
        activation['direct_ask'] = {
            'from_actor': 'frontdesk',
            'target': 'planner',
            'silence': True,
            'task_id': activation_id,
            'body_sha256': intake_sha256,
            'controller_rewrote_body': False,
        }
        atomic_write_json(activation_path, activation)
    return _DirectHandoff(
        context=context,
        activation_id=activation_id,
        activation_path=activation_path,
        activation=activation,
        intake_sha256=intake_sha256,
    )


def _ensure_source_task(context, *, plan_slug: str, request_id: str) -> str:
    from cli.services.plan_tasks import plan_task

    try:
        shown = plan_task(context, SimpleNamespace(action='task-show', task_id=request_id))
    except ValueError:
        plan_task(
            context,
            SimpleNamespace(
                action='task-create',
                plan_slug=plan_slug,
                title=f'Frontdesk intake {request_id}',
                task_id=request_id,
            ),
        )
        return request_id
    task = shown.get('task') if isinstance(shown.get('task'), dict) else {}
    if str(task.get('plan_slug') or '') != plan_slug:
        raise ValueError('frontdesk source task plan authority conflict')
    return request_id


def _validate_shape(dispatcher, request: MessageEnvelope) -> None:
    from cli.services.role_output_import import frontdesk_intake_missing_fields

    if not _looks_like_direct_handoff(request):
        raise dispatcher._dispatch_error(
            'frontdesk may only submit one direct ask --silence to planner with task id act-frontdesk-<request-id>'
        )
    if request.body_artifact:
        raise dispatcher._dispatch_error('frontdesk planner handoff must keep intake evidence inline')
    if request.reply_to:
        raise dispatcher._dispatch_error('frontdesk planner handoff cannot set reply_to')
    if dict(request.route_options or {}):
        raise dispatcher._dispatch_error('frontdesk planner handoff cannot use chain or route options')
    missing = frontdesk_intake_missing_fields(request.body)
    if missing:
        raise dispatcher._dispatch_error(
            f'frontdesk planner handoff is missing required intake fields: {", ".join(missing)}'
        )
    match = _ACTIVATION_TASK_RE.fullmatch(str(request.task_id or ''))
    assert match is not None
    request_id_match = _REQUEST_ID_RE.search(request.body)
    if request_id_match is None:
        raise dispatcher._dispatch_error('frontdesk planner handoff requires CCB_REQ_ID in intake evidence')
    request_id = request_id_match.group(1).strip()
    if request_id != match.group(1):
        raise dispatcher._dispatch_error('frontdesk task id must match the CCB_REQ_ID intake field')


def _looks_like_direct_handoff(request: MessageEnvelope) -> bool:
    return bool(
        is_frontdesk_submission(request)
        and str(request.to_agent or '').strip().lower() == 'planner'
        and str(request.message_type or '').strip().lower() == 'ask'
        and request.delivery_scope is DeliveryScope.SINGLE
        and bool(request.silence_on_success)
        and _ACTIVATION_TASK_RE.fullmatch(str(request.task_id or ''))
    )


def _existing_planner_job(dispatcher, request: MessageEnvelope):
    matches = {}
    for job in dispatcher._job_store.list_agent('planner'):
        if str(job.request.task_id or '') != str(request.task_id or ''):
            continue
        matches[job.job_id] = job
    if not matches:
        return None
    exact = [
        job
        for job in matches.values()
        if job.request.from_actor == request.from_actor
        and job.request.to_agent == request.to_agent
        and job.request.body == request.body
        and bool(job.request.silence_on_success) == bool(request.silence_on_success)
    ]
    if len(exact) != 1 or len(matches) != 1:
        raise dispatcher._dispatch_error('frontdesk activation request id conflict')
    return exact[0]


def _finalize(dispatcher, handoff: _DirectHandoff, job) -> None:
    from cli.services.frontdesk_intake import _start_auto_runner

    activation = dict(handoff.activation)
    ask = activation.get('ask') if isinstance(activation.get('ask'), dict) else {}
    prior_job_id = str(ask.get('job_id') or '').strip()
    if prior_job_id and prior_job_id != job.job_id:
        raise dispatcher._dispatch_error('frontdesk activation already references another planner job')
    activation['ask'] = {
        'target': 'planner',
        'job_id': job.job_id,
        'status': job.status.value,
        'sender': 'frontdesk',
        'silence': True,
    }
    activation['status'] = 'planner_submitted'
    atomic_write_json(handoff.activation_path, activation)
    if _job_import_settled(handoff.context, job.job_id):
        return
    try:
        activation['auto_runner'] = _start_auto_runner(
            handoff.context,
            activation_id=handoff.activation_id,
            wait_job_id=job.job_id,
        )
    except Exception as exc:
        activation['status'] = 'planner_submitted_runner_start_failed'
        activation['runner_start_error'] = f'{type(exc).__name__}: {exc}'
        atomic_write_json(handoff.activation_path, activation)
        raise
    activation['status'] = 'planner_submitted'
    activation.pop('runner_start_error', None)
    atomic_write_json(handoff.activation_path, activation)


def _job_import_settled(context, job_id: str) -> bool:
    path = Path(context.project.project_root) / '.ccb' / 'runtime' / 'role-output-imports.jsonl'
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except FileNotFoundError:
        return False
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        source = record.get('source_job') if isinstance(record.get('source_job'), dict) else {}
        observed_job_id = str(source.get('job_id') or record.get('job_id') or '')
        if observed_job_id != job_id:
            continue
        if str(record.get('status') or '') == 'ok':
            return True
        if (
            str(record.get('action') or '') == 'role_output_import_blocked'
            and str(record.get('reason') or '') == 'terminal_job_not_completed'
        ):
            return True
    return False


def _existing_receipt(job, *, accepted_at: str) -> SubmitReceipt:
    status = job.status
    if status not in {JobStatus.ACCEPTED, JobStatus.QUEUED, JobStatus.RUNNING}:
        status = JobStatus.RUNNING
    return SubmitReceipt(
        accepted_at=accepted_at,
        jobs=(
            AcceptedJobReceipt(
                job_id=job.job_id,
                agent_name=job.agent_name,
                target_kind=job.target_kind,
                target_name=job.target_name,
                provider_instance=job.provider_instance,
                status=status,
                accepted_at=accepted_at,
            ),
        ),
    )


def _context(dispatcher):
    layout = dispatcher._layout
    return SimpleNamespace(
        cwd=layout.project_root,
        paths=layout,
        project=SimpleNamespace(
            cwd=layout.project_root,
            project_root=layout.project_root,
            config_dir=layout.ccb_dir,
            project_id=layout.project_id,
            source='ccbd-frontdesk-direct-ask',
        ),
    )


def _direct_activation_path(dispatcher, activation_id: str) -> Path:
    return (
        Path(dispatcher._layout.project_root)
        / '.ccb'
        / 'runtime'
        / 'loops'
        / 'activations'
        / f'{activation_id}.json'
    )


__all__ = [
    'is_frontdesk_submission',
    'recover_frontdesk_direct_handoffs',
    'submit_frontdesk_direct_handoff',
]
