from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from agents.config_loader import load_project_config
from provider_core.runtime_shared import provider_start_parts
from storage.atomic import atomic_write_json

from .contracts import (
    HerdrRuntimeEnvRef,
    HerdrRuntimeManifest,
    HerdrRuntimeManifestPane,
    HerdrRuntimeManifestService,
    HerdrRuntimeManifestWorkspace,
)


MANIFEST_FILENAME = "herdr-runtime-manifest.json"


def herdr_runtime_manifest_path(paths) -> Path:
    return Path(paths.runtime_state_root) / "runtime" / MANIFEST_FILENAME


def write_herdr_runtime_manifest_for_start(
    context,
    command,
    *,
    session_name: str | None,
) -> Path:
    manifest = build_herdr_runtime_manifest_for_start(
        context,
        command,
        session_name=session_name,
    )
    path = herdr_runtime_manifest_path(context.paths)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, manifest.to_record())
    return path


def write_herdr_runtime_manifest(paths, manifest: HerdrRuntimeManifest) -> Path:
    path = herdr_runtime_manifest_path(paths)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, manifest.to_record())
    return path


def build_herdr_runtime_manifest_for_start(
    context,
    command,
    *,
    session_name: str | None,
) -> HerdrRuntimeManifest:
    config = load_project_config(context.project.project_root).config
    target_names = _target_agent_names(command, config.agents)
    panes = tuple(
        _pane_for_agent(name, config.agents[name], cwd=str(context.project.project_root))
        for name in target_names
        if name in config.agents
    )
    return HerdrRuntimeManifest(
        project_id=str(context.project.project_id),
        project_root=str(context.project.project_root),
        session_name=str(session_name or context.paths.ccbd_tmux_session_name),
        generation=_manifest_generation(context),
        services=(
            HerdrRuntimeManifestService(
                id="ccbd",
                command=("python", "-m", "ccbd"),
                cwd=str(context.project.project_root),
                ready={"kind": "ccb-lifecycle", "phase": "mounted"},
            ),
        ),
        workspaces=(
            HerdrRuntimeManifestWorkspace(
                name="project",
                cwd=str(context.project.project_root),
                panes=panes,
            ),
        ),
    )


def _pane_for_agent(name: str, spec, *, cwd: str) -> HerdrRuntimeManifestPane:
    provider = str(getattr(spec, "provider", "") or "").strip().lower()
    command = tuple([*provider_start_parts(provider), *tuple(getattr(spec, "startup_args", ()) or ())])
    return HerdrRuntimeManifestPane(
        slot=str(name),
        agent_name=str(name),
        provider_kind=provider,
        command=command,
        cwd=cwd,
        role="agent",
        env_refs=tuple(
            HerdrRuntimeEnvRef(name=str(key), source="ccb-provider-home")
            for key in sorted(_env_ref_names(spec))
        ),
        restart={"policy": "manual-or-ccb-approved"},
    )


def _target_agent_names(command, agents: Mapping[str, object]) -> tuple[str, ...]:
    requested = tuple(str(item).strip() for item in getattr(command, "agent_names", ()) or () if str(item).strip())
    if requested:
        return requested
    return tuple(sorted(str(name) for name in agents))


def _env_ref_names(spec) -> Iterable[str]:
    for key in dict(getattr(spec, "env", {}) or {}):
        yield str(key)
    profile = getattr(spec, "provider_profile", None)
    for key in dict(getattr(profile, "env", {}) or {}):
        yield str(key)


def _manifest_generation(context) -> int:
    try:
        from ccbd.services.project_namespace_state import ProjectNamespaceStateStore

        state = ProjectNamespaceStateStore(context.paths).load()
        value = int(getattr(state, "namespace_epoch", 0) or 0) if state is not None else 0
        if value > 0:
            return value
    except Exception:
        pass
    return 1


__all__ = [
    "MANIFEST_FILENAME",
    "build_herdr_runtime_manifest_for_start",
    "herdr_runtime_manifest_path",
    "write_herdr_runtime_manifest",
    "write_herdr_runtime_manifest_for_start",
]
