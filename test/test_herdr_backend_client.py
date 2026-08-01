from __future__ import annotations

import subprocess
import shlex
import sys

import pytest

import terminal_runtime.api as terminal_api
import terminal_runtime.herdr_backend_runtime.cli as herdr_cli
from terminal_runtime.backend_selection import TerminalBackendSelection
from terminal_runtime.herdr_backend import HerdrBackend
from terminal_runtime.herdr_backend_runtime.capabilities import HerdrCapabilityGate
from terminal_runtime.herdr_backend_runtime.cli import HerdrCliRequestAdapter
from terminal_runtime.herdr_backend_runtime.client import HerdrSocketClient
from terminal_runtime.mux_backend_contract import MuxCommandErrorV2


def test_herdr_capability_gate_blocks_missing_spike_evidence() -> None:
    gate = HerdrCapabilityGate.from_spike_evidence(
        None,
        capability_report_ref="evidence/herdr-contract-spike-evidence.json",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        gate.require_supported("create_session")

    assert exc_info.value.category == "unsupported"
    assert exc_info.value.backend_impl == "herdr"
    assert exc_info.value.evidence["failure_reason"] == "herdr-capability-missing"


@pytest.mark.parametrize(
    "spike_evidence",
    [
        {"adapter_recommendation": "stop"},
        {"adapter_recommendation": "needs-upstream-issue"},
        {"verdict": "blocked"},
        {"verdict": "failed"},
        {"failure_class": "windows-beta-gap"},
        {"capability_projection": {"blocking_gaps": ["server_restart_output_history"]}},
        {"capability_projection": {"blocking_gaps": "server_restart_output_history"}},
        {"capability_projection": {"blocking_gaps": [123]}},
        {"capability_projection": {"windows_beta_gaps": "server_restart_output_history"}},
        {"capability_projection": {"windows_beta_gaps": [False]}},
        {"capability_projection": {"command_status": {"send_input": "unknown"}}},
        {"capability_projection": {"command_status": {"send_input": "surprising-new-status"}}},
    ],
)
def test_herdr_capability_gate_fails_closed_for_blocking_spike_projection(
    spike_evidence: dict[str, object],
) -> None:
    gate = HerdrCapabilityGate.from_spike_evidence(
        spike_evidence,
        capability_report_ref="evidence/herdr-contract-spike-evidence.json",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        gate.require_supported("send_text")

    assert exc_info.value.category == "unsupported"
    assert exc_info.value.evidence["failure_reason"] == "unsupported-capability"


def test_herdr_capability_gate_allows_supported_spike_projection() -> None:
    gate = HerdrCapabilityGate.from_spike_evidence(
        {
            "adapter_recommendation": "continue",
            "verdict": "pass",
            "failure_class": "none",
            "capability_projection": {
                "command_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                },
                "semantic_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                },
                "windows_beta_gaps": [],
                "blocking_gaps": [],
            },
        },
        capability_report_ref="evidence/herdr-contract-spike-evidence.json",
    )

    capabilities = gate.require_supported("send_text")

    assert capabilities["backend_impl"] == "herdr"
    assert capabilities["blocking_gaps"] == []
    assert capabilities["source_ref"] == "evidence/herdr-contract-spike-evidence.json"


@pytest.mark.parametrize(
    "spike_evidence",
    [
        {
            "adapter_recommendation": "continue",
            "verdict": "unknown",
            "failure_class": "none",
            "capability_projection": {
                "command_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                },
                "semantic_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                },
                "windows_beta_gaps": [],
                "blocking_gaps": [],
            },
        },
        {
            "adapter_recommendation": "surprising",
            "verdict": "pass",
            "failure_class": "none",
            "capability_projection": {
                "command_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                },
                "semantic_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                },
                "windows_beta_gaps": [],
                "blocking_gaps": [],
            },
        },
    ],
)
def test_herdr_capability_gate_requires_known_continue_and_pass_verdict(
    spike_evidence: dict[str, object],
) -> None:
    gate = HerdrCapabilityGate.from_spike_evidence(
        spike_evidence,
        capability_report_ref="evidence/herdr-contract-spike-evidence.json",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        gate.require_supported("send_text")

    assert exc_info.value.category == "unsupported"


def test_herdr_capability_gate_does_not_surface_extra_upstream_capability_names() -> None:
    gate = HerdrCapabilityGate.from_spike_evidence(
        {
            "adapter_recommendation": "continue",
            "verdict": "pass",
            "failure_class": "none",
            "capability_projection": {
                "command_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                    "schema": "supported",
                },
                "semantic_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                    "schema": "supported",
                },
                "windows_beta_gaps": [],
                "blocking_gaps": [],
            },
        },
        capability_report_ref="evidence/herdr-contract-spike-evidence.json",
    )

    capabilities = gate.require_supported("capabilities")

    assert "schema" not in capabilities["command_status"]
    assert "schema" not in capabilities["semantic_status"]


def test_herdr_socket_client_schema_gate_passes_and_records_server_info() -> None:
    client = HerdrSocketClient(
        request_fn=_fake_herdr_request(),
        socket_ref="herdr://local",
    )

    server_info = client.server_info()

    assert server_info["api_schema"] == "Herdr API"
    assert server_info["platform"] == "windows"
    assert server_info["arch"] == "x64"
    assert server_info["socket_ref"] == "herdr://local"


def test_herdr_socket_client_schema_mismatch_is_structured_error() -> None:
    client = HerdrSocketClient(
        request_fn=_fake_herdr_request(server_info={"api_schema": "Unexpected API"}),
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.server_info()

    assert exc_info.value.category == "schema-mismatch"
    assert exc_info.value.backend_impl == "herdr"
    assert exc_info.value.operation == "server_info"
    assert "expected Herdr contract" in exc_info.value.detail
    assert exc_info.value.evidence["expected_api_schema"] == "Herdr API"
    assert exc_info.value.evidence["actual_api_schema"] == "Unexpected API"


@pytest.mark.parametrize(
    "server_info",
    [
        {"version": ""},
        {"platform": "linux"},
        {"arch": "arm64"},
    ],
)
def test_herdr_socket_client_server_info_gate_rejects_wrong_version_platform_or_arch(
    server_info: dict[str, object],
) -> None:
    client = HerdrSocketClient(
        request_fn=_fake_herdr_request(server_info=server_info),
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.server_info()

    assert exc_info.value.category == "schema-mismatch"
    assert exc_info.value.evidence["expected_platform"] == "windows"
    assert exc_info.value.evidence["expected_arch"] == "x64"


def test_herdr_socket_client_rejects_scalar_result_as_structured_error() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {"result": "ok"},
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.server_info()

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.operation == "server_info"


def test_herdr_socket_client_maps_failed_envelope_to_structured_error() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "status": "failed",
            "detail": "workspace create failed",
        },
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.operation == "create_session"
    assert "workspace create failed" in exc_info.value.detail


def test_herdr_socket_client_checks_outer_failed_status_before_result_unwrap() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "status": "failed",
            "detail": "outer failure",
            "result": {"namespace_id": "workspace-1", "session_name": "ccb-demo"},
        },
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")

    assert exc_info.value.category == "command-failed"
    assert "outer failure" in exc_info.value.detail


def test_herdr_socket_client_rejects_create_pane_session_mismatch() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "result": {"pane_id": "pane-1", "session_name": "other-session"}
        },
        socket_ref="herdr://local",
    )
    namespace = {
        "backend_family": "herdr-native",
        "backend_impl": "herdr",
        "namespace_id": "workspace-1",
        "session_name": "ccb-demo",
        "ipc_kind": "herdr_socket",
        "ipc_ref": "herdr://local",
        "restore_token": "ccb-demo::workspace-1",
    }

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.create_pane(namespace, command=[], cwd="D:/demo", env={}, title="demo")

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.evidence["expected_session_name"] == "ccb-demo"
    assert exc_info.value.evidence["actual_session_name"] == "other-session"


def test_herdr_socket_client_preserves_outer_detail_for_nested_failure() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "status": "ok",
            "detail": "outer diagnostic",
            "result": {"status": "failed", "pane_id": payload["pane_id"]},
        },
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.kill_pane(
            {
                "backend_impl": "herdr",
                "pane_id": "pane-1",
                "session_name": "ccb-demo",
                "window_name": None,
                "agent_slug": None,
            }
        )

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.detail == "outer diagnostic"


