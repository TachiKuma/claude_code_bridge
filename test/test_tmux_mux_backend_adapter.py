from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import terminal_runtime.api as terminal_api
from ccbd.services.project_namespace_runtime import controller as namespace_controller
from ccbd.services.project_namespace_runtime import backend as namespace_backend
from cli.services.runtime_launch_runtime import tmux_panes
from terminal_runtime.mux_backend_contract import MuxCommandError
from terminal_runtime.tmux_mux_backend import TmuxMuxBackendAdapter


class FakeTmuxBackend:
    backend_impl = "tmux"

    def __init__(
        self,
        *,
        socket_path: str | None = "/tmp/ccb.sock",
        socket_name: str | None = None,
        returncode: int = 0,
        stderr: str = "",
    ) -> None:
        self._socket_path = socket_path
        self._socket_name = socket_name
        self.returncode = returncode
        self.stderr = stderr
        self.calls: list[tuple[str, ...]] = []
        self.respawned: list[tuple[str, str, str | None]] = []
        self.sent: list[tuple[str, str]] = []
        self.created: list[tuple[str, str, str, int, str | None]] = []

    def _tmux_base(self) -> list[str]:
        if self._socket_path:
            return ["tmux", "-S", self._socket_path]
        if self._socket_name:
            return ["tmux", "-L", self._socket_name]
        return ["tmux"]

    def _tmux_run(self, args, *, check=False, capture=False, timeout=None):
        del check, timeout
        key = tuple(str(item) for item in args)
        self.calls.append(key)
        if key[:1] == ("attach",):
            self.calls.append(("capture", str(capture)))
        if key[:1] == ("list-panes",):
            stdout = "%7\tmain\n" if "#{window_name}" in key[-1] else "%7\n"
        elif key[:1] == ("list-windows",):
            stdout = "main\t1\t1\t/repo\teven-horizontal\n"
        else:
            stdout = ""
        return subprocess.CompletedProcess(["tmux", *key], self.returncode, stdout=stdout, stderr=self.stderr)

    def split_pane(self, parent_pane_id: str, *, direction: str, percent: int, cmd=None, cwd=None) -> str:
        self.calls.append(("split_pane", parent_pane_id, direction, str(percent), str(cmd), str(cwd)))
        return "%8"

    def create_pane(self, cmd: str, cwd: str, *, direction: str = "right", percent: int = 50, parent_pane: str | None = None) -> str:
        self.created.append((cmd, cwd, direction, percent, parent_pane))
        return "%9"

    def is_alive(self, pane_id: str) -> bool:
        self.calls.append(("is_alive", pane_id))
        return True

    def activate(self, pane_id: str) -> None:
        self.calls.append(("activate", pane_id))

    def get_current_pane_id(self) -> str:
        return "%1"

    def send_text(self, pane_id: str, text: str) -> None:
        self.sent.append((pane_id, text))

    def send_key(self, pane_id: str, key: str) -> bool:
        self.calls.append(("send_key", pane_id, key))
        return True

    def get_text(self, pane_id: str, *, lines: int = 20) -> str:
        self.calls.append(("get_text", pane_id, str(lines)))
        return "captured"

    def respawn_pane(self, pane_id: str, *, cmd: str, cwd: str | None = None, remain_on_exit: bool = True) -> None:
        del remain_on_exit
        self.respawned.append((pane_id, cmd, cwd))

    def kill_pane(self, pane_id: str) -> None:
        self.calls.append(("kill_pane", pane_id))

    def set_pane_identity(self, pane_id: str, **kwargs) -> None:
        self.calls.append(("set_pane_identity", pane_id, str(sorted(kwargs))))

    def ensure_pane_log(self, pane_id: str) -> Path:
        return Path(f"/tmp/{pane_id.strip('%')}.log")

    def pane_log_path(self, pane_id: str) -> Path:
        return Path(f"/tmp/{pane_id.strip('%')}.log")

    def describe_pane(self, pane_id: str, *, user_options=()):
        return {"pane_id": pane_id, "alive": "1", **{name: "" for name in user_options}}


def test_adapter_refs_capabilities_and_default_ipc_are_backend_neutral() -> None:
    adapter = TmuxMuxBackendAdapter(FakeTmuxBackend(socket_path=None, socket_name=None))

    namespace = adapter.namespace_ref(session_name="ccb-demo")
    pane = adapter.pane_ref("%7", session_name="ccb-demo", window_name="main")

    assert namespace == {
        "backend_family": "tmux-family",
        "backend_impl": "tmux",
        "namespace_id": "ccb-demo",
        "session_name": "ccb-demo",
        "ipc_kind": "socket_name",
        "ipc_ref": "<default>",
    }
    assert pane == {
        "backend_impl": "tmux",
        "pane_id": "%7",
        "session_name": "ccb-demo",
        "window_name": "main",
    }
    assert adapter.capabilities()["backend_impl"] == "tmux"
    assert adapter.capabilities()["semantic_status"]["namespace_lifecycle"] == "supported"


