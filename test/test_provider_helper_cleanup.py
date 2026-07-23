from __future__ import annotations

from types import SimpleNamespace

import provider_runtime.helper_cleanup as helper_cleanup
from provider_runtime.helper_cleanup import cleanup_stale_runtime_helper, terminate_helper_manifest_path
from provider_runtime.helper_manifest import build_runtime_helper_manifest
from storage.paths import PathLayout


def _write_helper(
    path,
    *,
    runtime_generation: int = 1,
    leader_pid: int = 777,
    pgid: int = 888,
    include_process_ref: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    process_ref = (
        ',"process_ref":{'
        '"kind":"process_tree","evidence_state":"degraded","job_id":null,'
        f'"owner_pid":{leader_pid},"root_pid":{leader_pid},"runtime_pid":{leader_pid},'
        f'"runtime_generation":{runtime_generation},"runtime_root":"{path.parent.as_posix()}/provider-runtime/codex",'
        '"source":"kill","observed_at":"2026-04-22T00:00:00Z"}'
        if include_process_ref
        else ''
    )
    path.write_text(
        (
            '{"schema_version":1,"record_type":"provider_helper_manifest","agent_name":"agent1",'
            f'"runtime_generation":{runtime_generation},"helper_kind":"codex_bridge","leader_pid":{leader_pid},"pgid":{pgid},'
            f'"started_at":"2026-04-22T00:00:00Z","owner_daemon_generation":5,"state":"running"{process_ref}}}\n'
        ),
        encoding='utf-8',
    )


def test_cleanup_stale_runtime_helper_reaps_superseded_manifest(tmp_path, monkeypatch) -> None:
    layout = PathLayout(tmp_path / 'repo')
    helper_path = layout.agent_helper_path('agent1')
    _write_helper(helper_path, runtime_generation=1, leader_pid=777, pgid=888, include_process_ref=True)
    killed: list[tuple[int, int]] = []

    monkeypatch.setattr(
        'provider_runtime.helper_cleanup._kill_helper_group',
        lambda pgid, sig: killed.append((pgid, int(sig))) or True,
    )
    monkeypatch.setattr('provider_runtime.helper_cleanup._wait_for_helper_exit', lambda leader_pid, timeout_s: True)

    reaped = cleanup_stale_runtime_helper(
        layout,
        SimpleNamespace(
            agent_name='agent1',
            provider='codex',
            runtime_generation=2,
            state='idle',
            runtime_root='/tmp/runtime-new',
        ),
    )

    assert reaped is True
    assert helper_path.exists() is False
    assert killed[0][0] == 888


def test_cleanup_stale_runtime_helper_keeps_current_owner_manifest(tmp_path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    helper_path = layout.agent_helper_path('agent1')
    _write_helper(helper_path, runtime_generation=3)

    reaped = cleanup_stale_runtime_helper(
        layout,
        SimpleNamespace(
            agent_name='agent1',
            provider='codex',
            runtime_generation=3,
            state='idle',
            runtime_root='/tmp/runtime-current',
        ),
    )

    assert reaped is False
    assert helper_path.exists() is True


def test_cleanup_stale_runtime_helper_requires_canonical_runtime_generation(tmp_path, monkeypatch) -> None:
    layout = PathLayout(tmp_path / 'repo')
    helper_path = layout.agent_helper_path('agent1')
    _write_helper(helper_path, runtime_generation=3, leader_pid=777, pgid=888, include_process_ref=True)
    killed: list[tuple[int, int]] = []

    monkeypatch.setattr(
        'provider_runtime.helper_cleanup._kill_helper_group',
        lambda pgid, sig: killed.append((pgid, int(sig))) or True,
    )
    monkeypatch.setattr('provider_runtime.helper_cleanup._wait_for_helper_exit', lambda leader_pid, timeout_s: True)

    reaped = cleanup_stale_runtime_helper(
        layout,
        SimpleNamespace(
            agent_name='agent1',
            provider='codex',
            binding_generation=3,
            runtime_generation=None,
            state='idle',
            runtime_root='/tmp/runtime-current',
        ),
    )

    assert reaped is True
    assert helper_path.exists() is False
    assert killed[0][0] == 888


def test_terminate_helper_manifest_path_clears_file_when_leader_is_gone(tmp_path, monkeypatch) -> None:
    layout = PathLayout(tmp_path / 'repo')
    helper_path = layout.agent_helper_path('agent1')
    _write_helper(helper_path, leader_pid=501, pgid=601, include_process_ref=True)
    killed: list[tuple[int, int]] = []

    monkeypatch.setattr(
        'provider_runtime.helper_cleanup._kill_helper_group',
        lambda pgid, sig: killed.append((pgid, int(sig))) or True,
    )
    monkeypatch.setattr('provider_runtime.helper_cleanup._wait_for_helper_exit', lambda leader_pid, timeout_s: True)

    assert terminate_helper_manifest_path(helper_path) is True
    assert helper_path.exists() is False
    assert killed[0][0] == 601


def test_terminate_helper_manifest_path_uses_windows_tree_cleanup_without_sigkill(tmp_path, monkeypatch) -> None:
    layout = PathLayout(tmp_path / 'repo')
    helper_path = layout.agent_helper_path('agent1')
    _write_helper(helper_path, leader_pid=501, pgid=0, include_process_ref=True)
    terminated: list[int] = []

    monkeypatch.setattr(helper_cleanup.os, 'name', 'nt')
    monkeypatch.delattr(helper_cleanup.signal, 'SIGKILL', raising=False)
    monkeypatch.setattr(helper_cleanup, '_is_pid_alive', lambda pid: True)
    monkeypatch.setattr(
        helper_cleanup,
        '_shared_terminate_pid_tree',
        lambda pid, timeout_s, is_pid_alive_fn: terminated.append(pid) or True,
    )

    assert terminate_helper_manifest_path(helper_path) is True
    assert terminated == [501]
    assert helper_path.exists() is False


def test_build_runtime_helper_manifest_includes_process_ref(tmp_path) -> None:
    runtime_root = tmp_path / 'repo' / '.ccb' / 'agents' / 'agent1' / 'provider-runtime' / 'codex'
    runtime_root.mkdir(parents=True)
    (runtime_root / 'bridge.pid').write_text('777\n', encoding='utf-8')

    manifest = build_runtime_helper_manifest(
        SimpleNamespace(
            agent_name='agent1',
            provider='codex',
            runtime_root=str(runtime_root),
            runtime_pid=888,
            pid=888,
            runtime_generation=4,
            started_at='2026-04-22T00:00:00Z',
            last_seen_at='2026-04-22T00:00:01Z',
            daemon_generation=9,
            process_ref=None,
        )
    )

    assert manifest is not None
    assert manifest.process_ref is not None
    assert manifest.process_ref['owner_pid'] == 777
    assert manifest.process_ref['root_pid'] == 777
    assert manifest.process_ref['runtime_generation'] == 4


def test_build_runtime_helper_manifest_uses_helper_process_ref_when_runtime_ref_points_elsewhere(tmp_path) -> None:
    runtime_root = tmp_path / 'repo' / '.ccb' / 'agents' / 'agent1' / 'provider-runtime' / 'codex'
    runtime_root.mkdir(parents=True)
    (runtime_root / 'bridge.pid').write_text('777\n', encoding='utf-8')

    manifest = build_runtime_helper_manifest(
        SimpleNamespace(
            agent_name='agent1',
            provider='codex',
            runtime_root=str(runtime_root),
            runtime_pid=888,
            pid=888,
            runtime_generation=4,
            started_at='2026-04-22T00:00:00Z',
            last_seen_at='2026-04-22T00:00:01Z',
            daemon_generation=9,
            process_ref={
                'kind': 'process_tree',
                'evidence_state': 'degraded',
                'job_id': None,
                'owner_pid': 888,
                'root_pid': 888,
                'runtime_pid': 888,
                'runtime_generation': 4,
                'runtime_root': str(runtime_root),
                'source': 'launch',
                'observed_at': '2026-04-22T00:00:00Z',
            },
        )
    )

    assert manifest is not None
    assert manifest.process_ref is not None
    assert manifest.process_ref['owner_pid'] == 777
    assert manifest.process_ref['root_pid'] == 777
    assert manifest.process_ref['runtime_pid'] == 888
