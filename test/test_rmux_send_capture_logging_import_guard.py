from __future__ import annotations

import subprocess
from pathlib import Path


RMUX_IO_PATHS = [
    Path("lib/terminal_runtime/rmux_backend.py"),
    *Path("lib/terminal_runtime/rmux_backend_runtime").glob("*.py"),
]


def test_rmux_send_capture_logging_does_not_import_tmux_or_psmux_backends() -> None:
    for path in RMUX_IO_PATHS:
        source = path.read_text(encoding="utf-8")
        assert "tmux_backend" not in source
        assert "psmux_backend" not in source
        assert "TmuxBackend" not in source
        assert "PsmuxBackend" not in source


def test_rmux_io_does_not_use_tmux_buffer_paste_fallback() -> None:
    source = Path("lib/terminal_runtime/rmux_backend_runtime/io.py").read_text(encoding="utf-8")

    for token in ("load-buffer", "paste-buffer", "delete-buffer"):
        assert token not in source


def test_rmux_io_does_not_inline_shell_pipe_literals() -> None:
    source = Path("lib/terminal_runtime/rmux_backend_runtime/io.py").read_text(encoding="utf-8").lower()

    for token in ("tee -a", "sh -lc", "powershell", "cmd /", "cmd.exe /"):
        assert token not in source


def test_current_diff_does_not_modify_provider_completion_parsers_or_ccbd_lifecycle() -> None:
    cp = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    changed = {_status_path(line).replace("\\", "/") for line in cp.stdout.splitlines() if line.strip()}
    forbidden_prefixes = (
        "lib/completion/detectors/",
        "lib/provider_pane_status/",
        "lib/provider_backends/codex/",
        "lib/provider_backends/claude/",
        "lib/provider_backends/agy/execution_runtime/",
        "lib/provider_backends/deepseek/execution",
        "lib/ccbd/",
        "lib/mobile_gateway/",
    )

    assert not [
        path
        for path in changed
        if path.startswith(forbidden_prefixes)
        and path not in {
            "test/test_rmux_completion_capture_fixtures.py",
            "test/test_rmux_send_capture_logging_import_guard.py",
        }
    ]


def _status_path(line: str) -> str:
    text = line.rstrip("\r\n")
    path = text[3:] if len(text) > 3 else text.strip()
    if " -> " in path:
        return path.rsplit(" -> ", 1)[1].strip()
    return path.strip()


def test_status_path_preserves_unstaged_modified_paths() -> None:
    assert _status_path(" M lib/provider_backends/codex/execution.py") == "lib/provider_backends/codex/execution.py"
    assert _status_path("M  lib/ccbd/app.py") == "lib/ccbd/app.py"
    assert _status_path("?? lib/mobile_gateway/new_file.py") == "lib/mobile_gateway/new_file.py"
    assert _status_path("R  old/path.py -> lib/provider_pane_status/new_path.py") == "lib/provider_pane_status/new_path.py"