def test_adapter_maps_socket_path_and_name_to_ipc_evidence() -> None:
    path_adapter = TmuxMuxBackendAdapter(FakeTmuxBackend(socket_path="~/ccb.sock"))
    name_adapter = TmuxMuxBackendAdapter(FakeTmuxBackend(socket_path=None, socket_name="ccb-demo"))

    assert path_adapter.namespace_ref(session_name="s")["ipc_kind"] == "unix_socket"
    assert not path_adapter.namespace_ref(session_name="s")["ipc_ref"].startswith("~")
    assert path_adapter.namespace_ref(session_name="s")["ipc_ref"].endswith("ccb.sock")
    assert name_adapter.namespace_ref(session_name="s")["ipc_kind"] == "socket_name"
    assert name_adapter.namespace_ref(session_name="s")["ipc_ref"] == "ccb-demo"


def test_adapter_namespace_lifecycle_preserves_tmux_command_order(tmp_path: Path) -> None:
    backend = FakeTmuxBackend()
    adapter = TmuxMuxBackendAdapter(backend)

    namespace = adapter.create_session(
        session_name="ccb-demo",
        project_root=str(tmp_path),
        window_name="main",
        terminal_size=(233, 61),
    )
    adapter.ensure_server_policy(namespace, timeout_s=0.0)
    root = adapter.session_root_pane(namespace, timeout_s=0.0)

    assert namespace["backend_impl"] == "tmux"
    assert root["pane_id"] == "%7"
    assert backend.calls[0][:2] == ("new-session", "-d")
    assert backend.calls[0][2:8] == ("-x", "233", "-y", "61", "-s", "ccb-demo")
    assert ("has-session", "-t", "ccb-demo") in backend.calls
    assert ("set-option", "-g", "destroy-unattached", "off") in backend.calls
    assert ("list-panes", "-t", "ccb-demo", "-F", "#{pane_id}") in backend.calls


def test_adapter_attach_namespace_uses_foreground_stdio_not_capture() -> None:
    backend = FakeTmuxBackend()
    adapter = TmuxMuxBackendAdapter(backend)
    namespace = adapter.namespace_ref(session_name="ccb-demo")

    assert adapter.attach_namespace(namespace, window_name="main") == 0

    assert ("attach", "-t", "ccb-demo:main") in backend.calls
    assert ("capture", "False") in backend.calls


@pytest.mark.parametrize(
    ("stderr", "category"),
    [
        ("no server running on /tmp/ccb.sock", "transient-unavailable"),
        ("error connecting to /tmp/ccb.sock (No such file or directory)", "transient-unavailable"),
        ("can't find session: missing", "not-found"),
        ("can't find window: missing", "not-found"),
        ("permission denied", "permission"),
        ("unknown command: frobnicate", "unsupported"),
        ("boom", "command-failed"),
    ],
)
def test_adapter_maps_tmux_returncode_failures_to_mux_error(stderr: str, category: str) -> None:
    adapter = TmuxMuxBackendAdapter(FakeTmuxBackend(returncode=1, stderr=stderr))

    with pytest.raises(MuxCommandError) as error:
        adapter.prepare_server(timeout_s=0.0)

    assert error.value.category == category
    assert error.value.backend_impl == "tmux"
    assert error.value.operation == "prepare_server"
    assert error.value.ipc_ref == "/tmp/ccb.sock"
    assert error.value.command == ("tmux", "-S", "/tmp/ccb.sock", "start-server")
    assert error.value.evidence["returncode"] == 1
    assert error.value.evidence["stderr"] == stderr


def test_adapter_maps_subprocess_exceptions_to_mux_error(monkeypatch) -> None:
    backend = FakeTmuxBackend()

    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["tmux", "start-server"], timeout=2.0, output="out", stderr="err")

    backend._tmux_run = _raise_timeout  # type: ignore[method-assign]
    adapter = TmuxMuxBackendAdapter(backend)

    with pytest.raises(MuxCommandError) as error:
        adapter.prepare_server(timeout_s=0.0)

    assert error.value.category == "transient-unavailable"
    assert error.value.command == ("tmux", "start-server")
    assert error.value.evidence["original_exception_type"] == "TimeoutExpired"
    assert error.value.evidence["timeout"] == 2.0
    assert error.value.evidence["stdout"] == "out"
    assert error.value.evidence["stderr"] == "err"


