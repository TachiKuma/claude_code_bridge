from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_package_scripts_do_not_define_release_or_publish_actions() -> None:
    package = json.loads((REPO_ROOT / 'package.json').read_text(encoding='utf-8'))
    scripts = package.get('scripts') or {}

    assert 'publish' not in scripts
    assert 'release' not in scripts
    assert 'tag' not in scripts
    assert scripts.get('pack:check') == 'npm pack --dry-run'


def test_rmux_packaging_contract_records_forbidden_release_actions_as_non_actions() -> None:
    text = (
        REPO_ROOT
        / 'docs'
        / 'plantree'
        / 'plans'
        / 'windows-rmux-native-backend'
        / 'topics'
        / 'rmux-packaging-support-contract.md'
    ).read_text(encoding='utf-8')

    assert '## Forbidden Release Actions' in text
    assert '`git push`' in text
    assert '`git tag`' in text
    assert '`npm publish`' in text
    assert 'release upload' in text
    assert 'does not authorize' in text
