from __future__ import annotations

from dataclasses import dataclass, field
import os

import pytest

from terminal_runtime.mux_backend_contract import MuxCommandError
from terminal_runtime.rmux_backend import RmuxBackend
from terminal_runtime.rmux_backend_runtime.capabilities import RmuxCapabilityGate, default_rmux_capability_gate
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


class FakeProviderCommandWrapper:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def wrap_provider_command(self, cmd: str, *, cwd: str | None) -> str:
        self.calls.append((cmd, cwd))
        return f"WRAPPED[{cmd}]"


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


def test_respawn_pane_wraps_provider_command_for_rmux_backend() -> None:
    client = FakeRmuxCommandClient()
    wrapper = FakeProviderCommandWrapper()
    backend = RmuxBackend(
        namespace="ccb-demo",
        command_client=client,
        command_status=_supported_status(),
        semantic_status={"namespace_lifecycle": "supported", "presentation": "supported"},
        log_command_builder=wrapper,
    )
    pane = backend.pane_ref("%1", session_name="ccb-demo", window_name="main")

    backend.respawn_pane(pane, cmd="export DEMO='1'; codex", cwd="D:/repo")

    assert wrapper.calls == [("export DEMO='1'; codex", "D:/repo")]
    assert ("set-option", "-p", "-t", "ccb-demo:main.%1", "remain-on-exit", "on") in client.calls
    assert (
        "respawn-pane",
        "-k",
        "-t",
        "ccb-demo:main.%1",
        "-c",
        "D:/repo",
        "WRAPPED[export DEMO='1'; codex]",
    ) in client.calls


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
    if os.name == "nt":
        assert "Start-Sleep" in backend.split_kwargs["cmd"]
        assert "powershell.exe" in backend.split_kwargs["cmd"]
    else:
        assert "while" in backend.split_kwargs["cmd"]


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
    assert ("set-option", "-p", "-t", "pane-C", "remain-on-exit", "on") in client.calls
    respawn_call = next(call for call in client.calls if call[:4] == ("respawn-pane", "-k", "-t", "pane-C"))
    assert respawn_call[:6] == ("respawn-pane", "-k", "-t", "pane-C", "-c", "D:/repo")
    assert "codex" in respawn_call[6]
    assert ("kill-pane", "-t", "pane-C") in client.calls


def test_split_pane_canonicalizes_returned_percent_index_alias_before_respawn() -> None:
    client = FakeRmuxCommandClient()
    client.add("list-panes", stdout="%2\tmain\n")
    client.add("split-window", stdout="%1\n")
    client.add("list-panes", stdout="%2\t0\n%3\t1\n")
    backend = _backend(client)
    namespace = backend.namespace_ref(session_name="ccb-demo")

    panes = backend.list_panes(namespace, window_name="main")
    child = backend.split_pane(panes[0], direction="right", percent=50, cwd="D:/repo")
    backend.respawn_pane(child, cmd="codex", cwd="D:/repo")

    assert child["pane_id"] == "%3"
    assert ("list-panes", "-t", "ccb-demo:main", "-F", "#{pane_id}\t#{pane_index}") in client.calls
    assert any(call[:4] == ("respawn-pane", "-k", "-t", "ccb-demo:main.%3") for call in client.calls)


def test_split_pane_prefers_returned_percent_index_over_existing_percent_id() -> None:
    client = FakeRmuxCommandClient()
    client.add("list-panes", stdout="%1\tmain\n")
    client.add("split-window", stdout="%1\n")
    client.add("list-panes", stdout="%1\t0\n%2\t1\n")
    backend = _backend(client)
    namespace = backend.namespace_ref(session_name="ccb-demo")

    panes = backend.list_panes(namespace, window_name="main")
    child = backend.split_pane(panes[0], direction="right", percent=50, cwd="D:/repo")

    assert child["pane_id"] == "%2"
    assert ("list-panes", "-t", "ccb-demo:main", "-F", "#{pane_id}\t#{pane_index}") in client.calls


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


def test_presentation_identity_qualifies_percent_pane_targets() -> None:
    client = FakeRmuxCommandClient()
    client.add("list-panes", stdout="%1\t0\n")
    client.add("list-panes", stdout="%1\t0\n")
    client.add("list-panes", stdout="%1\t0\n")
    backend = _backend(client)
    pane = backend.pane_ref("%0", session_name="ccb-demo", window_name="main")

    backend.set_pane_identity(
        pane,
        title="worker",
        user_options={"@ccb_agent": "codex"},
        border_style="fg=blue",
    )

    assert client.calls == [
        ("list-panes", "-t", "ccb-demo:main", "-F", "#{pane_id}\t#{pane_index}"),
        ("select-pane", "-t", "ccb-demo:main.%1", "-T", "worker"),
        ("list-panes", "-t", "ccb-demo:main", "-F", "#{pane_id}\t#{pane_index}"),
        ("set-option", "-p", "-t", "ccb-demo:main.%1", "@ccb_agent", "codex"),
        ("list-panes", "-t", "ccb-demo:main", "-F", "#{pane_id}\t#{pane_index}"),
        ("set-option", "-p", "-t", "ccb-demo:main.%1", "pane-border-style", "fg=blue"),
    ]


def test_presentation_identity_canonicalizes_percent_pane_without_window_name() -> None:
    client = FakeRmuxCommandClient()
    client.add("list-panes", stdout="other\t%9\t0\nccb-demo\t%1\t0\n")
    backend = _backend(client)
    pane = backend.pane_ref("%0", session_name="ccb-demo", window_name=None)

    backend.set_pane_user_option(pane, "@ccb_agent", "codex")

    assert client.calls == [
        ("list-panes", "-a", "-F", "#{session_name}\t#{pane_id}\t#{pane_index}"),
        ("set-option", "-p", "-t", "%1", "@ccb_agent", "codex"),
    ]


def test_presentation_identity_canonicalizes_percent_pane_without_session_name() -> None:
    client = FakeRmuxCommandClient()
    client.add("list-panes", stdout="%7\t0\n")
    backend = _backend(client)
    pane = {"backend_impl": "rmux", "pane_id": "%0", "session_name": "", "window_name": None}

    backend.set_pane_user_option(pane, "@ccb_agent", "codex")

    assert client.calls == [
        ("list-panes", "-a", "-F", "#{pane_id}\t#{pane_index}"),
        ("set-option", "-p", "-t", "%7", "@ccb_agent", "codex"),
    ]


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


def test_default_capability_gate_treats_malformed_report_as_unsupported(tmp_path) -> None:
    feature_dir = tmp_path / ".codestable" / "features" / "2026-07-19-rmux-route-approval"
    feature_dir.mkdir(parents=True)
    (feature_dir / "rmux-route-decision-summary.yaml").write_text(
        "\n".join(
            [
                "decision_status: approved",
                "capability_report: .codestable/features/2026-07-19-rmux-route-approval/capability-report.json",
                "report_facts:",
                "  blocking_gaps_count: 0",
                "parent_handoff:",
                "  route_approved: true",
            ]
        ),
        encoding="utf-8",
    )
    (feature_dir / "capability-report.json").write_text("not-json", encoding="utf-8")

    gate = default_rmux_capability_gate(tmp_path)

    with pytest.raises(MuxCommandError) as error:
        gate.require(
            "RmuxBackend.__init__",
            ("start-server",),
            backend_impl="rmux",
            ipc_ref="ccb-demo",
        )

    assert error.value.category == "unsupported"
    assert error.value.evidence["unsupported_commands"] == ("start-server",)


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
