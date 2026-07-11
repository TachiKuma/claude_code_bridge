#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ROLE_IDS = (
    'agentroles.ccb_frontdesk',
    'agentroles.ccb_planner',
    'agentroles.ccb_task_detailer',
    'agentroles.ccb_orchestrator',
    'agentroles.ccb_round_reviewer',
    'agentroles.coder',
    'agentroles.code_reviewer',
)
PLAN_SLUG = 'g5-fake-fullflow'
TASK_ID = 'g5-multi-workgroup-task'
TERMINAL_JOB_STATUSES = {'completed', 'failed', 'cancelled', 'timed_out'}


class SmokeFailure(RuntimeError):
    pass


def build_v3_config() -> str:
    return '''version = 3

[workflow]
mode = "agentic-loop"
profile = "agentic_loop_v1"
entry_role = "frontdesk"

[workflow.defaults]
provider = "fake"

[workflow.defaults.resident]
workspace_mode = "inplace"

[workflow.defaults.dynamic]
workspace_mode = "inplace"
reuse = "always_new"

[workflow.runtime]
max_workgroups = 4
max_parallel_workgroups = 4
max_active_dynamic_agents = 9
max_node_rework_rounds = 1
execution_window_max_panes = 6
multi_workgroup_workspace = "git-worktree-required"
integration_policy = "controller-owned"
default_lifetime = "current_activation"
name_template = "loop-{loop_id}-{node_id}-{profile}"
release_policy = "auto"
window_policy = "auto"

[workflow.resident.frontdesk]
role = "agentroles.ccb_frontdesk"

[workflow.resident.planner]
role = "agentroles.ccb_planner"

[workflow.dynamic.task_detailer]
role = "agentroles.ccb_task_detailer"
max_instances = 1

[workflow.dynamic.orchestrator]
role = "agentroles.ccb_orchestrator"
max_instances = 1

[workflow.dynamic.coder]
role = "agentroles.coder"
provider = "fake"
workspace_mode = "git-worktree"
max_instances = 4
legacy_aliases = ["worker"]

[workflow.dynamic.code_reviewer]
role = "agentroles.code_reviewer"
provider = "fake"
workspace_mode = "git-worktree"
max_instances = 4

[workflow.dynamic.ccb_round_reviewer]
role = "agentroles.ccb_round_reviewer"
provider = "fake"
max_instances = 1
'''


