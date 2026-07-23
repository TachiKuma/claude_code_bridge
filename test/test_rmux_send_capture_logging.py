from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from terminal_runtime.mux_backend_contract import MuxCommandError
from terminal_runtime.rmux_backend import RmuxBackend
from terminal_runtime.rmux_backend_runtime.client import RmuxSubprocessCommandClient
from terminal_runtime.rmux_backend_runtime.errors import map_rmux_result_error
from terminal_runtime.rmux_runner import RmuxCommandResult


def _supported_status(**overrides: str) -> dict[str, str]:
    commands = {
        "start-server",
        "new-session",
        "has-session",
        "list-windows",
        "list-panes",
        "send-keys",
        "capture-pane",
        "pipe-pane",
    }
    values = {command: "supported" for command in commands}
    values.update(overrides)
    return values


@dataclass
class FakeRmuxCommandClient:
    responses: dict[str, list[RmuxCommandResult]] = field(default_factory=dict)
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def add(
        self,
        command_name: str,
        *,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        stdout_bytes: bytes | None = None,
    ) -> None:
        self.responses.setdefault(command_name, []).append(
            RmuxCommandResult(
                command=("rmux", command_name),
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
                stdout_bytes=stdout_bytes,
            )
        )

    def run(self, args, *, input_text=None, timeout_s=None, foreground=False):
        del input_text, timeout_s, foreground
        command = tuple(str(arg) for arg in args)
        self.calls.append(command)
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


@dataclass(frozen=True)
class FakeLogCommandBuilder:
    command: str = "BUILDER_PIPE_APPEND"

    def build_pipe_log_command(self, log_path: Path) -> str:
        return f"{self.command}:{log_path.name}"


def _backend(
    client: FakeRmuxCommandClient | None = None,
    *,
    log_command_builder: FakeLogCommandBuilder | None = None,
    **status_overrides: str,
) -> RmuxBackend:
    return RmuxBackend(
        namespace="ccb-demo",
        command_client=client or FakeRmuxCommandClient(),
        command_status=_supported_status(**status_overrides),
        semantic_status={"pane_io": "supported", "pane_logging": "supported"},
        daemon_evidence={"backend_daemon_health": "healthy", "backend_daemon_endpoint": "pipe://rmux"},
        log_command_builder=log_command_builder,
    )


def _pane(backend: RmuxBackend):
    return backend.pane_ref("pane-A", session_name="ccb-demo", window_name="main")


def test_io_operations_fail_fast_on_unsupported_required_capabilities(tmp_path: Path) -> None:
    backend = _backend(**{"send-keys": "unsupported"})
    pane = _pane(backend)

    with pytest.raises(MuxCommandError) as send_error:
        backend.send_text(pane, "hello")
    assert send_error.value.category == "unsupported"
    assert send_error.value.operation == "send_text"

    with pytest.raises(MuxCommandError) as key_error:
        backend.send_key(pane, "Ctrl-C")
    assert key_error.value.category == "unsupported"
    assert key_error.value.operation == "send_key"

    backend = _backend(**{"capture-pane": "unsupported"})
    with pytest.raises(MuxCommandError) as capture_error:
        backend.capture_pane(_pane(backend))
    assert capture_error.value.category == "unsupported"
    assert capture_error.value.operation == "capture_pane"

    backend = _backend(**{"pipe-pane": "unsupported"})
    with pytest.raises(MuxCommandError) as log_error:
        backend.ensure_pane_log(_pane(backend), log_path=tmp_path / "pane.log")
    assert log_error.value.category == "unsupported"
    assert log_error.value.operation == "ensure_pane_log"


def test_send_text_noops_empty_text_and_chunks_large_text_with_submit() -> None:
    client = FakeRmuxCommandClient()
    backend = _backend(client)
    pane = _pane(backend)

    backend.send_text(pane, "")
    assert client.calls == []

    payload = "alpha\n" + ("x" * 5000) + " & | < >"
    backend.send_text(pane, payload)

    text_calls = [call for call in client.calls if call[:4] == ("send-keys", "-t", "pane-A", "-l")]
    assert len(text_calls) == 2
    assert "".join(call[4] for call in text_calls) == payload
    assert client.calls[-1] == ("send-keys", "-t", "pane-A", "Enter")
    assert all("load-buffer" not in call and "paste-buffer" not in call for call in client.calls)


def test_send_text_can_skip_submit_enter() -> None:
    client = FakeRmuxCommandClient()
    backend = _backend(client)

    backend.send_text(_pane(backend), "no submit", submit=False)

    assert client.calls == [("send-keys", "-t", "pane-A", "-l", "no submit")]


def test_io_operations_canonicalize_percent_pane_targets(tmp_path: Path) -> None:
    client = FakeRmuxCommandClient()
    client.add("list-panes", stdout="%2\t0\n")
    client.add("list-panes", stdout="%2\t0\n")
    client.add("capture-pane", stdout="pane text\n")
    client.add("list-panes", stdout="%2\t0\n")
    backend = _backend(client, log_command_builder=FakeLogCommandBuilder())
    pane = backend.pane_ref("%0", session_name="ccb-demo", window_name="main")

    backend.send_text(pane, "hello", submit=False)
    capture = backend.capture_pane(pane)
    log_path = backend.ensure_pane_log(pane, log_path=tmp_path / "pane.log")

    assert capture["diagnostics"]["pane_id"] == "ccb-demo:main.%2"
    assert log_path == str(tmp_path / "pane.log")
    assert client.calls == [
        ("list-panes", "-t", "ccb-demo:main", "-F", "#{pane_id}\t#{pane_index}"),
        ("send-keys", "-t", "ccb-demo:main.%2", "-l", "hello"),
        ("list-panes", "-t", "ccb-demo:main", "-F", "#{pane_id}\t#{pane_index}"),
        ("capture-pane", "-p", "-t", "ccb-demo:main.%2"),
        ("list-panes", "-t", "ccb-demo:main", "-F", "#{pane_id}\t#{pane_index}"),
        ("pipe-pane", "-o", "-t", "ccb-demo:main.%2", "BUILDER_PIPE_APPEND:pane.log"),
    ]


