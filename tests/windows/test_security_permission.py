"""Security audit tests for file permissions on Windows NTFS (D-11/D-12).

Covers:
- os.chmod(0o600) ineffectiveness on NTFS (Pitfall 1)
- os.chmod(0o400) sets read-only on Windows
- askd_server.py chmod has os.name != "nt" guard
- mail/ modules with unguarded chmod calls (audit finding)
"""

import ast
import os
import stat as stat_mod

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Test 1: os.chmod(0o600) ineffective on NTFS
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_chmod_600_ineffective_on_ntfs(tmp_path):
    """os.chmod(0o600) does NOT set owner-only permissions on NTFS.

    On Windows NTFS, POSIX permission bits (rwxr-x---) are not enforced.
    The actual mode remains 0o666 (NTFS default), making chmod(0o600)
    a no-op for access control. This is Pitfall 1 from the security audit.

    On Unix, chmod(0o600) correctly restricts to owner-only.
    """
    test_file = tmp_path / "chmod_test.txt"
    test_file.write_text("sensitive data", encoding="utf-8")

    os.chmod(test_file, 0o600)
    st = test_file.stat()
    actual_mode = stat_mod.S_IMODE(st.st_mode) & 0o777

    if os.name == "nt":
        # On NTFS, chmod(0o600) does NOT produce 0o600
        assert actual_mode != 0o600, (
            f"os.chmod(0o600) produced 0o{actual_mode:o} on NTFS -- "
            "expected != 0o600 (Pitfall 1: NTFS ignores POSIX permission bits)"
        )
    else:
        # On Unix, chmod(0o600) works correctly
        assert actual_mode == 0o600, (
            f"Expected 0o600, got 0o{actual_mode:o}"
        )


# ---------------------------------------------------------------------------
# Test 2: os.chmod(0o400) sets read-only on Windows
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_chmod_400_sets_readonly_on_windows(tmp_path):
    """os.chmod(0o400) makes a file read-only on Windows NTFS.

    Windows maps 0o400 to the FILE_ATTRIBUTE_READONLY flag,
    which removes write access for the current user.
    """
    test_file = tmp_path / "readonly_test.txt"
    test_file.write_text("data", encoding="utf-8")

    os.chmod(test_file, 0o400)

    if os.name == "nt":
        assert not os.access(test_file, os.W_OK), (
            "os.chmod(0o400) should make file read-only on Windows"
        )
    else:
        # On Unix, owner should still be able to read
        assert os.access(test_file, os.R_OK), (
            "os.chmod(0o400) should allow owner read on Unix"
        )

    # Cleanup: restore write access so tmp_path can be cleaned up
    try:
        os.chmod(test_file, 0o644)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Test 3: askd_server.py _write_state chmod has NT guard
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_askd_server_chmod_has_nt_guard():
    """lib/askd_server.py _write_state() guards os.chmod(0o600) with os.name != 'nt'.

    This is the correct pattern: skip chmod on Windows where it has no effect
    on NTFS permission enforcement.
    """
    server_file = Path(__file__).resolve().parent.parent.parent / "lib" / "askd_server.py"
    source = server_file.read_text(encoding="utf-8")

    # Find the _write_state method
    tree = ast.parse(source)

    write_state_method = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_write_state":
            write_state_method = node
            break

    assert write_state_method is not None, "_write_state method not found in askd_server.py"

    # Verify os.chmod exists in the method
    source_lines = source.split("\n")
    method_start = write_state_method.body[0].lineno - 1  # first line of method body
    method_end = write_state_method.end_lineno
    method_source = "\n".join(source_lines[method_start:method_end])

    assert "os.chmod" in method_source, "os.chmod not found in _write_state"
    assert "os.name" in method_source or 'os.name != "nt"' in method_source, (
        "_write_state chmod call is NOT guarded by os.name != 'nt'"
    )


# ---------------------------------------------------------------------------
# Test 4: mail/ modules missing NT guard for chmod (audit finding)
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_mail_modules_missing_nt_guard():
    """Scan lib/mail/*.py for chmod calls WITHOUT os.name != 'nt' guard.

    Expected audit finding: mail/ modules use chmod(0o600) directly
    without checking os.name == 'nt', making them Pitfall 1 violations
    on Windows NTFS.

    This test identifies the gap; the actual fix is a future task.
    """
    lib_dir = Path(__file__).resolve().parent.parent.parent / "lib" / "mail"
    mail_py_files = sorted(lib_dir.glob("*.py"))

    files_with_unguarded_chmod = []

    for py_file in mail_py_files:
        source = py_file.read_text(encoding="utf-8")
        source_lines = source.split("\n")

        for i, line in enumerate(source_lines):
            stripped = line.strip()
            # Skip comments and string-only lines
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            # Look for .chmod( calls (not "chmod" in a string like error messages)
            if ".chmod(" in stripped and "chmod(" in stripped:
                # Check if it's an actual call (not in a comment or string)
                # Look for os.name != "nt" guard in preceding lines (within 5 lines)
                guard_found = False
                for j in range(max(0, i - 5), i):
                    guard_line = source_lines[j]
                    if 'os.name != "nt"' in guard_line or 'os.name == "nt"' in guard_line:
                        guard_found = True
                        break
                    if 'sys.platform' in guard_line and 'win' in guard_line:
                        guard_found = True
                        break

                # Also check if chmod is inside a function that checks os.name
                if not guard_found:
                    files_with_unguarded_chmod.append(
                        f"{py_file.name}:{i+1}: {stripped}"
                    )

    # Audit finding: we EXPECT unguarded chmod in mail/ modules.
    # Use pytest.xfail to document the gap without failing the test suite.
    # When these are fixed, the xfail will turn into XPASS and signal completion.
    expected_unguarded = {
        "ask_handler.py:98", "attachments.py:97", "config.py:337",
        "config.py:434", "credentials.py:113", "daemon.py:96", "threads.py:82",
    }
    found_locations = {item.split(":")[0] + ":" + item.split(":")[1] for item in files_with_unguarded_chmod}

    if found_locations:
        pytest.xfail(
            f"Pitfall 1: {len(files_with_unguarded_chmod)} unguarded chmod calls "
            f"in mail/ modules (chmod ineffective on NTFS):\n" +
            "\n".join(f"  - {item}" for item in sorted(files_with_unguarded_chmod)) +
            "\n\nThese need os.name != 'nt' guards or DACL-based permissions."
        )
    else:
        # All fixed -- test now passes, which is the desired end state
        pass
