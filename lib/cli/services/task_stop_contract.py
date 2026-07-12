from __future__ import annotations

import re


_AFFIRMATIVE_DETAIL_READY_PATTERNS = (
    ('expected_stop', r'\bexpected\s+stop\s*(?::|is)\s*`?detail_ready`?\b'),
    ('terminal_expectation', r'\bterminal\s+expectation\s*(?:is\s+)?`?detail_ready`?\b'),
    (
        'terminal_status',
        r'\b(?:continue\s+)?with\s+terminal\s+status\s*(?:is\s+)?`?detail_ready`?\b',
    ),
    (
        'normative_stop',
        r'\b(?:must|shall)\b[^.!?\n]{0,120}\bstop\s+(?:at|as|on)\s+`?detail_ready`?\b',
    ),
    (
        'controller_visible_outcome',
        r'\bcontroller-visible\s+(?:task\s+)?outcome\s+remains\s+`?detail_ready`?\b',
    ),
)
_NEGATION_PATTERN = re.compile(r'\b(?:do\s+not|must\s+not|is\s+not|no\s+longer)\b', re.IGNORECASE)
_WEAK_MODAL_PATTERN = re.compile(r'\b(?:may|might|could|would|should|can)\b', re.IGNORECASE)
_CONDITIONAL_PATTERN = re.compile(r'^\s*(?:if|when|unless)\b', re.IGNORECASE)
_EXAMPLE_PATTERN = re.compile(
    r'(?:\b(?:example|for\s+example|sample|hypothetical)\b|\be\.g\.)',
    re.IGNORECASE,
)
_OTHER_TASK_PATTERN = re.compile(r'\b(?:other|another)\s+task\b', re.IGNORECASE)
_EXPLICIT_TASK_PATTERN = re.compile(r'\btask\s+`?[A-Za-z0-9][A-Za-z0-9_-]*`?\s*:', re.IGNORECASE)
_CONFLICTING_STATUS_PATTERN = re.compile(r'\b(?:replan_required|blocked|done|cancelled)\b', re.IGNORECASE)
_ENUMERATION_PATTERN = re.compile(r'\b(?:allowed\s+statuses|status\s+enum|schema|token(?:s)?)\s*:', re.IGNORECASE)


def match_detail_ready_stop_contract(text: object) -> dict[str, str] | None:
    """Return evidence for an explicit, affirmative detail_ready stop contract."""
    for statement in _contract_statements(str(text or '')):
        if _unsafe_statement(statement):
            continue
        for name, pattern in _AFFIRMATIVE_DETAIL_READY_PATTERNS:
            match = re.search(pattern, statement, flags=re.IGNORECASE)
            if match:
                return {'status': 'detail_ready', 'match': name, 'statement': statement.strip()}
    return None


def _contract_statements(text: str) -> tuple[str, ...]:
    statements: list[str] = []
    fenced = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith('```') or stripped.startswith('~~~'):
            fenced = not fenced
            continue
        if fenced or not stripped or stripped.startswith('>'):
            continue
        protected = re.sub(r'\be\.g\.', 'e_g_', stripped, flags=re.IGNORECASE)
        statements.extend(
            part.replace('e_g_', 'e.g.').strip()
            for part in re.split(r'(?<=[.!?])\s+', protected)
            if part.strip()
        )
    return tuple(statements)


def _unsafe_statement(statement: str) -> bool:
    return bool(
        '?' in statement
        or _NEGATION_PATTERN.search(statement)
        or _WEAK_MODAL_PATTERN.search(statement)
        or _CONDITIONAL_PATTERN.search(statement)
        or _EXAMPLE_PATTERN.search(statement)
        or _OTHER_TASK_PATTERN.search(statement)
        or _EXPLICIT_TASK_PATTERN.search(statement)
        or _CONFLICTING_STATUS_PATTERN.search(statement)
        or _ENUMERATION_PATTERN.search(statement)
    )


__all__ = ['match_detail_ready_stop_contract']
