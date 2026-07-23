from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rmux_windows_validation_matrix.py"
SPEC = importlib.util.spec_from_file_location("rmux_windows_validation_matrix", SCRIPT_PATH)
matrix = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = matrix
SPEC.loader.exec_module(matrix)


def test_scope_guard_allows_validation_assets() -> None:
    result = matrix.evaluate_scope_paths(
        [
            "scripts/rmux_windows_validation_matrix.py",
            "scripts/rmux-windows-validation-runbook.ps1",
            "test/test_rmux_windows_validation_matrix.py",
            "test/test_rmux_windows_validation_scope_guard.py",
            ".github/workflows/ccbd-rmux-windows-validation.yml",
            "docs/plantree/plans/windows-rmux-native-backend/topics/rmux-windows-validation-runbook.md",
            ".codestable/goals/2026-07-23-rmux-windows-validation-matrix/state.yaml",
        ],
        package_json_text='{"os": ["linux", "darwin"]}',
    )

    assert result.ok, result.errors


def test_scope_guard_rejects_package_os_change() -> None:
    result = matrix.evaluate_scope_paths([], package_json_text='{"os": ["linux", "darwin", "win32"]}')

    assert result.ok is False
    assert any("package.json os" in error for error in result.errors)


def test_scope_guard_rejects_backend_and_provider_parser_paths() -> None:
    result = matrix.evaluate_scope_paths(
        [
            "lib/terminal_runtime/rmux_backend.py",
            "lib/provider_backends/codex/session_parser.py",
        ]
    )

    assert result.ok is False
    assert "lib/terminal_runtime/rmux_backend.py" in result.evidence["forbidden_paths"]
    assert "lib/provider_backends/codex/session_parser.py" in result.evidence["forbidden_paths"]


def test_scope_guard_rejects_install_and_manual_docs_contracts() -> None:
    result = matrix.evaluate_scope_paths(["install.ps1", "README.md", "docs/manuals/windows.md"])

    assert result.ok is False
    assert result.evidence["forbidden_paths"] == ["README.md", "docs/manuals/windows.md", "install.ps1"]


def test_changed_paths_includes_deleted_forbidden_paths(monkeypatch) -> None:
    calls = []

    def fake_git_lines(args):
        calls.append(args)
        if args[:2] == ["git", "diff"]:
            return ["README.md"]
        return []

    monkeypatch.setattr(matrix, "_git_lines", fake_git_lines)

    assert matrix.changed_paths("BASE") == ["README.md"]
    assert "--diff-filter=ACDMRTUXB" in calls[0]
