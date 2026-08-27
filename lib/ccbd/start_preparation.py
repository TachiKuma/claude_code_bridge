from __future__ import annotations

from dataclasses import dataclass, replace
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import time

from agents.launch_config_fingerprint import (
    changed_signature_paths,
    provider_launch_config_signature,
)
from agents.policy import resolve_agent_launch_policy
from agents.store import AgentRestoreStore, AgentSpecStore
from cli.services.provider_hooks import prepare_provider_workspace, provider_workspace_path_for_prepare
from cli.services.runtime_launch import effective_start_command
from cli.services.runtime_launch_runtime import runtime_launcher
from ccbd.start_runtime.binding_runtime.common import (
    binding_pane_id,
    is_pane_runtime_ref,
    runtime_ref_backend,
)
from provider_backends.codex.session_runtime.live_identity import process_parent_snapshot
from provider_profiles.codex_home_config import codex_api_authority, codex_source_authority_config_payload
from provider_profiles import (
    load_resolved_provider_profile,
    provider_api_env_keys,
    validate_provider_runtime_home_uniqueness,
)
from runtime_observability import record_startup_operation, startup_operation_scope
from workspace.binding import WorkspaceBindingStore
from workspace.materializer import WorkspaceMaterializer
from workspace.planner import WorkspacePlanner
from workspace.validator import WorkspaceValidator


@dataclass(frozen=True)
class PreparedStartAgent:
    agent_name: str
    spec: object
    plan: object
    window_name: str | None
    raw_binding: object | None
    binding: object | None
    stale_binding: bool
    provider_prepared: bool = False
    provider_prepare_ms: float = 0.0
    binding_reject_reason: str | None = None
    binding_reject_details: tuple[str, ...] = ()
    effective_command: object | None = None


