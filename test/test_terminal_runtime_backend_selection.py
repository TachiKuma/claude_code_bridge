from __future__ import annotations

import terminal_runtime.backend_selection as backend_selection_module
from terminal_runtime.backend_selection import TerminalBackendSelection, TerminalLayoutService
from terminal_runtime.backend_resolver import build_herdr_capability_blocked_fixture, resolve_mux_backend_v2
from terminal_runtime.mux_backend_contract import make_capabilities


class _FakeBackend:
    def __init__(self, name: str) -> None:
        self.name = name


def test_backend_selection_caches_detected_backend() -> None:
    calls: list[str] = []
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: 'tmux',
        tmux_backend_factory=lambda: calls.append('tmux') or _FakeBackend('tmux'),
    )

    first = selection.get_backend()
    second = selection.get_backend()

    assert first is second
    assert isinstance(first, _FakeBackend)
    assert first.name == 'tmux'
    assert calls == ['tmux']


def test_backend_selection_uses_session_terminal_field() -> None:
    captured: dict[str, object] = {}

    def _tmux_backend_factory(socket_name=None, socket_path=None):
        captured['socket_name'] = socket_name
        captured['socket_path'] = socket_path
        return _FakeBackend('tmux')

    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=_tmux_backend_factory,
    )

    tmux_backend = selection.get_backend_for_session({'terminal': 'tmux', 'tmux_socket_name': 'sock-demo'})
    assert isinstance(tmux_backend, _FakeBackend)
    assert tmux_backend.name == 'tmux'
    assert captured['socket_name'] == 'sock-demo'
    assert captured['socket_path'] is None
    selection.get_backend_for_session({'terminal': 'tmux', 'tmux_socket_path': '/tmp/ccb.sock'})
    assert captured['socket_path'] == '/tmp/ccb.sock'
    assert selection.get_pane_id_from_session({'pane_id': '%1', 'tmux_session': '%old'}) == '%1'
    assert selection.get_pane_id_from_session({'tmux_session': '%old'}) == '%old'


def test_terminal_layout_service_delegates_to_runtime_layout() -> None:
    backend = _FakeBackend('tmux')
    captured: dict[str, object] = {}

    def fake_create_tmux_auto_layout(providers, **kwargs):
        captured['providers'] = providers
        captured.update(kwargs)

        class _Result:
            panes = {'a1': '%root'}

        return _Result()

    original = backend_selection_module.create_tmux_auto_layout
    backend_selection_module.create_tmux_auto_layout = fake_create_tmux_auto_layout
    service = TerminalLayoutService(
        tmux_backend_factory=lambda: backend,
        detached_session_name_fn=lambda **kwargs: 'ccb-demo-1',
        os_getpid_fn=lambda: 123,
        time_fn=lambda: 5.0,
        env={'TMUX': '/tmp/tmux'},
    )
    try:
        result = service.create_auto_layout(['a1'], cwd='/tmp/demo')
    finally:
        backend_selection_module.create_tmux_auto_layout = original

    assert result.panes == {'a1': '%root'}
    assert captured['providers'] == ['a1']
    assert captured['backend'] is backend
    assert captured['detached_session_name'] == 'ccb-demo-1'
    assert captured['inside_tmux'] is True


def test_mux_backend_resolver_blocks_native_windows_auto_without_capability_evidence() -> None:
    result = resolve_mux_backend_v2(
        requested_backend="auto",
        source="platform_default",
        platform_gate=_windows_x64_platform_gate(),
        capability_report=None,
        capability_report_ref=None,
    )

    assert result["blocked"] is True
    assert result["backend_family"] == "herdr-native"
    assert result["backend_impl"] == "herdr"
    assert result["effective_backend"] is None
    assert result["fallback_used"] is False
    assert result["failure_reason"] == "herdr-capability-missing"


