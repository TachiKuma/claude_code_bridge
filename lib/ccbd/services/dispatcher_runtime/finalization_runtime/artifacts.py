from __future__ import annotations

from dataclasses import replace

from completion.models import CompletionDecision, CompletionStatus
from storage.text_artifacts import artifact_stub, maybe_spill_text, write_text_artifact


def spill_terminal_reply_if_needed(
    dispatcher,
    current,
    decision: CompletionDecision,
    *,
    finished_at: str,
) -> CompletionDecision:
    diagnostics = dict(decision.diagnostics or {})
    if isinstance(diagnostics.get('reply_artifact'), dict):
        return decision
    if _force_reply_artifact(current):
        artifact = write_text_artifact(
            dispatcher._layout,
            text=decision.reply,
            kind='completion-reply',
            owner_id=current.job_id,
            now=finished_at,
        )
        reply = _forced_reply_artifact_stub(current, decision, artifact)
        diagnostics['artifact_reply_forced'] = True
    else:
        reply, artifact = maybe_spill_text(
            dispatcher._layout,
            text=decision.reply,
            kind='completion-reply',
            owner_id=current.job_id,
            prefix=f'CCB completion reply for job {current.job_id} is larger than 4 KiB and was stored as an artifact.',
            now=finished_at,
        )
    if artifact is None:
        return decision
    diagnostics['reply_artifact'] = artifact
    return replace(decision, reply=reply, diagnostics=diagnostics)


def _force_reply_artifact(current) -> bool:
    options = dict(getattr(current.request, 'route_options', None) or {})
    return bool(options.get('artifact_reply'))


def _forced_reply_artifact_stub(current, decision: CompletionDecision, artifact: dict[str, object]) -> str:
    if _is_empty_unsuccessful_reply(decision, artifact):
        reason = str(getattr(decision, 'reason', '') or 'unknown')
        lines = [
            (
                f'No provider completion reply was captured for job {current.job_id}; '
                'an empty --artifact-reply artifact was recorded for diagnostics.'
            ),
            f'Reason: {reason}',
            f"Full text: {artifact.get('path')}",
            f"Bytes: {artifact.get('bytes')}",
            f"SHA256: {artifact.get('sha256')}",
            '',
            'Instruction: do not treat this artifact as a successful reply; inspect trace/diagnostics and workspace evidence before acting.',
        ]
        return '\n'.join(lines).rstrip()
    return artifact_stub(
        prefix=f'CCB completion reply for job {current.job_id} was stored as an artifact by --artifact-reply.',
        artifact=artifact,
        include_preview=False,
    )


def _is_empty_unsuccessful_reply(decision: CompletionDecision, artifact: dict[str, object]) -> bool:
    if getattr(decision, 'status', None) is CompletionStatus.COMPLETED:
        return False
    try:
        return int(artifact.get('bytes') or 0) == 0
    except (TypeError, ValueError):
        return False


__all__ = ['spill_terminal_reply_if_needed']
