from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from terminal_runtime.fake_mux_backend import FakeMuxBackend
from terminal_runtime.mux_backend_contract import (
    DiagnosticsCapability,
    MuxBackend,
    MuxCommandError,
    MuxNamespaceRef,
    NamespaceLifecycle,
    PaneIO,
    PaneLogging,
    PanePresentation,
    WindowLayout,
)
from terminal_runtime.tmux_backend import TmuxBackend


def test_contract_module_does_not_import_tmux_implementation() -> None:
    source = Path("lib/terminal_runtime/mux_backend_contract.py").read_text(encoding="utf-8")

    assert "tmux_backend" not in source
    assert "terminal_runtime.tmux" not in source


def test_mux_backend_protocol_is_split_by_capability() -> None:
    for protocol in (
        NamespaceLifecycle,
        WindowLayout,
        PaneIO,
        PanePresentation,
        PaneLogging,
        DiagnosticsCapability,
    ):
        assert protocol in MuxBackend.__mro__

    public_methods = {
        name
        for name, value in vars(MuxBackend).items()
        if not name.startswith("_") and inspect.isfunction(value)
    }
    assert "_tmux_run" not in public_methods


def test_fake_backend_lifecycle_uses_backend_neutral_refs() -> None:
    backend = FakeMuxBackend(backend_impl="rmux", ipc_kind="named_pipe", ipc_ref=r"\\.\pipe\ccb-demo")

    namespace = backend.create_session(
        session_name="ccb-demo",
        project_root="D:/repo",
        window_name="main",
    )
    root = backend.session_root_pane(namespace)
    helper = backend.split_pane(root, direction="right", percent=40, cmd="python -q", cwd="D:/repo")

    assert namespace == {
        "backend_family": "tmux-family",
        "backend_impl": "rmux",
        "namespace_id": "ccb-demo",
        "session_name": "ccb-demo",
        "ipc_kind": "named_pipe",
        "ipc_ref": r"\\.\pipe\ccb-demo",
    }
    assert root["backend_impl"] == "rmux"
    assert not root["pane_id"].startswith("%")
    assert helper["window_name"] == "main"
    assert [pane["pane_id"] for pane in backend.list_panes(namespace, window_name="main")] == [
        root["pane_id"],
        helper["pane_id"],
    ]


def test_fake_backend_records_state_events_without_tmux_argv_mocking() -> None:
    backend = FakeMuxBackend()
    namespace = backend.create_session(session_name="ccb-demo", project_root="/repo", window_name="main")
    root = backend.session_root_pane(namespace)
    helper_window = backend.ensure_window(namespace, window_name="helper", project_root="/repo", select=True)
    helper = backend.window_root_pane(namespace, window_name="helper")

    backend.move_pane(root, target="helper")
    backend.swap_pane(root, target=helper)
    backend.reflow_window(namespace, window_name="helper", layout="even-horizontal", expected_panes=(root, helper))
    backend.select_layout(namespace, window_name="helper", layout="tiled")
    backend.send_text(root, "one\ntwo\nthree\n")
    backend.set_pane_identity(
        root,
        title="worker",
        user_options={"@ccb_agent": "worker"},
        border_style="fg=blue",
    )
    log_path = backend.ensure_pane_log(root)

    assert helper_window["window_name"] == "helper"
    assert backend.capture_pane(root, lines=2) == "two\nthree"
    assert log_path == backend.pane_log_path(root)
    assert backend.describe_pane(root, user_options=("@ccb_agent",)) == {
        "pane_id": root["pane_id"],
        "session_name": "ccb-demo",
        "window_name": "helper",
        "pane_title": "worker",
        "alive": "1",
        "@ccb_agent": "worker",
    }
    assert not any("_tmux_run" in str(event) for event in backend.event_log)
    assert [event["operation"] for event in backend.event_log].count("reflow_window") == 1


def test_fake_backend_failure_injection_raises_structured_mux_error() -> None:
    backend = FakeMuxBackend(
        backend_impl="psmux",
        command_status={"move-pane": "partial"},
        semantic_status={"layout_reflow": "workaround"},
        blocking_gaps=["swap-pane"],
    )
    namespace = backend.create_session(session_name="ccb-demo", project_root="/repo")
    root = backend.session_root_pane(namespace)

    backend.fail_next(
        "send_text",
        category="permission",
        detail="pipe ACL denied",
        command=["send-text"],
        evidence={"pipe": "demo"},
    )

    with pytest.raises(MuxCommandError) as error:
        backend.send_text(root, "payload")

    assert error.value.category == "permission"
    assert error.value.backend_impl == "psmux"
    assert error.value.operation == "send_text"
    assert error.value.command == ("send-text",)
    assert error.value.evidence == {"pipe": "demo", "pane_id": root["pane_id"]}
    assert backend.capabilities() == {
        "backend_impl": "psmux",
        "command_status": {"move-pane": "partial"},
        "semantic_status": {"layout_reflow": "workaround"},
        "blocking_gaps": ["swap-pane"],
    }


def test_fake_backend_requires_semantic_split_direction_literals() -> None:
    backend = FakeMuxBackend()
    namespace = backend.create_session(session_name="ccb-demo", project_root="/repo")
    root = backend.session_root_pane(namespace)

    with pytest.raises(ValueError):
        backend.split_pane(root, direction="-h", percent=50)  # type: ignore[arg-type]


def test_tmux_backend_public_methods_remain_available() -> None:
    assert TmuxBackend.backend_impl == "tmux"
    for method_name in (
        "send_text",
        "is_alive",
        "kill_pane",
        "activate",
        "create_pane",
        "split_pane",
        "set_pane_identity",
        "describe_pane",
        "ensure_pane_log",
        "pane_log_path",
    ):
        assert hasattr(TmuxBackend, method_name)


def test_contract_types_are_importable_for_future_adapters() -> None:
    namespace: MuxNamespaceRef = {
        "backend_family": "tmux-family",
        "backend_impl": "tmux",
        "namespace_id": "ccb-demo",
        "session_name": "ccb-demo",
        "ipc_kind": "socket_name",
        "ipc_ref": "ccb-demo",
    }

    assert namespace["backend_impl"] == "tmux"
