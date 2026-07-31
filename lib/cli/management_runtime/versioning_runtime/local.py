from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def get_version_info(dir_path: Path) -> dict:
    info = {
        "commit": None,
        "date": None,
        "branch_ref": None,
        "source_ref": None,
        "version": None,
        "build_time": None,
        "platform": None,
        "arch": None,
        "channel": None,
        "source_kind": None,
        "install_mode": None,
        "installed_at": None,
        "install_user_id": None,
        "install_user_name": None,
        "root_install": None,
        "sudo_user": None,
    }
    info.update(read_build_info(dir_path / "BUILD_INFO.json"))
    info.update(read_version_file(dir_path / "VERSION"))
    info.update(read_embedded_version_info(dir_path / "ccb"))
    git_info = git_version_info(dir_path)
    if git_info is not None:
        info.update(git_info)
    info = normalize_installation_info(info, dir_path=dir_path)
    return info


def read_embedded_version_info(ccb_file: Path) -> dict[str, str | None]:
    if not ccb_file.exists():
        return {}
    try:
        content = ccb_file.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    info: dict[str, str | None] = {}
    for line in content.split("\n")[:60]:
        key, value = version_assignment(line)
        if key is None or not value:
            continue
        info[key] = value
    return info


def version_assignment(line: str) -> tuple[str | None, str | None]:
    text = line.strip()
    if "=" not in text:
        return None, None
    name, raw_value = text.split("=", 1)
    value = raw_value.strip().strip('"').strip("'")
    mapping = {
        "VERSION": "version",
        "GIT_COMMIT": "commit",
        "GIT_DATE": "date",
    }
    return mapping.get(name.strip()), value or None


def read_version_file(version_file: Path) -> dict[str, str | None]:
    if not version_file.exists():
        return {}
    try:
        value = version_file.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return {}
    if not value:
        return {}
    return {"version": value}


def read_build_info(build_info_file: Path) -> dict[str, object]:
    if not build_info_file.exists():
        return {}
    try:
        payload = json.loads(build_info_file.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    normalized: dict[str, object] = {}
    for key in (
        "version",
        "commit",
        "date",
        "branch_ref",
        "source_ref",
        "build_time",
        "platform",
        "arch",
        "channel",
        "source_kind",
        "install_mode",
        "installed_at",
        "install_user_id",
        "install_user_name",
        "root_install",
        "sudo_user",
    ):
        value = payload.get(key)
        if key == "root_install" and isinstance(value, bool):
            normalized[key] = value
        else:
            normalized[key] = str(value).strip() if value not in (None, "") else None
    return normalized


def git_version_info(dir_path: Path) -> dict[str, str] | None:
    if not shutil.which("git") or not (dir_path / ".git").exists():
        return None
    commit = _git_output(dir_path, ["git", "-C", str(dir_path), "log", "-1", "--format=%h"])
    date = _git_output(dir_path, ["git", "-C", str(dir_path), "log", "-1", "--format=%ci"])
    branch = _git_output(dir_path, ["git", "-C", str(dir_path), "branch", "--show-current"])
    exact_tag = _git_output(dir_path, ["git", "-C", str(dir_path), "describe", "--tags", "--exact-match"])
    source_ref = _source_ref_from_git(dir_path, exact_tag=exact_tag)
    if not commit or not date:
        return None
    info: dict[str, str] = {
        "commit": commit,
        "date": date.split()[0],
    }
    if branch:
        info["branch_ref"] = f"refs/heads/{branch}"
    if source_ref:
        info["source_ref"] = source_ref
    return info


def _source_ref_from_git(dir_path: Path, *, exact_tag: str | None) -> str | None:
    if exact_tag:
        return f"refs/tags/{exact_tag}"
    tag_ref = "refs/tags/v8.5.2"
    if _git_succeeds(dir_path, ["git", "-C", str(dir_path), "rev-parse", "--verify", "-q", tag_ref]) and _git_succeeds(
        dir_path,
        ["git", "-C", str(dir_path), "merge-base", "--is-ancestor", tag_ref, "HEAD"],
    ):
        return tag_ref
    return None


def _git_output(dir_path: Path, args: list[str]) -> str | None:
    result = subprocess.run(
        args,
        cwd=dir_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    return text or None


def _git_succeeds(dir_path: Path, args: list[str]) -> bool:
    result = subprocess.run(
        args,
        cwd=dir_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode == 0


def normalize_installation_info(info: dict, *, dir_path: Path) -> dict:
    normalized = dict(info)
    if not normalized.get("install_mode"):
        normalized["install_mode"] = "source" if (dir_path / ".git").exists() else "release"
    if not normalized.get("source_kind"):
        normalized["source_kind"] = "source" if (dir_path / ".git").exists() else "release"
    if not normalized.get("channel"):
        normalized["channel"] = "dev" if (dir_path / ".git").exists() else None
    return normalized


def format_version_info(info: dict) -> str:
    parts = []
    if info.get("version"):
        parts.append(f"v{info['version']}")
    if info.get("commit"):
        parts.append(info["commit"])
    if info.get("date"):
        parts.append(info["date"])
    return " ".join(parts) if parts else "unknown"


__all__ = ['format_version_info', 'get_version_info']