def prepare_start_agents(
    *,
    targets: tuple[str, ...],
    config,
    paths,
    context,
    project_root: Path,
    project_id: str,
    tmux_socket_path: str | None,
    tmux_session_name: str | None,
    workspace_window_id: str | None,
    resolve_agent_binding_fn,
    project_binding_filter_fn,
    restore_state_builder,
    namespace_epoch: int | None = None,
    namespace_pane_records: dict[str, object] | None = None,
    force_restart_agents: tuple[str, ...] = (),
    namespace_agent_panes: dict[str, str] | None = None,
) -> tuple[PreparedStartAgent, ...]:
    clean_tmux_socket_path = str(tmux_socket_path or '').strip() or None
    spec_store = AgentSpecStore(paths)
    restore_store = AgentRestoreStore(paths)
    planner = WorkspacePlanner()
    binding_store = WorkspaceBindingStore()
    materializer = WorkspaceMaterializer()
    validator = WorkspaceValidator(binding_store)
    prepared: list[PreparedStartAgent] = []
    forced_restarts = frozenset(str(name) for name in force_restart_agents)

    try:
        validate_provider_runtime_home_uniqueness(layout=paths, specs=config.agents.values())
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    identity_snapshot = (
        process_parent_snapshot()
        if any(config.agents[agent_name].provider == 'codex' for agent_name in targets)
        else nullcontext()
    )
    with identity_snapshot:
        for agent_name in targets:
            spec = config.agents[agent_name]
            window_name = _window_name_for_agent(config, agent_name)
            binding_window_name = window_name if bool(getattr(config, 'windows_explicit', False)) else None
            previous_spec = _load_previous_agent_spec(spec_store, agent_name)
            spec_store.save(spec)
            policy = resolve_agent_launch_policy(
                spec,
                cli_restore=context.command.restore,
                cli_auto_permission=context.command.auto_permission,
            )
            plan = planner.plan(spec, context.project)
            materializer.materialize(plan)
            if plan.binding_path is not None:
                binding_store.save(plan)
            result = validator.validate(plan)
            if not result.ok:
                raise RuntimeError(f'workspace validation failed for {agent_name}: {result.errors}')

            raw_binding = resolve_agent_binding_fn(
                provider=spec.provider,
                agent_name=agent_name,
                workspace_path=plan.workspace_path,
                project_root=project_root,
                ensure_usable=False,
            )
            if clean_tmux_socket_path is not None:
                binding = project_binding_filter_fn(
                    raw_binding,
                    cmd_enabled=bool(getattr(config, 'cmd_enabled', False)),
                    tmux_socket_path=clean_tmux_socket_path,
                    tmux_session_name=tmux_session_name,
                    workspace_window_id=workspace_window_id,
                    agent_name=agent_name,
                    project_id=project_id,
                    window_name=binding_window_name,
                    namespace_epoch=namespace_epoch,
                    assigned_pane_id=(namespace_agent_panes or {}).get(agent_name),
                    namespace_pane_records=namespace_pane_records,
                )
            else:
                binding = resolve_agent_binding_fn(
                    provider=spec.provider,
                    agent_name=agent_name,
                    workspace_path=plan.workspace_path,
                    project_root=project_root,
                    ensure_usable=True,
                )
                if (
                    binding is None
                    and raw_binding is not None
                    and (
                        (
                            is_pane_runtime_ref(getattr(raw_binding, 'runtime_ref', None))
                            and runtime_ref_backend(getattr(raw_binding, 'runtime_ref', None)) != 'tmux'
                        )
                        or _binding_matches_assigned_pane(
                            raw_binding,
                            assigned_pane_id=(namespace_agent_panes or {}).get(agent_name),
                        )
                    )
                ):
                    binding = raw_binding

            force_restart = agent_name in forced_restarts
            if force_restart:
                binding = None
            profile_reject_reason = None
            launch_config_reject_reason = None
            binding_reject_details: tuple[str, ...] = ()
            if binding is not None:
                launch_config_reject_reason = _provider_launch_config_reject_reason(
                    previous_spec=previous_spec,
                    current_spec=spec,
                )
                if launch_config_reject_reason is not None:
                    binding_reject_details = _provider_launch_config_reject_details(
                        previous_spec=previous_spec,
                        current_spec=spec,
                    )
                    binding = None
                else:
                    profile_reject_reason = _provider_profile_reject_reason(
                        paths=paths,
                        spec=spec,
                        agent_name=agent_name,
                    )
                    if profile_reject_reason is not None:
                        binding_reject_details = _provider_profile_reject_details(
                            paths=paths,
                            spec=spec,
                            agent_name=agent_name,
                        )
                        binding = None

            if restore_store.load(agent_name) is None:
                restore_store.save(agent_name, restore_state_builder(policy.restore_mode.value))

            prepared.append(
                PreparedStartAgent(
                    agent_name=agent_name,
                    spec=spec,
                    plan=plan,
                    window_name=window_name,
                    raw_binding=raw_binding,
                    binding=binding,
                    stale_binding=raw_binding is not None and binding is None,
                    binding_reject_reason=_binding_reject_reason(
                        raw_binding=raw_binding,
                        binding=binding,
                        cmd_enabled=bool(getattr(config, 'cmd_enabled', False)),
                        tmux_session_name=tmux_session_name,
                        workspace_window_id=workspace_window_id,
                        agent_name=agent_name,
                        project_id=project_id,
                        window_name=binding_window_name,
                        namespace_epoch=namespace_epoch,
                        assigned_pane_id=(namespace_agent_panes or {}).get(agent_name),
                        namespace_pane_records=namespace_pane_records,
                    ) if not force_restart and launch_config_reject_reason is None and profile_reject_reason is None else (
                        'manual_restart' if force_restart else launch_config_reject_reason or profile_reject_reason
                    ),
                    binding_reject_details=binding_reject_details,
                )
            )

    return _prepare_provider_launch_set(
        prepared,
        paths=paths,
        context=context,
    )


