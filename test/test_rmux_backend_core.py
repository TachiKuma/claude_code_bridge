from __future__ import annotations

from dataclasses import dataclass, field
import os

import pytest

from terminal_runtime.mux_backend_contract import MuxCommandError
from terminal_runtime.rmux_backend import RmuxBackend
from terminal_runtime.rmux_backend_runtime.capabilities import RmuxCapabilityGate
from terminal_runtime.rmux_backend_runtime.errors import map_rmux_result_error
from terminal_runtime.rmux_runner import RmuxCommandResult
from ccbd.services.project_namespace_runtime import backend as namespace_backend


def _supported_status(**overrides: str) -> dict[str, str]:
    commands = {
        "start-server",
        "new-session",
        "has-session",
        "kill-session",
        "kill-server",
        "attach-session",
        "list-windows",
        "new-window",
        "select-window",
        "select-pane",
        "kill-window",
        "list-panes",
        "split-window",
        "respawn-pane",
        "kill-pane",
        "select-layout",
        "move-pane",
        "swap-pane",
        "display-message",
        "set-option",
        "set-window-option",
    }
    values = {command: "supported" for command in commands}
    values.update(overrides)
    return values


@dataclass
class FakeRmuxCommandClient:
    responses: dict[str, list[RmuxCommandResult]] = field(default_factory=dict)
    calls: list[tuple[str, ...]] = field(default_factory=list)
    foreground_calls: list[tuple[str, ...]] = field(default_factory=list)

    def add(self, command_name: str, *, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self.responses.setdefault(command_name, []).append(
            RmuxCommandResult(
                command=("rmux", command_name),
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
            )
        )

    def run(self, args, *, input_text=None, timeout_s=None, foreground=False):
        del input_text, timeout_s
        command = tuple(str(arg) for arg in args)
        self.calls.append(command)
        if foreground:
            self.foreground_calls.append(command)
        command_name = command[0]
        queue = self.responses.get(command_name) or []
        if queue:
            return queue.pop(0)
        return RmuxCommandResult(command=("rmux", *command), returncode=0, stdout="", stderr="")

    def run_checked(
        self,
        args,
        *,
        operation: str,
        timeout_s: float | None,
        ipc_ref: str | None,
        daemon_evidence: dict[str, object] | None = None,
    ):
        del timeout_s
        result = self.run(args)
        if result.returncode == 0:
            return result
        raise map_rmux_result_error(
            result,
            operation=operation,
            ipc_ref=ipc_ref,
            daemon_evidence=daemon_evidence,
        )


def _backend(client: FakeRmuxCommandClient | None = None, **status_overrides: str) -> RmuxBackend:
    return RmuxBackend(
        namespace="ccb-demo",
        command_client=client or FakeRmuxCommandClient(),
        command_status=_supported_status(**status_overrides),
        semantic_status={"namespace_lifecycle": "supported", "presentation": "supported"},
        daemon_evidence={"backend_daemon_health": "healthy", "backend_daemon_endpoint": "pipe://rmux"},
    )


def test_constructor_and_operation_fail_fast_on_unsupported_capability() -> None:
    with pytest.raises(MuxCommandError) as construction:
        RmuxBackend(
            namespace="ccb-demo",
            command_client=FakeRmuxCommandClient(),
            command_status=_supported_status(**{"start-server": "unsupported"}),
        )

    assert construction.value.category == "unsupported"
    assert construction.value.operation == "RmuxBackend.__init__"
    assert construction.value.evidence["unsupported_commands"] == ("start-server",)

    backend = _backend(**{"split-window": "unsupported"})
    parent = backend.pane_ref("pane-A", session_name="ccb-demo", window_name="main")

    with pytest.raises(MuxCommandError) as operation:
        backend.split_pane(parent, direction="right", percent=50)

    assert operation.value.category == "unsupported"
    assert operation.value.operation == "split_pane"
    assert operation.value.evidence["command_status"] == {"split-window": "unsupported"}

    backend = _backend(**{"new-window": "unsupported"})
    with pytest.raises(MuxCommandError) as window_guard:
        backend.create_session(
            session_name="ccb-demo",
            project_root="D:/repo",
            window_name="main",
        )

    assert window_guard.value.category == "unsupported"
    assert window_guard.value.operation == "create_session"
    assert window_guard.value.evidence["unsupported_commands"] == ("new-window",)


def test_namespace_window_core_maps_refs_and_records() -> None:
    client = FakeRmuxCommandClient()
    client.add("has-session", stderr="can't find session: missing", returncode=1)
    client.add("list-windows", stdout="main\t1\t1\tD:/repo\teven-horizontal\n")
    client.add("list-windows", stdout="main\t1\t1\tD:/repo\teven-horizontal\n")
    backend = _backend(client)

    namespace = backend.create_session(
        session_name="ccb-demo",
        project_root="D:/repo",
        window_name="main",
        terminal_size=(233, 61),
    )

    assert namespace == {
        "backend_family": "tmux-family",
        "backend_impl": "rmux",
        "namespace_id": "ccb-demo",
        "session_name": "ccb-demo",
        "ipc_kind": "socket_name",
        "ipc_ref": "ccb-demo",
    }
    assert backend.session_alive(namespace) is False
    assert backend.list_windows(namespace)[0] == {
        "session_name": "ccb-demo",
        "window_name": "main",
        "active": True,
        "pane_count": 1,
        "project_root": "D:/repo",
        "layout": "even-horizontal",
    }
    assert backend.ensure_window(namespace, window_name="main", project_root="D:/repo")["window_name"] == "main"
    assert client.calls[0][:2] == ("new-session", "-d")
    assert ("-x", "233", "-y", "61", "-s", "ccb-demo") == client.calls[0][2:8]


def test_windows_rmux_ignores_non_pipe_socket_path(monkeypatch) -> None:
    monkeypatch.setattr("terminal_runtime.rmux_backend.os.name", "nt")

    backend = RmuxBackend(
        namespace="ccb-demo",
        socket_path="C:/tmp/ccb-demo/tmux.sock",
        command_client=FakeRmuxCommandClient(),
        command_status=_supported_status(),
    )

    assert backend.socket_path is None
    assert backend.namespace == "ccb-demo"
    assert backend.namespace_ref(session_name="ccb-demo")["ipc_kind"] == "socket_name"


def test_namespace_split_pane_wraps_mux_parent_ref() -> None:
    class FakeMuxBackend:
        backend_family = "tmux-family"
        backend_impl = "rmux"
        namespace = "ccb-demo"

        def __init__(self) -> None:
            self.parent = None
            self.split_kwargs = {}

        def pane_ref(self, pane_id, *, session_name, window_name=None):
            return {
                "backend_impl": "rmux",
                "pane_id": pane_id,
                "session_name": session_name,
                "window_name": window_name,
            }

        def namespace_ref(self, *, session_name):
            return {
                "backend_family": "tmux-family",
                "backend_impl": "rmux",
                "namespace_id": session_name,
                "session_name": session_name,
                "ipc_kind": "socket_name",
                "ipc_ref": session_name,
            }

        def split_pane(self, parent, **kwargs):
            self.parent = parent
            self.split_kwargs = dict(kwargs)
            return {
                "backend_impl": "rmux",
                "pane_id": "%2",
                "session_name": parent["session_name"],
                "window_name": parent.get("window_name"),
            }

    backend = FakeMuxBackend()

    pane_id = namespace_backend.split_pane(
        backend,
        target="%1",
        direction="right",
        percent=50,
        project_root="D:/repo",
    )

    assert pane_id == "%2"
    assert backend.parent == {
        "backend_impl": "rmux",
        "pane_id": "%1",
        "session_name": "ccb-demo",
        "window_name": None,
    }
    assert "while" in backend.split_kwargs["cmd"]
    if os.name == "nt":
        assert "powershell.exe" in backend.split_kwargs["cmd"]


def test_namespace_pane_mutation_helpers_wrap_mux_refs() -> None:
    class FakeMuxBackend:
        backend_family = "tmux-family"
        backend_impl = "rmux"
        namespace = "ccb-demo"

        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def namespace_ref(self, *, session_name):
            return {"session_name": session_name}

        def pane_ref(self, pane_id, *, session_name, window_name=None):
            return {
                "backend_impl": "rmux",
                "pane_id": pane_id,
                "session_name": session_name,
                "window_name": window_name,
            }

        def set_pane_identity(self, pane, **kwargs):
            self.calls.append(("set_pane_identity", pane, kwargs))

        def set_pane_user_option(self, pane, name, value):
            self.calls.append(("set_pane_user_option", pane, (name, value)))

        def respawn_pane(self, pane, **kwargs):
            self.calls.append(("respawn_pane", pane, kwargs))

    backend = FakeMuxBackend()

    namespace_backend.apply_pane_identity(
        backend,
        "%1",
        title="cmd",
        agent_label="cmd",
        project_id="project-a",
        is_cmd=True,
    )
    namespace_backend.set_pane_user_option(backend, "%1", "@ccb_sidebar_helper_id", "sha256:abc")
    assert namespace_backend.respawn_pane(
        backend,
        "%1",
        cmd="codex",
        cwd="D:/repo",
        remain_on_exit=True,
    ) is True

    for _name, pane, *_rest in backend.calls:
        assert pane == {
            "backend_impl": "rmux",
            "pane_id": "%1",
            "session_name": "ccb-demo",
            "window_name": None,
        }


def test_session_alive_maps_unreachable_to_transient_error_with_evidence() -> None:
    client = FakeRmuxCommandClient()
    client.add("has-session", stderr=r"error connecting to \\.\pipe\rmux (No such file or directory)", returncode=1)
    backend = _backend(client)
    namespace = backend.namespace_ref(session_name="ccb-demo")

    with pytest.raises(MuxCommandError) as error:
        backend.session_alive(namespace)

    assert error.value.category == "transient-unavailable"
    assert error.value.operation == "session_alive"
    assert error.value.command == ("rmux", "has-session")
    assert error.value.evidence["daemon_evidence"]["backend_daemon_endpoint"] == "pipe://rmux"


def test_pane_core_uses_backend_local_refs_without_tmux_percent_requirement() -> None:
    client = FakeRmuxCommandClient()
    client.add("list-panes", stdout="pane-A\tmain\npane-B\tmain\n")
    client.add("split-window", stdout="pane-C\n")
    backend = _backend(client)
    namespace = backend.namespace_ref(session_name="ccb-demo")

    panes = backend.list_panes(namespace, window_name="main")
    child = backend.split_pane(panes[0], direction="bottom", percent=40, cmd="python -q", cwd="D:/repo")
    backend.respawn_pane(child, cmd="codex", cwd="D:/repo")
    backend.kill_pane(child)

    assert [pane["pane_id"] for pane in panes] == ["pane-A", "pane-B"]
    assert not child["pane_id"].startswith("%")
    assert child == {
        "backend_impl": "rmux",
        "pane_id": "pane-C",
        "session_name": "ccb-demo",
        "window_name": "main",
    }
    assert ("split-window", "-v", "-p", "40", "-t", "pane-A", "-P", "-F", "#{pane_id}", "-c", "D:/repo", "python -q") in client.calls
    assert ("respawn-pane", "-k", "-t", "pane-C", "-c", "D:/repo", "codex") in client.calls
    assert ("kill-pane", "-t", "pane-C") in client.calls


def test_error_mapping_keeps_command_daemon_and_malformed_output_evidence() -> None:
    client = FakeRmuxCommandClient()
    client.add("list-windows", stdout="not\tenough\n")
    backend = _backend(client)
    namespace = backend.namespace_ref(session_name="ccb-demo")

    with pytest.raises(MuxCommandError) as malformed:
        backend.list_windows(namespace)

    assert malformed.value.category == "command-failed"
    assert malformed.value.evidence["stdout"] == "not\tenough\n"
    assert malformed.value.evidence["daemon_evidence"]["backend_daemon_health"] == "healthy"

    client.add("kill-window", stderr="permission denied", returncode=1)
    with pytest.raises(MuxCommandError) as denied:
        backend.kill_window(namespace, target="ccb-demo:main")

    assert denied.value.category == "permission"
    assert denied.value.command == ("rmux", "kill-window")
    assert denied.value.evidence["daemon_evidence"]["backend_daemon_endpoint"] == "pipe://rmux"


def test_presentation_identity_records_partial_failure() -> None:
    client = FakeRmuxCommandClient()
    client.add("select-pane")
    client.add("set-option", stderr="permission denied", returncode=1)
    backend = _backend(client)
    pane = backend.pane_ref("pane-A", session_name="ccb-demo", window_name="main")

    with pytest.raises(MuxCommandError) as error:
        backend.set_pane_identity(
            pane,
            title="worker",
            user_options={"@ccb_agent": "codex"},
            border_style="fg=blue",
        )

    assert error.value.operation == "set_pane_identity"
    assert error.value.category == "permission"
    assert error.value.evidence["completed_identity_steps"] == ("title",)
    assert error.value.evidence["failed_identity_step"] == "set_pane_user_option"


def test_presentation_title_requires_select_pane_capability() -> None:
    backend = _backend(**{"select-pane": "unsupported"})
    pane = backend.pane_ref("pane-A", session_name="ccb-demo", window_name="main")

    with pytest.raises(MuxCommandError) as error:
        backend.set_pane_title(pane, "worker")

    assert error.value.category == "unsupported"
    assert error.value.operation == "set_pane_title"
    assert error.value.evidence["unsupported_commands"] == ("select-pane",)


def test_capability_gate_accepts_semantic_workaround_projection() -> None:
    gate = RmuxCapabilityGate(
        command_status={"select-pane": "workaround"},
        semantic_status={"user_options_title": "supported"},
    )

    gate.require(
        "set_pane_title",
        ("select-pane",),
        backend_impl="rmux",
        ipc_ref="ccb-demo",
        daemon_evidence={},
    )

    assert gate.capabilities()["command_status"]["select-pane"] == "workaround"


def test_attach_namespace_uses_foreground_command_client() -> None:
    client = FakeRmuxCommandClient()
    backend = _backend(client)
    namespace = backend.namespace_ref(session_name="ccb-demo")

    assert backend.attach_namespace(namespace, window_name="main") == 0

    assert client.foreground_calls == [("attach-session", "-t", "ccb-demo:main")]
    assert hasattr(backend, "send_text")
    assert hasattr(backend, "send_key")
    assert hasattr(backend, "capture_pane")
    assert hasattr(backend, "ensure_pane_log")
    assert hasattr(backend, "pane_log_path")