def run_smoke(
    *,
    project_root: Path,
    count: int,
    shape: str,
    ccb_test: Path,
    keep_running: bool = False,
    command_timeout_s: int = 240,
) -> dict[str, Any]:
    project_root = project_root.expanduser().resolve(strict=False)
    test_root = project_root.parent
    ccb_test = ccb_test.expanduser().resolve(strict=True)
    _validate_matrix(count=count, shape=shape)
    if project_root.exists():
        raise SmokeFailure(f'fresh project root already exists: {project_root}')
    project_root.mkdir(parents=True)
    role_store = project_root / 'roles'
    source_home = project_root / '.source-home'
    source_home.mkdir()
    logs_dir = project_root / '.ccb' / 'evidence' / 'g5-fake-fullflow' / 'logs'
    logs_dir.mkdir(parents=True)
    command_log: list[dict[str, Any]] = []
    env = _smoke_env(
        test_root=test_root,
        project_root=project_root,
        role_store=role_store,
        source_home=source_home,
    )
    report_path = project_root / '.ccb' / 'evidence' / 'g5-fake-fullflow' / 'report.json'
    cleanup_result: dict[str, Any] | None = None
    try:
        _prepare_repository(project_root)
        _write_config_and_plan(project_root)
        for role_id in ROLE_IDS:
            _run_logged(
                command_log,
                f'role_install_{role_id.rsplit(".", 1)[-1]}',
                [str(ccb_test), 'roles', 'install', role_id, '--skip-tools'],
                cwd=test_root,
                env=env,
                logs_dir=logs_dir,
                timeout_s=command_timeout_s,
            )
        config_validate = _run_logged(
            command_log,
            'config_validate',
            [str(ccb_test), '--project', str(project_root), 'config', 'validate', '--json'],
            cwd=test_root,
            env=env,
            logs_dir=logs_dir,
            timeout_s=command_timeout_s,
        )
        start = _run_logged(
            command_log,
            'start',
            [str(ccb_test), '--project', str(project_root)],
            cwd=test_root,
            env=env,
            logs_dir=logs_dir,
            timeout_s=command_timeout_s,
        )
        task_create = _run_logged(
            command_log,
            'task_create',
            [
                str(ccb_test), '--project', str(project_root), 'plan', 'task-create',
                '--plan', PLAN_SLUG, '--title', 'G5 fake multi-workgroup full-flow task',
                '--task-id', TASK_ID, '--json',
            ],
            cwd=test_root,
            env=env,
            logs_dir=logs_dir,
            timeout_s=command_timeout_s,
        )
        artifacts = _write_task_inputs(project_root, count=count, shape=shape)
        artifact_results = {}
        for kind in ('task_packet', 'execution_contract'):
            artifact_results[kind] = _run_logged(
                command_log,
                f'artifact_{kind}',
                [
                    str(ccb_test), '--project', str(project_root), 'plan', 'task-artifact',
                    '--task', TASK_ID, '--kind', kind, '--file', str(artifacts[kind]), '--json',
                ],
                cwd=test_root,
                env=env,
                logs_dir=logs_dir,
                timeout_s=command_timeout_s,
            )
        _git_commit_authority(project_root)
        ready = _run_logged(
            command_log,
            'ready_for_orchestration',
            [
                str(ccb_test), '--project', str(project_root), 'plan', 'task-status',
                '--task', TASK_ID, '--status', 'ready_for_orchestration',
                '--next-owner', 'orchestrator', '--activation-reason', 'g5_fake_fullflow', '--json',
            ],
            cwd=test_root,
            env=env,
            logs_dir=logs_dir,
            timeout_s=command_timeout_s,
        )
        runner_results = []
        for attempt in range(1, 4):
            runner = _run_logged(
                command_log,
                f'loop_runner_auto_{attempt}',
                [
                    str(ccb_test), '--project', str(project_root), 'loop', 'runner', '--auto',
                    '--max-steps', '64', '--poll-interval', '0.05', '--json',
                ],
                cwd=test_root,
                env=env,
                logs_dir=logs_dir,
                timeout_s=command_timeout_s,
            )
            runner_payload = _json_object(runner['stdout'])
            runner_results.append(runner_payload)
            shown = _task_show(
                command_log,
                ccb_test=ccb_test,
                project_root=project_root,
                test_root=test_root,
                env=env,
                logs_dir=logs_dir,
                timeout_s=command_timeout_s,
                label=f'task_show_after_runner_{attempt}',
            )
            if _task_record(shown).get('status') == 'done':
                break
        task_show = _task_show(
            command_log,
            ccb_test=ccb_test,
            project_root=project_root,
            test_root=test_root,
            env=env,
            logs_dir=logs_dir,
            timeout_s=command_timeout_s,
            label='task_show_final',
        )
        ps_result = _run_logged(
            command_log,
            'ps_final',
            [str(ccb_test), '--project', str(project_root), 'ps'],
            cwd=test_root,
            env=env,
            logs_dir=logs_dir,
            timeout_s=command_timeout_s,
        )
        report = _build_report(
            project_root=project_root,
            role_store=role_store,
            count=count,
            shape=shape,
            config_validate=_json_object(config_validate['stdout']),
            start_stdout=start['stdout'],
            task_create=_json_object(task_create['stdout']),
            artifact_results={key: _json_object(value['stdout']) for key, value in artifact_results.items()},
            ready=_json_object(ready['stdout']),
            runner_results=runner_results,
            task_show=task_show,
            ps_text=ps_result['stdout'],
            command_log=command_log,
        )
        _require_report_pass(report)
        _write_json(report_path, report)
        if not keep_running:
            cleanup_result = _run_logged(
                command_log,
                'external_cleanup',
                [str(ccb_test), '--project', str(project_root), 'kill', '-f'],
                cwd=test_root,
                env=env,
                logs_dir=logs_dir,
                timeout_s=command_timeout_s,
                allow_failure=True,
            )
            report['external_cleanup'] = _compact_command(cleanup_result)
            report['command_log'] = [_compact_command(item) for item in command_log]
            _write_json(report_path, report)
        return report
    except Exception as exc:
        failure = {
            'schema': 'ccb.g5.fake_multi_workgroup_smoke.v1',
            'status': 'failed',
            'project_root': str(project_root),
            'count': count,
            'shape': shape,
            'error': str(exc),
            'command_log': [_compact_command(item) for item in command_log],
        }
        _write_json(report_path, failure)
        if not keep_running and cleanup_result is None:
            try:
                _run_logged(
                    command_log,
                    'failure_cleanup',
                    [str(ccb_test), '--project', str(project_root), 'kill', '-f'],
                    cwd=test_root,
                    env=env,
                    logs_dir=logs_dir,
                    timeout_s=command_timeout_s,
                    allow_failure=True,
                )
            except Exception:
                pass
        raise


