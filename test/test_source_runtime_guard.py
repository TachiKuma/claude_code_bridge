from __future__ import annotations

import os
import importlib.util
import io
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
CCB = REPO_ROOT / "ccb.py"
CCB_TEST = REPO_ROOT / "ccb_test"


def _load_ccb_entry_module():
    spec = importlib.util.spec_from_file_location("ccb_entry_under_test", CCB)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_source_ccb(args: list[str], *, cwd: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("CCB_SOURCE_RUNTIME_OK", None)
    env.pop("CCB_SOURCE_ALLOWED_ROOTS", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CCB), *args],
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_ccb_test(args: list[str], *, cwd: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("CCB_SOURCE_RUNTIME_OK", None)
    env.pop("CCB_SOURCE_ALLOWED_ROOTS", None)
    env.pop("CCB_TEST_ROOTS", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CCB_TEST), *args],
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_source_ccb_allows_introspection_outside_test_roots() -> None:
    proc = _run_source_ccb(["--print-version"], cwd=REPO_ROOT)

    assert proc.returncode == 0
    assert proc.stdout.strip()


def test_native_windows_introspection_does_not_probe_herdr(monkeypatch, capsys) -> None:
    ccb_entry = _load_ccb_entry_module()
    import platforms.windows.os_platform as os_platform

    calls: list[tuple[str, ...]] = []

    def fail_if_called():
        raise AssertionError("introspection command must not probe Herdr")

    def fake_entrypoint(argv, **_kwargs):
        calls.append(tuple(argv))
        return 0

    monkeypatch.setattr(ccb_entry, "is_native_windows", lambda: True)
    monkeypatch.setattr(os_platform, "check_herdr_ready", fail_if_called)
    monkeypatch.setattr(ccb_entry, "run_cli_entrypoint", fake_entrypoint)

    for argv in (
        ["ccb.py", "--help"],
        ["ccb.py", "version"],
        ["ccb.py", "config", "validate"],
    ):
        monkeypatch.setattr(ccb_entry.sys, "argv", argv)
        assert ccb_entry.main() == 0

    assert calls == [("--help",), ("version",), ("config", "validate")]
    assert "Herdr" not in capsys.readouterr().err


def test_native_windows_runtime_command_probes_herdr_at_operation_time(
    monkeypatch,
    capsys,
) -> None:
    ccb_entry = _load_ccb_entry_module()
    import platforms.windows.os_platform as os_platform

    calls: list[str] = []

    def fake_check():
        calls.append("check")
        return False, "Herdr executable not found", SimpleNamespace()

    monkeypatch.setattr(ccb_entry, "is_native_windows", lambda: True)
    monkeypatch.setattr(os_platform, "check_herdr_ready", fake_check)
    monkeypatch.setattr(
        ccb_entry,
        "run_cli_entrypoint",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("runtime command must fail before CLI dispatch")
        ),
    )
    stderr = io.StringIO()
    monkeypatch.setattr(ccb_entry.sys, "stderr", stderr)
    monkeypatch.setattr(ccb_entry.sys, "argv", ["ccb.py", "start"])

    assert ccb_entry.main() == 1
    assert calls == ["check"]
    err = stderr.getvalue()
    assert "Herdr executable not found" in err
    assert "Herdr 未就绪" in err


def test_source_ccb_rejects_stateful_commands_outside_test_roots() -> None:
    proc = _run_source_ccb(["doctor"], cwd=REPO_ROOT)

    assert proc.returncode == 1
    assert "Refusing to run the CCB source checkout outside an allowed test project" in proc.stderr
    assert (
        "Use `/home/bfly/yunwei/ccb_source/ccb_test` from "
        "`/home/bfly/yunwei/test_ccb2` for source-change validation"
    ) in proc.stderr


def test_source_ccb_default_allowed_roots_are_dedicated_test_project_only() -> None:
    proc = _run_source_ccb(["doctor"], cwd=REPO_ROOT)

    allowed_line = next(line for line in proc.stderr.splitlines() if line.startswith("Allowed source roots:"))
    roots = [item.strip() for item in allowed_line.split(":", 1)[1].split(",")]
    assert roots == [str(REPO_ROOT.parent / "test_ccb2")]


