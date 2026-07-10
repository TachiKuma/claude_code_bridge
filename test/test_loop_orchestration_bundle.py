from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from cli.services.loop_orchestration_bundle import (
    ORCHESTRATION_BUNDLE_CANDIDATE_SCHEMA,
    build_single_node_candidate,
    bundle_digest,
    bundle_text,
    load_task_orchestration_bundle,
    normalize_bundle_candidate,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _record(project_root: Path, *, task_id: str = 'task-bundle') -> dict[str, object]:
    task_root = project_root / 'docs' / 'plantree' / 'plans' / 'demo' / 'tasks' / task_id
    artifacts: dict[str, dict[str, object]] = {}
    for kind, filename, text in (
        ('task_packet', 'task_packet.md', 'Build the requested feature.\n'),
        (
            'execution_contract',
            'execution_contract.md',
            'allowed_change_paths:\n- src/core/\n- src/cli/\n- tests/\nverification: python -m pytest\n',
        ),
        ('orchestration_notes', 'orchestration_notes.md', 'route: direct_execution\n'),
    ):
        path = task_root / filename
        _write(path, text)
        artifacts[kind] = {
            'path': path.relative_to(project_root).as_posix(),
            'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        }
    return {
        'task_id': task_id,
        'task_root': task_root.relative_to(project_root).as_posix(),
        'artifacts': artifacts,
    }


def _node(
    *,
    node_id: str,
    workgroup_id: str,
    allowed_paths: list[str],
    execution_contract_ref: str,
    depends_on: list[str] | None = None,
    integration_order: int,
) -> dict[str, object]:
    return {
        'node_id': node_id,
        'workgroup_id': workgroup_id,
        'worker_profile': 'coder',
        'reviewer_profile': 'code_reviewer',
        'depends_on': depends_on or [],
        'parallel_group': 'wave-1' if not depends_on else 'wave-2',
        'work_packet': f'Implement {node_id} and return verification evidence.',
        'allowed_paths': allowed_paths,
        'acceptance_refs': [execution_contract_ref],
        'verification_refs': [execution_contract_ref],
        'integration_order': integration_order,
    }


def _candidate(record: dict[str, object], nodes: list[dict[str, object]]) -> dict[str, object]:
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    return {
        'schema': ORCHESTRATION_BUNDLE_CANDIDATE_SCHEMA,
        'task_id': record['task_id'],
        'bundle_revision': 1,
        'nodes': nodes,
        'integration': {
            'verification_refs': [contract_ref],
            'project_root_verification_refs': [contract_ref],
        },
        'policy': {
            'max_node_rework_rounds': 1,
            'on_required_node_failure': 'partial_or_blocked',
            'on_structural_failure': 'replan_required',
        },
    }


def test_bundle_normalizes_two_disjoint_parallel_workgroups(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    candidate = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            ),
            _node(
                node_id='node-002',
                workgroup_id='wg-002',
                allowed_paths=['src/cli/'],
                execution_contract_ref=contract_ref,
                integration_order=20,
            ),
        ],
    )

    bundle, packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        source='test',
    )

    assert bundle['schema'] == 'ccb.loop.orchestration_bundle.v1'
    assert bundle['source'] == 'test'
    assert [node['node_id'] for node in bundle['nodes']] == ['node-001', 'node-002']
    assert set(packets) == {
        f'{record["task_root"]}/orchestration/work-packets/node-001.md',
        f'{record["task_root"]}/orchestration/work-packets/node-002.md',
    }


@pytest.mark.parametrize('count', [1, 2, 3, 4])
def test_bundle_supports_one_to_four_workgroups_with_deterministic_order(
    tmp_path: Path,
    count: int,
) -> None:
    project_root = tmp_path / f'repo-{count}'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    scopes = ['src/core/', 'src/cli/', 'tests/core/', 'tests/cli/']
    nodes = [
        _node(
            node_id=f'node-{index:03d}',
            workgroup_id=f'wg-{index:03d}',
            allowed_paths=[scopes[index - 1]],
            execution_contract_ref=contract_ref,
            integration_order=index * 10,
        )
        for index in range(1, count + 1)
    ]

    ordered, _packets = normalize_bundle_candidate(
        _candidate(record, nodes),
        record=record,
        project_root=project_root,
        source='test',
    )
    reversed_order, _reversed_packets = normalize_bundle_candidate(
        _candidate(record, list(reversed(nodes))),
        record=record,
        project_root=project_root,
        source='test',
    )

    assert [node['node_id'] for node in ordered['nodes']] == [f'node-{index:03d}' for index in range(1, count + 1)]
    assert reversed_order == ordered
    assert bundle_digest(reversed_order) == bundle_digest(ordered)