def _build_report(
    *,
    project_root: Path,
    role_store: Path,
    count: int,
    shape: str,
    config_validate: dict[str, Any],
    start_stdout: str,
    task_create: dict[str, Any],
    artifact_results: dict[str, dict[str, Any]],
    ready: dict[str, Any],
    runner_results: list[dict[str, Any]],
    task_show: dict[str, Any],
    ps_text: str,
    command_log: list[dict[str, Any]],
) -> dict[str, Any]:
    task = _task_record(task_show)
    bundle_artifact = _mapping(_mapping(task.get('artifacts')).get('orchestration_bundle'))
    bundle_path = project_root / str(bundle_artifact.get('path') or '')
    bundle = _read_json(bundle_path)
    loop_id = str(_mapping(task.get('current_loop')).get('loop_id') or '')
    if not loop_id:
        loop_id = _find_loop_id(project_root, TASK_ID)
    loop_dir = project_root / '.ccb' / 'runtime' / 'loops' / loop_id
    scheduler_state_path = loop_dir / 'workgroup_scheduler_state.json'
    round_path = loop_dir / 'round.json'
    integration_path = loop_dir / 'git-transaction.json'
    scheduler = _read_json(scheduler_state_path)
    round_record = _read_json(round_path)
    integration = _read_json(integration_path)
    jobs = _collect_jobs(project_root)
    node_records = []
    for node_id in sorted(_mapping(scheduler.get('nodes'))):
        node = _mapping(_mapping(scheduler['nodes']).get(node_id))
        integration_node = _mapping(_mapping(integration.get('nodes')).get(node_id))
        worker = _mapping(node.get('worker_rework') or node.get('worker'))
        reviewer = _mapping(node.get('reviewer_recheck') or node.get('reviewer'))
        node_records.append(
            {
                'node_id': node_id,
                'dependencies': list(node.get('depends_on') or ()),
                'status': node.get('status'),
                'worker_agent': node.get('worker_agent'),
                'reviewer_agent': node.get('reviewer_agent'),
                'worker_job_id': worker.get('job_id'),
                'worker_job_status': worker.get('status'),
                'reviewer_job_id': reviewer.get('job_id'),
                'reviewer_job_status': reviewer.get('status'),
                'worktree_path': integration_node.get('worktree_path'),
                'worktree_exists_after_cleanup': Path(str(integration_node.get('worktree_path') or '')).exists(),
                'branch': integration_node.get('branch'),
                'base_commit': integration_node.get('base_commit'),
                'reviewed_commit': integration_node.get('reviewed_commit'),
                'tree_digest': integration_node.get('tree_digest'),
            }
        )
    round_reviewer = _mapping(scheduler.get('round_reviewer'))
    topology = _mapping(round_record.get('topology'))
    release = _mapping(round_record.get('release') or topology.get('release'))
    observed_evidence = _mapping(topology.get('observed_evidence'))
    observed_path = Path(str(observed_evidence.get('path') or ''))
    raw_observed = _read_json(observed_path)
    integration_section = _mapping(integration.get('integration'))
    root_section = _mapping(integration.get('root'))
    expected_paths = [f'g5_outputs/node-{index:03d}.txt' for index in range(1, count + 1)]
    actual_paths = [path for path in expected_paths if (project_root / path).is_file()]
    dynamic_lines = [
        line for line in ps_text.splitlines()
        if 'source=loop' in line or 'loop-' + loop_id in line
    ]
    orchestrator_jobs = [
        item for item in jobs.values()
        if item.get('agent_name') and 'orchestrator' in str(item.get('agent_name'))
    ]
    runner_steps = [
        step
        for result in runner_results
        for step in result.get('steps') or ()
        if isinstance(step, dict)
    ]
    initial_frontier = next(
        (
            step for step in runner_steps
            if step.get('scheduler_action') == 'submitted_ready_frontier'
        ),
        {},
    )
    expected_initial_frontier_size = count if shape == 'parallel' else count - 1
    checks = {
        'config_v3_valid': (
            config_validate.get('config_version') == 3
            and config_validate.get('config_status') == 'valid'
        ),
        'start_succeeded': 'start_status: ok' in start_stdout,
        'task_created': bool(task_create),
        'task_artifacts_imported': all(bool(payload) for payload in artifact_results.values()),
        'ready_for_orchestration': ready.get('status') == 'ready_for_orchestration',
        'bundle_schema': bundle.get('schema') == 'ccb.loop.orchestration_bundle.v1',
        'bundle_node_count': len(bundle.get('nodes') or ()) == count,
        'bundle_capacity_digest': bool(bundle.get('capacity_digest')),
        'scheduler_terminal': scheduler.get('status') == 'pass',
        'all_nodes_integrated': all(item['status'] == 'integrated' for item in node_records),
        'all_jobs_completed': all(
            item.get(field) == 'completed'
            for item in node_records
            for field in ('worker_job_status', 'reviewer_job_status')
        ) and round_reviewer.get('status') == 'completed',
        'all_nodes_reviewed_commits': all(bool(item['reviewed_commit']) for item in node_records),
        'root_files_promoted': actual_paths == expected_paths,
        'merge_order_complete': integration_section.get('merge_order') == [item['node_id'] for item in node_records],
        'root_verification_passed': _mapping(root_section.get('verification')).get('status') == 'passed',
        'task_done': task.get('status') == 'done',
        'round_pass': round_record.get('round_result') == 'pass',
        'round_source_script_owned': round_record.get('round_result_source') == 'round_reviewer_reply',
        'release_clean': release.get('loop_topology_status') == 'released'
        and int(release.get('retained_count') or 0) == 0
        and int(release.get('release_incomplete_count') or 0) == 0,
        'raw_observed_exists': observed_path.is_file(),
        'raw_observed_no_live_agents': not _live_observed_agents(raw_observed),
        'dynamic_residue_absent': not dynamic_lines,
        'orchestrator_job_completed': any(item.get('status') == 'completed' for item in orchestrator_jobs),
        'initial_frontier_submitted_in_parallel': (
            len(initial_frontier.get('pending_job_ids') or ()) == expected_initial_frontier_size
        ),
        'git_root_not_drifted': not _git_status(project_root),
    }
    return {
        'schema': 'ccb.g5.fake_multi_workgroup_smoke.v1',
        'status': 'pass' if all(checks.values()) else 'failed',
        'project_root': str(project_root),
        'project_id': task_show.get('project_id'),
        'role_store': str(role_store),
        'provider': 'fake',
        'config_version': 3,
        'matrix': {'requested_count': count, 'requested_shape': shape},
        'task_id': TASK_ID,
        'loop_id': loop_id,
        'bundle': {
            'path': str(bundle_path),
            'bundle_revision': bundle.get('bundle_revision'),
            'bundle_digest': round_record.get('bundle_digest'),
            'task_digest': bundle.get('task_digest'),
            'capacity_digest': bundle.get('capacity_digest'),
            'node_count': len(bundle.get('nodes') or ()),
            'selection': bundle.get('selection'),
            'dependencies': {
                str(node.get('node_id')): list(node.get('depends_on') or ())
                for node in bundle.get('nodes') or () if isinstance(node, dict)
            },
        },
        'jobs': {
            'orchestrator': orchestrator_jobs,
            'nodes': node_records,
            'round_reviewer': round_reviewer,
        },
        'integration': {
            'state_path': str(integration_path),
            'status': integration.get('status'),
            'merge_order': integration_section.get('merge_order'),
            'checks': integration_section.get('checks'),
            'root': root_section,
        },
        'task': {
            'status': task.get('status'),
            'next_owner': task.get('next_owner'),
            'current_loop': task.get('current_loop'),
        },
        'round': {
            'path': str(round_path),
            'result': round_record.get('round_result'),
            'source': round_record.get('round_result_source'),
            'round_reviewer_job_id': round_reviewer.get('job_id'),
        },
        'release': {
            'released_count': release.get('released_count'),
            'retained_count': release.get('retained_count'),
            'release_incomplete_count': release.get('release_incomplete_count'),
            'observed_path': str(observed_path),
            'observed_agents': raw_observed.get('agents'),
            'live_agents': _live_observed_agents(raw_observed),
            'dynamic_residue': dynamic_lines,
        },
        'root_changes': {
            'expected_paths': expected_paths,
            'actual_paths': actual_paths,
            'git_status': _git_status(project_root),
        },
        'runner_results': runner_results,
        'execution': {
            'initial_frontier_job_ids': list(initial_frontier.get('pending_job_ids') or ()),
            'expected_initial_frontier_size': expected_initial_frontier_size,
        },
        'checks': checks,
        'paths': {
            'report': str(project_root / '.ccb' / 'evidence' / 'g5-fake-fullflow' / 'report.json'),
            'scheduler_state': str(scheduler_state_path),
            'round': str(round_path),
            'integration_state': str(integration_path),
            'raw_observed': str(observed_path),
        },
        'command_log': [_compact_command(item) for item in command_log],
    }