def _prepare_provider_launch_set(prepared, *, paths, context) -> tuple[PreparedStartAgent, ...]:
    finalized: list[PreparedStartAgent] = []
    for item in prepared:
        if item.binding is not None:
            finalized.append(item)
            continue
        launch_command = effective_start_command(context.command, item.spec)
        runtime_dir = paths.agent_provider_runtime_dir(item.agent_name, item.spec.provider)
        provider_workspace_path = provider_workspace_path_for_prepare(
            command=launch_command,
            spec=item.spec,
            plan=item.plan,
            runtime_dir=runtime_dir,
            launcher=runtime_launcher(item.spec.provider),
        )
        started_ns = time.monotonic_ns()
        record_startup_operation('provider_prepare_attempt_count')
        with startup_operation_scope('provider_prepare'):
            prepare_provider_workspace(
                layout=paths,
                spec=item.spec,
                workspace_path=provider_workspace_path,
                completion_dir=runtime_dir / 'completion',
                agent_name=item.agent_name,
                refresh_profile=True,
                auto_permission=launch_command.auto_permission,
            )
        record_startup_operation('provider_prepare_count')
        finalized.append(
            replace(
                item,
                provider_prepared=True,
                provider_prepare_ms=(time.monotonic_ns() - started_ns) / 1_000_000,
                effective_command=launch_command,
            )
        )
    return tuple(finalized)


def _provider_profile_reject_reason(*, paths, spec, agent_name: str) -> str | None:
    runtime_dir = paths.agent_provider_runtime_dir(agent_name, spec.provider)
    current = load_resolved_provider_profile(runtime_dir)
    if current is None:
        return None
    if str(getattr(current, 'provider', '') or '').strip().lower() != str(spec.provider).strip().lower():
        return 'provider_profile_changed'
    if str(getattr(current, 'agent_name', '') or '').strip().lower() != str(agent_name).strip().lower():
        return 'provider_profile_changed'
    desired = _provider_profile_signature(spec, paths=paths)
    actual = _resolved_provider_profile_signature(
        current,
        desired_home=desired['home'],
        desired_codex_home_authority=desired['codex_home_authority'],
    )
    return None if actual == desired else 'provider_profile_changed'


def _provider_profile_reject_details(*, paths, spec, agent_name: str) -> tuple[str, ...]:
    runtime_dir = paths.agent_provider_runtime_dir(agent_name, spec.provider)
    current = load_resolved_provider_profile(runtime_dir)
    if current is None:
        return ()
    details: list[str] = []
    if str(getattr(current, 'provider', '') or '').strip().lower() != str(spec.provider).strip().lower():
        details.append('provider_profile.provider')
    if str(getattr(current, 'agent_name', '') or '').strip().lower() != str(agent_name).strip().lower():
        details.append('provider_profile.agent_name')
    desired = _provider_profile_signature(spec, paths=paths)
    actual = _resolved_provider_profile_signature(
        current,
        desired_home=desired['home'],
        desired_codex_home_authority=desired['codex_home_authority'],
    )
    details.extend(changed_signature_paths('provider_profile', desired, actual))
    return tuple(dict.fromkeys(details))


def _load_previous_agent_spec(spec_store: AgentSpecStore, agent_name: str):
    try:
        return spec_store.load(agent_name)
    except Exception:
        return None


def _provider_launch_config_reject_reason(*, previous_spec, current_spec) -> str | None:
    if previous_spec is None:
        return None
    if provider_launch_config_signature(previous_spec) == provider_launch_config_signature(current_spec):
        return None
    return 'provider_launch_config_changed'


def _provider_launch_config_reject_details(*, previous_spec, current_spec) -> tuple[str, ...]:
    if previous_spec is None:
        return ()
    previous = provider_launch_config_signature(previous_spec)
    current = provider_launch_config_signature(current_spec)
    return tuple(changed_signature_paths('launch_config', current, previous))


def _provider_profile_signature(spec, *, paths) -> dict[str, object]:
    profile = spec.provider_profile
    return {
        'mode': str(getattr(profile, 'mode', 'inherit') or 'inherit').strip().lower(),
        'home': _normalized_desired_profile_home(paths=paths, profile=profile),
        'env': _desired_provider_profile_env(spec),
        'mcp_servers': dict(getattr(profile, 'mcp_servers', {}) or {}),
        'plugins': dict(getattr(profile, 'plugins', {}) or {}),
        'inherit_api': bool(getattr(profile, 'inherit_api', True)),
        'inherit_auth': bool(getattr(profile, 'inherit_auth', True)),
        'inherit_config': bool(getattr(profile, 'inherit_config', True)),
        'inherit_skills': bool(getattr(profile, 'inherit_skills', True)),
        'inherit_commands': bool(getattr(profile, 'inherit_commands', True)),
        'inherit_memory': bool(getattr(profile, 'inherit_memory', True)),
        'inherited_skill_include': tuple(getattr(profile, 'inherited_skill_include', ()) or ()),
        'inherited_skill_exclude': tuple(getattr(profile, 'inherited_skill_exclude', ()) or ()),
        'skill_overlays': _skill_overlay_signature(getattr(profile, 'skill_overlays', {}) or {}),
        'codex_home_authority': _desired_codex_home_authority_signature(spec),
    }


