import pytest

from cli.services.task_stop_contract import match_detail_ready_stop_contract


@pytest.mark.parametrize(
    'text',
    (
        'Expected stop: detail_ready',
        'Terminal expectation detail_ready.',
        'Preserve terminal expectation detail_ready.',
        'Continue with terminal status detail_ready.',
        'Proceed with terminal status detail_ready.',
        'The task must stop at detail_ready.',
        'The task shall stop as detail_ready.',
        'The controller-visible task outcome remains detail_ready.',
    ),
)
def test_match_detail_ready_stop_contract_accepts_explicit_normative_text(text: str) -> None:
    assert match_detail_ready_stop_contract(text) is not None


@pytest.mark.parametrize(
    'text',
    (
        'Do not preserve terminal expectation detail_ready.',
        'The task must not stop at detail_ready.',
        'detail_ready is not the terminal expectation.',
        'detail_ready is no longer the terminal expectation.',
        'The task may stop at detail_ready.',
        'The task might stop at detail_ready.',
        'The task could stop at detail_ready.',
        'The task would stop at detail_ready.',
        'The task should stop at detail_ready.',
        'The task can stop at detail_ready.',
        'If validation succeeds, expected stop: detail_ready.',
        'Should the expected stop be detail_ready?',
        'Example: Expected stop: detail_ready.',
        'For example, terminal expectation detail_ready.',
        'e.g. expected stop: detail_ready',
        'Sample: terminal expectation detail_ready.',
        'Hypothetical: expected stop: detail_ready.',
        '```\nExpected stop: detail_ready\n```',
        '> Expected stop: detail_ready',
        'Other task phase6b-l3: expected stop: detail_ready.',
        'Task phase6b-l3-other: expected stop: detail_ready.',
        'Expected stop: detail_ready, not replan_required.',
        'Expected stop: detail_ready or blocked.',
        'Allowed statuses: detail_ready, replan_required, blocked.',
        'detail_ready',
        'status enum: detail_ready',
    ),
)
def test_match_detail_ready_stop_contract_rejects_unsafe_context(text: str) -> None:
    assert match_detail_ready_stop_contract(text) is None