def test_adapter_maps_called_process_and_missing_binary_command_evidence(monkeypatch) -> None:
    backend = FakeTmuxBackend()

    def _raise_called(*args, **kwargs):
        raise subprocess.CalledProcessError(2, ["tmux", "start-server"], output="out", stderr="err")

    backend._tmux_run = _raise_called  # type: ignore[method-assign]
    adapter = TmuxMuxBackendAdapter(backend)

    with pytest.raises(MuxCommandError) as called:
        adapter.prepare_server(timeout_s=0.0)

    assert called.value.command == ("tmux", "start-server")
    assert called.value.evidence["returncode"] == 2
    assert called.value.evidence["stdout"] == "out"
    assert called.value.evidence["stderr"] == "err"

    def _raise_missing(*args, **kwargs):
        raise FileNotFoundError("tmux")

    backend._tmux_run = _raise_missing  # type: ignore[method-assign]
    with pytest.raises(MuxCommandError) as missing:
        adapter.prepare_server(timeout_s=0.0)

    assert missing.value.category == "unsupported"
    assert missing.value.command == ("tmux", "-S", "/tmp/ccb.sock", "start-server")


def test_adapter_pane_io_delegates_to_legacy_tmux_backend_methods() -> None:
    backend = FakeTmuxBackend()
    adapter = TmuxMuxBackendAdapter(backend)
    pane = adapter.pane_ref("%7", session_name="ccb-demo", window_name="main")

    adapter.send_text(pane, "payload")
    adapter.respawn_pane(pane, cmd="codex", cwd="/repo")

    assert backend.sent == [("%7", "payload")]
    assert backend.respawned == [("%7", "codex", "/repo")]
    assert adapter.capture_pane(pane) == "captured"
    assert adapter.ensure_pane_log(pane).replace("\\", "/") == "/tmp/7.log"
    assert adapter.is_alive("%7") is True
    adapter.activate("%7")
    assert adapter.create_pane("cmd", "/repo") == "%9"
    assert adapter.split_pane("%7", direction="right", percent=50) == "%8"


def test_ccbd_namespace_helpers_use_mux_backend_without_private_runner(tmp_path: Path) -> None:
    class MuxOnly:
        backend_family = "tmux-family"

        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def namespace_ref(self, *, session_name: str):
            return {
                "backend_family": "tmux-family",
                "backend_impl": "tmux",
                "namespace_id": session_name,
                "session_name": session_name,
                "ipc_kind": "socket_name",
                "ipc_ref": "<default>",
            }

        def prepare_server(self, *, timeout_s=None):
            self.calls.append(("prepare_server", timeout_s))

        def ensure_server_policy(self, *, timeout_s=None):
            self.calls.append(("ensure_server_policy", timeout_s))

        def create_session(self, **kwargs):
            self.calls.append(("create_session", kwargs))
            return self.namespace_ref(session_name=kwargs["session_name"])

        def session_alive(self, namespace, *, timeout_s=None):
            self.calls.append(("session_alive", namespace["session_name"]))
            return True

        def list_windows(self, namespace):
            self.calls.append(("list_windows", namespace["session_name"]))
            return ({"window_name": "main", "active": True},)

        def ensure_window(self, namespace, **kwargs):
            self.calls.append(("ensure_window", kwargs))
            return {"window_name": kwargs["window_name"], "active": bool(kwargs["select"])}

        def kill_window(self, namespace, *, target):
            self.calls.append(("kill_window", target))

        def window_root_pane(self, namespace, *, window_name, timeout_s=None):
            self.calls.append(("window_root_pane", window_name))
            return {"pane_id": "%7"}

        def session_root_pane(self, namespace, *, timeout_s=None):
            self.calls.append(("session_root_pane", namespace["session_name"]))
            return {"pane_id": "%8"}

        def select_window(self, namespace, *, target):
            self.calls.append(("select_window", target))

        def kill_server(self):
            self.calls.append(("kill_server", None))
            return True

    backend = MuxOnly()

    namespace_backend.prepare_server(backend, timeout_s=0.0)
    namespace_backend.create_session(backend, session_name="ccb-demo", project_root=tmp_path, window_name="main")
    namespace_backend.ensure_server_policy(backend, timeout_s=0.0)
    assert namespace_backend.session_alive(backend, "ccb-demo", timeout_s=0.0) is True
    assert namespace_backend.list_windows(backend, "ccb-demo")[0].window_name == "main"
    assert namespace_backend.create_window(backend, session_name="ccb-demo", window_name="work", project_root=tmp_path).window_name == "work"
    assert namespace_backend.window_root_pane(backend, target_window="ccb-demo:main") == "%7"
    assert namespace_backend.session_root_pane(backend, "ccb-demo") == "%8"
    namespace_backend.select_window(backend, target="ccb-demo:main")
    namespace_backend.kill_window(backend, target="ccb-demo:main")
    assert namespace_backend.kill_server(backend) is True

    assert not hasattr(backend, "_tmux_run")
    assert [call[0] for call in backend.calls] == [
        "prepare_server",
        "create_session",
        "ensure_server_policy",
        "session_alive",
        "list_windows",
        "ensure_window",
        "window_root_pane",
        "session_root_pane",
        "select_window",
        "kill_window",
        "kill_server",
    ]