def test_source_ccb_rejects_legacy_sibling_project_arg_without_override() -> None:
    legacy_project = REPO_ROOT.parent / "test_ccb"

    proc = _run_source_ccb(["--project", str(legacy_project), "doctor"], cwd=REPO_ROOT)

    assert proc.returncode == 1
    assert "Refusing to run the CCB source checkout outside an allowed test project" in proc.stderr
    assert f"Allowed source roots: {REPO_ROOT.parent / 'test_ccb2'}" in proc.stderr


def test_source_ccb_rejects_legacy_named_external_cwd_without_override(tmp_path: Path) -> None:
    legacy_named_project = tmp_path / "test_ccb"
    legacy_named_project.mkdir()

    proc = _run_source_ccb(["doctor"], cwd=legacy_named_project)

    assert proc.returncode == 1
    assert "Refusing to run the CCB source checkout outside an allowed test project" in proc.stderr
    assert f"Allowed source roots: {REPO_ROOT.parent / 'test_ccb2'}" in proc.stderr


def test_source_ccb_allows_stateful_commands_under_configured_test_root(tmp_path: Path) -> None:
    allowed = tmp_path / "test-project"
    project = allowed / "repo"
    project.mkdir(parents=True)
    (project / ".ccb").mkdir()
    (project / ".ccb" / "ccb.config").write_text("cmd; agent1:codex\n", encoding="utf-8")

    proc = _run_source_ccb(
        ["config", "validate"],
        cwd=project,
        extra_env={"CCB_SOURCE_ALLOWED_ROOTS": str(allowed)},
    )

    assert proc.returncode == 0
    assert "config_status: valid" in proc.stdout


def test_source_ccb_allows_project_arg_under_configured_test_root_from_source_cwd(tmp_path: Path) -> None:
    allowed = tmp_path / "test-project"
    project = allowed / "repo"
    project.mkdir(parents=True)
    (project / ".ccb").mkdir()
    (project / ".ccb" / "ccb.config").write_text("cmd; agent1:codex\n", encoding="utf-8")

    proc = _run_source_ccb(
        ["--project", str(project), "config", "validate"],
        cwd=REPO_ROOT,
        extra_env={"CCB_SOURCE_ALLOWED_ROOTS": str(allowed)},
    )

    assert proc.returncode == 0
    assert "config_status: valid" in proc.stdout


