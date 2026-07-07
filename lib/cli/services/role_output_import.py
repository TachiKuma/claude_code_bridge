from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

from cli.models import ParsedAskCommand
from storage.atomic import atomic_write_json, atomic_write_text

from .ask import submit_ask
from .plan_tasks import plan_task


_VALID_ROUTES = frozenset({'direct_execution', 'needs_detail', 'macro_adjustment_request', 'blocked', 'partial_completion'})
_EXECUTION_ROUTES = frozenset({'direct_execution', 'partial_completion'})
_NEEDS_DETAIL_READINESS = frozenset({'ready', 'needs_clarification'})
_VALID_READINESS = frozenset({'ready', 'needs_clarification', 'blocked', 'not_ready'})
_SEGMENT_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
_SLUG_RE = re.compile(r'[^A-Za-z0-9_-]+')
_PLANNER_CONTRACT_SINGLE_TASK = 'single_task'
_PLANNER_CONTRACT_TASK_SET = 'task_set'
_PLANNER_CONTRACTS = frozenset({_PLANNER_CONTRACT_SINGLE_TASK, _PLANNER_CONTRACT_TASK_SET})
_TASK_SET_INTENT_MARKERS = (
    'route-mix',
    'route mix',
    'l1-l4',
    'l1/l4',
    'multiple tasks',
    'multi-task',
    'task set',
    'bounded task set',
    'route-mix validation',
    'task set validation',
)


def consume_explicit_role_output(context, command, services=None) -> dict[str, object]:
    deps = _deps(services)
    job_id = _normalize_job_id(getattr(command, 'role_job_id', None))
    activation = _activation_for_job(context, job_id)
    return _consume_job(context, command, deps, job_id=job_id, activation=activation)


def consume_activation_role_output(context, command, services=None) -> dict[str, object] | None:
    deps = _deps(services)
    first_pending: dict[str, object] | None = None
    for activation_path, activation in _iter_activation_records(context):
        ask = activation.get('ask') if isinstance(activation.get('ask'), dict) else {}
        job_id = str(ask.get('job_id') or '').strip()
        target = str(ask.get('target') or '').strip()
        if not job_id or _job_settled_for_activation_scan(context, job_id):
            continue
        if target not in {'planner', 'orchestrator', 'task_detailer'}:
            continue
        if _activation_already_satisfied(context, deps, activation=activation, target=target):
            continue
        payload = _consume_job(context, command, deps, job_id=job_id, activation=activation)
        if payload is None:
            continue
        if payload.get('loop_runner_status') == 'pending':
            payload['activation_path'] = str(activation_path)
            if first_pending is None:
                first_pending = payload
            continue
        return payload
    return first_pending


def _consume_job(context, command, deps, *, job_id: str, activation: dict[str, object] | None) -> dict[str, object] | None:
    original_job_id = job_id
    if _job_already_consumed(context, job_id):
        return _already_consumed_payload(context, job_id=job_id)
    snapshot = _load_job_snapshot(context, job_id)
    if snapshot is None:
        return _pending_payload(context, job_id=job_id, agent_name=None, reason='missing_completion_snapshot')
    decision = snapshot.get('latest_decision') if isinstance(snapshot.get('latest_decision'), dict) else {}
    terminal = bool(decision.get('terminal') or (snapshot.get('state') or {}).get('terminal'))
    agent_name = str(snapshot.get('agent_name') or '').strip()
    if not terminal:
        return _pending_payload(context, job_id=job_id, agent_name=agent_name, reason='job_not_terminal')
    status = str(decision.get('status') or '').strip().lower()
    if status != 'completed':
        retry = _retry_successor_for_job(context, job_id, agent_name=agent_name)
        if retry is not None:
            retry_status = str(retry.get('status') or '')
            retry_job_id = str(retry.get('job_id') or '').strip()
            retry_agent_name = str(retry.get('agent_name') or agent_name or '').strip() or None
            if retry_status == 'pending':
                return _pending_payload(
                    context,
                    job_id=retry_job_id or job_id,
                    agent_name=retry_agent_name,
                    reason=str(retry.get('reason') or 'retry_successor_not_terminal'),
                )
            retry_snapshot = retry.get('snapshot')
            if isinstance(retry_snapshot, dict):
                snapshot = retry_snapshot
                job_id = str(snapshot.get('job_id') or retry_job_id or job_id)
                decision = snapshot.get('latest_decision') if isinstance(snapshot.get('latest_decision'), dict) else {}
                terminal = bool(decision.get('terminal') or (snapshot.get('state') or {}).get('terminal'))
                agent_name = str(snapshot.get('agent_name') or agent_name or '').strip()
                if not terminal:
                    return _pending_payload(context, job_id=job_id, agent_name=agent_name, reason='retry_successor_not_terminal')
                status = str(decision.get('status') or '').strip().lower()
    reply = str(decision.get('reply') or '')
    if status != 'completed':
        return _blocked_payload(
            context,
            job_id=job_id,
            agent_name=agent_name,
            reason='terminal_job_not_completed',
            evidence={'terminal_status': status or 'unknown'},
        )
    resolved_reply = _resolve_completion_reply_artifact(context, reply)
    if resolved_reply.get('status') == 'blocked':
        return _blocked_payload(
            context,
            job_id=job_id,
            agent_name=agent_name,
            reason=str(resolved_reply.get('reason') or 'completion_reply_artifact_unavailable'),
            evidence=resolved_reply,
        )
    reply = str(resolved_reply.get('reply') or reply)
    if not reply.strip():
        return _blocked_payload(context, job_id=job_id, agent_name=agent_name, reason='missing_reply')
    normalized_agent = _base_agent_name(agent_name)
    def _with_retry_metadata(payload: dict[str, object]) -> dict[str, object]:
        return _attach_retry_metadata(payload, snapshot=snapshot, original_job_id=original_job_id)

    if normalized_agent == 'frontdesk':
        return _with_retry_metadata(_consume_frontdesk(context, command, deps, snapshot=snapshot, reply=reply))
    if normalized_agent == 'planner':
        return _with_retry_metadata(_consume_planner(context, command, deps, snapshot=snapshot, reply=reply, activation=activation))
    if normalized_agent == 'orchestrator':
        return _with_retry_metadata(_consume_orchestrator(context, command, deps, snapshot=snapshot, reply=reply, activation=activation))
    if normalized_agent == 'task_detailer':
        return _with_retry_metadata(_consume_task_detailer(context, command, deps, snapshot=snapshot, reply=reply, activation=activation))
    return _blocked_payload(
        context,
        job_id=job_id,
        agent_name=agent_name,
        reason='unsupported_role_output_agent',
        evidence={'supported_agents': ['frontdesk', 'planner', 'orchestrator', 'task_detailer']},
    )


def _consume_frontdesk(context, command, deps, *, snapshot: dict[str, object], reply: str) -> dict[str, object]:
    job_id = str(snapshot.get('job_id') or '')
    existing_handoff = _frontdesk_handoff_marker(context, job_id)
    if existing_handoff is not None:
        return _consume_existing_frontdesk_handoff(context, snapshot=snapshot, reply=reply, handoff=existing_handoff)
    missing = _frontdesk_intake_missing_fields(reply)
    if missing:
        return _blocked_payload(
            context,
            job_id=job_id,
            agent_name=str(snapshot.get('agent_name') or ''),
            reason='frontdesk_reply_missing_required_anchors',
            evidence={'missing_fields': missing},
        )
    plan_slug, plan_result = _resolve_or_bootstrap_plan(context, command)
    if plan_slug is None:
        return plan_result
    activation_id = f'act-{uuid4().hex[:12]}'
    planner_contract = planner_contract_for_frontdesk_text(reply)
    activation = {
        'schema_version': 1,
        'record_type': 'ccb_loop_frontdesk_planner_activation',
        'activation_id': activation_id,
        'project_id': context.project.project_id,
        'project_root': str(context.project.project_root),
        'action': 'activate_planner_from_frontdesk',
        'plan_slug': plan_slug,
        'source_job': _job_trace(snapshot, reply),
        'planner_contract': planner_contract,
        'required_next_output': planner_required_output_for_contract(planner_contract),
        'script_write_rules': planner_script_write_rules_for_contract(planner_contract),
    }
    activation_path = _activation_path(context, activation_id)
    atomic_write_json(activation_path, activation)
    summary = deps.submit_ask(
        context,
        ParsedAskCommand(
            project=None,
            target='planner',
            sender='system',
            message=_planner_from_frontdesk_message(activation, reply),
            task_id=activation_id,
            compact=True,
            artifact_request=True,
        ),
    )
    job = _single_job(summary.jobs, target='planner')
    activation['ask'] = {
        'target': 'planner',
        'job_id': str(job['job_id']),
        'status': job.get('status'),
    }
    atomic_write_json(activation_path, activation)
    record = _log_import(
        context,
        {
            'action': 'activated_planner_from_frontdesk',
            'status': 'ok',
            'source_job': _job_trace(snapshot, reply),
            'plan_slug': plan_slug,
            'activation_id': activation_id,
            'activation_path': str(activation_path),
            'ask': activation['ask'],
            'plan_bootstrap': plan_result,
        },
    )
    return _base_payload(
        context,
        loop_runner_status='ok',
        action='activated_planner_from_frontdesk',
        job_id=job_id,
        agent_name=str(snapshot.get('agent_name') or ''),
        extra={
            'plan_slug': plan_slug,
            'activation_id': activation_id,
            'activation_path': str(activation_path),
            'ask': activation['ask'],
            'role_output_import': record,
            'next_activation': 'stop_after_one_activation',
        },
    )