def test_runtime_launch_detached_pane_uses_mux_backend_session_contract(tmp_path: Path) -> None:
    class MuxOnly:
        backend_family = "tmux-family"

        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def create_session(self, **kwargs):
            self.calls.append(("create_session", kwargs))
            return {"session_name": kwargs["session_name"], "ipc_ref": "<default>"}

        def ensure_server_policy(self):
            self.calls.append(("ensure_server_policy", None))

        def session_root_pane(self, namespace):
            self.calls.append(("session_root_pane", namespace["session_name"]))
            return {"pane_id": "%9", "session_name": namespace["session_name"], "window_name": None}

        def respawn_pane(self, pane, **kwargs):
            self.calls.append(("respawn_pane", (pane["pane_id"], kwargs)))

    backend = MuxOnly()

    pane_id = tmux_panes.create_detached_tmux_pane(
        backend,
        cmd="codex",
        cwd=tmp_path,
        session_name="ccb-agent1",
    )

    assert pane_id == "%9"
    assert [call[0] for call in backend.calls] == [
        "create_session",
        "ensure_server_policy",
        "session_root_pane",
        "respawn_pane",
    ]
    assert not hasattr(backend, "_tmux_run")


def test_runtime_launch_mux_detached_policy_is_best_effort(tmp_path: Path) -> None:
    class MuxOnly:
        backend_family = "tmux-family"

        def __init__(self) -> None:
            self.calls: list[str] = []

        def create_session(self, **kwargs):
            self.calls.append("create_session")
            return {"session_name": kwargs["session_name"]}

        def ensure_server_policy(self):
            self.calls.append("ensure_server_policy")
            raise RuntimeError("policy failed")

        def session_root_pane(self, namespace):
            self.calls.append("session_root_pane")
            return {"pane_id": "%9"}

        def respawn_pane(self, pane, **kwargs):
            self.calls.append("respawn_pane")

    backend = MuxOnly()

    assert tmux_panes.create_detached_tmux_pane(backend, cmd="codex", cwd=tmp_path, session_name="ccb-agent1") == "%9"
    assert backend.calls == ["create_session", "ensure_server_policy", "session_root_pane", "respawn_pane"]


def test_default_tmux_factories_wrap_tmux_backend_in_mux_adapter(monkeypatch) -> None:
    class TmuxFactoryBackend(FakeTmuxBackend):
        pass

    terminal_api._backend_cache = None
    monkeypatch.setattr(terminal_api, "TmuxBackend", TmuxFactoryBackend)
    backend = terminal_api.get_backend("tmux")

    assert isinstance(backend, TmuxMuxBackendAdapter)
    assert isinstance(backend.tmux_backend, TmuxFactoryBackend)

    session_backend = terminal_api.get_backend_for_session({"terminal_backend": "tmux", "tmux_socket_path": "/tmp/demo.sock"})
    assert isinstance(session_backend, TmuxMuxBackendAdapter)
    assert session_backend.namespace_ref(session_name="s")["ipc_ref"] == "/tmp/demo.sock"


def test_project_namespace_default_tmux_backend_wraps_adapter(monkeypatch) -> None:
    class TmuxFactoryBackend(FakeTmuxBackend):
        pass

    monkeypatch.setattr(namespace_controller, "TmuxBackend", TmuxFactoryBackend)

    backend = namespace_controller.default_project_namespace_backend()

    assert isinstance(backend, TmuxMuxBackendAdapter)
    assert isinstance(backend.tmux_backend, TmuxFactoryBackend)