def _prepare_repository(project_root: Path) -> None:
    (project_root / '.gitignore').write_text(
        '/.ccb/\n/roles/\n/.source-home/\n/bin/\n'
        f'/docs/plantree/plans/{PLAN_SLUG}/tasks/\n',
        encoding='utf-8',
    )
    _git(project_root, 'init')
    _git(project_root, 'config', 'user.name', 'G5 Smoke')
    _git(project_root, 'config', 'user.email', 'g5-smoke@localhost')


def _write_config_and_plan(project_root: Path) -> None:
    config_path = project_root / '.ccb' / 'ccb.config'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(build_v3_config(), encoding='utf-8')
    plan_root = project_root / 'docs' / 'plantree' / 'plans' / PLAN_SLUG
    plan_root.mkdir(parents=True)
    (plan_root / 'README.md').write_text('# G5 Fake Full-Flow Plan\n', encoding='utf-8')
    _git(project_root, 'add', '.gitignore', 'docs')
    _git(project_root, 'commit', '-m', 'G5 smoke base')


def _write_task_inputs(project_root: Path, *, count: int, shape: str) -> dict[str, Path]:
    inputs = project_root / '.ccb' / 'evidence' / 'g5-fake-fullflow' / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    paths = [f'g5_outputs/node-{index:03d}.txt' for index in range(1, count + 1)]
    contract = json.dumps({'count': count, 'shape': shape, 'allowed_paths': paths}, sort_keys=True)
    allowed_lines = '\n'.join(f'- {path}' for path in paths)
    verification_lines = '\n'.join(
        '- python -c "from pathlib import Path; assert Path(\'' + path + '\').is_file()"'
        for path in paths
    )
    task_packet = inputs / 'task_packet.md'
    execution_contract = inputs / 'execution_contract.md'
    task_packet.write_text(
        '# Task Packet\n\n'
        f'g5_multi_workgroup_smoke: {contract}\n\n'
        'Goal: exercise the real G3 scheduler, R2 integration, and T1 topology with fake provider jobs.\n\n'
        'Allowed Change Paths:\n'
        f'{allowed_lines}\n',
        encoding='utf-8',
    )
    execution_contract.write_text(
        '# Execution Contract\n\n'
        f'g5_multi_workgroup_smoke: {contract}\n\n'
        'allowed_change_paths:\n'
        f'{allowed_lines}\n\n'
        '## Verification Commands\n'
        f'{verification_lines}\n',
        encoding='utf-8',
    )
    return {'task_packet': task_packet, 'execution_contract': execution_contract}