def test_mux_backend_resolver_blocks_auto_when_platform_gate_is_missing() -> None:
    result = resolve_mux_backend_v2(
        requested_backend="auto",
        source="platform_default",
        platform_gate=None,
        capability_report=_supported_herdr_capabilities(),
        capability_report_ref="evidence/herdr-capabilities.json",
    )

    assert result["blocked"] is True
    assert result["backend_family"] == "herdr-native"
    assert result["backend_impl"] == "herdr"
    assert result["effective_backend"] is None
    assert result["failure_reason"] == "platform-gate-blocked"


def test_mux_backend_resolver_selects_herdr_only_after_native_windows_capability_validation() -> None:
    result = resolve_mux_backend_v2(
        requested_backend="auto",
        source="platform_default",
        platform_gate=_windows_x64_platform_gate(),
        capability_report=_supported_herdr_capabilities(),
        capability_report_ref="evidence/herdr-capabilities.json",
    )

    assert result["backend_family"] == "herdr-native"
    assert result["backend_impl"] == "herdr"
    assert result["effective_backend"] == "herdr"
    assert result["fallback_used"] is False
    assert result["capability_report_ref"] == "evidence/herdr-capabilities.json"


def test_mux_backend_resolver_blocks_windows_beta_gaps() -> None:
    capability_report = _supported_herdr_capabilities()
    capability_report["windows_beta_gaps"] = ["server_restart_output_history"]

    result = resolve_mux_backend_v2(
        requested_backend="auto",
        source="platform_default",
        platform_gate=_windows_x64_platform_gate(),
        capability_report=capability_report,
        capability_report_ref="evidence/herdr-capabilities.json",
    )

    assert result["blocked"] is True
    assert result["effective_backend"] is None
    assert result["failure_reason"] == "unsupported-capability"


def test_mux_backend_resolver_preserves_non_windows_auto_legacy_selection() -> None:
    result = resolve_mux_backend_v2(
        requested_backend="auto",
        source="auto_probe",
        platform_gate={"supported": False, "os_platform": "linux", "cpu_arch": "x64"},
        capability_report=None,
        capability_report_ref=None,
        legacy_default_backend="rmux",
    )

    assert result["backend_family"] == "tmux-family"
    assert result["backend_impl"] == "rmux"
    assert result["effective_backend"] == "rmux"


def test_mux_backend_resolver_preserves_structured_herdr_failure_reasons() -> None:
    capability_report = {
        "blocked": True,
        "backend_family": "herdr-native",
        "backend_impl": "herdr",
        "requested_backend": "herdr",
        "effective_backend": None,
        "source": "auto_probe",
        "platform_gate": _windows_x64_platform_gate(),
        "fallback_used": False,
        "fallback_reason": None,
        "capability_report_ref": "evidence/herdr-capabilities.json",
        "failure_reason": "schema-mismatch",
        "diagnostic": "schema mismatch",
    }
    result = resolve_mux_backend_v2(
        requested_backend="herdr",
        source="cli",
        platform_gate=_windows_x64_platform_gate(),
        capability_report=capability_report,
        capability_report_ref="evidence/herdr-capabilities.json",
    )

    assert result["blocked"] is True
    assert result["failure_reason"] == "schema-mismatch"
    assert result["fallback_used"] is False


def test_mux_backend_resolver_keeps_malformed_blocked_report_fail_closed() -> None:
    result = resolve_mux_backend_v2(
        requested_backend="herdr",
        source="cli",
        platform_gate=_windows_x64_platform_gate(),
        capability_report={
            "blocked": True,
            "backend_family": "herdr-native",
            "backend_impl": "herdr",
        },
        capability_report_ref="evidence/malformed.json",
    )

    assert result["blocked"] is True
    assert result["failure_reason"] == "invalid-request"
    assert result["diagnostic"] == "Herdr selection is blocked by malformed capability evidence"
    assert result["fallback_used"] is False


def test_mux_backend_resolver_keeps_non_mapping_capability_report_fail_closed() -> None:
    result = resolve_mux_backend_v2(
        requested_backend="herdr",
        source="cli",
        platform_gate=_windows_x64_platform_gate(),
        capability_report=["not-a-capability-report"],  # type: ignore[arg-type]
        capability_report_ref="evidence/malformed.json",
    )

    assert result["blocked"] is True
    assert result["failure_reason"] == "invalid-request"
    assert result["diagnostic"] == "Herdr selection is blocked by malformed capability evidence"
    assert result["fallback_used"] is False