def test_bundle_rejects_more_than_four_workgroups_and_missing_root_fields(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    oversized = _candidate(
        record,
        [
            _node(
                node_id=f'node-{index:03d}',
                workgroup_id=f'wg-{index:03d}',
                allowed_paths=[f'src/core/{index}/'],
                execution_contract_ref=contract_ref,
                integration_order=index * 10,
            )
            for index in range(1, 6)
        ],
    )
    with pytest.raises(ValueError, match='exceeds max_workgroups=4'):
        normalize_bundle_candidate(oversized, record=record, project_root=project_root, source='test')

    missing_policy = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            )
        ],
    )
    missing_policy.pop('policy')
    with pytest.raises(ValueError, match='missing fields: policy'):
        normalize_bundle_candidate(missing_policy, record=record, project_root=project_root, source='test')


def test_bundle_rejects_parallel_scope_overlap(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    candidate = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            ),
            _node(
                node_id='node-002',
                workgroup_id='wg-002',
                allowed_paths=['src/core/api.py'],
                execution_contract_ref=contract_ref,
                integration_order=20,
            ),
        ],
    )

    with pytest.raises(ValueError, match='overlapping allowed paths'):
        normalize_bundle_candidate(candidate, record=record, project_root=project_root, source='test')


def test_bundle_accepts_overlapping_scope_when_dependency_orders_nodes(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    candidate = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            ),
            _node(
                node_id='node-002',
                workgroup_id='wg-002',
                allowed_paths=['src/core/api.py'],
                execution_contract_ref=contract_ref,
                depends_on=['node-001'],
                integration_order=20,
            ),
        ],
    )

    bundle, _packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        source='test',
    )

    assert bundle['nodes'][1]['depends_on'] == ['node-001']


def test_bundle_rejects_cycle_and_scope_outside_execution_contract(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    cycle = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                depends_on=['node-002'],
                integration_order=10,
            ),
            _node(
                node_id='node-002',
                workgroup_id='wg-002',
                allowed_paths=['src/cli/'],
                execution_contract_ref=contract_ref,
                depends_on=['node-001'],
                integration_order=20,
            ),
        ],
    )
    with pytest.raises(ValueError, match='dependency cycle'):
        normalize_bundle_candidate(cycle, record=record, project_root=project_root, source='test')

    outside = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['README.md'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            )
        ],
    )
    with pytest.raises(ValueError, match='exceed execution contract scope'):
        normalize_bundle_candidate(outside, record=record, project_root=project_root, source='test')


def test_single_node_bundle_round_trips_and_detects_stale_task_digest(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    candidate = build_single_node_candidate(record, project_root=project_root)
    bundle, packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        source='deterministic_single_node',
    )
    for relative, text in packets.items():
        _write(project_root / relative, text)
    bundle_path = project_root / record['task_root'] / 'orchestration_bundle.json'
    text = bundle_text(bundle)
    _write(bundle_path, text)
    record['artifacts']['orchestration_bundle'] = {
        'path': bundle_path.relative_to(project_root).as_posix(),
        'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'bundle_digest': bundle_digest(bundle),
    }

    loaded, artifact = load_task_orchestration_bundle(project_root, record)
    assert loaded == bundle
    assert artifact['bundle_digest'] == bundle_digest(bundle)

    record['artifacts']['execution_contract']['sha256'] = 'changed'
    with pytest.raises(ValueError, match='task_digest is stale'):
        load_task_orchestration_bundle(project_root, record)


def test_bundle_loader_rejects_tampered_normalized_node_even_with_updated_file_digest(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    candidate = build_single_node_candidate(record, project_root=project_root)
    bundle, packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        source='deterministic_single_node',
    )
    for relative, text in packets.items():
        _write(project_root / relative, text)
    bundle['nodes'][0]['worker_profile'] = 'untrusted_worker'
    bundle_path = project_root / record['task_root'] / 'orchestration_bundle.json'
    text = bundle_text(bundle)
    _write(bundle_path, text)
    record['artifacts']['orchestration_bundle'] = {
        'path': bundle_path.relative_to(project_root).as_posix(),
        'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'bundle_digest': bundle_digest(bundle),
        'task_digest': bundle['task_digest'],
    }

    with pytest.raises(ValueError, match='worker_profile must be coder'):
        load_task_orchestration_bundle(project_root, record)
