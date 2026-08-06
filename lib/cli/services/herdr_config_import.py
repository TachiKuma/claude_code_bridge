""""ccb config import-herdr" — A-lite import mode.

Reads the current Herdr session's workspace/pane topology and generates a
``.ccb/ccb.config`` draft.  Does NOT overwrite an existing config file.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def import_herdr_config(
    *,
    project_dir: str,
    output_path: str | None = None,
    herdr_executable: str | None = None,
    herdr_session: str | None = None,
    dry_run: bool = True,
) -> dict[str, object]:
    """Generate a CCB config draft from the current Herdr topology.

    Args:
        project_dir: Absolute path to the CCB project directory.
        output_path: Optional explicit output path.  Defaults to
            ``<project_dir>/.ccb/ccb.config.herdr-import``.
        herdr_executable: Path to the ``herdr`` binary.  Auto-resolved if None.
        herdr_session: Herdr session name.  Auto-detected if None.
        dry_run: If True (default), print to stdout and do NOT write to
            ``.ccb/ccb.config``.

    Returns:
        A dict with keys ``ok``, ``config``, ``warnings``, ``written_path``.
    """
    import shutil
    import subprocess
    import sys

    exe = str(herdr_executable or "").strip() or _resolve_herdr(shutil.which)
    if not exe:
        return {"ok": False, "reason": "Herdr executable not found", "config": None, "warnings": []}

    # -- snapshot -----------------------------------------------------------
    snapshot = _herdr_snapshot(exe, session=herdr_session)
    if snapshot is None:
        return {"ok": False, "reason": "Failed to read Herdr session snapshot", "config": None, "warnings": []}

    # -- build config -------------------------------------------------------
    config, warnings = _build_ccb_config(snapshot, project_dir=project_dir)
    config["_herdr_import_meta"] = {
        "herdr_version": snapshot.get("version", "unknown"),
        "herdr_session": snapshot.get("session_name", herdr_session or "unknown"),
        "imported_at": _now_iso(),
        "source": "ccb config import-herdr (A-lite)",
    }

    # -- output -------------------------------------------------------------
    target = Path(output_path) if output_path else Path(project_dir) / ".ccb" / "ccb.config.herdr-import"
    existing_config = Path(project_dir) / ".ccb" / "ccb.config"

    result: dict[str, object] = {
        "ok": True,
        "config": config,
        "warnings": warnings,
        "written_path": str(target),
    }

    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        json.dump(config, sys.stdout, indent=2, ensure_ascii=False)
        print()  # trailing newline

    if existing_config.exists():
        warnings.append(
            f"Existing .ccb/ccb.config found — import draft written to {target.name}. "
            "Review and merge manually."
        )
        result["warnings"] = warnings

    return result


def _resolve_herdr(which_fn) -> str | None:
    exe = which_fn("herdr")
    if exe:
        return exe
    # Windows common paths
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Herdr", "herdr.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Herdr", "herdr.exe"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _herdr_snapshot(
    exe: str,
    *,
    session: str | None,
) -> dict[str, object] | None:
    import subprocess

    cmd = [exe]
    if session:
        cmd.extend(["--session", session])
    cmd.extend(["api", "snapshot"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            env=_herdr_env(),
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None

    snapshot = payload.get("result", payload).get("snapshot")
    if not isinstance(snapshot, Mapping):
        return None
    return dict(snapshot)


def _build_ccb_config(
    snapshot: Mapping[str, object],
    *,
    project_dir: str,
) -> tuple[dict[str, object], list[str]]:
    """Map Herdr workspace/pane topology to CCB agent config."""
    warnings: list[str] = []
    agents: list[dict[str, object]] = []

    workspaces = snapshot.get("workspaces")
    panes = snapshot.get("panes")

    if not isinstance(workspaces, list) or not isinstance(panes, list):
        return {"version": 3, "agents": []}, ["No workspaces or panes found in Herdr snapshot"]

    pane_by_id: dict[str, Mapping[str, object]] = {}
    for pane in panes:
        if isinstance(pane, Mapping):
            pid = str(pane.get("pane_id") or "")
            if pid:
                pane_by_id[pid] = pane

    for workspace in workspaces:
        if not isinstance(workspace, Mapping):
            continue
        workspace_label = str(workspace.get("label") or "").strip()
        workspace_id = str(workspace.get("workspace_id") or "").strip()

        workspace_panes = [
            p for p in panes
            if isinstance(p, Mapping) and str(p.get("workspace_id") or "") == workspace_id
        ]

        for pane in workspace_panes:
            pane_label = str(pane.get("label") or "").strip()
            cwd = str(pane.get("cwd") or project_dir)

            agent_config = _pane_to_agent_config(
                pane_label=pane_label,
                workspace_label=workspace_label,
                cwd=cwd,
            )
            if agent_config is not None:
                agents.append(agent_config)
            else:
                warnings.append(f"Skipped pane {pane.get('pane_id')}: unknown agent kind for label {pane_label!r}")

    config: dict[str, object] = {
        "version": 3,
        "agents": agents,
    }

    if not agents:
        warnings.append("No agent mappings generated — check Herdr pane labels")
        config["agents"] = [
            {
                "role": "agentroles.architect",
                "provider": "claude",
                "workspace": project_dir,
                "label": "imported-agent",
                "layout": {"position": "main"},
            }
        ]

    return config, warnings


def _pane_to_agent_config(
    *,
    pane_label: str,
    workspace_label: str,
    cwd: str,
) -> dict[str, object] | None:
    """Map a Herdr pane label to a CCB agent config entry."""
    label_lower = pane_label.lower()

    # Known provider keywords
    provider_map: dict[str, str] = {
        "claude": "claude",
        "codex": "codex",
        "gemini": "gemini",
        "grok": "grok",
        "kimi": "kimi",
        "deepseek": "deepseek",
        "qwen": "qwen",
        "copilot": "copilot",
        "opencode": "opencode",
        "droid": "droid",
        "pi": "pi",
        "mimo": "mimo",
        "cursor": "cursor",
        "cmd": None,  # skip command panes
        "powershell": None,
        "pwsh": None,
    }

    provider = None
    for keyword, mapped in provider_map.items():
        if keyword in label_lower:
            provider = mapped
            break

    if provider is None:
        # Unknown agent kind — skip with warning
        return None

    if provider_map.get(label_lower) is None and label_lower in ("cmd", "powershell", "pwsh"):
        return None

    # Default role based on position
    role = "agentroles.developer"

    return {
        "role": role,
        "provider": provider,
        "workspace": cwd,
        "label": pane_label,
        "layout": {"position": "main"},
        "_herdr_source": {
            "pane_label": pane_label,
            "workspace_label": workspace_label,
        },
    }


def _herdr_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
        env.pop(key, None)
    if "HERDR_CONFIG_PATH" not in env:
        env["HERDR_CONFIG_PATH"] = os.path.join(
            os.environ.get("USERPROFILE", os.path.expanduser("~")),
            "AppData", "Roaming", "herdr", "config.toml",
        )
    return env


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = ["import_herdr_config"]
