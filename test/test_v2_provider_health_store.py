from __future__ import annotations

from pathlib import Path

from provider_runtime import (
    build_process_ref,
    process_ref_allows_destructive_cleanup,
    ProgressState,
    ProviderCompletionState,
    ProviderHealthSnapshot,
    ProviderHealthSnapshotStore,
)
from storage.paths import PathLayout


def test_provider_health_snapshot_store_tracks_job_history(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    store = ProviderHealthSnapshotStore(layout)

    store.append(
        ProviderHealthSnapshot(
            job_id='job-1',
            provider='codex',
            agent_name='Agent1',
            runtime_alive=True,
            session_reachable=True,
            progress_state=ProgressState.ACCEPTED,
            completion_state=ProviderCompletionState.NOT_COMPLETE,
            last_progress_at='2026-03-30T12:00:00Z',
            observed_at='2026-03-30T12:00:00Z',
            diagnostics={'phase': 'accepted'},
        )
    )
    store.append(
        ProviderHealthSnapshot(
            job_id='job-1',
            provider='codex',
            agent_name='agent1',
            runtime_alive=True,
            session_reachable=True,
            progress_state=ProgressState.OUTPUT_ADVANCING,
            completion_state=ProviderCompletionState.TERMINAL_COMPLETE,
            last_progress_at='2026-03-30T12:00:03Z',
            observed_at='2026-03-30T12:00:05Z',
            diagnostics={'phase': 'complete'},
        )
    )

    latest = store.latest('job-1')
    assert latest is not None
    assert latest.agent_name == 'agent1'
    assert latest.progress_state is ProgressState.OUTPUT_ADVANCING
    assert latest.completion_state is ProviderCompletionState.TERMINAL_COMPLETE
    assert len(store.list_job('job-1')) == 2
    assert len(store.list_all()) == 2


def test_process_ref_records_job_identity_without_handle(tmp_path: Path) -> None:
    runtime_root = tmp_path / 'repo' / '.ccb' / 'agents' / 'agent1' / 'provider-runtime' / 'codex'
    runtime = type(
        'Runtime',
        (),
        {
            'runtime_pid': 501,
            'pid': 501,
            'runtime_generation': 3,
            'runtime_root': str(runtime_root),
        },
    )()

    process_ref = build_process_ref(
        runtime=runtime,
        source='launch',
        clock=lambda: '2026-07-22T00:00:00Z',
        job_id='job:agent1:3',
        owner_pid=501,
        os_name='nt',
    )

    assert process_ref is not None
    assert process_ref['kind'] == 'windows_job_object'
    assert process_ref['evidence_state'] == 'attached'
    assert process_ref['job_id'] == 'job:agent1:3'
    assert 'handle' not in process_ref
    assert process_ref_allows_destructive_cleanup(
        process_ref,
        runtime=runtime,
        project_root=tmp_path / 'repo',
        pid=501,
    ) is True


def test_process_ref_cleanup_requires_runtime_generation(tmp_path: Path) -> None:
    runtime_root = tmp_path / 'repo' / '.ccb' / 'agents' / 'agent1'
    ref = {
        'kind': 'process_tree',
        'evidence_state': 'degraded',
        'job_id': None,
        'owner_pid': 501,
        'root_pid': 501,
        'runtime_pid': 501,
        'runtime_generation': None,
        'runtime_root': str(runtime_root),
        'source': 'kill',
        'observed_at': '2026-07-22T00:00:00Z',
    }
    runtime = type('Runtime', (), {'runtime_pid': 501, 'pid': 501, 'runtime_generation': 3, 'runtime_root': str(runtime_root)})()

    assert process_ref_allows_destructive_cleanup(ref, runtime=runtime, project_root=tmp_path / 'repo', pid=501) is False
    ref['runtime_generation'] = 4
    assert process_ref_allows_destructive_cleanup(ref, runtime=runtime, project_root=tmp_path / 'repo', pid=501) is False
    ref['runtime_generation'] = 3
    assert process_ref_allows_destructive_cleanup(ref, runtime=runtime, project_root=tmp_path / 'repo', pid=501) is True