def test_mux_backend_resolver_rejects_incomplete_herdr_capability_evidence() -> None:
    reports = [
        make_capabilities(
            backend_impl="herdr",
            command_status={},
            semantic_status={},
            source_ref="evidence/empty.json",
        ),
        {
            **_supported_herdr_capabilities(),
            "windows_beta_gaps": ["server_restart_output_history"],
        },
        make_capabilities(
            backend_impl="tmux",
            command_status={
                "session_attach": "supported",
                "pane_spawn": "supported",
                "send_input": "supported",
                "read_output": "supported",
                "kill_pane": "supported",
            },
            semantic_status={
                "session_attach": "supported",
                "pane_spawn": "supported",
                "send_input": "supported",
                "read_output": "supported",
                "kill_pane": "supported",
            },
            source_ref="evidence/wrong-backend.json",
        ),
        make_capabilities(
            backend_impl="herdr",
            command_status={
                "session_attach": "supported",
                "pane_spawn": "supported",
                "send_input": "supported",
                "read_output": "supported",
            },
            semantic_status={
                "session_attach": "supported",
                "pane_spawn": "supported",
                "send_input": "supported",
                "read_output": "supported",
                "kill_pane": "supported",
            },
            source_ref="evidence/missing-required.json",
        ),
        {
            **_supported_herdr_capabilities(),
            "command_status": {
                "session_attach": "supported",
                "pane_spawn": "supported",
                "send_input": "unknown",
                "read_output": "supported",
                "kill_pane": "supported",
            },
        },
    ]

    for capability_report in reports:
        result = resolve_mux_backend_v2(
            requested_backend="auto",
            source="platform_default",
            platform_gate=_windows_x64_platform_gate(),
            capability_report=capability_report,  # type: ignore[arg-type]
            capability_report_ref="evidence/herdr-capabilities.json",
        )

        assert result["blocked"] is True
        assert result["failure_reason"] == "unsupported-capability"
        assert result["effective_backend"] is None


def test_herdr_blocked_fixture_preserves_recognized_failure_class() -> None:
    result = build_herdr_capability_blocked_fixture(
        {"failure_class": "platform-gate-blocked"},
        capability_report_ref="evidence/herdr-contract-spike-evidence.json",
    )

    assert result["blocked"] is True
    assert result["failure_reason"] == "platform-gate-blocked"
    assert result["fallback_used"] is False


def test_mux_backend_resolver_blocks_windows_x64_when_gate_is_not_admitted() -> None:
    gate_variants = [
        {"supported": False},
        {"python_bitness": "32bit"},
        {"is_wsl": True},
    ]

    for updates in gate_variants:
        platform_gate = _windows_x64_platform_gate()
        platform_gate.update(updates)
        result = resolve_mux_backend_v2(
            requested_backend="auto",
            source="platform_default",
            platform_gate=platform_gate,
            capability_report=_supported_herdr_capabilities(),
            capability_report_ref="evidence/herdr-capabilities.json",
        )

        assert result["blocked"] is True
        assert result["failure_reason"] == "platform-gate-blocked"
        assert result["effective_backend"] is None
        assert result["fallback_used"] is False


def _windows_x64_platform_gate() -> dict[str, object]:
    return {
        "supported": True,
        "os_platform": "win32",
        "cpu_arch": "x64",
        "python_bitness": "64bit",
        "is_wsl": False,
    }


def _supported_herdr_capabilities() -> dict[str, object]:
    return make_capabilities(
        backend_impl="herdr",
        command_status={
            "session_attach": "supported",
            "pane_spawn": "supported",
            "send_input": "supported",
            "read_output": "supported",
            "kill_pane": "supported",
        },
        semantic_status={
            "session_attach": "supported",
            "pane_spawn": "supported",
            "send_input": "supported",
            "read_output": "supported",
            "kill_pane": "supported",
        },
        source_ref="evidence/herdr-capabilities.json",
    )