def test_herdr_socket_client_rejects_unknown_status() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {"status": "error", "detail": "unknown status"},
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.kill_pane(
            {
                "backend_impl": "herdr",
                "pane_id": "pane-1",
                "session_name": "ccb-demo",
                "window_name": None,
                "agent_slug": None,
            }
        )

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.evidence["status"] == "error"


@pytest.mark.parametrize("status", ["unsupported", "transient-unavailable", "not-found"])
def test_herdr_socket_client_preserves_recognized_error_status_categories(status: str) -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {"status": status, "detail": "structured failure"},
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.kill_pane(
            {
                "backend_impl": "herdr",
                "pane_id": "pane-1",
                "session_name": "ccb-demo",
                "window_name": None,
                "agent_slug": None,
            }
        )

    assert exc_info.value.category == status


def test_herdr_socket_client_requires_operation_status() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {"pane_id": "pane-1"},
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.kill_pane(
            {
                "backend_impl": "herdr",
                "pane_id": "pane-1",
                "session_name": "ccb-demo",
                "window_name": None,
                "agent_slug": None,
            }
        )

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.evidence["status"] == ""


def test_herdr_socket_client_wraps_missing_ref_fields_as_structured_error() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {"session_name": "ccb-demo"},
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.operation == "create_session"


def test_herdr_socket_client_normalizes_disallowed_session_scoped_namespace_ipc_ref() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "result": {
                "namespace_id": "workspace-1",
                "session_name": "ccb-demo",
                "ipc_ref": "herdr://ccb-demo",
            }
        },
        socket_ref="herdr://override",
    )

    namespace = client.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")

    assert namespace["ipc_ref"] == "herdr://override"


def test_herdr_socket_client_preserves_allowed_session_scoped_namespace_ipc_ref() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "result": {
                "namespace_id": "workspace-1",
                "session_name": "ccb-demo",
                "ipc_ref": "herdr://ccb-demo",
            }
        },
        socket_ref="herdr://default",
        allow_session_scoped_ipc_refs=True,
    )

    namespace = client.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")

    assert namespace["ipc_ref"] == "herdr://ccb-demo"


def test_herdr_socket_client_normalizes_foreign_session_scoped_namespace_ipc_ref() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "result": {
                "namespace_id": "workspace-1",
                "session_name": "ccb-demo",
                "ipc_ref": "herdr://foreign",
            }
        },
        socket_ref="herdr://default",
        allow_session_scoped_ipc_refs=True,
    )

    namespace = client.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")

    assert namespace["ipc_ref"] == "herdr://default"


def test_herdr_socket_client_rejects_restore_response_namespace_mismatch() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "result": {
                "namespace_id": "workspace-2",
                "session_name": "ccb-demo",
                "restore_token": payload["restore_token"],
            }
        },
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.restore_session(restore_token="ccb-demo::workspace-1")

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.evidence["expected_namespace_id"] == "workspace-1"
    assert exc_info.value.evidence["actual_namespace_id"] == "workspace-2"


def test_herdr_socket_client_rejects_restore_response_session_mismatch() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "result": {
                "namespace_id": "workspace-1",
                "session_name": "other-session",
                "restore_token": payload["restore_token"],
            }
        },
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.restore_session(restore_token="expected-session::workspace-1")

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.evidence["expected_session_name"] == "expected-session"
    assert exc_info.value.evidence["actual_session_name"] == "other-session"


def test_herdr_socket_client_rejects_restore_response_token_mismatch() -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {
            "result": {
                "namespace_id": "workspace-1",
                "session_name": "expected-session",
                "restore_token": "expected-session::workspace-2",
            }
        },
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.restore_session(restore_token="expected-session::workspace-1")

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.evidence["expected_restore_token"] == "expected-session::workspace-1"
    assert exc_info.value.evidence["actual_restore_token"] == "expected-session::workspace-2"


