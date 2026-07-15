from __future__ import annotations

from pathlib import Path
import time

from .binding import launch_binding_hint, relabel_project_namespace_pane
from .service_agents import prepare_agents
from .service_context import build_start_context, record_namespace_action
from .service_tmux import (
    bootstrap_cmd_pane_if_needed,
    cleanup_tmux_orphans_if_needed,
    project_socket_active_panes,
    record_active_panes,
    tmux_layout_for_start,
    tmux_namespace_runtime,
)
from .summary import StartFlowSummary


def run_start_flow(
    *,
    project_root: Path,
    project_id: str,
    paths,
    config,
    runtime_service,
    requested_agents: tuple[str, ...],
    restore: bool,
    auto_permission: bool,
    cleanup_tmux_orphans: bool,
    interactive_tmux_layout: bool,
    tmux_socket_path: str | None,
    tmux_session_name: str | None,
    tmux_workspace_window_name: str | None,
    namespace_epoch: int | None,
    workspace_window_id: str | None,
    workspace_epoch: int | None,
    namespace_agent_panes: dict[str, str] | None,
    namespace_pane_records: dict[str, object] | None,
    namespace_active_panes: tuple[str, ...] | None,
    fresh_namespace: bool,
    fresh_workspace: bool,
    clock,
    deps,
) -> StartFlowSummary:
    flow_started_ns = time.monotonic_ns()
    timings_ms: dict[str, float] = {}
    stage_started_ns = flow_started_ns
    command, context = build_start_context(
        project_root=project_root,
        project_id=project_id,
        paths=paths,
        requested_agents=requested_agents,
        restore=restore,
        auto_permission=auto_permission,
    )
    layout_plan = deps.build_project_layout_plan_fn(config, requested_agents=command.agent_names)
    timings_ms['context_and_layout_plan'] = _elapsed_ms(stage_started_ns)
    targets = layout_plan.target_agent_names
    actions_taken: list[str] = []
    agent_results: list[object] = []
    stage_started_ns = time.monotonic_ns()
    tmux_backend, root_pane_id = tmux_namespace_runtime(
        deps,
        tmux_socket_path=tmux_socket_path,
        tmux_session_name=tmux_session_name,
        tmux_workspace_window_name=tmux_workspace_window_name,
    )
    timings_ms['tmux_namespace_runtime'] = _elapsed_ms(stage_started_ns)

    record_namespace_action(
        actions_taken,
        tmux_socket_path=tmux_socket_path,
        tmux_session_name=tmux_session_name,
        namespace_epoch=namespace_epoch,
    )

    stage_started_ns = time.monotonic_ns()
    prepared_agents = prepare_agents(
        deps,
        targets=targets,
        config=config,
        paths=paths,
        context=context,
        project_root=project_root,
        project_id=project_id,
        tmux_socket_path=tmux_socket_path,
        tmux_session_name=tmux_session_name,
        workspace_window_id=workspace_window_id,
        namespace_epoch=namespace_epoch,
        namespace_pane_records=namespace_pane_records,
    )
    timings_ms['agent_prepare_and_classify'] = _elapsed_ms(stage_started_ns)
    prepared_by_agent = {item.agent_name: item for item in prepared_agents}

    stage_started_ns = time.monotonic_ns()
    tmux_layout = tmux_layout_for_start(
        deps,
        context,
        config=config,
        prepared_agents=prepared_agents,
        interactive_tmux_layout=interactive_tmux_layout,
        tmux_backend=tmux_backend,
        root_pane_id=root_pane_id,
        namespace_agent_panes=namespace_agent_panes,
        actions_taken=actions_taken,
    )
    timings_ms['tmux_layout'] = _elapsed_ms(stage_started_ns)

    stage_started_ns = time.monotonic_ns()
    active_panes_by_socket: dict[str | None, list[str]] = {}
    active_project_panes, cmd_pane_id = project_socket_active_panes(
        tmux_layout=tmux_layout,
        tmux_socket_path=tmux_socket_path,
        config=config,
        root_pane_id=root_pane_id,
        namespace_active_panes=namespace_active_panes,
    )
    bootstrap_cmd_pane_if_needed(
        deps,
        fresh_namespace=(fresh_namespace or fresh_workspace),
        cmd_pane_id=cmd_pane_id,
        project_root=project_root,
        project_id=project_id,
        tmux_socket_path=tmux_socket_path,
        namespace_epoch=namespace_epoch,
        actions_taken=actions_taken,
    )
    timings_ms['active_panes_and_cmd'] = _elapsed_ms(stage_started_ns)

    agents_started_ns = time.monotonic_ns()
    for style_index, agent_name in enumerate(targets):
        prepared = prepared_by_agent[agent_name]
        execution = deps.start_agent_runtime_impl(
            context=context,
            command=command,
            runtime_service=runtime_service,
            agent_name=agent_name,
            spec=prepared.spec,
            plan=prepared.plan,
            binding=prepared.binding,
            raw_binding=prepared.raw_binding,
            stale_binding=prepared.stale_binding,
            assigned_pane_id=tmux_layout.agent_panes.get(agent_name),
            style_index=style_index,
            project_id=project_id,
            tmux_socket_path=tmux_socket_path,
            namespace_epoch=namespace_epoch,
            workspace_window_id=workspace_window_id,
            workspace_epoch=workspace_epoch,
            window_name=prepared.window_name,
            namespace_pane_records=namespace_pane_records,
            provider_prepared=prepared.provider_prepared,
            provider_prepare_ms=prepared.provider_prepare_ms,
            binding_reject_reason=prepared.binding_reject_reason,
            ensure_agent_runtime_fn=deps.ensure_agent_runtime_fn,
            launch_binding_hint_fn=lambda **kwargs: launch_binding_hint(deps, **kwargs),
            relabel_project_namespace_pane_fn=lambda **kwargs: relabel_project_namespace_pane(deps, **kwargs),
            same_tmux_socket_path_fn=deps.same_tmux_socket_path_fn,
        )
        actions_taken.extend(execution.actions_taken)
        record_active_panes(
            active_panes_by_socket,
            active_project_panes,
            execution=execution,
        )
        agent_results.append(execution.agent_result)
    timings_ms['agent_runtime_commit'] = _elapsed_ms(agents_started_ns)

    stage_started_ns = time.monotonic_ns()
    cleanup_summaries = cleanup_tmux_orphans_if_needed(
        deps,
        cleanup_tmux_orphans=cleanup_tmux_orphans,
        project_id=project_id,
        paths=paths,
        active_panes_by_socket=active_panes_by_socket,
        project_socket_active_panes=active_project_panes,
        tmux_socket_path=tmux_socket_path,
        clock=clock,
        actions_taken=actions_taken,
    )
    timings_ms['tmux_cleanup'] = _elapsed_ms(stage_started_ns)
    timings_ms['flow_total'] = _elapsed_ms(flow_started_ns)
    return StartFlowSummary(
        project_root=str(project_root),
        project_id=project_id,
        started=targets,
        socket_path=str(paths.ccbd_socket_path),
        cleanup_summaries=tuple(cleanup_summaries),
        actions_taken=tuple(actions_taken),
        agent_results=tuple(agent_results),
        timings_ms=timings_ms,
    )


def _elapsed_ms(started_ns: int) -> float:
    return (time.monotonic_ns() - started_ns) / 1_000_000


__all__ = ['run_start_flow']
