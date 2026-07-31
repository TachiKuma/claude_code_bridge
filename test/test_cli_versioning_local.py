from __future__ import annotations

import json
from pathlib import Path

from cli.management_runtime.versioning_runtime.local import format_version_info, get_version_info


def test_get_version_info_reads_build_metadata_files(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "VERSION").write_text("6.0.1\n", encoding="utf-8")
    (tmp_path / "BUILD_INFO.json").write_text(
        json.dumps(
            {
                "version": "6.0.1",
                "commit": "abc1234",
                "date": "2026-04-09",
                "branch_ref": "refs/heads/feature/windows-herdr",
                "source_ref": "refs/tags/v8.5.2",
                "build_time": "2026-04-09T10:11:12Z",
                "platform": "linux",
                "arch": "x86_64",
                "channel": "stable",
                "source_kind": "release",
                "install_mode": "release",
                "installed_at": "2026-04-09T10:15:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "cli.management_runtime.versioning_runtime.local.git_version_info",
        lambda dir_path: None,
    )

    info = get_version_info(tmp_path)

    assert info["version"] == "6.0.1"
    assert info["commit"] == "abc1234"
    assert info["date"] == "2026-04-09"
    assert info["branch_ref"] == "refs/heads/feature/windows-herdr"
    assert info["source_ref"] == "refs/tags/v8.5.2"
    assert info["build_time"] == "2026-04-09T10:11:12Z"
    assert info["platform"] == "linux"
    assert info["arch"] == "x86_64"
    assert info["channel"] == "stable"
    assert info["source_kind"] == "release"
    assert info["install_mode"] == "release"
    assert info["installed_at"] == "2026-04-09T10:15:00Z"


def test_get_version_info_reads_embedded_ccb_metadata(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "ccb").write_text(
        'VERSION="1.2.3"\nGIT_COMMIT="abc123"\nGIT_DATE="2026-04-06"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "cli.management_runtime.versioning_runtime.local.git_version_info",
        lambda dir_path: None,
    )

    info = get_version_info(tmp_path)

    assert info["commit"] == "abc123"
    assert info["date"] == "2026-04-06"
    assert info["version"] == "1.2.3"
    assert info["install_mode"] == "release"
    assert info["source_kind"] == "release"
    assert format_version_info(info) == "v1.2.3 abc123 2026-04-06"


def test_get_version_info_prefers_git_metadata_when_available(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "ccb").write_text('VERSION="1.2.3"\n', encoding="utf-8")
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(
        "cli.management_runtime.versioning_runtime.local.git_version_info",
        lambda dir_path: {"commit": "def456", "date": "2026-04-07"},
    )

    info = get_version_info(tmp_path)

    assert info["commit"] == "def456"
    assert info["date"] == "2026-04-07"
    assert info["version"] == "1.2.3"
    assert info["install_mode"] == "source"
    assert info["source_kind"] == "source"
    assert info["channel"] == "dev"


def test_get_version_info_exposes_branch_and_source_refs_from_git_metadata(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr("cli.management_runtime.versioning_runtime.local.shutil.which", lambda _name: "git")
    monkeypatch.setattr(
        "cli.management_runtime.versioning_runtime.local._git_output",
        lambda _dir_path, args: {
            "git -C {} log -1 --format=%h".format(tmp_path): "abc1234",
            "git -C {} log -1 --format=%ci".format(tmp_path): "2026-04-09 10:11:12 +0000",
            "git -C {} branch --show-current".format(tmp_path): "feature/windows-herdr",
            "git -C {} describe --tags --exact-match".format(tmp_path): "v8.5.2",
        }.get(" ".join(args)),
    )

    info = get_version_info(tmp_path)

    assert info["commit"] == "abc1234"
    assert info["date"] == "2026-04-09"
    assert info["branch_ref"] == "refs/heads/feature/windows-herdr"
    assert info["source_ref"] == "refs/tags/v8.5.2"


def test_get_version_info_uses_v852_ancestor_tag_as_source_ref_on_feature_branch(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr("cli.management_runtime.versioning_runtime.local.shutil.which", lambda _name: "git")
    monkeypatch.setattr(
        "cli.management_runtime.versioning_runtime.local._git_output",
        lambda _dir_path, args: {
            "git -C {} log -1 --format=%h".format(tmp_path): "def5678",
            "git -C {} log -1 --format=%ci".format(tmp_path): "2026-04-10 10:11:12 +0000",
            "git -C {} branch --show-current".format(tmp_path): "feature/windows-herdr",
            "git -C {} describe --tags --exact-match".format(tmp_path): None,
        }.get(" ".join(args)),
    )
    monkeypatch.setattr(
        "cli.management_runtime.versioning_runtime.local._git_succeeds",
        lambda _dir_path, args: "refs/tags/v8.5.2" in args,
    )

    info = get_version_info(tmp_path)

    assert info["branch_ref"] == "refs/heads/feature/windows-herdr"
    assert info["source_ref"] == "refs/tags/v8.5.2"
