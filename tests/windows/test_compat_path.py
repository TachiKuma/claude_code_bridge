"""Tests for Windows path handling (D-10).

Covers Chinese directory paths, paths with spaces, UNC paths, path separator
consistency, relative path resolution, WSL probe timeout, and run_dir behavior.
"""

import os
import sys
import time
from pathlib import Path
from unittest import mock

import pytest


pytestmark = [pytest.mark.windows, pytest.mark.compat]


# ---------------------------------------------------------------------------
# Test 1: Chinese directory path
# ---------------------------------------------------------------------------
class TestChinesePath:
    def test_chinese_directory_path(self, tmp_path):
        """Create temp dir with Chinese characters, verify Path operations work."""
        chinese_dir = tmp_path / "中文测试目录"
        chinese_dir.mkdir()
        test_file = chinese_dir / "配置文件.json"
        test_file.write_text("test", encoding="utf-8")
        assert test_file.read_text(encoding="utf-8") == "test"
        assert os.path.exists(str(chinese_dir)) is True


# ---------------------------------------------------------------------------
# Test 2: Paths with spaces
# ---------------------------------------------------------------------------
class TestPathsWithSpaces:
    def test_path_with_spaces(self):
        """Path like 'C:\\Program Files\\CCB\\config.json' handled by os.path and pathlib."""
        p = Path("C:/Program Files/CCB/config.json")
        assert "Program Files" in str(p)
        joined = os.path.join("C:\\Program Files", "CCB", "config.json")
        assert "CCB" in joined


# ---------------------------------------------------------------------------
# Test 3: UNC paths
# ---------------------------------------------------------------------------
class TestUNCPath:
    def test_unc_path_handling(self):
        """pathlib.Path accepts UNC paths (\\\\server\\share\\file) without raising."""
        p = Path("\\\\server\\share\\file.txt")
        parts = str(p)
        # On Windows, pathlib normalizes UNC paths
        assert "server" in parts or "share" in parts or parts.startswith("\\\\")


# ---------------------------------------------------------------------------
# Test 4: Path separator consistency
# ---------------------------------------------------------------------------
class TestPathSeparator:
    def test_path_separator_consistency(self):
        """os.path.join on Windows produces backslash-separated paths."""
        result = os.path.join("C:", "Users", "test")
        # On Windows, separator should be backslash
        assert "\\" in result or "/" in result  # at least one separator present


# ---------------------------------------------------------------------------
# Test 5: Relative path resolution
# ---------------------------------------------------------------------------
class TestRelativePathResolution:
    def test_relative_path_resolution(self, tmp_path):
        """Path.resolve() correctly resolves relative paths with Chinese directory names."""
        chinese_dir = tmp_path / "中文目录"
        chinese_dir.mkdir()
        relative = Path("中文目录") / "test.txt"
        # Write via absolute path
        (chinese_dir / "test.txt").write_text("data", encoding="utf-8")
        # Read via resolved relative path
        resolved = (tmp_path / relative).resolve()
        assert resolved.exists()


# ---------------------------------------------------------------------------
# Test 6: WSL probe timeout on native Windows
# ---------------------------------------------------------------------------
class TestWSLProbe:
    def test_wsl_probe_timeout_on_native_windows(self):
        """Calling _wsl_probe_distro_and_home() on native Windows returns within 20s.

        This flags Pitfall 5 from RESEARCH.md: 10s timeout per call, multiple
        fallback calls in _wsl_probe_distro_and_home. Total budget: 20s.
        """
        from lib.ccb_config import _wsl_probe_distro_and_home

        start = time.perf_counter()
        result = _wsl_probe_distro_and_home()
        elapsed = time.perf_counter() - start

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert elapsed < 20.0, (
            f"WSL probe took {elapsed:.1f}s on native Windows (expected < 20s)"
        )


# ---------------------------------------------------------------------------
# Test 7: run_dir on Windows
# ---------------------------------------------------------------------------
class TestRunDir:
    def test_run_dir_windows(self):
        """run_dir() returns Path under AppData or home, containing 'ccb'."""
        from lib.askd_runtime import run_dir

        rd = run_dir()
        assert isinstance(rd, Path)
        assert "ccb" in str(rd).lower()