@pytest.mark.parametrize(
    "response",
    [
        {"session_name": "expected-session", "restore_token": "expected-session::workspace-1"},
        {"namespace_id": "workspace-1", "restore_token": "expected-session::workspace-1"},
        {"namespace_id": "workspace-1", "session_name": "expected-session"},
    ],
)
def test_herdr_socket_client_requires_restore_response_identity_fields(
    response: dict[str, object],
) -> None:
    client = HerdrSocketClient(
        request_fn=lambda operation, payload: {"result": dict(response)},
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.restore_session(restore_token="expected-session::workspace-1")

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.operation == "restore_session"


@pytest.mark.parametrize("restore_token", ["workspace-1", "::workspace-1", "ccb-demo::", "ccb-demo::workspace-1::extra"])
def test_herdr_socket_client_rejects_restore_token_without_session_scope(restore_token: str) -> None:
    client = HerdrSocketClient(
        request_fn=_fake_herdr_request(),
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.restore_session(restore_token=restore_token)

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.operation == "restore_session"


@pytest.mark.parametrize(
    ("operation", "invoke"),
    [
        ("server_info", lambda client: client.server_info()),
        (
            "create_session",
            lambda client: client.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo"),
        ),
        ("restore_session", lambda client: client.restore_session(restore_token="ccb-demo::workspace-1")),
        (
            "create_pane",
            lambda client: client.create_pane(
                {
                    "backend_family": "herdr-native",
                    "backend_impl": "herdr",
                    "namespace_id": "workspace-1",
                    "session_name": "ccb-demo",
                    "ipc_kind": "herdr_socket",
                    "ipc_ref": "herdr://local",
                    "restore_token": None,
                },
                command=[],
                cwd="D:/demo",
                env={},
                title="workspace",
            ),
        ),
    ],
)
def test_herdr_socket_client_rejects_wrapped_success_without_result(
    operation: str,
    invoke,
) -> None:
    client = HerdrSocketClient(
        request_fn=lambda requested_operation, payload: {"status": "ok"},
        socket_ref="herdr://local",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        invoke(client)

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.operation == operation


def test_herdr_backend_facade_returns_refs_and_operation_evidence() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")
    restored = backend.restore_session(restore_token=namespace["restore_token"] or "")
    pane = backend.create_pane(
        namespace,
        command=["python", "-V"],
        cwd="D:/demo",
        env={"SECRET_TOKEN": "must-not-leak"},
        title="workspace",
    )
    send = backend.send_text(pane, "secret typed text")
    captured, capture = backend.capture_pane(pane, lines=20)
    killed = backend.kill_pane(pane)

    assert namespace["backend_family"] == "herdr-native"
    assert namespace["backend_impl"] == "herdr"
    assert namespace["ipc_kind"] == "herdr_socket"
    assert namespace["restore_token"] == "ccb-demo::workspace-1"
    assert restored["namespace_id"] == namespace["namespace_id"]
    assert pane["backend_impl"] == "herdr"
    assert pane["pane_id"] == "pane-1"
    assert send["operation"] == "send_text"
    assert send["status"] == "ok"
    assert "secret typed text" not in str(send)
    assert "python ready" in captured
    assert capture["operation"] == "capture_pane"
    assert killed["operation"] == "kill_pane"


def test_herdr_backend_updates_liveness_after_kill() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")
    pane = backend.create_pane(namespace, command=[], cwd="D:/demo", env={}, title="workspace")

    assert backend.is_alive("pane-1") is True
    backend.kill_pane(pane)

    assert backend.is_alive("pane-1") is False


def test_herdr_backend_attach_namespace_uses_v2_namespace_ref_without_restore_token_leak() -> None:
    payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "attach_namespace":
            payloads.append(dict(payload))
            return {"status": "ok", "namespace_id": payload["namespace_id"]}
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")

    evidence = backend.attach_namespace(namespace, window_name="workspace")

    assert evidence["operation"] == "attach_namespace"
    assert evidence["status"] == "ok"
    assert payloads == [
        {
            "namespace_id": "workspace-1",
            "session_name": "ccb-demo",
            "ipc_ref": "herdr://local",
            "window_name": "workspace",
        }
    ]
    assert "restore_token" not in str(payloads)


def test_herdr_backend_liveness_probe_clears_stale_pane() -> None:
    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "capture_pane":
            raise MuxCommandErrorV2(
                category="not-found",
                backend_impl="herdr",
                operation="capture_pane",
                detail="pane not found",
            )
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")
    pane = backend.create_pane(namespace, command=[], cwd="D:/demo", env={}, title="workspace")

    assert backend.is_alive(pane["pane_id"]) is False


def test_herdr_backend_legacy_create_pane_uses_lazy_session_and_returns_pane_id() -> None:
    payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "create_pane":
            payloads.append(payload)
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    pane_id = backend.create_pane("python -V", "D:/demo")

    assert pane_id == "pane-1"
    assert backend.is_alive(pane_id) is True
    assert payloads[0]["command"] == ["python -V"]


def test_herdr_backend_legacy_create_pane_preserves_explicit_command_kwarg() -> None:
    payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "create_pane":
            payloads.append(payload)
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    pane_id = backend.create_pane("python", "D:/demo", command=["python", "-V"])

    assert pane_id == "pane-1"
    assert payloads[0]["command"] == ["python", "-V"]


def test_herdr_backend_legacy_namespaces_are_keyed_by_cwd() -> None:
    create_session_payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "create_session":
            create_session_payloads.append(payload)
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    backend.create_pane("python -V", "D:/one")
    backend.create_pane("python -V", "D:/two")
    backend.create_pane("python -V", "D:/one")

    assert [payload["cwd"] for payload in create_session_payloads] == ["D:/one", "D:/two"]


def test_herdr_backend_legacy_parent_pane_must_be_known() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.create_pane("python -V", "D:/demo", parent_pane="missing-pane")

    assert exc_info.value.category == "not-found"
    assert exc_info.value.operation == "create_pane"


def test_herdr_backend_threads_split_geometry_to_client() -> None:
    create_pane_payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "create_pane":
            create_pane_payloads.append(payload)
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")
    pane = backend.create_pane(namespace, command=[], cwd="D:/demo", env={}, title="root")

    backend.split_pane(pane, direction="down", percent=25, command=[], cwd="D:/demo", env={}, title="child")

    assert create_pane_payloads[1]["direction"] == "down"
    assert create_pane_payloads[1]["percent"] == 25
    assert create_pane_payloads[1]["parent_pane"] == pane["pane_id"]


def test_herdr_backend_namespace_create_pane_preserves_parent_pane() -> None:
    create_pane_payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "create_pane":
            create_pane_payloads.append(payload)
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")

    backend.create_pane(
        namespace,
        parent_pane="pane-root",
        direction="down",
        percent=25,
        command=[],
        cwd="D:/demo",
        env={},
        title="child",
    )

    assert create_pane_payloads[0]["parent_pane"] == "pane-root"
    assert create_pane_payloads[0]["direction"] == "down"
    assert create_pane_payloads[0]["percent"] == 25


def test_herdr_backend_rejects_invalid_namespace_ref_dict() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.create_pane({"namespace_id": "workspace-1"}, cwd="D:/demo")

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.operation == "create_pane"

    with pytest.raises(MuxCommandErrorV2):
        backend.create_pane(
            {
                "backend_impl": "herdr",
                "namespace_id": "workspace-1",
                "session_name": "ccb-demo",
                "ipc_kind": "socket_path",
                "ipc_ref": "C:/tmp/herdr.sock",
                "restore_token": None,
            },
            cwd="D:/demo",
        )


def test_herdr_backend_explicit_socket_override_rejects_session_derived_namespace_ref() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://override"),
        capability_gate=_supported_gate(),
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.create_pane(
            {
                "backend_family": "herdr-native",
                "backend_impl": "herdr",
                "namespace_id": "workspace-1",
                "session_name": "ccb-demo",
                "ipc_kind": "herdr_socket",
                "ipc_ref": "herdr://ccb-demo",
                "restore_token": None,
            },
            cwd="D:/demo",
        )

    assert exc_info.value.category == "command-failed"


def test_herdr_backend_allows_session_scoped_namespace_ref_when_client_declares_it() -> None:
    payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "create_pane":
            payloads.append(payload)
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(
            request_fn=request,
            socket_ref="herdr://ccb-demo",
            allow_session_scoped_ipc_refs=True,
        ),
        capability_gate=_supported_gate(),
    )

    backend.create_pane(
        {
            "backend_family": "herdr-native",
            "backend_impl": "herdr",
            "namespace_id": "workspace-1",
            "session_name": "restored-session",
            "ipc_kind": "herdr_socket",
            "ipc_ref": "herdr://restored-session",
            "restore_token": "restored-session::workspace-1",
        },
        cwd="D:/demo",
    )

    assert payloads[0]["session_name"] == "restored-session"
    assert payloads[0]["ipc_ref"] == "herdr://ccb-demo"
    with pytest.raises(MuxCommandErrorV2):
        backend.create_pane(
            {
                "backend_impl": "herdr",
                "namespace_id": "workspace-1",
                "session_name": "ccb-demo",
                "ipc_kind": "herdr_socket",
                "ipc_ref": "herdr://foreign",
                "restore_token": None,
            },
            cwd="D:/demo",
        )


def test_herdr_backend_capture_rejects_foreign_pane_ref() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")
    backend.create_pane(namespace, command=[], cwd="D:/demo", env={}, title="workspace")

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.capture_pane(
            {
                "backend_impl": "herdr",
                "pane_id": "pane-1",
                "session_name": "foreign-session",
                "window_name": None,
                "agent_slug": None,
            },
            lines=10,
        )

    assert exc_info.value.category == "not-found"
    assert exc_info.value.operation == "capture_pane"


def test_herdr_backend_accepts_uncached_v2_pane_ref() -> None:
    captured_payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "capture_pane":
            captured_payloads.append(payload)
            return {"status": "ok", "pane_id": payload["pane_id"], "text": "restored ready"}
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    backend.namespace_ref("restored-session", "workspace-1")

    text, evidence = backend.capture_pane(
        {
            "backend_impl": "herdr",
            "pane_id": "restored-pane",
            "session_name": "restored-session",
            "window_name": None,
            "agent_slug": None,
        },
        lines=10,
    )

    assert text == "restored ready"
    assert evidence["status"] == "ok"
    assert captured_payloads[0]["session_name"] == "restored-session"


def test_herdr_backend_rejects_uncached_v2_pane_ref_without_known_namespace() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.capture_pane(
            {
                "backend_impl": "herdr",
                "pane_id": "foreign-pane",
                "session_name": "foreign-session",
                "window_name": None,
                "agent_slug": None,
            },
            lines=10,
        )

    assert exc_info.value.category == "not-found"


def test_herdr_backend_io_operations_run_schema_gate_for_uncached_v2_ref() -> None:
    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "server_info":
            return {
                "version": "herdr 0.7.5-preview",
                "api_schema": "Unexpected API",
                "platform": "windows",
                "arch": "x64",
            }
        raise AssertionError(f"unexpected operation after schema mismatch: {operation}")

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    backend.namespace_ref("restored-session", "workspace-1")

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.capture_pane(
            {
                "backend_impl": "herdr",
                "pane_id": "restored-pane",
                "session_name": "restored-session",
                "window_name": None,
                "agent_slug": None,
            },
            lines=10,
        )

    assert exc_info.value.category == "schema-mismatch"


def test_herdr_backend_liveness_transient_failure_does_not_evict_pane() -> None:
    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "capture_pane":
            raise MuxCommandErrorV2(
                category="transient-unavailable",
                backend_impl="herdr",
                operation="capture_pane",
                detail="temporary failure",
            )
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")
    pane = backend.create_pane(namespace, command=[], cwd="D:/demo", env={}, title="workspace")

    assert backend.is_alive(pane["pane_id"]) is True
    assert backend._panes[pane["pane_id"]] == pane


def test_herdr_backend_liveness_schema_mismatch_fails_closed() -> None:
    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "server_info":
            return {
                "version": "herdr 0.7.5-preview",
                "api_schema": "Unexpected API",
                "platform": "windows",
                "arch": "x64",
            }
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    backend._panes["pane-1"] = {
        "backend_impl": "herdr",
        "pane_id": "pane-1",
        "session_name": "ccb-demo",
        "window_name": None,
        "agent_slug": None,
    }

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.is_alive("pane-1")

    assert exc_info.value.category == "schema-mismatch"


def test_herdr_backend_is_alive_accepts_v2_pane_ref_with_known_namespace() -> None:
    captured_payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "capture_pane":
            captured_payloads.append(payload)
            return {"status": "ok", "pane_id": payload["pane_id"], "text": "ready"}
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    backend.namespace_ref("restored-session", "workspace-1")

    assert backend.is_alive(
        {
            "backend_impl": "herdr",
            "pane_id": "restored-pane",
            "session_name": "restored-session",
            "window_name": None,
            "agent_slug": None,
        }
    ) is True
    assert captured_payloads[0]["pane_id"] == "restored-pane"


def test_herdr_backend_is_alive_rejects_v2_pane_ref_without_known_namespace() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    assert backend.is_alive(
        {
            "backend_impl": "herdr",
            "pane_id": "foreign-pane",
            "session_name": "foreign-session",
            "window_name": None,
            "agent_slug": None,
        }
    ) is False


def test_herdr_backend_namespace_ref_is_local_builder() -> None:
    calls: list[str] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        calls.append(operation)
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    namespace = backend.namespace_ref("ccb-demo", "workspace-1")

    assert namespace["namespace_id"] == "workspace-1"
    assert namespace["ipc_kind"] == "herdr_socket"
    assert calls == []


def test_herdr_backend_split_unknown_pane_is_structured_not_found() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.split_pane(
            {
                "backend_impl": "herdr",
                "pane_id": "restored-pane",
                "session_name": "ccb-demo",
                "window_name": None,
                "agent_slug": None,
            }
        )

    assert exc_info.value.category == "not-found"
    assert exc_info.value.operation == "split_pane"


def test_herdr_backend_split_accepts_v2_pane_ref_with_known_namespace() -> None:
    create_pane_payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "create_pane":
            create_pane_payloads.append(payload)
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    backend.namespace_ref("restored-session", "workspace-1")

    pane = backend.split_pane(
        {
            "backend_impl": "herdr",
            "pane_id": "restored-pane",
            "session_name": "restored-session",
            "window_name": None,
            "agent_slug": None,
        },
        direction="down",
        percent=25,
        command=[],
        cwd="D:/demo",
        env={},
        title="child",
    )

    assert pane["pane_id"] == "pane-1"
    assert create_pane_payloads[0]["parent_pane"] == "restored-pane"
    assert create_pane_payloads[0]["session_name"] == "restored-session"


def test_herdr_backend_split_rejects_ambiguous_known_namespace() -> None:
    create_pane_payloads: list[dict[str, object]] = []

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "create_pane":
            create_pane_payloads.append(payload)
        return _fake_herdr_request()(operation, payload)

    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=request, socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    backend.namespace_ref("restored-session", "workspace-1")
    backend.namespace_ref("restored-session", "workspace-2")

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.split_pane(
            {
                "backend_impl": "herdr",
                "pane_id": "restored-pane",
                "session_name": "restored-session",
                "window_name": None,
                "agent_slug": None,
            },
            command=[],
            cwd="D:/demo",
            env={},
        )

    assert exc_info.value.category == "not-found"
    assert "ambiguous" in exc_info.value.detail
    assert create_pane_payloads == []


def test_herdr_backend_send_and_kill_unknown_pane_are_structured_not_found() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )

    with pytest.raises(MuxCommandErrorV2) as send_exc:
        backend.send_text("missing-pane", "hello")
    with pytest.raises(MuxCommandErrorV2) as kill_exc:
        backend.kill_pane("missing-pane")

    assert send_exc.value.category == "not-found"
    assert send_exc.value.operation == "send_text"
    assert kill_exc.value.category == "not-found"
    assert kill_exc.value.operation == "kill_pane"


def test_herdr_backend_activate_is_structured_unsupported() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")
    pane = backend.create_pane(namespace, command=[], cwd="D:/demo", env={}, title="workspace")

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.activate(pane["pane_id"])

    assert exc_info.value.category == "unsupported"
    assert exc_info.value.operation == "activate"


def test_herdr_backend_rejects_foreign_pane_ref() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(request_fn=_fake_herdr_request(), socket_ref="herdr://local"),
        capability_gate=_supported_gate(),
    )
    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="ccb-demo")
    backend.create_pane(namespace, command=[], cwd="D:/demo", env={}, title="workspace")

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        backend.send_text(
            {
                "backend_impl": "herdr",
                "pane_id": "pane-1",
                "session_name": "foreign-session",
                "window_name": None,
                "agent_slug": None,
            },
            "hello",
        )

    assert exc_info.value.category == "not-found"
    assert exc_info.value.operation == "send_text"