def _consume_existing_frontdesk_handoff(
    context,
    *,
    snapshot: dict[str, object],
    reply: str,
    handoff: dict[str, object],
) -> dict[str, object]:
    job_id = str(snapshot.get('job_id') or '')
    status = str(handoff.get('status') or '').strip().lower()
    if status not in {'starting', 'started'}:
        return _blocked_payload(
            context,
            job_id=job_id,
            agent_name=str(snapshot.get('agent_name') or ''),
            reason='frontdesk_handoff_not_started',
            evidence={
                'handoff_status': status or 'unknown',
                'handoff_reason': handoff.get('reason'),
                'handoff_marker_path': handoff.get('marker_path'),
            },
        )
    result = _frontdesk_handoff_result(handoff)
    record = _log_import(
        context,
        {
            'action': 'frontdesk_handoff_already_started',
            'status': 'ok',
            'source_job': _job_trace(snapshot, reply),
            'handoff': _compact_frontdesk_handoff(handoff),
            'handoff_result': result,
        },
    )
    return _base_payload(
        context,
        loop_runner_status='ok',
        action='frontdesk_handoff_already_started',
        job_id=job_id,
        agent_name=str(snapshot.get('agent_name') or ''),
        extra={
            'handoff': _compact_frontdesk_handoff(handoff),
            'handoff_result': result,
            'role_output_import': record,
            'next_activation': 'stop_after_existing_frontdesk_handoff',
        },
    )