def test_send_key_maps_allowlisted_control_keys_and_rejects_unknown() -> None:
    client = FakeRmuxCommandClient()
    backend = _backend(client)
    pane = _pane(backend)

    assert backend.send_key(pane, "Ctrl-C") is True
    assert backend.send_key(pane, "Ctrl-D") is True
    assert backend.send_key(pane, "Left") is True
    assert backend.send_key(pane, "NotAKey") is False

    assert client.calls == [
        ("send-keys", "-t", "pane-A", "C-c"),
        ("send-keys", "-t", "pane-A", "C-z"),
        ("send-keys", "-t", "pane-A", "Enter"),
        ("send-keys", "-t", "pane-A", "Left"),
    ]


def test_capture_pane_returns_structured_policy_and_preserves_text() -> None:
    client = FakeRmuxCommandClient()
    client.add("capture-pane", stdout="first line  \n\x1b[32m宽字符\x1b[0m\n")
    backend = _backend(client)

    result = backend.capture_pane(_pane(backend), start=-50, end=-1, ansi=True)

    assert result["text"] == "first line  \n\x1b[32m宽字符\x1b[0m\n"
    assert result["raw_bytes"] == result["text"].encode("utf-8", errors="replace")
    assert result["start_line"] == -50
    assert result["end_line"] == -1
    assert result["ansi_mode"] == "ansi"
    assert result["trim_policy"] == "preserve"
    assert result["diagnostics"]["pane_id"] == "pane-A"
    assert client.calls == [("capture-pane", "-p", "-t", "pane-A", "-e", "-S", "-50", "-E", "-1")]


def test_capture_pane_prefers_true_stdout_bytes_when_available() -> None:
    client = FakeRmuxCommandClient()
    client.add("capture-pane", stdout="bad\ufffdtext", stdout_bytes=b"bad\xfftext")
    backend = _backend(client)

    result = backend.capture_pane(_pane(backend))

    assert result["text"] == "bad\ufffdtext"
    assert result["raw_bytes"] == b"bad\xfftext"
    assert result["diagnostics"]["raw_bytes_source"] == "stdout_bytes"


def test_subprocess_client_capture_pane_collects_binary_stdout() -> None:
    observed: dict[str, object] = {}

    def run_fn(args, **kwargs):
        observed["args"] = tuple(args)
        observed["kwargs"] = dict(kwargs)

        class Completed:
            returncode = 0
            stdout = b"raw\xffpane"
            stderr = b""

        return Completed()

    client = RmuxSubprocessCommandClient(executable="rmux", namespace="ccb-demo", run_fn=run_fn)

    result = client.run(["capture-pane", "-p", "-t", "pane-A"])

    assert observed["args"] == ("rmux", "-L", "ccb-demo", "capture-pane", "-p", "-t", "pane-A")
    assert observed["kwargs"]["text"] is False
    assert result.stdout == "raw\ufffdpane"
    assert result.stdout_bytes == b"raw\xffpane"


def test_capture_pane_lines_uses_tail_range_for_compatibility() -> None:
    client = FakeRmuxCommandClient()
    client.add("capture-pane", stdout="tail\n")
    backend = _backend(client)

    result = backend.capture_pane(_pane(backend), lines=20)

    assert result["text"] == "tail\n"
    assert result["start_line"] == -20
    assert client.calls == [("capture-pane", "-p", "-t", "pane-A", "-S", "-20")]


def test_capture_and_send_failures_keep_daemon_evidence() -> None:
    client = FakeRmuxCommandClient()
    client.add("capture-pane", stderr="can't find pane: pane-A", returncode=1)
    backend = _backend(client)

    with pytest.raises(MuxCommandError) as error:
        backend.capture_pane(_pane(backend))

    assert error.value.category == "not-found"
    assert error.value.operation == "capture_pane"
    assert error.value.command == ("rmux", "capture-pane")
    assert error.value.evidence["daemon_evidence"]["backend_daemon_endpoint"] == "pipe://rmux"


def test_ensure_pane_log_uses_builder_output_and_prepares_path(tmp_path: Path) -> None:
    client = FakeRmuxCommandClient()
    backend = _backend(client, log_command_builder=FakeLogCommandBuilder())
    pane = _pane(backend)
    log_path = tmp_path / "logs" / "pane-A.log"

    result = backend.ensure_pane_log(pane, log_path=log_path)

    assert result == str(log_path)
    assert log_path.exists()
    assert client.calls == [("pipe-pane", "-o", "-t", "pane-A", f"BUILDER_PIPE_APPEND:{log_path.name}")]
    assert "tee -a" not in client.calls[0][-1]
    assert "powershell" not in client.calls[0][-1].lower()
    assert "cmd /" not in client.calls[0][-1].lower()


def test_pane_log_path_is_rmux_scoped() -> None:
    backend = _backend()

    result = backend.pane_log_path(_pane(backend))

    assert result is not None
    assert "rmux" in result
    assert result.endswith("pane-pane-A.log")
