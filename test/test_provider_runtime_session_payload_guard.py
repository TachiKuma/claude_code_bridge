from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PROVIDER_LAUNCHERS = (
    "lib/provider_backends/agy/launcher.py",
    "lib/provider_backends/claude/launcher_runtime/service.py",
    "lib/provider_backends/codex/launcher.py",
    "lib/provider_backends/deepseek/launcher.py",
    "lib/provider_backends/droid/launcher.py",
    "lib/provider_backends/gemini/launcher_runtime/service.py",
    "lib/provider_backends/kimi/launcher.py",
    "lib/provider_backends/mimo/launcher.py",
    "lib/provider_backends/native_cli_support/launcher.py",
    "lib/provider_backends/opencode/launcher.py",
)

TMUX_BACKEND_ALLOWED = {
    "lib/cli/services/runtime_launch.py",
}

PROVIDER_RUNTIME_SESSION_BOUNDARY = (
    "lib/cli/services/runtime_launch_runtime/session_files.py",
    "lib/provider_backends/pane_log_support/session.py",
    "lib/provider_core/session_binding_evidence.py",
    "lib/provider_core/session_binding_evidence_runtime/fields.py",
    "lib/ccbd/services/provider_runtime_facts.py",
    "lib/provider_backends/codex/comm_runtime/session_runtime_runtime/loading.py",
    "lib/provider_backends/gemini/comm_runtime/session_runtime.py",
    "lib/provider_backends/opencode/runtime/session_runtime.py",
    *PROVIDER_LAUNCHERS,
)


def test_provider_launchers_do_not_write_canonical_tmux_payload_keys() -> None:
    offenders: list[str] = []
    forbidden = (
        '"terminal": "tmux"',
        "'terminal': 'tmux'",
        '"tmux_session": pane_id',
        "'tmux_session': pane_id",
    )
    for relative in PROVIDER_LAUNCHERS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in forbidden:
            if needle in text:
                offenders.append(f"{relative}: {needle}")

    assert offenders == []


def test_tmux_backend_direct_dependency_stays_in_adapter_boundary() -> None:
    offenders: list[str] = []
    for relative in PROVIDER_RUNTIME_SESSION_BOUNDARY:
        if relative in TMUX_BACKEND_ALLOWED:
            continue
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        if "TmuxBackend" in text:
            offenders.append(relative)

    assert offenders == []


def test_provider_specific_tmux_env_names_are_compatibility_fallbacks() -> None:
    expected_fallbacks = {
        "lib/provider_backends/codex/comm_runtime/session_runtime_runtime/loading.py": "CCB_MUX_PANE_ID",
        "lib/provider_backends/gemini/comm_runtime/session_runtime.py": "CCB_MUX_PANE_ID",
        "lib/provider_backends/opencode/runtime/session_runtime.py": "CCB_MUX_PANE_ID",
    }
    for relative, canonical_key in expected_fallbacks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert canonical_key in text
        assert "_TMUX_SESSION" in text