def _frontdesk_handoff_marker(context, job_id: str) -> dict[str, object] | None:
    marker_path = Path(context.project.project_root) / '.ccb' / 'runtime' / 'frontdesk-handoff' / f'{job_id}.json'
    try:
        payload = json.loads(marker_path.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    payload = dict(payload)
    payload['marker_path'] = str(marker_path)
    return payload


def _frontdesk_handoff_result(handoff: dict[str, object]) -> dict[str, object] | None:
    stdout_path = str(handoff.get('stdout_path') or '').strip()
    if not stdout_path:
        return None
    try:
        payload = json.loads(Path(stdout_path).read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _compact_frontdesk_handoff(handoff: dict[str, object]) -> dict[str, object]:
    return {
        key: handoff.get(key)
        for key in (
            'status',
            'job_id',
            'plan_slug',
            'pid',
            'stdout_path',
            'stderr_path',
            'marker_path',
            'recorded_at',
        )
        if handoff.get(key) is not None
    }


def _consume_planner(
    context,
    command,
    deps,
    *,
    snapshot: dict[str, object],
    reply: str,
    activation: dict[str, object] | None,
) -> dict[str, object]:
    job_id = str(snapshot.get('job_id') or '')
    planner_contract = _planner_contract_from_activation(activation, reply=reply)
    parsed = _parse_planner_reply_for_contract(reply, planner_contract=planner_contract)
    if parsed.get('status') != 'ok':
        return _blocked_payload(
            context,
            job_id=job_id,
            agent_name=str(snapshot.get('agent_name') or ''),
            reason=str(parsed.get('reason') or 'planner_reply_invalid'),
            evidence=dict(parsed),
        )
    if parsed.get('planner_contract') == _PLANNER_CONTRACT_TASK_SET:
        return _consume_planner_task_set(
            context,
            command,
            deps,
            snapshot=snapshot,
            reply=reply,
            activation=activation,
            parsed=parsed,
        )
    plan_slug, plan_result = _resolve_or_bootstrap_plan(context, command, activation=activation)
    if plan_slug is None:
        return plan_result
    task_id = _first_optional_text(
        getattr(command, 'task_id', None),
        activation.get('task_id') if activation is not None else None,
    )
    title = str(parsed.get('title') or 'Planner task').strip()
    task_payload = _ensure_task(context, deps, plan_slug=plan_slug, title=title, task_id=task_id, snapshot=snapshot, reply=reply)
    task_id = str(task_payload.get('task_id') or '')
    import_root = _role_import_dir(context, job_id)
    task_packet_path = import_root / 'task_packet.md'
    execution_contract_path = import_root / 'execution_contract.md'
    atomic_write_text(task_packet_path, str(parsed['task_packet']))
    atomic_write_text(execution_contract_path, str(parsed['execution_contract']))
    task_packet_import = deps.plan_task(
        context,
        SimpleNamespace(
            action='task-artifact',
            task_id=task_id,
            artifact_kind='task_packet',
            file_path=str(task_packet_path),
            actor_source='loop_runner_role_output_import',
            actor='loop_runner',
            job_id=job_id,
        ),
    )
    execution_contract_import = deps.plan_task(
        context,
        SimpleNamespace(
            action='task-artifact',
            task_id=task_id,
            artifact_kind='execution_contract',
            file_path=str(execution_contract_path),
            actor_source='loop_runner_role_output_import',
            actor='loop_runner',
            job_id=job_id,
        ),
    )
    ready = deps.plan_task(
        context,
        SimpleNamespace(
            action='task-status',
            task_id=task_id,
            status='ready_for_orchestration',
            next_owner='orchestrator',
            activation_reason='planner_reply_imported',
        ),
    )
    record = _log_import(
        context,
        {
            'action': 'imported_planner_task_authority',
            'status': 'ok',
            'source_job': _job_trace(snapshot, reply),
            'plan_slug': plan_slug,
            'task_id': task_id,
            'created_task': bool(task_payload.get('created')),
            'artifacts': {
                'task_packet': task_packet_import.get('artifact'),
                'execution_contract': execution_contract_import.get('artifact'),
            },
            'status_transition': _compact_plan_payload(ready),
            'plan_bootstrap': plan_result,
        },
    )
    return _base_payload(
        context,
        loop_runner_status='ok',
        action='imported_planner_task_authority',
        job_id=job_id,
        agent_name=str(snapshot.get('agent_name') or ''),
        extra={
            'plan_slug': plan_slug,
            'task_id': task_id,
            'task_status': ready.get('status'),
            'next_owner': ready.get('next_owner'),
            'created_task': bool(task_payload.get('created')),
            'imports': {
                'task_packet': _compact_plan_payload(task_packet_import),
                'execution_contract': _compact_plan_payload(execution_contract_import),
            },
            'role_output_import': record,
            'next_activation': 'orchestrator',
        },
    )


def _consume_planner_task_set(
    context,
    command,
    deps,
    *,
    snapshot: dict[str, object],
    reply: str,
    activation: dict[str, object] | None,
    parsed: dict[str, object],
) -> dict[str, object]:
    job_id = str(snapshot.get('job_id') or '')
    plan_slug, plan_result = _resolve_or_bootstrap_plan(context, command, activation=activation)
    if plan_slug is None:
        return plan_result
    import_root = _role_import_dir(context, job_id)
    imported_tasks: list[dict[str, object]] = []
    for task in tuple(parsed.get('tasks') or ()):
        if not isinstance(task, dict):
            continue
        task_id = str(task.get('task_id') or '')
        title = str(task.get('title') or _task_title_from_packet(str(task.get('task_packet') or ''))).strip()
        task_payload = _ensure_task(
            context,
            deps,
            plan_slug=plan_slug,
            title=title,
            task_id=task_id,
            snapshot=snapshot,
            reply=reply,
        )
        task_id = str(task_payload.get('task_id') or task_id)
        task_import_root = import_root / task_id
        task_packet_path = task_import_root / 'task_packet.md'
        execution_contract_path = task_import_root / 'execution_contract.md'
        atomic_write_text(task_packet_path, str(task['task_packet']))
        atomic_write_text(execution_contract_path, str(task['execution_contract']))
        task_packet_import = deps.plan_task(
            context,
            SimpleNamespace(
                action='task-artifact',
                task_id=task_id,
                artifact_kind='task_packet',
                file_path=str(task_packet_path),
                actor_source='loop_runner_role_output_import',
                actor='loop_runner',
                job_id=job_id,
            ),
        )
        execution_contract_import = deps.plan_task(
            context,
            SimpleNamespace(
                action='task-artifact',
                task_id=task_id,
                artifact_kind='execution_contract',
                file_path=str(execution_contract_path),
                actor_source='loop_runner_role_output_import',
                actor='loop_runner',
                job_id=job_id,
            ),
        )
        ready = deps.plan_task(
            context,
            SimpleNamespace(
                action='task-status',
                task_id=task_id,
                status='ready_for_orchestration',
                next_owner='orchestrator',
                activation_reason='planner_task_set_imported',
            ),
        )
        imported_tasks.append(
            {
                'task_id': task_id,
                'title': title,
                'route': task.get('route'),
                'readiness': task.get('readiness'),
                'created_task': bool(task_payload.get('created')),
                'artifacts': {
                    'task_packet': task_packet_import.get('artifact'),
                    'execution_contract': execution_contract_import.get('artifact'),
                },
                'status_transition': _compact_plan_payload(ready),
            }
        )
    record = _log_import(
        context,
        {
            'action': 'imported_planner_task_set_authority',
            'status': 'ok',
            'source_job': _job_trace(snapshot, reply),
            'planner_contract': _PLANNER_CONTRACT_TASK_SET,
            'plan_slug': plan_slug,
            'task_ids': [task['task_id'] for task in imported_tasks],
            'tasks': imported_tasks,
            'plan_bootstrap': plan_result,
        },
    )
    return _base_payload(
        context,
        loop_runner_status='ok',
        action='imported_planner_task_set_authority',
        job_id=job_id,
        agent_name=str(snapshot.get('agent_name') or ''),
        extra={
            'plan_slug': plan_slug,
            'planner_contract': _PLANNER_CONTRACT_TASK_SET,
            'task_ids': [task['task_id'] for task in imported_tasks],
            'tasks': imported_tasks,
            'task_count': len(imported_tasks),
            'role_output_import': record,
            'next_activation': 'orchestrator',
        },
    )


def _consume_orchestrator(
    context,
    command,
    deps,
    *,
    snapshot: dict[str, object],
    reply: str,
    activation: dict[str, object] | None,
) -> dict[str, object]:
    job_id = str(snapshot.get('job_id') or '')
    task_id = str(getattr(command, 'task_id', None) or '').strip()
    if not task_id and activation is not None:
        task_id = str(activation.get('task_id') or '').strip()
    if not task_id:
        return _blocked_payload(
            context,
            job_id=job_id,
            agent_name=str(snapshot.get('agent_name') or ''),
            reason='orchestrator_import_requires_task_id',
        )
    parsed = _parse_orchestrator_reply(reply)
    if parsed.get('status') != 'ok':
        return _blocked_payload(
            context,
            job_id=job_id,
            agent_name=str(snapshot.get('agent_name') or ''),
            reason=str(parsed.get('reason') or 'orchestrator_reply_invalid'),
            evidence=dict(parsed),
        )
    import_root = _role_import_dir(context, job_id)
    notes_path = import_root / 'orchestration_notes.md'
    atomic_write_text(notes_path, str(parsed['orchestration_notes']))
    imported = deps.plan_task(
        context,
        SimpleNamespace(
            action='task-artifact',
            task_id=task_id,
            artifact_kind='orchestration_notes',
            file_path=str(notes_path),
            route=str(parsed['route']),
            actor_source='loop_runner_role_output_import',
            actor='loop_runner',
            job_id=job_id,
        ),
    )
    record = _log_import(
        context,
        {
            'action': 'imported_orchestration_notes',
            'status': 'ok',
            'source_job': _job_trace(snapshot, reply),
            'task_id': task_id,
            'route': parsed['route'],
            'artifact': imported.get('artifact'),
        },
    )
    return _base_payload(
        context,
        loop_runner_status='ok',
        action='imported_orchestration_notes',
        job_id=job_id,
        agent_name=str(snapshot.get('agent_name') or ''),
        extra={
            'task_id': task_id,
            'task_status': imported.get('status'),
            'next_owner': imported.get('next_owner'),
            'route': parsed['route'],
            'import': _compact_plan_payload(imported),
            'role_output_import': record,
            'next_activation': _next_activation_for_route(str(parsed['route'])),
        },
    )


def _consume_task_detailer(
    context,
    command,
    deps,
    *,
    snapshot: dict[str, object],
    reply: str,
    activation: dict[str, object] | None,
) -> dict[str, object]:
    job_id = str(snapshot.get('job_id') or '')
    task_id = _first_optional_text(
        getattr(command, 'task_id', None),
        activation.get('task_id') if activation is not None else None,
    )
    if not task_id:
        return _blocked_payload(
            context,
            job_id=job_id,
            agent_name=str(snapshot.get('agent_name') or ''),
            reason='task_detailer_import_requires_task_id',
        )
    parsed = _parse_task_detailer_reply(reply)
    if parsed.get('status') != 'ok':
        return _blocked_payload(
            context,
            job_id=job_id,
            agent_name=str(snapshot.get('agent_name') or ''),
            reason=str(parsed.get('reason') or 'task_detailer_reply_invalid'),
            evidence=dict(parsed),
        )
    import_root = _role_import_dir(context, job_id)
    detail_design_path = import_root / 'task-detail-design.md'
    detail_summary_path = import_root / 'brief-update-summary.md'
    detail_packet_path = import_root / 'detail-packet.manifest.json'
    atomic_write_text(detail_design_path, str(parsed['detail_design']))
    atomic_write_text(detail_summary_path, str(parsed['detail_summary']))
    atomic_write_text(detail_packet_path, str(parsed['detail_packet']))
    detail_design_import = deps.plan_task(
        context,
        SimpleNamespace(
            action='task-artifact',
            task_id=task_id,
            artifact_kind='detail_design',
            file_path=str(detail_design_path),
            actor_source='loop_runner_role_output_import',
            actor='loop_runner',
            job_id=job_id,
        ),
    )
    detail_summary_import = deps.plan_task(
        context,
        SimpleNamespace(
            action='task-artifact',
            task_id=task_id,
            artifact_kind='detail_summary',
            file_path=str(detail_summary_path),
            actor_source='loop_runner_role_output_import',
            actor='loop_runner',
            job_id=job_id,
        ),
    )
    detail_packet_import = deps.plan_task(
        context,
        SimpleNamespace(
            action='task-artifact',
            task_id=task_id,
            artifact_kind='detail_packet',
            file_path=str(detail_packet_path),
            actor_source='loop_runner_role_output_import',
            actor='loop_runner',
            job_id=job_id,
        ),
    )
    ready = deps.plan_task(
        context,
        SimpleNamespace(
            action='task-status',
            task_id=task_id,
            status='detail_ready',
            next_owner='planner',
            activation_reason='detail_ready_from_task_detailer',
        ),
    )
    record = _log_import(
        context,
        {
            'action': 'imported_task_detailer_detail_authority',
            'status': 'ok',
            'source_job': _job_trace(snapshot, reply),
            'task_id': task_id,
            'created_task': False,
            'artifacts': {
                'detail_design': detail_design_import.get('artifact'),
                'detail_summary': detail_summary_import.get('artifact'),
                'detail_packet': detail_packet_import.get('artifact'),
            },
            'status_transition': _compact_plan_payload(ready),
        },
    )
    return _base_payload(
        context,
        loop_runner_status='ok',
        action='imported_task_detailer_detail_authority',
        job_id=job_id,
        agent_name=str(snapshot.get('agent_name') or ''),
        extra={
            'task_id': task_id,
            'task_status': ready.get('status'),
            'next_owner': ready.get('next_owner'),
            'created_task': False,
            'imports': {
                'detail_design': _compact_plan_payload(detail_design_import),
                'detail_summary': _compact_plan_payload(detail_summary_import),
                'detail_packet': _compact_plan_payload(detail_packet_import),
            },
            'role_output_import': record,
            'next_activation': 'orchestrator',
        },
    )


def _parse_planner_reply(reply: str) -> dict[str, object]:
    task_packet = _fenced_section(reply, ('task-packet.md', 'task_packet.md'))
    readiness_text = _fenced_section(reply, ('readiness.json',))
    missing = []
    if not task_packet:
        missing.append('task-packet.md fenced section')
    if not readiness_text:
        missing.append('readiness.json fenced section')
    if missing:
        return {'status': 'blocked', 'reason': 'planner_reply_missing_required_sections', 'missing_fields': missing}
    try:
        readiness = json.loads(readiness_text)
    except json.JSONDecodeError as exc:
        return {'status': 'blocked', 'reason': 'planner_readiness_json_invalid', 'error': str(exc)}
    if not isinstance(readiness, dict):
        return {'status': 'blocked', 'reason': 'planner_readiness_json_not_object'}
    readiness_value = str(readiness.get('readiness') or '').strip().lower()
    route = str(readiness.get('route') or '').strip().lower()
    if route not in _VALID_ROUTES:
        return {'status': 'blocked', 'reason': 'unknown_route', 'route': route or None, 'expected_routes': sorted(_VALID_ROUTES)}
    if readiness_value not in _VALID_READINESS:
        return {
            'status': 'blocked',
            'reason': 'unknown_readiness',
            'readiness': readiness_value or 'missing',
            'route': route,
            'expected_readiness': sorted(_VALID_READINESS),
        }
    if route in _EXECUTION_ROUTES and readiness_value != 'ready':
        return {
            'status': 'blocked',
            'reason': 'planner_readiness_not_ready',
            'readiness': readiness_value or 'missing',
            'route': route,
        }
    if route == 'needs_detail' and readiness_value not in _NEEDS_DETAIL_READINESS:
        return {
            'status': 'blocked',
            'reason': 'planner_readiness_incompatible_with_route',
            'readiness': readiness_value or 'missing',
            'route': route,
            'expected_readiness': sorted(_NEEDS_DETAIL_READINESS),
        }
    allowed_paths = _string_list(readiness.get('allowed_paths'))
    verification = _string_list(readiness.get('verification'))
    blockers = _string_list(readiness.get('blockers'))
    missing_fields = []
    if route in _EXECUTION_ROUTES and not allowed_paths:
        missing_fields.append('readiness.allowed_paths')
    if not verification:
        missing_fields.append('readiness.verification')
    if route == 'needs_detail' and readiness_value == 'needs_clarification' and not blockers:
        missing_fields.append('readiness.blockers')
    if missing_fields:
        return {'status': 'blocked', 'reason': 'planner_readiness_missing_required_fields', 'missing_fields': missing_fields}
    invalid_allowed_paths = _invalid_allowed_paths(allowed_paths)
    if invalid_allowed_paths:
        return {
            'status': 'blocked',
            'reason': 'planner_readiness_invalid_allowed_paths',
            'invalid_allowed_paths': invalid_allowed_paths,
        }
    execution_contract = _fenced_section(reply, ('execution-contract.md', 'execution_contract.md'))
    if not execution_contract:
        execution_contract = _normalized_execution_contract(
            route=route,
            allowed_paths=allowed_paths,
            verification=verification,
        )
    title = _task_title_from_packet(task_packet)
    return {
        'status': 'ok',
        'task_packet': task_packet.strip() + '\n',
        'execution_contract': execution_contract.strip() + '\n',
        'readiness': readiness,
        'route': route,
        'allowed_paths': allowed_paths,
        'verification': verification,
        'title': title,
    }


def _parse_planner_reply_for_contract(reply: str, *, planner_contract: str) -> dict[str, object]:
    if planner_contract == _PLANNER_CONTRACT_TASK_SET:
        parsed = _parse_planner_task_set_reply(reply)
        if parsed.get('status') == 'ok':
            return parsed
        evidence = dict(parsed)
        if _has_single_task_planner_sections(reply):
            evidence['single_task_reply_detected'] = True
            evidence['reason'] = 'planner_task_set_required'
            return evidence
        return evidence
    parsed = _parse_planner_reply(reply)
    if parsed.get('status') == 'ok':
        parsed['planner_contract'] = _PLANNER_CONTRACT_SINGLE_TASK
    return parsed


def _parse_planner_task_set_reply(reply: str) -> dict[str, object]:
    task_set_text = _fenced_section(reply, ('task-set.json', 'task_set.json'))
    if not task_set_text:
        return {
            'status': 'blocked',
            'reason': 'planner_task_set_required',
            'missing_fields': ['task-set.json fenced section'],
            'planner_contract': _PLANNER_CONTRACT_TASK_SET,
        }
    try:
        task_set = json.loads(task_set_text)
    except json.JSONDecodeError as exc:
        return {
            'status': 'blocked',
            'reason': 'planner_task_set_json_invalid',
            'error': str(exc),
            'planner_contract': _PLANNER_CONTRACT_TASK_SET,
        }
    if not isinstance(task_set, dict):
        return {
            'status': 'blocked',
            'reason': 'planner_task_set_json_not_object',
            'planner_contract': _PLANNER_CONTRACT_TASK_SET,
        }
    raw_tasks = task_set.get('tasks')
    if not isinstance(raw_tasks, list) or not raw_tasks:
        return {
            'status': 'blocked',
            'reason': 'planner_task_set_missing_tasks',
            'planner_contract': _PLANNER_CONTRACT_TASK_SET,
        }
    if len(raw_tasks) > 12:
        return {
            'status': 'blocked',
            'reason': 'planner_task_set_too_large',
            'task_count': len(raw_tasks),
            'max_tasks': 12,
            'planner_contract': _PLANNER_CONTRACT_TASK_SET,
        }
    tasks: list[dict[str, object]] = []
    seen_task_ids: set[str] = set()
    for index, raw_task in enumerate(raw_tasks):
        parsed = _parse_planner_task_set_item(raw_task, index=index)
        if parsed.get('status') != 'ok':
            return {
                **parsed,
                'planner_contract': _PLANNER_CONTRACT_TASK_SET,
            }
        task_id = str(parsed['task_id'])
        if task_id in seen_task_ids:
            return {
                'status': 'blocked',
                'reason': 'planner_task_set_duplicate_task_id',
                'task_id': task_id,
                'planner_contract': _PLANNER_CONTRACT_TASK_SET,
            }
        seen_task_ids.add(task_id)
        tasks.append(parsed)
    return {
        'status': 'ok',
        'planner_contract': _PLANNER_CONTRACT_TASK_SET,
        'tasks': tasks,
        'task_count': len(tasks),
    }


def _parse_planner_task_set_item(raw_task: object, *, index: int) -> dict[str, object]:
    prefix = f'tasks[{index}]'
    if not isinstance(raw_task, dict):
        return {'status': 'blocked', 'reason': 'planner_task_set_task_not_object', 'task_index': index}
    try:
        task_id = _normalize_segment(raw_task.get('task_id'), label=f'{prefix}.task_id')
    except ValueError as exc:
        return {'status': 'blocked', 'reason': 'planner_task_set_invalid_task_id', 'task_index': index, 'error': str(exc)}
    task_packet = str(raw_task.get('task_packet') or '').strip()
    route = str(raw_task.get('route') or '').strip().lower()
    readiness_value = str(raw_task.get('readiness') or '').strip().lower()
    title = str(raw_task.get('title') or '').strip() or _task_title_from_packet(task_packet)
    allowed_paths = _string_list(raw_task.get('allowed_paths'))
    verification = _string_list(raw_task.get('verification'))
    blockers = _string_list(raw_task.get('blockers'))
    missing_fields: list[str] = []
    if not task_packet:
        missing_fields.append(f'{prefix}.task_packet')
    if not title:
        missing_fields.append(f'{prefix}.title')
    if route not in _VALID_ROUTES:
        return {
            'status': 'blocked',
            'reason': 'unknown_route',
            'task_index': index,
            'task_id': task_id,
            'route': route or None,
            'expected_routes': sorted(_VALID_ROUTES),
        }
    if readiness_value not in _VALID_READINESS:
        return {
            'status': 'blocked',
            'reason': 'unknown_readiness',
            'task_index': index,
            'task_id': task_id,
            'readiness': readiness_value or 'missing',
            'route': route,
            'expected_readiness': sorted(_VALID_READINESS),
        }
    if route in _EXECUTION_ROUTES and readiness_value != 'ready':
        return {
            'status': 'blocked',
            'reason': 'planner_readiness_not_ready',
            'task_index': index,
            'task_id': task_id,
            'readiness': readiness_value or 'missing',
            'route': route,
        }
    if route == 'needs_detail' and readiness_value not in _NEEDS_DETAIL_READINESS:
        return {
            'status': 'blocked',
            'reason': 'planner_readiness_incompatible_with_route',
            'task_index': index,
            'task_id': task_id,
            'readiness': readiness_value or 'missing',
            'route': route,
            'expected_readiness': sorted(_NEEDS_DETAIL_READINESS),
        }
    if route in _EXECUTION_ROUTES and not allowed_paths:
        missing_fields.append(f'{prefix}.allowed_paths')
    if not verification:
        missing_fields.append(f'{prefix}.verification')
    if route == 'needs_detail' and readiness_value == 'needs_clarification' and not blockers:
        missing_fields.append(f'{prefix}.blockers')
    if route == 'blocked' and not blockers:
        missing_fields.append(f'{prefix}.blockers')
    if missing_fields:
        return {
            'status': 'blocked',
            'reason': 'planner_task_set_missing_required_fields',
            'task_index': index,
            'task_id': task_id,
            'missing_fields': missing_fields,
        }
    invalid_allowed_paths = _invalid_allowed_paths(allowed_paths)
    if invalid_allowed_paths:
        return {
            'status': 'blocked',
            'reason': 'planner_readiness_invalid_allowed_paths',
            'task_index': index,
            'task_id': task_id,
            'invalid_allowed_paths': invalid_allowed_paths,
        }
    execution_contract = str(raw_task.get('execution_contract') or '').strip()
    if not execution_contract:
        execution_contract = _normalized_execution_contract(
            route=route,
            allowed_paths=allowed_paths,
            verification=verification,
        )
    return {
        'status': 'ok',
        'task_id': task_id,
        'title': title,
        'route': route,
        'readiness': readiness_value,
        'task_packet': task_packet + '\n',
        'execution_contract': execution_contract.strip() + '\n',
        'allowed_paths': allowed_paths,
        'verification': verification,
        'blockers': blockers,
    }


def _has_single_task_planner_sections(reply: str) -> bool:
    return bool(_fenced_section(reply, ('task-packet.md', 'task_packet.md')) or _fenced_section(reply, ('readiness.json',)))


def _parse_task_detailer_reply(reply: str) -> dict[str, object]:
    detail_labels = (
        'task-detail-design.md',
        'task-detail-design',
        'brief-update-summary.md',
        'brief-update-summary',
        'detail-packet.manifest.json',
        'detail-packet.md',
        'detail-packet',
    )
    detail_terminator_labels = (
        'task-detail-design.md',
        'brief-update-summary.md',
        'detail-packet.manifest.json',
        'detail-packet.md',
    )
    detail_design = _labeled_section(
        reply,
        ('task-detail-design.md', 'task-detail-design'),
        terminator_names=detail_terminator_labels,
    )
    detail_summary = _labeled_section(
        reply,
        ('brief-update-summary.md', 'brief-update-summary'),
        terminator_names=detail_terminator_labels,
    )
    detail_packet = _labeled_section(
        reply,
        ('detail-packet.manifest.json', 'detail-packet.md', 'detail-packet'),
        terminator_names=detail_terminator_labels,
    )
    readiness = _task_detailer_readiness(reply)
    missing = []
    if not detail_design:
        missing.append('task-detail-design.md section')
    if not detail_summary:
        missing.append('brief-update-summary.md section')
    if not detail_packet:
        missing.append('detail-packet.manifest.json section')
    if missing:
        return {'status': 'blocked', 'reason': 'task_detailer_reply_missing_required_sections', 'missing_fields': missing}
    if readiness != 'detail_ready':
        return {
            'status': 'blocked',
            'reason': 'task_detailer_reply_not_detail_ready',
            'readiness': readiness or 'missing',
        }
    return {
        'status': 'ok',
        'detail_design': detail_design,
        'detail_summary': detail_summary,
        'detail_packet': detail_packet,
        'readiness': readiness,
    }


def _resolve_completion_reply_artifact(context, reply: str) -> dict[str, object]:
    if 'CCB completion reply' not in reply or 'Full text:' not in reply:
        return {'status': 'ok', 'reply': reply}
    path_match = re.search(r'(?m)^Full text:\s*(.+?)\s*$', reply)
    sha_match = re.search(r'(?m)^SHA256:\s*([0-9a-fA-F]{64})\s*$', reply)
    if not path_match or not sha_match:
        return {'status': 'blocked', 'reason': 'completion_reply_artifact_notice_incomplete'}
    artifact_path = Path(path_match.group(1).strip())
    project_root = Path(context.project.project_root)
    if not _path_within(artifact_path, project_root):
        return {
            'status': 'blocked',
            'reason': 'completion_reply_artifact_outside_project',
            'artifact_path': str(artifact_path),
        }
    try:
        artifact_text = artifact_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return {
            'status': 'blocked',
            'reason': 'completion_reply_artifact_missing',
            'artifact_path': str(artifact_path),
        }
    actual_sha = hashlib.sha256(artifact_text.encode('utf-8')).hexdigest()
    expected_sha = sha_match.group(1).lower()
    if actual_sha != expected_sha:
        return {
            'status': 'blocked',
            'reason': 'completion_reply_artifact_sha256_mismatch',
            'artifact_path': str(artifact_path),
            'expected_sha256': expected_sha,
            'actual_sha256': actual_sha,
        }
    return {
        'status': 'ok',
        'reply': artifact_text,
        'artifact_path': str(artifact_path),
        'sha256': actual_sha,
    }


def _parse_orchestrator_reply(reply: str) -> dict[str, object]:
    match = re.search(r'(?mi)^\s*[-*]?\s*route\s*:\s*([A-Za-z_]+)\b', reply)
    if not match:
        return {'status': 'blocked', 'reason': 'orchestrator_reply_missing_route'}
    route = match.group(1).strip().lower()
    if route not in _VALID_ROUTES:
        return {'status': 'blocked', 'reason': 'unknown_route', 'route': route, 'expected_routes': sorted(_VALID_ROUTES)}
    if not re.search(r'(?mi)^\s*[-*]?\s*orchestration[_ ]notes\s*:', reply):
        return {'status': 'blocked', 'reason': 'orchestrator_reply_missing_orchestration_notes'}
    return {'status': 'ok', 'route': route, 'orchestration_notes': reply.strip() + '\n'}


def _fenced_section(text: str, names: tuple[str, ...]) -> str:
    for name in names:
        escaped = re.escape(name).replace(r'\-', '[-_ ]')
        pattern = (
            rf'(?is)(?:^|\n)\s*(?:#+\s*)?(?:\*\*)?\s*{escaped}\s*(?:\*\*)?\s*\n'
            r'```[A-Za-z0-9_-]*\s*\n(.*?)\n```'
        )
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ''


def _labeled_section(text: str, names: tuple[str, ...], *, terminator_names: tuple[str, ...] | None = None) -> str:
    for name in names:
        escaped = re.escape(name).replace(r'\-', '[-_ ]')
        pattern = (
            rf'(?im)(?:^|\n)\s*(?:#+\s*)?(?:\*\*)?\s*{escaped}\s*(?:\*\*)?\s*$'
        )
        match = re.search(pattern, text)
        if match:
            body_start = match.end()
            tail = text[body_start:]
            terminator = _labeled_section_terminator(tail, terminator_names or names)
            body = tail[:terminator].strip()
            fenced = _fenced_block(body)
            return fenced or body
    return ''


def _labeled_section_terminator(text: str, names: tuple[str, ...]) -> int:
    matches = []
    for name in names:
        escaped = re.escape(name).replace(r'\-', '[-_ ]')
        pattern = rf'(?im)^\s*(?:#+\s*)?(?:\*\*)?\s*{escaped}\s*(?:\*\*)?\s*$'
        match = re.search(pattern, text)
        if match:
            matches.append(match.start())
    return min(matches) if matches else len(text)


def _fenced_block(text: str) -> str:
    match = re.search(r'(?is)```[A-Za-z0-9_-]*\s*\n(.*?)\n```', text)
    if not match:
        return ''
    return match.group(1).strip()


def _task_detailer_readiness(reply: str) -> str:
    patterns = (
        r'(?mi)^\s*(?:detail\s+)?readiness(?:\s+recommendation)?\s*:\s*`?([A-Za-z_]+)`?\s*$',
        r'(?mi)^\s*detail\s+status\s*:\s*`?([A-Za-z_]+)`?\s*$',
        r'(?mi)^\s*readiness\s*:\s*`?([A-Za-z_]+)`?\s*$',
    )
    for pattern in patterns:
        match = re.search(pattern, reply)
        if match:
            return match.group(1).strip().lower()
    return ''


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def _normalized_execution_contract(*, route: str, allowed_paths: tuple[str, ...], verification: tuple[str, ...]) -> str:
    lines = [
        '# Execution Contract',
        '',
        f'Route: {route}',
        '',
        'Allowed Change Paths:',
    ]
    lines.extend(f'- {path}' for path in allowed_paths)
    lines.extend(['', 'Verification:'])
    lines.extend(f'- {item}' for item in verification)
    return '\n'.join(lines)


def _task_title_from_packet(task_packet: str) -> str:
    for raw_line in task_packet.splitlines():
        line = raw_line.strip()
        if not line.startswith('#'):
            continue
        text = line.lstrip('#').strip()
        if text.lower().startswith('task:'):
            text = text.split(':', 1)[1].strip()
        if text:
            return text
    return 'Planner task'


def _ensure_task(
    context,
    deps,
    *,
    plan_slug: str,
    title: str,
    task_id: str | None,
    snapshot: dict[str, object],
    reply: str,
) -> dict[str, object]:
    if task_id:
        try:
            payload = deps.plan_task(context, SimpleNamespace(action='task-show', task_id=task_id))
            payload['created'] = False
            return payload
        except ValueError:
            pass
    payload = deps.plan_task(
        context,
        SimpleNamespace(
            action='task-create',
            plan_slug=plan_slug,
            title=title,
            task_id=task_id,
            authority_trace={
                'source': 'loop_runner_role_output_import',
                'source_job': _job_trace(snapshot, reply),
            },
        ),
    )
    payload['created'] = True
    return payload


def _resolve_or_bootstrap_plan(
    context,
    command,
    *,
    activation: dict[str, object] | None = None,
) -> tuple[str | None, dict[str, object]]:
    raw = str(getattr(command, 'plan_slug', None) or '').strip()
    if not raw and activation is not None:
        raw = str(activation.get('plan_slug') or '').strip()
    if not raw:
        existing = _existing_plan_slugs(context)
        if len(existing) == 1:
            raw = existing[0]
    if not raw:
        return None, _blocked_payload(
            context,
            job_id=str(getattr(command, 'role_job_id', None) or ''),
            agent_name=None,
            reason='role_output_import_requires_plan_slug',
            evidence={'hint': 'pass --plan <plan_slug> or create exactly one plan root first'},
        )
    try:
        plan_slug = _normalize_segment(raw, label='plan')
    except ValueError as exc:
        return None, _blocked_payload(
            context,
            job_id=str(getattr(command, 'role_job_id', None) or ''),
            agent_name=None,
            reason='invalid_plan_slug',
            evidence={'error': str(exc)},
        )
    plan_root = Path(context.project.project_root) / 'docs' / 'plantree' / 'plans' / plan_slug
    created = False
    if not plan_root.is_dir():
        _bootstrap_plan_root(context, plan_slug=plan_slug)
        created = True
    return plan_slug, {
        'status': 'ok',
        'plan_slug': plan_slug,
        'created': created,
        'plan_root': str(plan_root.relative_to(context.project.project_root)),
    }


def _bootstrap_plan_root(context, *, plan_slug: str) -> None:
    root = Path(context.project.project_root)
    plantree = root / 'docs' / 'plantree'
    plan_root = plantree / 'plans' / plan_slug
    if not (plantree / 'README.md').exists():
        atomic_write_text(plantree / 'README.md', '# Plan Tree\n\nScript-owned CCB plan tree.\n')
    if not (plan_root / 'README.md').exists():
        atomic_write_text(plan_root / 'README.md', f'# {plan_slug}\n\nScript-owned plan root.\n')
    if not (plan_root / 'brief.md').exists():
        atomic_write_text(plan_root / 'brief.md', f'# {plan_slug} Brief\n\nCreated by loop runner role-output import.\n')
    (plan_root / 'tasks').mkdir(parents=True, exist_ok=True)


def planner_contract_for_frontdesk_text(text: str) -> str:
    return _PLANNER_CONTRACT_TASK_SET if _frontdesk_text_requests_task_set(text) else _PLANNER_CONTRACT_SINGLE_TASK


def planner_required_output_for_contract(planner_contract: str) -> str:
    if planner_contract == _PLANNER_CONTRACT_TASK_SET:
        return 'reply-only task-set.json with bounded planner tasks for supervisor-owned import'
    return 'reply-only task-packet.md plus readiness.json for supervisor-owned import'


def planner_script_write_rules_for_contract(planner_contract: str) -> list[str]:
    base_rules = [
        'Reply only; do not run ccb, ccb_test, ccb plan, ccb loop, ccb ask, artifact import, or wrapper commands.',
        'Supervisor/runner scripts own plan/task authority creation, artifact imports, and status transitions.',
    ]
    if planner_contract == _PLANNER_CONTRACT_TASK_SET:
        return [
            base_rules[0],
            'Return exactly one fenced **task-set.json** section with one task object per requested bounded task.',
            'Do not collapse multi-task or route-mix validation into a controller-owned meta task.',
            base_rules[1],
        ]
    return [
        base_rules[0],
        'Return explicit fenced **task-packet.md** and **readiness.json** sections.',
        base_rules[1],
    ]


def _planner_contract_from_activation(
    activation: dict[str, object] | None,
    *,
    reply: str = '',
) -> str:
    raw_contract = ''
    if activation is not None:
        raw_contract = str(activation.get('planner_contract') or '').strip()
    if raw_contract in _PLANNER_CONTRACTS:
        return raw_contract
    intake_preview = ''
    if activation is not None and isinstance(activation.get('source_intake'), dict):
        intake_preview = str(activation['source_intake'].get('preview') or '')
    return planner_contract_for_frontdesk_text('\n'.join(part for part in (intake_preview, reply) if part))


def _frontdesk_text_requests_task_set(text: str) -> bool:
    lowered = str(text or '').lower()
    if any(marker in lowered for marker in _TASK_SET_INTENT_MARKERS):
        return True
    route_mentions = sum(1 for route in _VALID_ROUTES if route in lowered)
    return route_mentions >= 2 and ('task' in lowered or 'validation' in lowered)


def _planner_from_frontdesk_message(activation: dict[str, object], frontdesk_reply: str) -> str:
    planner_contract = _planner_contract_from_activation(activation, reply=frontdesk_reply)
    if planner_contract == _PLANNER_CONTRACT_TASK_SET:
        return _planner_task_set_from_frontdesk_message(activation, frontdesk_reply)
    return _planner_single_task_from_frontdesk_message(activation, frontdesk_reply)


def _planner_single_task_from_frontdesk_message(activation: dict[str, object], frontdesk_reply: str) -> str:
    return (
        'Role: planner\n'
        f"Activation id: {activation.get('activation_id')}\n"
        f"Plan: {activation.get('plan_slug')}\n"
        f"Source frontdesk job: {(activation.get('source_job') or {}).get('job_id')}\n\n"
        f'Planner contract: {_PLANNER_CONTRACT_SINGLE_TASK}\n\n'
        'Frontdesk intake evidence:\n'
        f'{frontdesk_reply.strip()}\n\n'
        'Required reply-only output. Use these exact labels and fenced blocks; do not use alternate headings, '
        'unfenced JSON, tables, or prose-only summaries:\n'
        '**task-packet.md**\n'
        '```markdown\n'
        '# Task: <title>\n'
        'Route: <direct_execution|needs_detail|macro_adjustment_request|blocked|partial_completion>\n'
        'Allowed paths:\n'
        '- <relative path>\n'
        'Verification:\n'
        '- <command>\n'
        '```\n\n'
        '**readiness.json**\n'
        '```json\n'
        '{"readiness":"ready","route":"direct_execution","blockers":[],"allowed_paths":["path"],"verification":["command"]}\n'
        '```\n\n'
        'For route needs_detail, use readiness "needs_clarification", include non-empty blockers and verification, '
        'and use "allowed_paths":[] because implementation is not authorized yet.\n\n'
        'For route blocked, use readiness "blocked", include non-empty blockers and blocker verification, '
        'and use "allowed_paths":[] because implementation is not authorized.\n\n'
        'Authority boundary:\n'
        '- Reply only with semantic planning artifacts.\n'
        '- Do not run ccb, ccb_test, ccb plan, ccb loop, ccb ask, artifact import, status, runtime, cleanup, or wrapper commands.\n'
        '- Supervisor/runner scripts own plan/task authority creation, artifact imports, and status transitions.'
    )


def _planner_task_set_from_frontdesk_message(activation: dict[str, object], frontdesk_reply: str) -> str:
    return (
        'Role: planner\n'
        f"Activation id: {activation.get('activation_id')}\n"
        f"Plan: {activation.get('plan_slug')}\n"
        f"Source frontdesk job: {(activation.get('source_job') or {}).get('job_id')}\n\n"
        f'Planner contract: {_PLANNER_CONTRACT_TASK_SET}\n\n'
        'Frontdesk intake evidence:\n'
        f'{frontdesk_reply.strip()}\n\n'
        'Required reply-only output for this multi-task/route-mix intake. Use exactly one fenced '
        '**task-set.json** block. Do not collapse this into a controller-owned validation task, report task, '
        'B7 task, cleanup task, or other meta task:\n'
        '**task-set.json**\n'
        '```json\n'
        '{\n'
        '  "tasks": [\n'
        '    {\n'
        '      "task_id": "phase6b-l1-doc-direct-execution",\n'
        '      "title": "L1 bounded documentation direct execution",\n'
        '      "route": "direct_execution",\n'
        '      "readiness": "ready",\n'
        '      "task_packet": "# Task: L1 bounded documentation direct execution\\nRoute: direct_execution\\n",\n'
        '      "execution_contract": "# Execution Contract\\nRoute: direct_execution\\n",\n'
        '      "allowed_paths": ["relative/path"],\n'
        '      "verification": ["command"],\n'
        '      "blockers": []\n'
        '    }\n'
        '  ]\n'
        '}\n'
        '```\n\n'
        'Task-set rules:\n'
        '- Include one task object for each bounded task requested by frontdesk.\n'
        '- Each task_id must be stable, unique, and match [A-Za-z0-9][A-Za-z0-9_-]{0,79}.\n'
        '- Routes must be direct_execution, needs_detail, macro_adjustment_request, blocked, or partial_completion.\n'
        '- direct_execution and partial_completion tasks must be readiness "ready" with non-empty allowed_paths and verification.\n'
        '- needs_detail tasks may use readiness "needs_clarification" with blockers, allowed_paths [], and verification.\n'
        '- blocked tasks must use readiness "blocked", blockers, allowed_paths [], and verification.\n\n'
        'Authority boundary:\n'
        '- Reply only with semantic planning artifacts.\n'
        '- Do not run ccb, ccb_test, ccb plan, ccb loop, ccb ask, artifact import, status, runtime, cleanup, or wrapper commands.\n'
        '- Supervisor/runner scripts own plan/task authority creation, artifact imports, and status transitions.'
    )


def frontdesk_intake_missing_fields(reply: str) -> list[str]:
    return _frontdesk_intake_missing_fields(reply)


def planner_from_frontdesk_intake_message(activation: dict[str, object], frontdesk_reply: str) -> str:
    return _planner_from_frontdesk_message(activation, frontdesk_reply)


def _load_job_snapshot(context, job_id: str) -> dict[str, object] | None:
    path = Path(context.project.project_root) / '.ccb' / 'ccbd' / 'snapshots' / f'{job_id}.json'
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        raise ValueError(f'completion snapshot is invalid JSON: {path}') from exc
    if not isinstance(payload, dict):
        raise ValueError(f'completion snapshot is invalid: {path}')
    return payload


def _retry_successor_for_job(context, job_id: str, *, agent_name: str | None) -> dict[str, object] | None:
    source_job_id = job_id
    current_job_id = job_id
    lineage: list[dict[str, object]] = []
    for _depth in range(8):
        record = _latest_retry_successor_record(context, current_job_id, agent_name=agent_name)
        if record is None:
            return None
        successor_job_id = str(record.get('job_id') or '').strip()
        if not successor_job_id or successor_job_id == current_job_id:
            return None
        successor_agent = str(record.get('agent_name') or agent_name or '').strip()
        lineage.append(
            {
                'retry_source_job_id': current_job_id,
                'job_id': successor_job_id,
                'agent_name': successor_agent,
                'status': record.get('status'),
            }
        )
        snapshot = _load_job_snapshot(context, successor_job_id)
        if snapshot is None:
            return {
                'status': 'pending',
                'job_id': successor_job_id,
                'agent_name': successor_agent,
                'reason': 'retry_successor_missing_completion_snapshot',
                'retry_source_job_id': source_job_id,
                'retry_lineage': lineage,
            }
        decision = snapshot.get('latest_decision') if isinstance(snapshot.get('latest_decision'), dict) else {}
        terminal = bool(decision.get('terminal') or (snapshot.get('state') or {}).get('terminal'))
        if not terminal:
            return {
                'status': 'pending',
                'job_id': successor_job_id,
                'agent_name': successor_agent,
                'reason': 'retry_successor_not_terminal',
                'retry_source_job_id': source_job_id,
                'retry_lineage': lineage,
            }
        status = str(decision.get('status') or '').strip().lower()
        if status == 'completed':
            resolved = dict(snapshot)
            resolved['retry_source_job_id'] = source_job_id
            resolved['retry_successor_job_id'] = successor_job_id
            resolved['retry_lineage'] = lineage
            return {
                'status': 'completed',
                'job_id': successor_job_id,
                'agent_name': successor_agent,
                'snapshot': resolved,
                'retry_source_job_id': source_job_id,
                'retry_successor_job_id': successor_job_id,
                'retry_lineage': lineage,
            }
        current_job_id = successor_job_id
    return None


def _latest_retry_successor_record(context, source_job_id: str, *, agent_name: str | None) -> dict[str, object] | None:
    candidates: dict[str, dict[str, object]] = {}
    for record in _iter_agent_job_records(context, agent_name=agent_name):
        provider_options = record.get('provider_options') if isinstance(record.get('provider_options'), dict) else {}
        if str(provider_options.get('retry_source_job_id') or '').strip() != source_job_id:
            continue
        retry_job_id = str(record.get('job_id') or '').strip()
        if not retry_job_id:
            continue
        candidates[retry_job_id] = record
    if not candidates:
        return None
    return sorted(
        candidates.values(),
        key=lambda item: str(item.get('updated_at') or item.get('created_at') or item.get('job_id') or ''),
    )[-1]


def _iter_agent_job_records(context, *, agent_name: str | None):
    agents_root = Path(context.project.project_root) / '.ccb' / 'agents'
    if agent_name:
        paths = (agents_root / _base_agent_name(agent_name) / 'jobs.jsonl',)
    else:
        paths = tuple(agents_root.glob('*/jobs.jsonl'))
    for path in paths:
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except FileNotFoundError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def _iter_activation_records(context):
    activations_dir = Path(context.project.project_root) / '.ccb' / 'runtime' / 'loops' / 'activations'
    if not activations_dir.is_dir():
        return
    for path in sorted(activations_dir.glob('act-*.json')):
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield path, payload


def _activation_for_job(context, job_id: str) -> dict[str, object] | None:
    for _path, activation in _iter_activation_records(context):
        ask = activation.get('ask') if isinstance(activation.get('ask'), dict) else {}
        if str(ask.get('job_id') or '').strip() == job_id:
            return activation
    return None


def _activation_already_satisfied(context, deps, *, activation: dict[str, object], target: str) -> bool:
    task_id = str(activation.get('task_id') or '').strip()
    if not task_id:
        return False
    ask = activation.get('ask') if isinstance(activation.get('ask'), dict) else {}
    job_id = str(ask.get('job_id') or '').strip()
    if not job_id:
        return False
    try:
        shown = deps.plan_task(context, SimpleNamespace(action='task-show', task_id=task_id))
    except ValueError:
        return False
    task = shown.get('task') if isinstance(shown.get('task'), dict) else {}
    artifacts = task.get('artifacts') if isinstance(task.get('artifacts'), dict) else {}
    if target == 'orchestrator':
        artifact = artifacts.get('orchestration_notes')
        reason = str(activation.get('reason_for_activation') or '')
        if reason == 'orchestrator_route_needs_detail_detail_ready':
            return _artifact_imported_from_job(artifact, job_id=job_id)
        return isinstance(artifact, dict)
    if target == 'planner':
        return _artifact_imported_from_job(
            artifacts.get('task_packet'),
            job_id=job_id,
        ) and _artifact_imported_from_job(
            artifacts.get('execution_contract'),
            job_id=job_id,
        )
    return False


def _artifact_imported_from_job(artifact: object, *, job_id: str) -> bool:
    if not isinstance(artifact, dict):
        return False
    actor = artifact.get('actor') if isinstance(artifact.get('actor'), dict) else {}
    return str(actor.get('source') or '') == 'loop_runner_role_output_import' and str(actor.get('job_id') or '') == job_id


def _role_import_dir(context, job_id: str) -> Path:
    path = Path(context.project.project_root) / '.ccb' / 'runtime' / 'role-output-imports' / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _activation_path(context, activation_id: str) -> Path:
    path = Path(context.project.project_root) / '.ccb' / 'runtime' / 'loops' / 'activations' / f'{activation_id}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _import_log_path(context) -> Path:
    return Path(context.project.project_root) / '.ccb' / 'runtime' / 'role-output-imports.jsonl'


def _log_import(context, record: dict[str, object]) -> dict[str, object]:
    payload = {
        'schema_version': 1,
        'record_type': 'ccb_loop_role_output_import',
        'imported_at': _utc_now(),
        **record,
    }
    path = _import_log_path(context)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(payload, sort_keys=True) + '\n')
    return payload


def _job_already_consumed(context, job_id: str) -> bool:
    for record in _iter_import_log(context):
        if _import_record_matches_job(record, job_id=job_id):
            if str(record.get('status') or '') == 'ok':
                return True
    return False


def _job_settled_for_activation_scan(context, job_id: str) -> bool:
    for record in _iter_import_log(context):
        if not _import_record_matches_job(record, job_id=job_id):
            continue
        status = str(record.get('status') or '')
        if status == 'ok':
            return True
        if status == 'blocked' and str(record.get('action') or '') == 'role_output_import_blocked':
            return True
    return False


def _import_record_job_id(record: dict[str, object]) -> str:
    source_job = record.get('source_job') if isinstance(record.get('source_job'), dict) else {}
    return str(source_job.get('job_id') or record.get('job_id') or '')


def _import_record_matches_job(record: dict[str, object], *, job_id: str) -> bool:
    if _import_record_job_id(record) == job_id:
        return True
    source_job = record.get('source_job') if isinstance(record.get('source_job'), dict) else {}
    if str(source_job.get('retry_source_job_id') or '') == job_id:
        return True
    lineage = source_job.get('retry_lineage')
    if isinstance(lineage, list):
        for item in lineage:
            if not isinstance(item, dict):
                continue
            if str(item.get('retry_source_job_id') or '') == job_id:
                return True
    return False


def _iter_import_log(context):
    path = _import_log_path(context)
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except FileNotFoundError:
        return
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _already_consumed_payload(context, *, job_id: str) -> dict[str, object]:
    return _base_payload(
        context,
        loop_runner_status='ok',
        action='role_output_already_consumed',
        job_id=job_id,
        agent_name=None,
        extra={'idempotent': True, 'next_activation': 'inspect'},
    )


def _pending_payload(context, *, job_id: str, agent_name: str | None, reason: str) -> dict[str, object]:
    return _base_payload(
        context,
        loop_runner_status='pending',
        action='role_output_pending',
        job_id=job_id,
        agent_name=agent_name,
        extra={'reason': reason, 'next_activation': 'role_output_import'},
    )


def _blocked_payload(
    context,
    *,
    job_id: str,
    agent_name: str | None,
    reason: str,
    evidence: dict[str, object] | None = None,
) -> dict[str, object]:
    evidence_payload = evidence or {}
    trace = _log_import(
        context,
        {
            'action': 'role_output_import_blocked',
            'status': 'blocked',
            'job_id': job_id,
            'agent_name': agent_name,
            'reason': reason,
            'evidence': evidence_payload,
        },
    )
    return _base_payload(
        context,
        loop_runner_status='blocked',
        action='role_output_import_blocked',
        job_id=job_id,
        agent_name=agent_name,
        extra={'reason': reason, 'evidence': evidence_payload, 'role_output_import': trace, 'next_activation': 'inspect'},
    )


def _base_payload(
    context,
    *,
    loop_runner_status: str,
    action: str,
    job_id: str,
    agent_name: str | None,
    extra: dict[str, object],
) -> dict[str, object]:
    return {
        'schema_version': 1,
        'record_type': 'ccb_loop_runner_once',
        'loop_runner_status': loop_runner_status,
        'project_id': context.project.project_id,
        'project_root': str(context.project.project_root),
        'action': action,
        'source': 'loop_runner_role_output_import',
        'job_id': job_id,
        'agent_name': agent_name,
        **extra,
    }


def _attach_retry_metadata(
    payload: dict[str, object],
    *,
    snapshot: dict[str, object],
    original_job_id: str,
) -> dict[str, object]:
    retry_source_job_id = str(snapshot.get('retry_source_job_id') or '').strip()
    retry_successor_job_id = str(snapshot.get('retry_successor_job_id') or snapshot.get('job_id') or '').strip()
    if not retry_source_job_id or retry_source_job_id == original_job_id == retry_successor_job_id:
        return payload
    payload['retry_source_job_id'] = retry_source_job_id
    payload['retry_successor_job_id'] = retry_successor_job_id
    lineage = snapshot.get('retry_lineage')
    if isinstance(lineage, list):
        payload['retry_lineage'] = lineage
    return payload


def _job_trace(snapshot: dict[str, object], reply: str) -> dict[str, object]:
    decision = snapshot.get('latest_decision') if isinstance(snapshot.get('latest_decision'), dict) else {}
    trace = {
        'job_id': snapshot.get('job_id'),
        'agent_name': snapshot.get('agent_name'),
        'terminal_status': decision.get('status'),
        'finished_at': decision.get('finished_at'),
        'reply_sha256': hashlib.sha256(reply.encode('utf-8')).hexdigest(),
    }
    retry_source_job_id = str(snapshot.get('retry_source_job_id') or '').strip()
    retry_successor_job_id = str(snapshot.get('retry_successor_job_id') or '').strip()
    if retry_source_job_id:
        trace['retry_source_job_id'] = retry_source_job_id
    if retry_successor_job_id:
        trace['retry_successor_job_id'] = retry_successor_job_id
    lineage = snapshot.get('retry_lineage')
    if isinstance(lineage, list):
        trace['retry_lineage'] = lineage
    return trace


def _compact_plan_payload(payload: dict[str, object] | None) -> dict[str, object]:
    if payload is None:
        return {}
    return {
        'action': payload.get('action'),
        'task_id': payload.get('task_id'),
        'status': payload.get('status'),
        'next_owner': payload.get('next_owner'),
        'plan_slug': payload.get('plan_slug'),
        'task_root': payload.get('task_root'),
    }


def _next_activation_for_route(route: str) -> str:
    if route in {'direct_execution', 'partial_completion'}:
        return 'ask_first_execution'
    if route == 'needs_detail':
        return 'task_detailer'
    if route == 'macro_adjustment_request':
        return 'planner_status_transition_required'
    if route == 'blocked':
        return 'blocker_evidence_required'
    return 'inspect'


def _existing_plan_slugs(context) -> tuple[str, ...]:
    plans_root = Path(context.project.project_root) / 'docs' / 'plantree' / 'plans'
    if not plans_root.is_dir():
        return ()
    return tuple(sorted(path.name for path in plans_root.iterdir() if path.is_dir()))


def _has_heading(text: str, heading: str) -> bool:
    escaped = re.escape(heading)
    return bool(re.search(rf'(?mi)^\s*(?:#+\s*)?(?:\*\*)?\s*{escaped}\s*(?:\*\*)?\s*$', text))


def _has_label(text: str, label: str) -> bool:
    escaped = re.escape(label)
    return bool(re.search(rf'(?mi)^\s*(?:[-*]\s*)?(?:\*\*)?\s*{escaped}\s*(?:\*\*)?\s*:', text))


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


def _single_job(jobs, *, target: str) -> dict[str, object]:
    matches = [job for job in tuple(jobs or ()) if str(job.get('agent_name') or job.get('target_name') or '') == target]
    if len(matches) != 1:
        raise RuntimeError(f'expected one ask job for {target}; got {len(matches)}')
    job = dict(matches[0])
    if not str(job.get('job_id') or '').strip():
        raise RuntimeError(f'ask job for {target} did not return job_id')
    return job


def _string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    result = []
    for item in value:
        text = str(item or '').strip()
        if text:
            result.append(text)
    return tuple(result)


def _first_optional_text(*values: object) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _invalid_allowed_paths(paths: tuple[str, ...]) -> list[str]:
    invalid: list[str] = []
    for raw in paths:
        path = Path(raw)
        if raw in {'.', './'} or path.is_absolute() or '..' in path.parts:
            invalid.append(raw)
            continue
        if path.parts and path.parts[0] in {'.ccb', '.git'}:
            invalid.append(raw)
    return invalid


def _normalize_job_id(value: object) -> str:
    text = str(value or '').strip()
    if not _SEGMENT_RE.fullmatch(text):
        raise ValueError(f'job_id must match {_SEGMENT_RE.pattern}: {text!r}')
    return text


def _normalize_segment(value: object, *, label: str) -> str:
    text = str(value or '').strip()
    if not _SEGMENT_RE.fullmatch(text):
        raise ValueError(f'{label} must match {_SEGMENT_RE.pattern}: {text!r}')
    return text


def _base_agent_name(agent_name: str) -> str:
    text = str(agent_name or '').strip()
    if text in {'frontdesk', 'planner', 'orchestrator'}:
        return text
    return text


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _deps(services):
    services = services or SimpleNamespace()
    return SimpleNamespace(
        plan_task=getattr(services, 'plan_task', plan_task),
        submit_ask=getattr(services, 'submit_ask', submit_ask),
    )


__all__ = [
    'consume_activation_role_output',
    'consume_explicit_role_output',
    'frontdesk_intake_missing_fields',
    'planner_contract_for_frontdesk_text',
    'planner_from_frontdesk_intake_message',
    'planner_required_output_for_contract',
    'planner_script_write_rules_for_contract',
]
