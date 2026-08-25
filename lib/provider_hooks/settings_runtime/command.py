from __future__ import annotations

from pathlib import Path
import shlex


def build_hook_command(
    *,
    provider: str,
    script_path: Path,
    python_executable: str,
    completion_dir: Path,
    agent_name: str,
    workspace_path: Path,
) -> str:
    parts = [
        *_script_command_prefix(script_path, python_executable),
        '--provider',
        str(provider),
        '--completion-dir',
        _shell_path(completion_dir),
        '--agent-name',
        str(agent_name),
        '--workspace',
        _shell_path(workspace_path),
    ]
    return ' '.join(shlex.quote(str(part)) for part in parts)


def build_activity_hook_command(
    *,
    provider: str,
    script_path: Path,
    python_executable: str,
    project_id: str,
    agent_name: str,
    runtime_dir: Path,
    workspace_path: Path,
) -> str:
    parts = [
        *_script_command_prefix(script_path, python_executable),
        '--provider',
        str(provider),
        '--project-id',
        str(project_id),
        '--agent-name',
        str(agent_name),
        '--runtime-dir',
        _shell_path(runtime_dir),
        '--workspace',
        _shell_path(workspace_path),
    ]
    return ' '.join(shlex.quote(str(part)) for part in parts)


def _script_command_prefix(script_path: Path, python_executable: str) -> list[str]:
    script = Path(script_path).expanduser()
    if script.suffix.lower() == '.py':
        return [_shell_path(python_executable), _shell_path(script)]
    return [_shell_path(script)]


def _shell_path(path: object) -> str:
    return Path(path).expanduser().as_posix()


__all__ = ['build_activity_hook_command', 'build_hook_command']
