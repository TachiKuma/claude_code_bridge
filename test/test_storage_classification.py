from __future__ import annotations

import os
from pathlib import Path

from storage.paths import PathLayout
from storage_classification import summarize_storage


def _write(path: Path, text: str = 'x') -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _records_by_suffix(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(item['relative_path']): item for item in payload['entries']}


def test_storage_classification_keeps_provider_authority_and_cache_separate(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    ccb = project_root / '.ccb'
    codex_home = ccb / 'agents' / 'agent1' / 'provider-state' / 'codex' / 'home'
    claude_home = ccb / 'agents' / 'agent2' / 'provider-state' / 'claude' / 'home'
    gemini_home = ccb / 'agents' / 'agent3' / 'provider-state' / 'gemini' / 'home'

    _write(ccb / 'ccb.config', 'agent1:codex\n')
    _write(ccb / 'history' / 'handoff.md', '# handoff\n')
    _write(ccb / 'workspaces' / 'agent1' / 'notes.txt', 'workspace change\n')
    _write(ccb / 'agents' / 'agent1' / 'runtime.json', '{}\n')
    _write(codex_home / 'sessions' / '2026' / 'session.jsonl')
    _write(codex_home / '.ccb-session-namespace.json', '{}\n')
    _write(codex_home / 'auth.json', '{}\n')
    _write(codex_home / 'config.toml', '# config\n')
    _write(codex_home / '.tmp' / 'plugins' / 'plugins' / 'demo' / 'SKILL.md')
    _write(codex_home / '.tmp' / 'plugins.sha', 'abc\n')

    _write(claude_home / '.claude.json', '{}\n')
    _write(claude_home / '.claude' / '.credentials.json', '{}\n')
    _write(claude_home / '.config' / 'claude-code' / 'auth.json', '{}\n')
    _write(claude_home / '.claude' / 'settings.json', '{}\n')
    _write(claude_home / '.local' / 'share' / 'claude' / 'versions' / '2.1.137' / 'claude', 'bin\n')
    if hasattr(os, 'symlink'):
        (claude_home / '.local' / 'bin').mkdir(parents=True, exist_ok=True)
        os.symlink('../share/claude/versions/2.1.137/claude', claude_home / '.local' / 'bin' / 'claude')

    _write(gemini_home / '.gemini' / 'tmp' / 'checkpoint.json', '{}\n')
    _write(gemini_home / '.gemini' / 'oauth_creds.json', '{}\n')
    _write(gemini_home / '.gemini' / 'settings.json', '{}\n')
    _write(gemini_home / '.npm' / '_cacache' / 'content-v2' / 'sha512' / 'aa' / 'blob')

    payload = summarize_storage(PathLayout(project_root))
    records = _records_by_suffix(payload)

    assert payload['shared_cache_status'] == 'disabled'
    assert payload['shared_cache_reason'] == 'not_implemented'
    assert records['agents/agent1/runtime.json']['storage_class'] == 'authority'
    assert records['history/handoff.md']['storage_class'] == 'user_content'
    assert records['workspaces/agent1/notes.txt']['storage_class'] == 'workspace'
    assert records['agents/agent1/provider-state/codex/home/sessions/2026/session.jsonl']['storage_class'] == 'session'
    assert records['agents/agent1/provider-state/codex/home/.ccb-session-namespace.json']['storage_class'] == 'session'
    assert records['agents/agent1/provider-state/codex/home/auth.json']['storage_class'] == 'secret'
    assert records['agents/agent1/provider-state/codex/home/config.toml']['storage_class'] == 'projected_config'
    assert (
        records['agents/agent1/provider-state/codex/home/.tmp/plugins/plugins/demo/SKILL.md']['storage_class']
        == 'startup_authority_bundle'
    )
    assert records['agents/agent1/provider-state/codex/home/.tmp/plugins.sha']['storage_class'] == 'startup_authority_bundle'

    assert records['agents/agent2/provider-state/claude/home/.claude.json']['storage_class'] == 'session'
    assert records['agents/agent2/provider-state/claude/home/.claude/.credentials.json']['storage_class'] == 'secret'
    assert records['agents/agent2/provider-state/claude/home/.config/claude-code/auth.json']['storage_class'] == 'secret'
    assert records['agents/agent2/provider-state/claude/home/.claude/settings.json']['storage_class'] == 'projected_config'
    assert (
        records['agents/agent2/provider-state/claude/home/.local/share/claude/versions/2.1.137/claude']['storage_class']
        == 'rebuildable_cache'
    )
    assert records['agents/agent2/provider-state/claude/home/.local/share/claude/versions/2.1.137/claude']['active'] is False
    assert (
        records['agents/agent2/provider-state/claude/home/.local/share/claude/versions/2.1.137/claude'][
            'is_active_version'
        ]
        is True
    )
    assert (
        records['agents/agent2/provider-state/claude/home/.local/share/claude/versions/2.1.137/claude'][
            'reachable_from_current_symlink'
        ]
        is True
    )
    assert records['agents/agent2/provider-state/claude/home/.local/bin/claude']['active'] is True
    assert records['agents/agent2/provider-state/claude/home/.local/bin/claude']['is_active_version'] is False

    assert records['agents/agent3/provider-state/gemini/home/.gemini/tmp/checkpoint.json']['storage_class'] == 'session'
    assert records['agents/agent3/provider-state/gemini/home/.gemini/oauth_creds.json']['storage_class'] == 'secret'
    assert records['agents/agent3/provider-state/gemini/home/.gemini/settings.json']['storage_class'] == 'projected_config'
    assert (
        records['agents/agent3/provider-state/gemini/home/.npm/_cacache/content-v2/sha512/aa/blob']['storage_class']
        == 'rebuildable_cache'
    )


def test_storage_classification_surfaces_profile_backed_runtime_home(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    profile_home = project_root / '.ccb' / 'provider-profiles' / 'agent2' / 'codex'
    _write(profile_home / 'sessions' / '2026' / 'session.jsonl')
    _write(profile_home / 'auth.json', '{}\n')
    _write(profile_home / '.tmp' / 'plugins' / 'plugins' / 'demo' / 'SKILL.md')

    payload = summarize_storage(PathLayout(project_root))
    records = _records_by_suffix(payload)

    assert records['provider-profiles/agent2/codex/sessions/2026/session.jsonl']['storage_class'] == 'session'
    assert records['provider-profiles/agent2/codex/auth.json']['storage_class'] == 'secret'
    assert (
        records['provider-profiles/agent2/codex/.tmp/plugins/plugins/demo/SKILL.md']['storage_class']
        == 'startup_authority_bundle'
    )
