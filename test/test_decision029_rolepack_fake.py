from __future__ import annotations

import json
from pathlib import Path

import pytest

from ccbd.api_models import DeliveryScope, JobRecord, JobStatus, MessageEnvelope
from cli.services.role_command_policy import claude_permission_allowlist, load_role_command_policy
from provider_execution.fake import FakeProviderAdapter
from rolepacks.manifest import load_role_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DRAFTS = REPO_ROOT / 'docs/plantree/plans/agentic-loop-workflow/drafts'
CORPUS_PATH = REPO_ROOT / 'test/fixtures/decision029_task_set_closure.v1.json'
RESULT_BY_AGGREGATE = {
    'pass': 'closure_complete',
    'partial': 'closure_partial',
    'replan_required': 'task_set_replanned',
    'blocked': 'closure_blocked',
}


def _corpus() -> dict[str, object]:
    return json.loads(CORPUS_PATH.read_text(encoding='utf-8'))


def _job(*, agent_name: str, body: str) -> JobRecord:
    return JobRecord(
        job_id=f'job-{agent_name}',
        submission_id=None,
        agent_name=agent_name,
        provider='fake',
        request=MessageEnvelope(
            project_id='project-decision029',
            to_agent=agent_name,
            from_actor='system',
            body=body,
            task_id='decision029-closure',
            reply_to=None,
            message_type='ask',
            delivery_scope=DeliveryScope.SINGLE,
        ),
        status=JobStatus.QUEUED,
        terminal_decision=None,
        cancel_requested_at=None,
        created_at='2026-07-12T00:00:00Z',
        updated_at='2026-07-12T00:00:00Z',
    )


def _planner_body(closure: dict[str, object]) -> str:
    envelope = {
        'schema': 'ccb.plan.task_set_closure_transport.v1',
        'closure': closure,
        'closure_intent': {
            'intent_id': 'intent-decision029',
            'task_set_id': closure['task_set_id'],
            'task_set_revision': closure['task_set_revision'],
            'ordered_terminal_evidence_digest': closure['ordered_terminal_evidence_digest'],
            'closure_digest': closure['closure_digest'],
        },
    }
    return '**task-set-closure.json**\n```json\n' + json.dumps(envelope, sort_keys=True) + '\n```'


def _payload(reply: str, label: str) -> dict[str, object]:
    prefix = f'**{label}**\n```json\n'
    assert reply.startswith(prefix)
    assert reply.endswith('\n```')
    return json.loads(reply[len(prefix) : -4])


def test_decision029_corpus_covers_frozen_scenarios() -> None:
    corpus = _corpus()
    assert corpus['schema'] == 'ccb.decision029.fake_closure_corpus.v1'
    assert [case['case_id'] for case in corpus['scenarios']] == [
        'all-pass',
        'pass-blocked-partial',
        'pass-partial',
        'multiple-replan-one-aggregate',
        'all-blocked',
        'notification-not-required',
        'stale-plan-revision-shape',
        'malformed-missing-unresolved',
        'non-success-laundering',
    ]


@pytest.mark.parametrize('case_id', ('all-pass', 'pass-blocked-partial', 'pass-partial', 'multiple-replan-one-aggregate', 'all-blocked', 'notification-not-required', 'stale-plan-revision-shape'))
def test_fake_planner_derives_exact_closure_reply_from_script_envelope(case_id: str) -> None:
    case = next(item for item in _corpus()['scenarios'] if item['case_id'] == case_id)
    closure = case['closure']
    submission = FakeProviderAdapter(latency_seconds=0).start(
        _job(agent_name='planner', body=_planner_body(closure)),
        context=None,
        now='2026-07-12T00:00:00Z',
    )

    proposal = _payload(submission.reply, 'planner-backfill.json')
    assert proposal['mode'] == 'task_set_closure'
    assert proposal['expected_plan_revision'] == closure['expected_plan_revision']
    assert proposal['task_or_task_set_id'] == closure['task_set_id']
    assert proposal['task_or_task_set_revision'] == closure['task_set_revision']
    assert proposal['closure_evidence_digest'] == closure['ordered_terminal_evidence_digest']
    assert proposal['aggregate_result'] == closure['aggregate_result'] == case['expected']['aggregate_result']
    assert proposal['result'] == case['expected']['result'] == RESULT_BY_AGGREGATE[closure['aggregate_result']]
    for field in ('accepted_scope', 'unresolved_scope', 'blockers', 'replan_inputs', 'evidence_refs'):
        assert proposal[field] == closure[field]
    assert proposal['frontdesk_notification_required'] is closure['frontdesk_notification_required']
    status = proposal['frontdesk_status']
    for field in ('aggregate_result', 'accepted_scope', 'unresolved_scope', 'blockers', 'next_milestone', 'evidence_refs'):
        assert status[field] == proposal[field]
    assert submission.reply.count('"frontdesk_status"') == 1


def test_fake_planner_preserves_stale_digest_for_runtime_rejection() -> None:
    case = next(item for item in _corpus()['scenarios'] if item['case_id'] == 'stale-plan-revision-shape')
    reply = FakeProviderAdapter(latency_seconds=0).start(
        _job(agent_name='planner', body=_planner_body(case['closure'])),
        context=None,
        now='2026-07-12T00:00:00Z',
    ).reply
    proposal = _payload(reply, 'planner-backfill.json')

    assert proposal['expected_plan_revision'] == case['closure']['expected_plan_revision']
    assert proposal['expected_plan_revision'] != case['runtime_current_plan_revision']
    assert case['expected']['fake_outcome'] == 'reply_then_runtime_reject'