def _git_commit_authority(project_root: Path) -> None:
    status = _git_status(project_root)
    if status:
        raise SmokeFailure(f'project root dirty before scheduler preflight: {status}')


def _task_show(
    command_log: list[dict[str, Any]],
    *,
    ccb_test: Path,
    project_root: Path,
    test_root: Path,
    env: dict[str, str],
    logs_dir: Path,
    timeout_s: int,
    label: str,
) -> dict[str, Any]:
    result = _run_logged(
        command_log,
        label,
        [str(ccb_test), '--project', str(project_root), 'plan', 'task-show', '--task', TASK_ID, '--json'],
        cwd=test_root,
        env=env,
        logs_dir=logs_dir,
        timeout_s=timeout_s,
    )
    return _json_object(result['stdout'])


def _run_logged(
    command_log: list[dict[str, Any]],
    label: str,
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    logs_dir: Path,
    timeout_s: int,
    allow_failure: bool = False,
) -> dict[str, Any]:
    if any(item.get('label') == label for item in command_log):
        raise SmokeFailure(f'duplicate command label: {label}')
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_s,
    )
    stdout_path = logs_dir / f'{label}.stdout'
    stderr_path = logs_dir / f'{label}.stderr'
    stdout_path.write_text(completed.stdout, encoding='utf-8')
    stderr_path.write_text(completed.stderr, encoding='utf-8')
    record = {
        'label': label,
        'argv': argv,
        'cwd': str(cwd),
        'returncode': completed.returncode,
        'stdout': completed.stdout,
        'stderr': completed.stderr,
        'stdout_path': str(stdout_path),
        'stderr_path': str(stderr_path),
    }
    command_log.append(record)
    if completed.returncode != 0 and not allow_failure:
        raise SmokeFailure(
            f'{label} failed rc={completed.returncode}: {completed.stderr or completed.stdout}'
        )
    return record


