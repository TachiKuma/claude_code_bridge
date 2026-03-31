"""Security audit tests for process security (D-12).

Covers:
- No eval() calls in lib/ codebase (code injection prevention)
- No exec() calls in lib/ codebase (code injection prevention)
- No subprocess shell=True in lib/ and bin/ (command injection prevention)
- No hardcoded secrets in lib/ (credential exposure prevention)
"""

import glob
import os
import re

import pytest
from pathlib import Path


def _get_lib_py_files() -> list[str]:
    """Get all Python files in lib/ directory."""
    lib_dir = Path(__file__).resolve().parent.parent.parent / "lib"
    return sorted(str(p) for p in lib_dir.glob("*.py"))


def _get_bin_py_files() -> list[str]:
    """Get all Python files in bin/ directory."""
    bin_dir = Path(__file__).resolve().parent.parent.parent / "bin"
    return sorted(str(p) for p in bin_dir.glob("*.py"))


def _scan_for_pattern(files: list[str], pattern: re.Pattern) -> list[tuple[str, int, str]]:
    """Scan files for regex pattern, excluding comment-only lines.

    Returns list of (file, line_number, line_content) matches.
    """
    findings = []
    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, 1):
                    stripped = line.strip()
                    # Skip full-line comments
                    if stripped.startswith("#"):
                        continue
                    # Skip docstring-only lines (heuristic)
                    if stripped.startswith(('"""', "'''")):
                        continue
                    if pattern.search(line):
                        findings.append((filepath, line_num, stripped))
        except Exception:
            pass
    return findings


# ---------------------------------------------------------------------------
# Test 1: No eval() in lib/
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_no_eval_in_lib():
    """No eval() calls in lib/*.py (D-12: code injection prevention).

    eval() is dangerous as it executes arbitrary Python expressions.
    The CCB codebase should never use eval() for any purpose.
    """
    lib_files = _get_lib_py_files()
    pattern = re.compile(r'\beval\s*\(')
    findings = _scan_for_pattern(lib_files, pattern)

    assert len(findings) == 0, (
        f"eval() calls found in lib/ (D-12 violation):\n" +
        "\n".join(f"  {f}:{n}: {line}" for f, n, line in findings)
    )


# ---------------------------------------------------------------------------
# Test 2: No exec() in lib/
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_no_exec_in_lib():
    """No exec() calls in lib/*.py (D-12: code injection prevention).

    exec() is dangerous as it executes arbitrary Python statements.
    The CCB codebase should never use exec() for any purpose.
    """
    lib_files = _get_lib_py_files()
    pattern = re.compile(r'\bexec\s*\(')
    findings = _scan_for_pattern(lib_files, pattern)

    assert len(findings) == 0, (
        f"exec() calls found in lib/ (D-12 violation):\n" +
        "\n".join(f"  {f}:{n}: {line}" for f, n, line in findings)
    )


# ---------------------------------------------------------------------------
# Test 3: No shell=True in lib/ and bin/
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_no_shell_true_in_lib_and_bin():
    """No subprocess shell=True in lib/*.py and bin/*.py (D-12: command injection prevention).

    shell=True passes the command through the system shell, enabling
    shell metacharacter injection. The CCB codebase should always use
    list-form arguments to subprocess calls.
    """
    all_files = _get_lib_py_files() + _get_bin_py_files()
    pattern = re.compile(r'shell\s*=\s*True')
    findings = _scan_for_pattern(all_files, pattern)

    assert len(findings) == 0, (
        f"shell=True found (D-12 violation):\n" +
        "\n".join(f"  {f}:{n}: {line}" for f, n, line in findings)
    )


# ---------------------------------------------------------------------------
# Test 4: No hardcoded secrets in lib/
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_no_hardcoded_secrets_in_lib():
    """No hardcoded password/secret/api_key string literals in lib/*.py (D-12).

    Scan for patterns like password="literal", secret="literal", api_key="literal".
    Environment variable lookups (os.environ, os.getenv) are excluded.
    Function parameters and variable assignments from env vars are excluded.
    """
    lib_files = _get_lib_py_files()
    pattern = re.compile(
        r'(?i)(password|secret|api_key|apikey)\s*=\s*["\'][^"\']+["\']'
    )
    findings = _scan_for_pattern(lib_files, pattern)

    # Filter out known false positives:
    # - os.environ / os.getenv lookups (not hardcoded)
    # - function parameter defaults that are empty strings
    filtered = []
    for f, n, line in findings:
        # Allow empty string defaults
        if '""' in line or "''" in line:
            continue
        # Allow lines that reference env vars
        if "os.environ" in line or "os.getenv" in line or "ENV" in line:
            continue
        filtered.append((f, n, line))

    assert len(filtered) == 0, (
        f"Hardcoded secrets found in lib/ (D-12):\n" +
        "\n".join(f"  {f}:{n}: {line}" for f, n, line in filtered)
    )
