from __future__ import annotations

from .backend import build_backend


def namespace_ref_for(namespace) -> dict[str, object]:
    projector = getattr(namespace, 'namespace_ref', None)
    if callable(projector):
        return dict(projector())
    return {
        'backend_family': str(getattr(namespace, 'namespace_backend_family', None) or 'tmux-family'),
        'backend_impl': namespace_backend_impl(namespace),
        'namespace_id': namespace_id(namespace),
        'session_name': namespace_session_name(namespace),
        'ipc_kind': namespace_ipc_kind(namespace),
        'ipc_ref': namespace_ipc_ref(namespace),
    }


def namespace_backend_impl(namespace) -> str:
    return str(getattr(namespace, 'backend_impl', None) or 'tmux').strip().lower() or 'tmux'


def namespace_id(namespace) -> str:
    return (
        str(getattr(namespace, 'namespace_id', None) or '').strip()
        or str(getattr(namespace, 'project_id', None) or '').strip()
        or namespace_session_name(namespace)
    )


def namespace_session_name(namespace) -> str:
    return (
        str(getattr(namespace, 'namespace_session_name', None) or '').strip()
        or str(getattr(namespace, 'tmux_session_name', None) or '').strip()
    )


def namespace_tmux_socket_path(namespace) -> str:
    return str(getattr(namespace, 'tmux_socket_path', None) or '').strip()


def namespace_ipc_kind(namespace) -> str:
    value = str(getattr(namespace, 'namespace_ipc_kind', None) or '').strip()
    if value:
        return value
    return 'named_pipe' if namespace_backend_impl(namespace) in {'rmux', 'psmux'} else 'unix_socket'


def namespace_ipc_ref(namespace) -> str:
    value = str(getattr(namespace, 'namespace_ipc_ref', None) or '').strip()
    if value:
        return value
    if namespace_ipc_kind(namespace) == 'named_pipe':
        return namespace_id(namespace)
    return namespace_tmux_socket_path(namespace)


def build_backend_for_namespace(backend_factory, namespace):
    return build_backend(
        backend_factory,
        socket_path=namespace_tmux_socket_path(namespace),
        namespace=namespace_session_name(namespace),
        namespace_ref=namespace_ref_for(namespace),
    )


__all__ = [
    'build_backend_for_namespace',
    'namespace_backend_impl',
    'namespace_id',
    'namespace_ipc_kind',
    'namespace_ipc_ref',
    'namespace_ref_for',
    'namespace_session_name',
    'namespace_tmux_socket_path',
]