def _normalized_desired_profile_home(*, paths, profile) -> str | None:
    raw_home = str(getattr(profile, 'home', '') or '').strip()
    if not raw_home:
        return None
    path = Path(raw_home).expanduser()
    if not path.is_absolute():
        path = Path(paths.project_root) / path
    return str(path.resolve())


def _resolved_provider_profile_signature(
    profile,
    *,
    desired_home: str | None,
    desired_codex_home_authority: object | None,
) -> dict[str, object]:
    return {
        'mode': str(getattr(profile, 'mode', 'inherit') or 'inherit').strip().lower(),
        'home': (
            str(getattr(profile, 'runtime_home', None) or getattr(profile, 'profile_root', '') or '').strip() or None
        ) if desired_home is not None else None,
        'env': dict(getattr(profile, 'env', {}) or {}),
        'mcp_servers': dict(getattr(profile, 'mcp_servers', {}) or {}),
        'plugins': dict(getattr(profile, 'plugins', {}) or {}),
        'inherit_api': bool(getattr(profile, 'inherit_api', True)),
        'inherit_auth': bool(getattr(profile, 'inherit_auth', True)),
        'inherit_config': bool(getattr(profile, 'inherit_config', True)),
        'inherit_skills': bool(getattr(profile, 'inherit_skills', True)),
        'inherit_commands': bool(getattr(profile, 'inherit_commands', True)),
        'inherit_memory': bool(getattr(profile, 'inherit_memory', True)),
        'inherited_skill_include': tuple(getattr(profile, 'inherited_skill_include', ()) or ()),
        'inherited_skill_exclude': tuple(getattr(profile, 'inherited_skill_exclude', ()) or ()),
        'skill_overlays': _skill_overlay_signature(getattr(profile, 'skill_overlays', {}) or {}),
        'codex_home_authority': _resolved_codex_home_authority_signature(
            profile,
            expected=desired_codex_home_authority,
        ),
    }


def _desired_codex_home_authority_signature(spec) -> dict[str, object] | None:
    if str(getattr(spec, 'provider', '') or '').strip().lower() != 'codex':
        return None
    authority = codex_api_authority(SimpleNamespace(env=_desired_provider_profile_env(spec)))
    if authority is None:
        return None
    return {
        'model_provider': authority.provider_id,
        'model_provider_config': {
            'name': authority.provider_id,
            'base_url': authority.base_url,
            'wire_api': authority.wire_api,
            'requires_openai_auth': authority.requires_openai_auth,
        },
    }


def _resolved_codex_home_authority_signature(profile, *, expected: object | None) -> dict[str, object] | None:
    if expected is None or str(getattr(profile, 'provider', '') or '').strip().lower() != 'codex':
        return None
    runtime_home = str(getattr(profile, 'runtime_home', '') or '').strip()
    if not runtime_home:
        return None
    try:
        return codex_source_authority_config_payload(
            Path(runtime_home) / 'config.toml',
            include_route=True,
            include_login=False,
        )
    except Exception:
        return None


def _desired_provider_profile_env(spec) -> dict[str, str]:
    profile = spec.provider_profile
    provider = str(spec.provider)
    api_keys = provider_api_env_keys(provider)
    env = dict(getattr(profile, 'env', {}) or {})
    # `agents.<name>.env` takes precedence over `provider_profile.env` for API
    # credentials, mirroring `_profile_spec_with_agent_api_env` in the
    # materializer so drift detection resolves the same values home projection
    # does.
    for key, value in dict(getattr(spec, 'env', {}) or {}).items():
        if str(key) in api_keys and str(value).strip():
            env[str(key)] = str(value)
    mode = str(getattr(profile, 'mode', 'inherit') or 'inherit').strip().lower()
    if mode != 'inherit' or provider.strip().lower() == 'codex':
        return {str(key): str(value) for key, value in env.items()}
    return {str(key): str(value) for key, value in env.items() if str(key) in api_keys}