def test_terminal_backend_selection_creates_herdr_only_after_gates_pass() -> None:
    created: list[str] = []
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "herdr",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: created.append("herdr") or "herdr-backend",
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend("herdr") == "herdr-backend"
    assert created == ["herdr"]


def test_terminal_backend_selection_fails_closed_without_herdr_capability_evidence() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "herdr",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: "herdr-backend",
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: None,
        herdr_capability_report_ref_fn=lambda: None,
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        selection.get_backend("herdr")

    assert exc_info.value.category == "unsupported"
    assert exc_info.value.operation == "select_backend"
    assert exc_info.value.evidence["selection"]["failure_reason"] == "herdr-capability-missing"


def test_terminal_backend_selection_does_not_return_stale_tmux_for_explicit_herdr() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "tmux",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: "herdr-backend",
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend("tmux") == "tmux"
    assert selection.get_backend("herdr") == "herdr-backend"


def test_terminal_backend_selection_does_not_return_stale_herdr_for_explicit_tmux() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "herdr",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: "herdr-backend",
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend("herdr") == "herdr-backend"
    assert selection.get_backend("tmux") == "tmux"


def test_terminal_backend_selection_preserves_non_windows_auto_legacy_fallback() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "auto",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: "herdr-backend",
        platform_gate_fn=lambda: {"supported": False, "os_platform": "linux", "cpu_arch": "x64"},
        herdr_capability_report_fn=lambda: None,
        herdr_capability_report_ref_fn=lambda: None,
    )

    assert selection.get_backend("auto") == "tmux"


def test_terminal_backend_selection_auto_blocks_when_herdr_schema_gate_fails() -> None:
    backend = HerdrBackend(
        client=HerdrSocketClient(
            request_fn=_fake_herdr_request(server_info={"api_schema": "Unexpected API"}),
            socket_ref="herdr://local",
        ),
        capability_gate=_supported_gate(),
    )
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "auto",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: backend,
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend("auto") is None


def test_terminal_backend_selection_preserves_explicit_herdr_prepare_failure() -> None:
    backend = _PrepareFailsBackend()
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "herdr",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: backend,
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        selection.get_backend("herdr")

    assert exc_info.value.category == "schema-mismatch"
    assert exc_info.value.operation == "server_info"
    assert backend.prepare_calls == 1


def test_terminal_backend_selection_auto_returns_none_on_herdr_prepare_failure() -> None:
    backend = _PrepareFailsBackend()
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "auto",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: backend,
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend("auto") is None
    assert backend.prepare_calls == 1


def test_terminal_backend_selection_auto_returns_none_on_herdr_factory_failure() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "auto",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: (_ for _ in ()).throw(RuntimeError("factory failed")),
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend("auto") is None


def test_terminal_backend_selection_explicit_herdr_wraps_factory_failure() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "auto",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: (_ for _ in ()).throw(RuntimeError("factory failed")),
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        selection.get_backend("herdr")

    assert exc_info.value.category == "transient-unavailable"
    assert exc_info.value.operation == "select_backend"


def test_terminal_backend_selection_platform_default_routes_herdr_when_detect_is_empty() -> None:
    backend = _PreparedBackend()
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: backend,
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend() is backend
    assert backend.prepare_calls == 1


def test_terminal_backend_selection_platform_default_prepare_failure_returns_none() -> None:
    backend = _PrepareFailsBackend()
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: backend,
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend() is None
    assert backend.prepare_calls == 1


def test_terminal_backend_selection_implicit_failure_does_not_cache_none() -> None:
    failing_backend = _PrepareFailsBackend()
    prepared_backend = _PreparedBackend()
    factories = [lambda: failing_backend, lambda: prepared_backend]
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: factories.pop(0)(),
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend() is None
    assert selection.get_backend() is prepared_backend
    assert prepared_backend.prepare_calls == 1


