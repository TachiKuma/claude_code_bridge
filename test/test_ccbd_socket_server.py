from __future__ import annotations

from pathlib import Path

from ccbd.socket_server import CcbdSocketServer
from ccbd.control_plane_transport.fake import FakeControlPlaneTransport


def test_socket_server_exposes_control_plane_endpoint_descriptor(tmp_path: Path) -> None:
    socket_path = tmp_path / 'ccbd.sock'
    server = CcbdSocketServer(socket_path)

    endpoint = server.control_plane_endpoint

    assert endpoint['kind'] == 'unix_socket'
    assert endpoint['legacy_socket_path'] == str(socket_path)
    assert server.socket_path == socket_path


def test_socket_server_prefers_injected_transport_endpoint() -> None:
    transport = FakeControlPlaneTransport()
    server = CcbdSocketServer('legacy.sock', control_plane_transport=transport)

    assert server.control_plane_endpoint == transport.endpoint
