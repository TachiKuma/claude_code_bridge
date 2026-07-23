from __future__ import annotations

from types import SimpleNamespace

from ccbd.supervision.cmd_slot import _build_namespace_backend
from ccbd.supervision.evidence import runtime_active_pane_id
from ccbd.supervision.loop_runtime import runtime_belongs_to_project_namespace


def test_rmux_supervision_accepts_backend_local_pane_id_without_percent_prefix() -> None:
    runtime = SimpleNamespace(
        backend_impl='rmux',
        runtime_ref='rmux:pane-a',
        active_pane_id='pane-a',
        pane_ref={'backend_impl': 'rmux', 'pane_id': 'pane-a'},
    )

    assert runtime_active_pane_id(runtime) == 'pane-a'


def test_rmux_supervision_namespace_match_uses_namespace_ref_without_tmux_socket() -> None:
    runtime = SimpleNamespace(
        tmux_socket_path=None,
        namespace_ref={
            'backend_impl': 'rmux',
            'namespace_id': 'ccbd-ns-1',
            'session_name': 'ccbd-ns-1',
        },
    )
    ctx = SimpleNamespace(layout=SimpleNamespace(ccbd_tmux_session_name='ccbd-ns-1', ccbd_tmux_socket_path='unused'))

    assert runtime_belongs_to_project_namespace(ctx, runtime) is True


def test_rmux_cmd_slot_backend_uses_canonical_namespace_ref_without_tmux_socket() -> None:
    calls: list[dict[str, object]] = []

    def _backend_factory(**kwargs):
        calls.append(kwargs)
        return object()

    namespace = SimpleNamespace(
        backend_impl='rmux',
        namespace_backend_family='tmux-family',
        namespace_id='ns-1',
        namespace_session_name='ns-1',
        namespace_ipc_kind='named_pipe',
        namespace_ipc_ref=r'\\.\pipe\ccb-rmux-ns-1',
        tmux_socket_path='',
        tmux_session_name='legacy-session',
    )
    controller = SimpleNamespace(_backend_factory=_backend_factory)

    assert _build_namespace_backend(controller, namespace) is not None
    assert calls == [
        {
            'namespace_ref': {
                'backend_family': 'tmux-family',
                'backend_impl': 'rmux',
                'namespace_id': 'ns-1',
                'session_name': 'ns-1',
                'ipc_kind': 'named_pipe',
                'ipc_ref': r'\\.\pipe\ccb-rmux-ns-1',
            },
            'namespace': 'ns-1',
            'socket_path': r'\\.\pipe\ccb-rmux-ns-1',
        }
    ]