def test_terminal_backend_selection_rechecks_dynamic_herdr_inputs_after_tmux_cache() -> None:
    detected = ["tmux", None]
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: detected.pop(0),
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: "herdr",
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend() == "tmux"
    assert selection.get_backend() == "herdr"


def test_terminal_backend_selection_explicit_request_does_not_pollute_cache() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "tmux",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: "herdr",
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    assert selection.get_backend("herdr") == "herdr"
    assert selection.cached_backend is None
    assert selection.get_backend() == "tmux"
    assert selection.cached_backend == "tmux"


def test_terminal_backend_selection_reuses_explicit_backend_without_implicit_cache_pollution() -> None:
    created: list[str] = []
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "tmux",
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: created.append("herdr") or _PreparedBackend(),
        platform_gate_fn=_windows_x64_platform_gate,
        herdr_capability_report_fn=lambda: _supported_gate().capabilities,
        herdr_capability_report_ref_fn=lambda: "evidence/herdr-capabilities.json",
    )

    first = selection.get_backend("herdr")
    second = selection.get_backend("herdr")

    assert first is second
    assert created == ["herdr"]
    assert selection.cached_backend is None


def test_terminal_backend_selection_non_windows_platform_default_falls_back_to_tmux() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: "tmux",
        herdr_backend_factory=lambda: "herdr",
        platform_gate_fn=lambda: {"supported": False, "os_platform": "linux", "cpu_arch": "x64"},
        herdr_capability_report_fn=lambda: None,
        herdr_capability_report_ref_fn=lambda: None,
    )

    assert selection.get_backend() == "tmux"


def test_terminal_api_get_backend_threads_production_herdr_wiring(monkeypatch) -> None:
    monkeypatch.setattr(terminal_api, "_backend_cache", None)
    monkeypatch.setattr(terminal_api, "_herdr_platform_gate", _windows_x64_platform_gate)
    monkeypatch.setattr(terminal_api, "_herdr_capability_report", lambda: _supported_gate().capabilities)
    monkeypatch.setattr(terminal_api, "_herdr_capability_report_ref", lambda: "evidence/herdr-capabilities.json")
    monkeypatch.setattr(terminal_api, "_herdr_request_adapter", lambda: _FakeRequestAdapter())

    backend = terminal_api.get_backend("herdr")

    assert isinstance(backend, HerdrBackend)


def test_terminal_api_get_backend_herdr_defaults_fail_closed(monkeypatch) -> None:
    monkeypatch.setattr(terminal_api, "_backend_cache", None)

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        terminal_api.get_backend("herdr")

    assert exc_info.value.operation == "select_backend"


def test_terminal_api_get_backend_auto_preserves_non_windows_tmux(monkeypatch) -> None:
    monkeypatch.setattr(terminal_api, "_backend_cache", None)
    monkeypatch.setattr(terminal_api, "_backend_cache_key", None)
    monkeypatch.setattr(
        terminal_api,
        "_herdr_platform_gate",
        lambda: {"supported": False, "os_platform": "linux", "cpu_arch": "x64"},
    )
    monkeypatch.setattr(terminal_api, "_herdr_capability_report", lambda: None)
    monkeypatch.setattr(terminal_api, "TmuxBackend", lambda: "tmux")

    assert terminal_api.get_backend("auto") == "tmux"


def test_terminal_api_get_backend_rechecks_auto_after_tmux_cache(monkeypatch) -> None:
    detected = ["tmux", None]
    monkeypatch.setattr(terminal_api, "_backend_cache", None)
    monkeypatch.setattr(terminal_api, "_backend_cache_key", None)
    monkeypatch.setattr(terminal_api, "detect_terminal", lambda: detected.pop(0))
    monkeypatch.setattr(terminal_api, "TmuxBackend", lambda: "tmux")
    monkeypatch.setattr(terminal_api, "_herdr_platform_gate", _windows_x64_platform_gate)
    monkeypatch.setattr(terminal_api, "_herdr_capability_report", lambda: _supported_gate().capabilities)
    monkeypatch.setattr(terminal_api, "_herdr_capability_report_ref", lambda: "evidence/herdr-capabilities.json")
    monkeypatch.setattr(terminal_api, "_herdr_request_adapter", lambda: _FakeRequestAdapter())

    assert terminal_api.get_backend() == "tmux"
    assert isinstance(terminal_api.get_backend(), HerdrBackend)


def test_terminal_api_explicit_backend_request_bypasses_module_cache(monkeypatch) -> None:
    stale_backend = "tmux"
    monkeypatch.setattr(terminal_api, "_backend_cache", stale_backend)
    monkeypatch.setattr(terminal_api, "_backend_cache_key", "tmux")
    monkeypatch.setattr(terminal_api, "_herdr_platform_gate", _windows_x64_platform_gate)
    monkeypatch.setattr(terminal_api, "_herdr_capability_report", lambda: _supported_gate().capabilities)
    monkeypatch.setattr(terminal_api, "_herdr_capability_report_ref", lambda: "evidence/herdr-capabilities.json")
    monkeypatch.setattr(terminal_api, "_herdr_request_adapter", lambda: _FakeRequestAdapter())

    backend = terminal_api.get_backend("herdr")

    assert isinstance(backend, HerdrBackend)
    assert terminal_api._backend_cache is stale_backend


def test_terminal_api_herdr_runtime_env_bypasses_implicit_cache(monkeypatch) -> None:
    monkeypatch.setattr(terminal_api, "_backend_cache", "stale")
    monkeypatch.setattr(terminal_api, "_backend_cache_key", "tmux")
    monkeypatch.setattr(terminal_api, "detect_terminal", lambda: "tmux")
    monkeypatch.setattr(terminal_api, "TmuxBackend", lambda: "fresh")
    monkeypatch.setenv("CCB_HERDR_SESSION", "runtime-session")

    assert terminal_api.get_backend() == "fresh"
    assert terminal_api._backend_cache == "stale"