def test_source_ccb_explicit_override_allows_one_off_run(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    (project / ".ccb").mkdir()
    (project / ".ccb" / "ccb.config").write_text("cmd; agent1:codex\n", encoding="utf-8")

    proc = _run_source_ccb(["config", "validate"], cwd=project, extra_env={"CCB_SOURCE_RUNTIME_OK": "1"})

    assert proc.returncode == 0
    assert "config_status: valid" in proc.stdout


def test_ccb_test_rejects_source_checkout_cwd() -> None:
    proc = _run_ccb_test(["doctor"], cwd=REPO_ROOT)

    assert proc.returncode == 1
    assert "Refusing to run `ccb_test` from the CCB source checkout" in proc.stderr
    assert "cd /home/bfly/yunwei/test_ccb2 && /home/bfly/yunwei/ccb_source/ccb_test config validate" in proc.stderr


def test_ccb_test_rejects_external_project_without_allowed_root(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    (project / ".ccb").mkdir()
    (project / ".ccb" / "ccb.config").write_text("cmd; agent1:codex\n", encoding="utf-8")

    proc = _run_ccb_test(["config", "validate"], cwd=project)

    assert proc.returncode == 1
    assert "Refusing to run `ccb_test` outside an allowed source-test project" in proc.stderr
    assert f"Allowed source-test roots: {REPO_ROOT.parent / 'test_ccb2'}" in proc.stderr


def test_ccb_test_allows_external_project_with_explicit_test_root(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    (project / ".ccb").mkdir()
    (project / ".ccb" / "ccb.config").write_text("cmd; agent1:codex\n", encoding="utf-8")

    proc = _run_ccb_test(["config", "validate"], cwd=project, extra_env={"CCB_TEST_ROOTS": str(tmp_path)})

    assert proc.returncode == 0
    assert "config_status: valid" in proc.stdout


def test_ccb_test_allows_external_project_with_explicit_source_allowed_root(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    (project / ".ccb").mkdir()
    (project / ".ccb" / "ccb.config").write_text("cmd; agent1:codex\n", encoding="utf-8")

    proc = _run_ccb_test(["config", "validate"], cwd=project, extra_env={"CCB_SOURCE_ALLOWED_ROOTS": str(tmp_path)})

    assert proc.returncode == 0
    assert "config_status: valid" in proc.stdout


def test_ccb_test_rejects_legacy_sibling_project_arg_without_override(tmp_path: Path) -> None:
    external = tmp_path / "external"
    external.mkdir()
    legacy_project = REPO_ROOT.parent / "test_ccb"

    proc = _run_ccb_test(["--project", str(legacy_project), "doctor"], cwd=external)

    assert proc.returncode == 1
    assert "Refusing to run `ccb_test` outside an allowed source-test project" in proc.stderr
    assert f"Checked project path: {legacy_project}" in proc.stderr


def test_ccb_test_allows_project_arg_under_explicit_test_root(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    project = allowed / "repo"
    external = tmp_path / "external"
    project.mkdir(parents=True)
    external.mkdir()
    (project / ".ccb").mkdir()
    (project / ".ccb" / "ccb.config").write_text("cmd; agent1:codex\n", encoding="utf-8")

    proc = _run_ccb_test(
        ["--project", str(project), "config", "validate"],
        cwd=external,
        extra_env={"CCB_TEST_ROOTS": str(allowed)},
    )

    assert proc.returncode == 0
    assert "config_status: valid" in proc.stdout


def test_ccb_test_rejects_project_arg_inside_source_checkout(tmp_path: Path) -> None:
    external = tmp_path / "external"
    external.mkdir()

    proc = _run_ccb_test(["--project", str(REPO_ROOT), "doctor"], cwd=external)

    assert proc.returncode == 1
    assert "Refusing to run `ccb_test` against a project inside the CCB source checkout" in proc.stderr


def test_ccb_test_diagnose_reports_wrapper_roots_and_allowance(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    project.mkdir()

    proc = _run_ccb_test(["--diagnose"], cwd=project)

    assert proc.returncode == 0
    assert f"wrapper: {CCB_TEST}" in proc.stdout
    assert f"source_ccb: {CCB}" in proc.stdout
    assert f"cwd: {project}" in proc.stdout
    assert f"default_roots: {REPO_ROOT.parent / 'test_ccb2'}" in proc.stdout
    assert f"effective_roots: {REPO_ROOT.parent / 'test_ccb2'}" in proc.stdout
    assert "allowed_source_test_project: no" in proc.stdout


def test_ccb_test_diagnose_reports_explicit_allowed_root(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    project.mkdir()

    proc = _run_ccb_test(["diagnose"], cwd=project, extra_env={"CCB_TEST_ROOTS": str(tmp_path)})

    assert proc.returncode == 0
    assert f"env_CCB_TEST_ROOTS: {tmp_path}" in proc.stdout
    assert f"checked_paths: {project}" in proc.stdout
    assert "allowed_source_test_project: yes" in proc.stdout


def test_ccb_test_accepts_only_fresh_well_formed_benchmark_trace_envelope() -> None:
    namespace = runpy.run_path(str(CCB_TEST))
    entry_ns = namespace["_CCB_TEST_PROCESS_ENTRY_NS"]
    validate = namespace["_valid_startup_trace_envelope"]
    valid = {
        "CCB_STARTUP_TIMING_TRACE": "1",
        "CCB_STARTUP_TRACE_ID": "trace_" + "a" * 32,
        "CCB_STARTUP_TRACE_SPAWN_NS": str(entry_ns - 1),
    }

    assert validate(valid) is True
    assert validate({**valid, "CCB_STARTUP_TRACE_ID": "trace_invalid"}) is False
    assert validate({**valid, "CCB_STARTUP_TRACE_SPAWN_NS": str(entry_ns + 1)}) is False
    assert validate({**valid, "CCB_STARTUP_TRACE_WRAPPER_ENTRY_NS": "1"}) is False