def _skill_overlay_signature(overlays: dict[str, object]) -> dict[str, object]:
    signature: dict[str, object] = {}
    for name, overlay in dict(overlays).items():
        to_record = getattr(overlay, 'to_record', None)
        signature[str(name)] = to_record() if callable(to_record) else overlay
    return signature


def _changed_signature_paths(prefix: str, desired: object, actual: object) -> tuple[str, ...]:
    if isinstance(desired, dict) and isinstance(actual, dict):
        changed: list[str] = []
        for key in sorted(set(desired) | set(actual)):
            child_prefix = f'{prefix}.{key}'
            if key not in desired or key not in actual:
                changed.append(child_prefix)
                continue
            changed.extend(changed_signature_paths(child_prefix, desired[key], actual[key]))
        return tuple(changed)
    return () if desired == actual else (prefix,)


def _binding_reject_reason(
    *,
    raw_binding,
    binding,
    cmd_enabled: bool,
    tmux_session_name: str | None,
    workspace_window_id: str | None,
    agent_name: str,
    project_id: str,
    window_name: str | None,
    namespace_epoch: int | None,
    assigned_pane_id: str | None,
    namespace_pane_records: dict[str, object] | None,
) -> str | None:
    if binding is not None:
        return None
    if raw_binding is None:
        return 'binding_missing'
    runtime_ref = str(getattr(raw_binding, 'runtime_ref', None) or '').strip()
    if not is_pane_runtime_ref(runtime_ref):
        return 'runtime_not_tmux'
    pane_state = str(getattr(raw_binding, 'pane_state', None) or '').strip().lower()
    runtime_backend = runtime_ref_backend(runtime_ref)
    if cmd_enabled and runtime_backend == 'tmux' and pane_state != 'alive':
        return f'pane_{pane_state or "state_missing"}'
    if not cmd_enabled and pane_state not in {'alive', 'unknown', ''}:
        return f'pane_{pane_state}'
    if cmd_enabled and runtime_backend != 'tmux' and pane_state not in {'alive', 'unknown', ''}:
        return f'pane_{pane_state}'
    identity_state = str(getattr(raw_binding, 'provider_identity_state', None) or '').strip().lower()
    if identity_state == 'mismatch':
        return 'provider_identity_mismatch'
    if cmd_enabled and identity_state and identity_state not in {'match', 'rotated_in_process'}:
        return 'provider_identity_unproven'
    if window_name is not None and namespace_epoch is None:
        return 'namespace_epoch_missing'
    pane_id = _binding_pane_id(raw_binding)
    if pane_id is None:
        return 'pane_id_missing'
    if namespace_pane_records is not None:
        record = namespace_pane_records.get(pane_id)
        if record is None:
            return 'namespace_pane_missing'
        mismatch_reason = getattr(record, 'mismatch_reason', None)
        if callable(mismatch_reason):
            reason = mismatch_reason(
                tmux_session_name=str(tmux_session_name or ''),
                project_id=project_id,
                role='agent',
                slot_key=agent_name,
                managed_by='ccbd',
                window_id=None if window_name is not None else workspace_window_id,
                window_name=window_name,
                namespace_epoch=namespace_epoch if window_name is not None else None,
            )
            if reason is not None:
                return str(reason)
    return 'project_namespace_mismatch'


def _binding_pane_id(binding) -> str | None:
    return binding_pane_id(binding)


def _binding_matches_assigned_pane(binding, *, assigned_pane_id: str | None) -> bool:
    assigned = str(assigned_pane_id or '').strip()
    if not assigned:
        return False
    return _binding_pane_id(binding) == assigned


def _window_name_for_agent(config, agent_name: str) -> str | None:
    for window in getattr(config, 'windows', ()) or ():
        if agent_name in tuple(getattr(window, 'agent_names', ()) or ()):
            return str(getattr(window, 'name', '') or '').strip() or None
    return None


__all__ = ['PreparedStartAgent', 'prepare_start_agents']