def test_terminal_api_platform_gate_uses_live_wsl_runtime(monkeypatch) -> None:
    monkeypatch.setattr(terminal_api, "is_windows", lambda: True)
    monkeypatch.setattr(terminal_api, "_is_wsl_impl", lambda: True)
    monkeypatch.setattr(terminal_api.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(terminal_api.platform, "architecture", lambda: ("64bit", "WindowsPE"))

    gate = terminal_api._herdr_platform_gate()

    assert gate["supported"] is False
    assert gate["is_wsl"] is True
    assert gate["platform_gate_ref"] == "runtime"


def test_terminal_api_capability_report_can_use_runtime_override(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(terminal_api, "_ROOT_DIR", tmp_path)
    report_path = tmp_path / "evidence" / "herdr-capabilities.json"
    report_path.parent.mkdir()
    report_path.write_text(
        '{"backend_impl":"herdr","command_status":{"session_attach":"supported","pane_spawn":"supported","send_input":"supported","read_output":"supported","kill_pane":"supported"},"semantic_status":{"session_attach":"supported","pane_spawn":"supported","send_input":"supported","read_output":"supported","kill_pane":"supported"},"windows_beta_gaps":[],"blocking_gaps":[],"source_ref":"runtime"}',
        encoding="utf-8",
    )
    monkeypatch.setenv("CCB_HERDR_CAPABILITY_REPORT", str(report_path))

    assert terminal_api._herdr_capability_report()["source_ref"] == "evidence/herdr-capabilities.json"
    assert terminal_api._herdr_capability_report_ref() == "evidence/herdr-capabilities.json"


def test_terminal_api_malformed_capability_report_is_invalid_request(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(terminal_api, "_ROOT_DIR", tmp_path)
    report_path = tmp_path / "evidence" / "herdr-capabilities.json"
    report_path.parent.mkdir()
    report_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv("CCB_HERDR_CAPABILITY_REPORT", str(report_path))

    report = terminal_api._herdr_capability_report()

    assert report is not None
    assert report["blocked"] is True
    assert report["failure_reason"] == "invalid-request"
    assert terminal_api._herdr_capability_report_ref() == "evidence/herdr-capabilities.json"


def test_terminal_api_missing_configured_capability_report_is_invalid_request(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(terminal_api, "_ROOT_DIR", tmp_path)
    report_path = tmp_path / "evidence" / "missing.json"
    monkeypatch.setenv("CCB_HERDR_CAPABILITY_REPORT", str(report_path))

    report = terminal_api._herdr_capability_report()

    assert report is not None
    assert report["blocked"] is True
    assert report["failure_reason"] == "invalid-request"


def test_terminal_api_capability_report_uses_external_override_without_leaking_absolute_ref(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(terminal_api, "_ROOT_DIR", tmp_path / "repo")
    report_path = tmp_path / "outside" / "herdr-capabilities.json"
    report_path.parent.mkdir()
    report_path.write_text('{"source_ref":"C:/Users/Administrator/secret/herdr-capabilities.json"}', encoding="utf-8")
    monkeypatch.setenv("CCB_HERDR_CAPABILITY_REPORT", str(report_path))

    assert terminal_api._herdr_capability_report()["source_ref"] == "herdr-capabilities.json"
    assert terminal_api._herdr_capability_report_ref() == "herdr-capabilities.json"


def test_terminal_api_capability_gate_rejects_malformed_supported_report() -> None:
    gate = terminal_api._herdr_capability_gate({"backend_impl": "herdr"})

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        gate.require_supported("prepare_server")

    assert exc_info.value.evidence["failure_reason"] == "invalid-request"


def test_terminal_api_capability_gate_rejects_contradictory_report_metadata() -> None:
    capabilities = dict(_supported_gate().capabilities or {})
    capabilities.update(
        {
            "adapter_recommendation": "stop",
            "verdict": "failed",
            "failure_class": "windows-beta-gap",
        }
    )
    gate = terminal_api._herdr_capability_gate(capabilities)

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        gate.require_supported("prepare_server")

    assert exc_info.value.evidence["failure_reason"] == "invalid-request"


def test_terminal_api_herdr_request_adapter_uses_socket_ref_override(monkeypatch) -> None:
    monkeypatch.setenv("CCB_HERDR_SOCKET_REF", "herdr://override")

    adapter = terminal_api._herdr_request_adapter()

    assert adapter.socket_ref == "herdr://override"


def test_herdr_cli_request_adapter_maps_server_info_and_core_operations() -> None:
    commands: list[list[str]] = []

    def run_fn(command, **kwargs):
        commands.append(command)
        assert command[1:3] == ["--session", "ccb-demo"]
        joined = " ".join(command)
        if "status --json" in joined:
            return _completed('{"client":{"version":"0.7.5-preview"},"server":{"socket":"C:/tmp/herdr.sock"}}')
        if "--version" in joined:
            return _completed("herdr 0.7.5-preview\n")
        if "api schema --json" in joined:
            return _completed('{"title":"Herdr API"}')
        if "workspace create" in joined:
            return _completed(
                '{"result":{"workspace":{"workspace_id":"w1"},"root_pane":{"pane_id":"w1:p1","workspace_id":"w1"}}}'
            )
        if "workspace list" in joined:
            return _completed('{"result":{"workspaces":[{"workspace_id":"w1","label":"demo"}]}}')
        if "pane list" in joined:
            return _completed(
                '{"result":{"panes":[{"pane_id":"w1:p1","workspace_id":"w1"},{"pane_id":"w1:p2","workspace_id":"w1"}]}}'
            )
        if "pane split" in joined:
            return _completed('{"result":{"pane":{"pane_id":"w1:p2","workspace_id":"w1"}}}')
        if "pane run" in joined:
            return _completed("")
        if "pane read" in joined:
            return _completed("ready")
        if "pane close" in joined:
            return _completed('{"result":{"type":"ok"}}')
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    assert adapter("server_info", {})["api_schema"] == "Herdr API"
    namespace = adapter("create_session", {"project_id": "demo", "cwd": "D:/demo", "title": "demo"})
    restored = adapter("restore_session", {"restore_token": namespace["restore_token"]})
    pane = adapter("create_pane", {"namespace_id": namespace["namespace_id"], "cwd": "D:/demo"})
    sent = adapter("send_text", {"pane_id": pane["pane_id"], "text": "hello"})
    captured = adapter("capture_pane", {"pane_id": pane["pane_id"], "lines": 10})
    killed = adapter("kill_pane", {"pane_id": pane["pane_id"]})

    assert namespace["namespace_id"] == "w1"
    assert namespace["restore_token"] == "ccb-demo::w1"
    assert namespace["session_name"] == "ccb-demo"
    assert restored["restore_token"] == "ccb-demo::w1"
    assert restored["session_name"] == "ccb-demo"
    assert pane["pane_id"] == "w1:p2"
    assert pane["session_name"] == "ccb-demo"
    assert sent["status"] == "ok"
    assert captured["text"] == "ready"
    assert killed["status"] == "ok"
    assert commands


def test_herdr_backend_uses_cli_adapter_envelope_contract_for_core_operations() -> None:
    commands: list[list[str]] = []

    def run_fn(command, **kwargs):
        commands.append(command)
        joined = " ".join(command)
        if "status --json" in joined:
            return _completed('{"client":{"version":"0.7.5-preview"}}')
        if "--version" in joined:
            return _completed("herdr 0.7.5-preview\n")
        if "api schema --json" in joined:
            return _completed('{"title":"Herdr API"}')
        if "workspace create" in joined:
            return _completed(
                '{"result":{"workspace":{"workspace_id":"w1"},"root_pane":{"pane_id":"w1:p1","workspace_id":"w1"}}}'
            )
        if "pane list" in joined:
            return _completed(
                '{"result":{"panes":[{"pane_id":"w1:p1","workspace_id":"w1"},{"pane_id":"w1:p2","workspace_id":"w1"}]}}'
            )
        if "pane split" in joined:
            return _completed('{"result":{"pane":{"pane_id":"w1:p2","workspace_id":"w1"}}}')
        if "pane run" in joined:
            return _completed("")
        if "pane read" in joined:
            return _completed("ready")
        if "pane close" in joined:
            return _completed('{"result":{"type":"ok"}}')
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )
    backend = HerdrBackend(
        client=HerdrSocketClient(
            request_fn=adapter,
            socket_ref=adapter.socket_ref,
            allow_session_scoped_ipc_refs=adapter.allow_session_scoped_ipc_refs,
        ),
        capability_gate=_supported_gate(),
    )

    namespace = backend.create_session(project_id="demo", cwd="D:/demo", title="demo")
    pane = backend.create_pane(namespace, command=["python", "-V"], cwd="D:/demo", env={}, title="root")
    split = backend.split_pane(pane, command=[], cwd="D:/demo", env={}, title="child")
    send = backend.send_text(split, "hello")
    captured, capture = backend.capture_pane(split, lines=5)
    killed = backend.kill_pane(split)

    assert pane["pane_id"] == "w1:p2"
    assert split["pane_id"] == "w1:p2"
    assert send["status"] == "ok"
    assert captured == "ready"
    assert capture["status"] == "ok"
    assert killed["status"] == "ok"
    assert any("pane run" in " ".join(command) for command in commands)


def test_herdr_cli_request_adapter_rejects_exit_zero_failed_json_status() -> None:
    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "workspace create" in joined:
            return _completed(
                '{"status":"failed","detail":"workspace failed","result":{"workspace":{"workspace_id":"w1"}}}'
            )
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("create_session", {"project_id": "demo", "cwd": "D:/demo", "title": "demo"})

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.detail == "workspace failed"


def test_herdr_cli_request_adapter_rejects_create_session_without_workspace_id() -> None:
    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "workspace create" in joined:
            return _completed('{"result":{"workspace":{},"root_pane":{}}}')
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("create_session", {"project_id": "demo", "cwd": "D:/demo", "title": "demo"})

    assert exc_info.value.category == "command-failed"
    assert "workspace_id" in exc_info.value.detail


def test_herdr_cli_request_adapter_rejects_create_pane_without_pane_id() -> None:
    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "pane list" in joined:
            return _completed('{"result":{"panes":[{"pane_id":"w1:p1","workspace_id":"w1"}]}}')
        if "pane split" in joined:
            return _completed('{"result":{"pane":{"workspace_id":"w1"}}}')
        if "pane run" in joined:
            raise AssertionError("pane run must not execute without pane_id")
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("create_pane", {"namespace_id": "w1", "session_name": "ccb-demo"})

    assert exc_info.value.category == "command-failed"
    assert "pane_id" in exc_info.value.detail


def test_herdr_cli_request_adapter_rejects_non_list_create_pane_command() -> None:
    def run_fn(command, **kwargs):
        raise AssertionError("command validation should happen before Herdr command execution")

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("create_pane", {"namespace_id": "w1", "session_name": "ccb-demo", "command": "python -V"})

    assert exc_info.value.category == "command-failed"
    assert "list of argv parts" in exc_info.value.detail


def test_herdr_cli_request_adapter_kill_pane_accepts_empty_success_output() -> None:
    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "pane close" in joined:
            return _completed("")
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    killed = adapter("kill_pane", {"pane_id": "w1:p1", "session_name": "ccb-demo"})

    assert killed["status"] == "ok"
    assert killed["pane_id"] == "w1:p1"


def test_herdr_cli_request_adapter_rejects_nested_failed_json_status() -> None:
    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "pane list" in joined:
            return _completed('{"result":{"panes":[{"pane_id":"w1:p1","workspace_id":"w1"}]}}')
        if "pane split" in joined:
            return _completed(
                '{"status":"ok","detail":"outer detail","result":{"status":"failed","message":"split failed","pane":{"pane_id":"w1:p2","workspace_id":"w1"}}}'
            )
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("create_pane", {"namespace_id": "w1", "session_name": "ccb-demo"})

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.detail == "split failed"


def test_herdr_cli_request_adapter_runs_command_after_create_pane_split() -> None:
    commands: list[list[str]] = []

    def run_fn(command, **kwargs):
        commands.append(command)
        joined = " ".join(command)
        if "pane list" in joined:
            return _completed('{"result":{"panes":[{"pane_id":"w1:p1","workspace_id":"w1"}]}}')
        if "pane split" in joined:
            return _completed('{"result":{"pane":{"pane_id":"w1:p2","workspace_id":"w1"}}}')
        if "pane run" in joined:
            assert command[1:3] == ["--session", "ccb-demo"]
            expected_command = (
                subprocess.list2cmdline(["python", "-c", "print('a b')"])
                if sys.platform.startswith("win")
                else shlex.join(["python", "-c", "print('a b')"])
            )
            assert command[-2:] == ["w1:p2", expected_command]
            return _completed("")
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    pane = adapter(
        "create_pane",
        {"namespace_id": "w1", "session_name": "ccb-demo", "command": ["python", "-c", "print('a b')"]},
    )

    assert pane["pane_id"] == "w1:p2"
    assert any("pane run" in " ".join(command) for command in commands)


def test_herdr_cli_request_adapter_focuses_workspace_for_attach_namespace() -> None:
    commands: list[list[str]] = []

    def run_fn(command, **kwargs):
        commands.append(command)
        return _completed("")

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    attached = adapter(
        "attach_namespace",
        {"namespace_id": "w1", "session_name": "restored-session", "restore_token": "secret"},
    )

    assert attached["status"] == "ok"
    assert attached["namespace_id"] == "w1"
    assert commands == [["herdr", "--session", "restored-session", "workspace", "focus", "w1"]]
    assert "secret" not in str(commands)


def test_herdr_cli_request_adapter_rejects_create_pane_env_override() -> None:
    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=lambda command, **kwargs: (_ for _ in ()).throw(AssertionError(command)),
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("create_pane", {"namespace_id": "w1", "env": {"SECRET": "value"}})

    assert exc_info.value.category == "command-failed"
    assert "environment overrides" in exc_info.value.detail


def test_herdr_cli_request_adapter_threads_session_scope_and_split_geometry() -> None:
    split_commands: list[list[str]] = []

    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "pane list" in joined:
            assert command[1:3] == ["--session", "restored-session"]
            return _completed('{"result":{"panes":[{"pane_id":"w1:p1","workspace_id":"w1"}]}}')
        if "pane split" in joined:
            split_commands.append(command)
            assert command[1:3] == ["--session", "restored-session"]
            return _completed('{"result":{"pane":{"pane_id":"w1:p2","workspace_id":"w1"}}}')
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    pane = adapter(
        "create_pane",
        {
            "namespace_id": "w1",
            "ipc_ref": "herdr://restored-session",
            "session_name": "restored-session",
            "cwd": "D:/demo",
            "direction": "down",
            "percent": 25,
            "parent_pane": "w1:p1",
        },
    )

    assert pane["pane_id"] == "w1:p2"
    assert pane["session_name"] == "restored-session"
    assert "pane list" not in " ".join(" ".join(command) for command in split_commands)
    assert "w1:p1" in split_commands[0]
    assert "--direction" in split_commands[0]
    assert split_commands[0][split_commands[0].index("--direction") + 1] == "down"
    assert split_commands[0][split_commands[0].index("--ratio") + 1] == "0.25"


def test_herdr_cli_request_adapter_rejects_parent_pane_outside_namespace() -> None:
    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "pane list" in joined:
            return _completed('{"result":{"panes":[{"pane_id":"other:p1","workspace_id":"other"}]}}')
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter(
            "create_pane",
            {
                "namespace_id": "w1",
                "session_name": "ccb-demo",
                "parent_pane": "other:p1",
            },
        )

    assert exc_info.value.category == "command-failed"
    assert "unknown Herdr parent pane" in exc_info.value.detail


def test_herdr_cli_request_adapter_preserves_socket_ref_override_in_namespace() -> None:
    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "workspace create" in joined:
            return _completed(
                '{"result":{"workspace":{"workspace_id":"w1"},"root_pane":{"pane_id":"w1:p1","workspace_id":"w1"}}}'
            )
        if "workspace list" in joined:
            return _completed('{"result":{"workspaces":[{"workspace_id":"w1","label":"demo"}]}}')
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
        socket_ref="herdr://override",
    )

    namespace = adapter("create_session", {"project_id": "demo", "cwd": "D:/demo", "title": "demo"})
    restored = adapter("restore_session", {"restore_token": namespace["restore_token"]})

    assert namespace["session_name"] == "ccb-demo"
    assert namespace["ipc_ref"] == "herdr://override"
    assert restored["session_name"] == "ccb-demo"
    assert restored["ipc_ref"] == "herdr://override"


def test_herdr_cli_request_adapter_restore_uses_restored_session_ipc_ref() -> None:
    commands: list[list[str]] = []

    def run_fn(command, **kwargs):
        commands.append(command)
        joined = " ".join(command)
        if "workspace list" in joined:
            assert command[1:3] == ["--session", "restored-session"]
            return _completed('{"result":{"workspaces":[{"workspace_id":"w1","label":"demo"}]}}')
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    restored = adapter("restore_session", {"restore_token": "restored-session::w1"})

    assert restored["session_name"] == "restored-session"
    assert restored["ipc_ref"] == "herdr://restored-session"
    assert commands


def test_herdr_cli_request_adapter_restore_failure_uses_restored_session_ipc_ref() -> None:
    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "workspace list" in joined:
            assert command[1:3] == ["--session", "restored-session"]
            return _completed('{"result":{"workspaces":[]}}')
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("restore_session", {"restore_token": "restored-session::w1"})

    assert exc_info.value.ipc_ref == "herdr://restored-session"


@pytest.mark.parametrize("restore_token", ["w1", "::w1", "ccb-demo::", "ccb-demo::w1::extra"])
def test_herdr_cli_request_adapter_rejects_restore_token_without_session_scope(
    restore_token: str,
) -> None:
    def run_fn(command, **kwargs):
        raise AssertionError("restore token validation should happen before Herdr command execution")

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("restore_session", {"restore_token": restore_token})

    assert exc_info.value.category == "command-failed"
    assert exc_info.value.operation == "restore_session"


def test_herdr_cli_request_adapter_normalizes_capture_line_count() -> None:
    commands: list[list[str]] = []

    def run_fn(command, **kwargs):
        commands.append(command)
        return _completed("ready")

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    captured = adapter("capture_pane", {"pane_id": "p1", "session_name": "ccb-demo", "lines": -5})

    assert captured["text"] == "ready"
    assert commands[0][commands[0].index("--lines") + 1] == "1"


def test_herdr_cli_request_adapter_supports_is_alive_probe() -> None:
    commands: list[list[str]] = []

    def run_fn(command, **kwargs):
        commands.append(command)
        return _completed("ready")

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    result = adapter("is_alive", {"pane_id": "p1", "session_name": "ccb-demo"})

    assert result["status"] == "ok"
    assert result["alive"] is True
    assert "pane read" in " ".join(commands[0])


def test_herdr_cli_request_adapter_is_alive_maps_not_found_to_false() -> None:
    def request_fn(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "capture_pane":
            raise MuxCommandErrorV2(
                category="not-found",
                backend_impl="herdr",
                operation="capture_pane",
                detail="pane not found",
            )
        raise AssertionError(operation)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=lambda command, **kwargs: _completed(""),
        which_fn=lambda name: "herdr",
    )
    adapter._capture_pane = lambda payload: request_fn("capture_pane", dict(payload))  # type: ignore[method-assign]

    result = adapter("is_alive", {"pane_id": "p1", "session_name": "ccb-demo"})

    assert result["status"] == "ok"
    assert result["alive"] is False


def test_herdr_cli_request_adapter_is_alive_maps_command_not_found_to_false() -> None:
    def run_fn(command, **kwargs):
        raise _called_process_error(command, stderr="pane not found")

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    result = adapter("is_alive", {"pane_id": "p1", "session_name": "ccb-demo"})

    assert result["status"] == "ok"
    assert result["alive"] is False


def test_herdr_cli_request_adapter_redacts_send_text_failure_evidence() -> None:
    secret = "TOKEN=super-secret-value"

    def run_fn(command, **kwargs):
        raise _called_process_error(command, stderr="send failed")

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("send_text", {"pane_id": "p1", "text": secret})

    assert secret not in str(exc_info.value.evidence)
    assert exc_info.value.evidence["argv"][-1] == "<redacted>"
    assert exc_info.value.evidence["operation"] == "send_text"


def test_herdr_cli_request_adapter_command_failure_uses_effective_session_ipc_ref() -> None:
    def run_fn(command, **kwargs):
        assert command[1:3] == ["--session", "restored-session"]
        raise _called_process_error(command, stderr="send failed")

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        adapter("send_text", {"pane_id": "p1", "session_name": "restored-session", "text": "hello"})

    assert exc_info.value.ipc_ref == "herdr://restored-session"


def test_herdr_cli_request_adapter_server_info_rejects_non_windows_runtime(monkeypatch) -> None:
    def run_fn(command, **kwargs):
        joined = " ".join(command)
        if "status --json" in joined:
            return _completed('{"client":{"version":"0.7.5-preview"}}')
        if "--version" in joined:
            return _completed("herdr 0.7.5-preview\n")
        if "api schema --json" in joined:
            return _completed('{"title":"Herdr API"}')
        raise AssertionError(joined)

    monkeypatch.setattr(herdr_cli.sys, "platform", "linux")
    monkeypatch.setattr(herdr_cli.platform, "machine", lambda: "aarch64")
    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )
    client = HerdrSocketClient(request_fn=adapter, socket_ref=adapter.socket_ref)

    with pytest.raises(MuxCommandErrorV2) as exc_info:
        client.server_info()

    assert exc_info.value.category == "schema-mismatch"
    assert exc_info.value.evidence["actual_platform"] == "linux"
    assert exc_info.value.evidence["actual_arch"] == "arm64"


def test_herdr_cli_request_adapter_omits_empty_cwd_arguments() -> None:
    commands: list[list[str]] = []

    def run_fn(command, **kwargs):
        commands.append(command)
        joined = " ".join(command)
        if "workspace create" in joined:
            assert "--cwd" not in command
            return _completed(
                '{"result":{"workspace":{"workspace_id":"w1"},"root_pane":{"pane_id":"w1:p1","workspace_id":"w1"}}}'
            )
        if "pane list" in joined:
            return _completed('{"result":{"panes":[{"pane_id":"w1:p1","workspace_id":"w1"}]}}')
        if "pane split" in joined:
            assert "--cwd" not in command
            return _completed('{"result":{"pane":{"pane_id":"w1:p2","workspace_id":"w1"}}}')
        raise AssertionError(joined)

    adapter = HerdrCliRequestAdapter(
        session_name="ccb-demo",
        herdr_executable="herdr",
        run_fn=run_fn,
        which_fn=lambda name: "herdr",
    )

    namespace = adapter("create_session", {"project_id": "demo", "cwd": "", "title": "demo"})
    pane = adapter("create_pane", {"namespace_id": namespace["namespace_id"], "cwd": ""})

    assert namespace["namespace_id"] == "w1"
    assert pane["pane_id"] == "w1:p2"
    assert commands


def _supported_gate() -> HerdrCapabilityGate:
    return HerdrCapabilityGate.from_spike_evidence(
        {
            "adapter_recommendation": "continue",
            "verdict": "pass",
            "failure_class": "none",
            "capability_projection": {
                "command_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                },
                "semantic_status": {
                    "session_attach": "supported",
                    "pane_spawn": "supported",
                    "send_input": "supported",
                    "read_output": "supported",
                    "kill_pane": "supported",
                },
                "windows_beta_gaps": [],
                "blocking_gaps": [],
            },
        },
        capability_report_ref="evidence/herdr-capabilities.json",
    )


def _windows_x64_platform_gate() -> dict[str, object]:
    return {
        "supported": True,
        "os_platform": "win32",
        "cpu_arch": "x64",
        "python_bitness": "64bit",
        "is_wsl": False,
    }


def _fake_herdr_request(
    *,
    server_info: dict[str, object] | None = None,
):
    state = {
        "server_info": {
            "version": "herdr 0.7.5-preview",
            "api_schema": "Herdr API",
            "platform": "windows",
            "arch": "x64",
        },
        "namespace": {
            "namespace_id": "workspace-1",
            "session_name": "ccb-demo",
            "restore_token": "ccb-demo::workspace-1",
        },
        "pane": {
            "pane_id": "pane-1",
            "session_name": "ccb-demo",
            "output": "python ready",
        },
    }
    if server_info is not None:
        state["server_info"].update(server_info)

    def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "server_info":
            return dict(state["server_info"])
        if operation == "create_session":
            return dict(state["namespace"])
        if operation == "restore_session":
            if payload["restore_token"] != "ccb-demo::workspace-1":
                raise AssertionError(f"unexpected restore_token: {payload['restore_token']!r}")
            return dict(state["namespace"])
        if operation == "create_pane":
            pane = dict(state["pane"])
            pane["session_name"] = payload.get("session_name") or pane["session_name"]
            return pane
        if operation == "send_text":
            if payload["text"] != "secret typed text":
                raise AssertionError(f"unexpected send_text payload: {payload['text']!r}")
            return {"status": "ok", "pane_id": payload["pane_id"]}
        if operation == "capture_pane":
            return {"status": "ok", "pane_id": payload["pane_id"], "text": state["pane"]["output"]}
        if operation == "kill_pane":
            return {"status": "ok", "pane_id": payload["pane_id"]}
        raise AssertionError(f"unexpected fake Herdr operation {operation}")

    return request


class _FakeRequestAdapter:
    socket_ref = "herdr://local"

    def __call__(self, operation: str, payload: dict[str, object]) -> dict[str, object]:
        return _fake_herdr_request()(operation, payload)


class _PrepareFailsBackend:
    def __init__(self) -> None:
        self.prepare_calls = 0

    def prepare_server(self) -> None:
        self.prepare_calls += 1
        raise MuxCommandErrorV2(
            category="schema-mismatch",
            backend_impl="herdr",
            operation="server_info",
            detail="schema mismatch",
            ipc_ref="herdr://local",
        )


class _PreparedBackend:
    def __init__(self) -> None:
        self.prepare_calls = 0

    def prepare_server(self) -> None:
        self.prepare_calls += 1


def _completed(stdout: str):
    class _Result:
        def __init__(self, stdout: str) -> None:
            self.stdout = stdout
            self.stderr = ""

    return _Result(stdout)


def _called_process_error(command: list[str], *, stderr: str = "") -> Exception:
    return subprocess.CalledProcessError(1, command, stderr=stderr)
