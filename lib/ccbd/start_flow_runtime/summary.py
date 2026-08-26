from __future__ import annotations

from dataclasses import dataclass, field

from ccbd.models import CcbdStartupAgentResult
from cli.services.tmux_project_cleanup import ProjectTmuxCleanupSummary


@dataclass(frozen=True)
class StartFlowSummary:
    project_root: str
    project_id: str
    started: tuple[str, ...]
    socket_path: str
    cleanup_summaries: tuple[ProjectTmuxCleanupSummary, ...] = ()
    actions_taken: tuple[str, ...] = ()
    agent_results: tuple[CcbdStartupAgentResult, ...] = ()
    timings_ms: dict[str, float] = field(default_factory=dict)
    ready_gate: object | None = None

    def to_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            'project_root': self.project_root,
            'project_id': self.project_id,
            'started': list(self.started),
            'socket_path': self.socket_path,
            'actions_taken': list(self.actions_taken),
            'cleanup_summaries': [
                {
                    'socket_name': item.socket_name,
                    'owned_panes': list(item.owned_panes),
                    'active_panes': list(item.active_panes),
                    'orphaned_panes': list(item.orphaned_panes),
                    'killed_panes': list(item.killed_panes),
                }
                for item in self.cleanup_summaries
            ],
            'agent_results': [item.to_record() for item in self.agent_results],
            'timings_ms': dict(self.timings_ms),
        }
        if self.ready_gate is not None:
            record['ready_gate'] = self.ready_gate.to_record()
        return record


__all__ = ['StartFlowSummary']