def _smoke_env(*, test_root: Path, project_root: Path, role_store: Path, source_home: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            'HOME': str(source_home),
            'CCB_SOURCE_HOME': str(source_home),
            'CCB_TEST_ROOTS': str(test_root),
            'AGENT_ROLES_STORE': str(role_store),
            'CCB_NO_ATTACH': '1',
            'CCB_REPLY_LANG': 'en',
            'CCB_RUNTIME_ACCELERATOR_CODEX': '0',
        }
    )
    return env


def _collect_jobs(project_root: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for path in project_root.glob('.ccb/**/jobs.jsonl'):
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            job_id = str(payload.get('job_id') or '')
            if job_id:
                latest[job_id] = payload
    return latest


def _find_loop_id(project_root: Path, task_id: str) -> str:
    for path in sorted((project_root / '.ccb' / 'runtime' / 'loops').glob('*/workgroup_scheduler_state.json')):
        payload = _read_json(path)
        if payload.get('task_id') == task_id:
            return str(payload.get('loop_id') or path.parent.name)
    return ''


def _live_observed_agents(observed: dict[str, Any]) -> list[dict[str, Any]]:
    terminal = {'released', 'missing', 'removed', 'unloaded'}
    return [
        item for item in observed.get('agents') or ()
        if isinstance(item, dict) and str(item.get('observed_state') or '') not in terminal
    ]


def _require_report_pass(report: dict[str, Any]) -> None:
    failed = [name for name, value in _mapping(report.get('checks')).items() if value is not True]
    if report.get('status') != 'pass' or failed:
        raise SmokeFailure(f'G5 full-flow report checks failed: {failed}')


def _task_record(payload: dict[str, Any]) -> dict[str, Any]:
    task = payload.get('task')
    return task if isinstance(task, dict) else {}


def _json_object(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _compact_command(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item.get(key)
        for key in ('label', 'argv', 'cwd', 'returncode', 'stdout_path', 'stderr_path')
    }


def _git(project_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ['git', *args],
        cwd=str(project_root),
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise SmokeFailure(f'git {" ".join(args)} failed: {completed.stderr or completed.stdout}')
    return completed.stdout.strip()


def _git_status(project_root: Path) -> list[str]:
    output = _git(project_root, 'status', '--porcelain=v1', '--untracked-files=all')
    return output.splitlines() if output else []


def _validate_matrix(*, count: int, shape: str) -> None:
    if count not in {1, 2, 3, 4}:
        raise SmokeFailure('count must be 1, 2, 3, or 4')
    if shape not in {'parallel', 'mixed_dag'}:
        raise SmokeFailure('shape must be parallel or mixed_dag')
    if shape == 'mixed_dag' and count < 3:
        raise SmokeFailure('mixed_dag requires count >= 3')


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the G5 source/fake multi-workgroup full-flow smoke.')
    parser.add_argument('--root', required=True)
    parser.add_argument('--count', type=int, required=True)
    parser.add_argument('--shape', choices=('parallel', 'mixed_dag'), default='parallel')
    parser.add_argument('--ccb-test', default=str(REPO_ROOT / 'ccb_test'))
    parser.add_argument('--keep-running', action='store_true')
    parser.add_argument('--command-timeout', type=int, default=240)
    parser.add_argument('--json', action='store_true')
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    try:
        report = run_smoke(
            project_root=Path(args.root),
            count=int(args.count),
            shape=str(args.shape),
            ccb_test=Path(args.ccb_test),
            keep_running=bool(args.keep_running),
            command_timeout_s=int(args.command_timeout),
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f'smoke_status: failed\nerror: {exc}', file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f'smoke_status: {report["status"]}')
        print(f'project_root: {report["project_root"]}')
        print(f'report: {report["paths"]["report"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