@pytest.mark.parametrize('case_id', ('malformed-missing-unresolved', 'non-success-laundering'))
def test_fake_planner_rejects_malformed_or_laundered_closure(case_id: str) -> None:
    case = next(item for item in _corpus()['scenarios'] if item['case_id'] == case_id)
    with pytest.raises(ValueError, match=case['expected']['error']):
        FakeProviderAdapter(latency_seconds=0).start(
            _job(agent_name='planner', body=_planner_body(case['closure'])),
            context=None,
            now='2026-07-12T00:00:00Z',
        )


def test_fake_frontdesk_renders_validated_user_report_without_reinterpretation() -> None:
    case = next(item for item in _corpus()['scenarios'] if item['case_id'] == 'pass-blocked-partial')
    planner_reply = FakeProviderAdapter(latency_seconds=0).start(
        _job(agent_name='planner', body=_planner_body(case['closure'])),
        context=None,
        now='2026-07-12T00:00:00Z',
    ).reply
    status = _payload(planner_reply, 'planner-backfill.json')['frontdesk_status']
    status['planner_feedback_digest'] = 'sha256:' + 'd' * 64
    body = '**frontdesk-status.json**\n```json\n' + json.dumps(status, sort_keys=True) + '\n```'

    submission = FakeProviderAdapter(latency_seconds=0).start(
        _job(agent_name='frontdesk', body=body),
        context=None,
        now='2026-07-12T00:00:00Z',
    )

    assert submission.reply == status['user_report_body']
    assert 'closure_complete' not in submission.reply
    assert status['aggregate_result'] == 'partial'
    assert status['unresolved_scope'] == case['closure']['unresolved_scope']


@pytest.mark.parametrize(
    ('field', 'value', 'error'),
    (
        ('schema', 'ccb.planner.frontdesk_status.v0', 'status schema'),
        ('unresolved_scope', [], 'non-success unresolved_scope'),
    ),
)
def test_fake_frontdesk_rejects_malformed_or_laundered_status(
    field: str,
    value: object,
    error: str,
) -> None:
    case = next(item for item in _corpus()['scenarios'] if item['case_id'] == 'pass-blocked-partial')
    planner_reply = FakeProviderAdapter(latency_seconds=0).start(
        _job(agent_name='planner', body=_planner_body(case['closure'])),
        context=None,
        now='2026-07-12T00:00:00Z',
    ).reply
    status = _payload(planner_reply, 'planner-backfill.json')['frontdesk_status']
    status[field] = value
    body = '**frontdesk-status.json**\n```json\n' + json.dumps(status, sort_keys=True) + '\n```'

    with pytest.raises(ValueError, match=error):
        FakeProviderAdapter(latency_seconds=0).start(
            _job(agent_name='frontdesk', body=body),
            context=None,
            now='2026-07-12T00:00:00Z',
        )


def test_closure_rolepack_templates_use_digest_revision_and_exact_mode() -> None:
    planner_root = WORKFLOW_DRAFTS / 'agentroles.ccb_planner'
    backfill = json.loads((planner_root / 'templates/planner-backfill.json').read_text(encoding='utf-8'))
    skill = (planner_root / 'skills/planner-closure-backfill/SKILL.md').read_text(encoding='utf-8')

    assert backfill['mode'] == 'task_set_closure'
    assert backfill['expected_plan_revision'] == 'sha256:<64 lowercase hex>'
    assert list(backfill).count('frontdesk_status') == 1
    assert 'expected_plan_revision is a digest' in skill
    assert 'pass -> closure_complete' in skill
    assert 'partial -> closure_partial' in skill
    assert 'replan_required -> task_set_replanned' in skill
    assert 'blocked -> closure_blocked' in skill
    assert 'No PlanTree write' in skill


def test_planner_and_frontdesk_command_surfaces_remain_narrow() -> None:
    planner = load_role_manifest(WORKFLOW_DRAFTS / 'agentroles.ccb_planner')
    planner_policy = load_role_command_policy(planner)
    frontdesk = load_role_manifest(WORKFLOW_DRAFTS / 'agentroles.ccb_frontdesk')
    frontdesk_policy = load_role_command_policy(frontdesk)

    assert planner_policy is not None
    assert planner_policy.allowed == ()
    assert planner_policy.provider_tools == ()
    assert claude_permission_allowlist(planner_policy) == ()
    assert {'shell_exec', 'generic_ccb', 'file_write', 'test_exec', 'wait', 'watch', 'arbitrary_target', 'notification_send'} <= set(planner_policy.forbidden_effects)

    assert frontdesk_policy is not None
    assert len(frontdesk_policy.allowed) == 1
    assert frontdesk_policy.allowed[0].required_args[-1] == 'planner'
    assert frontdesk_policy.provider_tools == (('codex', 'ccb_frontdesk_ask_planner'),)
    assert claude_permission_allowlist(frontdesk_policy) == ('Bash(ask --silence --compact --inline-request --task-id *)',)
    assert {'generic_ccb', 'file_write', 'test_exec', 'wait', 'watch', 'arbitrary_target', 'frontdesk_status_forward'} <= set(frontdesk_policy.forbidden_effects)


def test_frontdesk_rolepack_renders_only_validated_status_and_never_forwards_it() -> None:
    root = WORKFLOW_DRAFTS / 'agentroles.ccb_frontdesk'
    combined = '\n'.join(
        (root / path).read_text(encoding='utf-8')
        for path in (
            'memory.md',
            'adapters/ccb/memory.md',
            'skills/frontdesk-intake/SKILL.md',
            'templates/workflow-status-report.md',
        )
    )
    assert 'validated `ccb.planner.frontdesk_status.v1`' in combined
    assert 'byte-for-byte' in combined
    assert 'render only `user_report_body`' in combined.lower()
    assert 'never forward' in combined.lower()
    assert 'never mutate authority' in combined.lower()
