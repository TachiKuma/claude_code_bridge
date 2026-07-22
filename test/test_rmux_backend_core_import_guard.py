from __future__ import annotations

from pathlib import Path


def test_rmux_backend_core_does_not_import_tmux_or_psmux_implementations() -> None:
    paths = [
        Path("lib/terminal_runtime/rmux_backend.py"),
        *Path("lib/terminal_runtime/rmux_backend_runtime").glob("*.py"),
    ]

    for path in paths:
        source = path.read_text(encoding="utf-8")
        assert "tmux_backend" not in source
        assert "psmux_backend" not in source
        assert "TmuxBackend" not in source
        assert "PsmuxBackend" not in source


def test_rmux_backend_core_does_not_own_io_logging_or_foreground_attach() -> None:
    source = Path("lib/terminal_runtime/rmux_backend.py").read_text(encoding="utf-8")

    forbidden = (
        "def send_text",
        "def send_key",
        "def capture_pane",
        "def get_pane_content",
        "def ensure_pane_log",
        "def pane_log_path",
        "pipe-pane",
        "attach_session_foreground",
    )
    for token in forbidden:
        assert token not in source


def test_tmux_backend_paths_do_not_import_rmux_backend() -> None:
    for path in (
        Path("lib/terminal_runtime/tmux_backend.py"),
        Path("lib/terminal_runtime/tmux_mux_backend.py"),
        Path("lib/terminal_runtime/tmux_backend_panes.py"),
    ):
        source = path.read_text(encoding="utf-8")
        assert "rmux_backend" not in source
