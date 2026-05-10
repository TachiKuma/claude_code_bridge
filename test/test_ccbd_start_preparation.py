from __future__ import annotations

from pathlib import Path

import pytest

from agents.config_loader import load_project_config
from ccbd.start_preparation import prepare_start_agents
from cli.context import CliContextBuilder
from cli.models import ParsedStartCommand
from project.resolver import bootstrap_project
from storage.paths import PathLayout


def test_prepare_start_agents_rejects_git_worktree_for_non_git_project(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo-start-prep-non-git-worktree'
    (project_root / '.ccb').mkdir(parents=True)
    (project_root / 'README.md').write_text('not a git repo\n', encoding='utf-8')
    (project_root / '.ccb' / 'ccb.config').write_text('agent1:codex(worktree)\n', encoding='utf-8')
    bootstrap_project(project_root)
    command = ParsedStartCommand(project=None, agent_names=(), restore=True, auto_permission=False)
    context = CliContextBuilder().build(command, cwd=project_root, bootstrap_if_missing=False)
    config = load_project_config(project_root).config
    paths = PathLayout(project_root)

    with pytest.raises(RuntimeError, match='git-worktree workspace requires a git repository'):
        prepare_start_agents(
            targets=('agent1',),
            config=config,
            paths=paths,
            context=context,
            project_root=project_root,
            project_id=context.project.project_id,
            tmux_socket_path=None,
            tmux_session_name=None,
            workspace_window_id=None,
            resolve_agent_binding_fn=lambda **kwargs: None,
            project_binding_filter_fn=lambda binding, **kwargs: binding,
            restore_state_builder=lambda restore_mode: {'restore_mode': restore_mode},
        )

    assert paths.workspace_path('agent1').exists() is False


def test_prepare_start_agents_rejects_duplicate_effective_provider_homes(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo-start-prep-duplicate-provider-home'
    shared_home = tmp_path / 'shared-codex-home'
    (project_root / '.ccb').mkdir(parents=True)
    (project_root / '.ccb' / 'ccb.config').write_text(
        f"""version = 2
default_agents = ["agent1", "agent2"]

[agents.agent1]
provider = "codex"
target = "."
workspace_mode = "inplace"
restore = "auto"
permission = "manual"

[agents.agent1.provider_profile]
mode = "isolated"
home = "{shared_home}"

[agents.agent2]
provider = "codex"
target = "."
workspace_mode = "inplace"
restore = "auto"
permission = "manual"

[agents.agent2.provider_profile]
mode = "isolated"
home = "{shared_home}"
""",
        encoding='utf-8',
    )
    bootstrap_project(project_root)
    command = ParsedStartCommand(project=None, agent_names=(), restore=True, auto_permission=False)
    context = CliContextBuilder().build(command, cwd=project_root, bootstrap_if_missing=False)
    config = load_project_config(project_root).config
    paths = PathLayout(project_root)

    with pytest.raises(RuntimeError, match='duplicate effective codex_home'):
        prepare_start_agents(
            targets=('agent1',),
            config=config,
            paths=paths,
            context=context,
            project_root=project_root,
            project_id=context.project.project_id,
            tmux_socket_path=None,
            tmux_session_name=None,
            workspace_window_id=None,
            resolve_agent_binding_fn=lambda **kwargs: None,
            project_binding_filter_fn=lambda binding, **kwargs: binding,
            restore_state_builder=lambda restore_mode: {'restore_mode': restore_mode},
        )
