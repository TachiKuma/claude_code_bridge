from __future__ import annotations

from types import SimpleNamespace

from ccbd.services.project_namespace_pane import snapshot_project_namespace_panes
from ccbd.services.project_namespace_runtime.materialize_topology import (
    _list_sidebar_geometry_records,
    existing_topology_agent_panes,
    topology_active_panes,
    topology_recreate_reason,
)


def test_startup_pane_snapshot_serves_topology_and_binding_without_rescan() -> None:
    calls: list[list[str]] = []

    class Backend:
        def _tmux_run(self, args, **kwargs):
            del kwargs
            calls.append(list(args))
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    '%1\tccb-demo\t@0\tmain\t0\tagent\tagent1\tmain\t\t\tproj-1\tccbd\t7'
                    '\tagent1\tagent1\tlabel-1\tborder-1\tactive-1\tsession-1\t120\t80\n'
                    '%2\tccb-demo\t@1\treview\t0\tagent\tagent2\treview\t\t\tproj-1\tccbd\t7'
                    '\tagent2\tagent2\tlabel-2\tborder-2\tactive-2\tsession-2\t120\t80\n'
                    '%3\tccb-demo\t@1\treview\t0\tsidebar\tsidebar:review\treview\treview\thelper-v1'
                    '\tproj-1\tccbd\t7\tSidebar\tccb\tlabel-3\tborder-3\tactive-3\t\t120\t20\n'
                ),
            )

        def list_panes_by_user_options(self, expected):
            raise AssertionError(f'unexpected topology rescan: {expected}')

    backend = Backend()
    records = snapshot_project_namespace_panes(backend)
    assert records is not None
    controller = SimpleNamespace(_project_id='proj-1')
    context = SimpleNamespace(
        backend=backend,
        current=None,
        desired_workspace_window_name='main',
        desired_session_name='ccb-demo',
    )
    topology_plan = SimpleNamespace(
        sidebar_enabled=False,
        windows=(
            SimpleNamespace(name='main', agent_names=('agent1',)),
            SimpleNamespace(name='review', agent_names=('agent2',)),
        ),
    )

    agent_panes = existing_topology_agent_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    )
    active_panes = topology_active_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    )
    recreate_reason = topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    )
    sidebar_geometry = _list_sidebar_geometry_records(
        object(),
        session_name='ccb-demo',
        project_id='proj-1',
        pane_records=records,
    )

    assert len(calls) == 1
    assert calls[0][:3] == ['list-panes', '-a', '-F']
    assert agent_panes == {'agent1': '%1', 'agent2': '%2'}
    assert active_panes == ('%3', '%1', '%2')
    assert recreate_reason is None
    assert sidebar_geometry == [
        {
            'pane_id': '%3',
            'window_width': '120',
            'pane_width': '20',
            'sidebar_instance': 'review',
        }
    ]
    assert records['%2'].window_id == '@1'
    assert records['%2'].ccb_window == 'review'
    assert records['%2'].namespace_epoch == 7
    assert records['%2'].pane_title == 'agent2'
    assert records['%2'].label_style == 'label-2'
    assert records['%2'].ccb_session_id == 'session-2'
    assert records['%2'].window_width == 120
    assert records['%2'].pane_width == 80
    assert records['%3'].sidebar_helper_id == 'helper-v1'
