from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from agents.models import AgentState
from ccbd.api_models import JobStatus
from ccbd.project_view.runtime_status import RuntimeStatusInput, build_runtime_status
from ccbd.services.project_namespace_state import ProjectNamespaceState
from platforms.windows.herdr.lifecycle_bridge import HerdrAgentLifecycleBridge
from platforms.windows.herdr.runtime.contracts import (
    HerdrRuntimeBinding,
    HerdrRuntimeBoundPane,
    HerdrRuntimeEvent,
)
from platforms.windows.herdr.runtime.events import HerdrRuntimeEventProjector
from provider_core.herdr_hook_guard import filter_herdr_agent_hooks


ROOT = Path(__file__).resolve().parents[1]


class _Reporter:
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, object], dict[str, object]]] = []

    def report_pane_agent(self, pane: dict[str, object], **kwargs: object) -> None:
        self.calls.append((dict(pane), dict(kwargs)))


def test_integration_gate_events_feed_runtime_read_model_without_business_completion() -> None:
    binding = _binding(state='idle', seq=1)
    projector = HerdrRuntimeEventProjector(binding)

    assert projector.apply_event(_event(state='done', seq=2)) is True
    pane_status = projector.status_for_pane('pane-1')
    assert pane_status is not None

    status = build_runtime_status(
        RuntimeStatusInput(
            project_id='proj-1',
            agent_name='agent1',
            namespace=_namespace(),
            runtime=SimpleNamespace(
                pane_id='pane-1',
                runtime_generation=7,
                herdr_runtime_snapshot={
                    'source': 'event',
                    'panes': [pane_status.to_record()],
                },
            ),
            job=SimpleNamespace(status=JobStatus.RUNNING, job_id='job-open'),
        )
    )

    assert status is not None
    assert status['state'] == 'idle'
    assert status['agent_status'] == 'done'
    assert status['agent_status_source'] == 'event'
    assert status['unseen_done'] is True
    assert status['job_status'] == 'running'
    assert status['job_id'] == 'job-open'


def test_integration_gate_polling_fallback_keeps_reason_and_unknown_semantics() -> None:
    status = build_runtime_status(
        RuntimeStatusInput(
            project_id='proj-1',
            agent_name='agent1',
            namespace=_namespace(),
            runtime=SimpleNamespace(
                pane_id='pane-1',
                runtime_generation=7,
                herdr_runtime_snapshot={
                    'source': 'snapshot_polling',
                    'fallback_reason': 'runtime_events_unsupported',
                    'panes': [
                        {
                            'pane_id': 'pane-1',
                            'runtime_state': 'unknown',
                            'seq': 3,
                        }
                    ],
                },
            ),
            job=None,
        )
    )

    assert status is not None
    assert status['state'] == 'unknown'
    assert status['agent_status'] == 'unknown'
    assert status['agent_status_source'] == 'snapshot_polling'
    assert status['agent_status_fallback_reason'] == 'runtime_events_unsupported'
    assert status['agent_status_seq'] == 3


def test_integration_gate_ccb_authority_seq_and_hook_filter_do_not_compete() -> None:
    reporter = _Reporter()
    bridge = HerdrAgentLifecycleBridge(
        backend_factory=lambda: reporter,
        namespace_ref_fn=lambda: {
            'backend_impl': 'herdr',
            'session_name': 'ccb-demo',
        },
    )

    assert bridge.sync(provider='codex', state=AgentState.BUSY, pane_id='pane-1') is True
    assert bridge.sync(provider='codex', state=AgentState.IDLE, pane_id='pane-1') is True
    filtered, diagnostics = filter_herdr_agent_hooks(
        {
            'Stop': [
                {'hooks': [{'type': 'command', 'command': 'pwsh herdr-agent-state.ps1'}]},
                {'hooks': [{'type': 'command', 'command': 'echo managed-stop'}]},
            ],
        }
    )

    assert [call[1]['seq'] for call in reporter.calls] == [1, 2]
    assert reporter.calls[0][1]['provider_kind'] == 'codex'
    assert reporter.calls[0][1]['state'] == 'working'
    assert filtered['Stop'][0]['hooks'][0]['command'] == 'echo managed-stop'  # type: ignore[index]
    assert diagnostics['status'] == 'risk_detected'
    assert diagnostics['seq_policy'] == 'ccb_monotonic_seq_not_hook_time_ns'


def test_integration_gate_docs_keep_wezterm_herdr_and_ensure_runtime_boundaries() -> None:
    context = _read('CONTEXT.md')
    adr = _read('docs/adr/0002-观测聚合协作模型.md')
    spec = _read('.scratch/observational-aggregation-cooperation/spec.md')
    legacy_spec = _read('.scratch/wezterm-ccb-herdr-hosting/spec.md')

    assert 'Frontend Surface' in context
    assert 'Host Runtime' in context
    assert '业务完成权威' in context
    assert '不实现 WezTermBackend' in spec
    assert 'WezTerm 是 **OS 窗口宿主' in adr
    assert '`ensure_runtime(manifest)` 定义为 Collaboration Control Plane 的长期运行时收敛职责' in spec
    assert '真正上游事件源仍待 Herdr 提供' not in legacy_spec
    assert '上游 Herdr 原生 `runtime.ensure` 成熟后再切换' not in legacy_spec


def _binding(*, state: str, seq: int) -> HerdrRuntimeBinding:
    return HerdrRuntimeBinding(
        project_id='proj-1',
        server_id='server-1',
        server_version='0.8.2',
        api_schema='Herdr API',
        session_name='ccb-demo',
        workspace_id='workspace-1',
        runtime_generation=7,
        ready=True,
        capabilities={'runtime_events': 'supported'},
        panes=(
            HerdrRuntimeBoundPane(
                slot='agent1',
                pane_id='pane-1',
                agent_id='agent1',
                provider_kind='codex',
                state=state,
                state_seq=seq,
            ),
        ),
    )


def _event(*, state: str, seq: int) -> HerdrRuntimeEvent:
    return HerdrRuntimeEvent(
        event_type='pane.agent_status_changed',
        event_id=f'evt-{seq}',
        server_id='server-1',
        session_name='ccb-demo',
        workspace_id='workspace-1',
        pane_id='pane-1',
        agent_id='agent1',
        provider_kind='codex',
        runtime_generation=7,
        seq=seq,
        state=state,
        occurred_at='2026-08-25T00:00:00Z',
    )


def _namespace() -> ProjectNamespaceState:
    return ProjectNamespaceState(
        project_id='proj-1',
        namespace_epoch=1,
        tmux_socket_path='',
        tmux_session_name='ccb-demo',
        namespace_backend_family='herdr-native',
        backend_impl='herdr',
        namespace_id='workspace-1',
        namespace_session_name='ccb-demo',
        namespace_ipc_kind='herdr_socket',
        namespace_ipc_ref='herdr://ccb-demo',
        frontend={'kind': 'wezterm', 'status': 'wezterm_tab_attached', 'mux_available': True},
        layout_version=3,
        workspace_window_name='workspace',
        ui_attachable=True,
    )


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')
