from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_package_os_does_not_enable_win32_in_baseline_gate_feature() -> None:
    package = json.loads((REPO_ROOT / 'package.json').read_text(encoding='utf-8'))

    assert 'win32' not in package.get('os', [])


def test_postinstall_artifact_route_does_not_claim_win32_support() -> None:
    text = (REPO_ROOT / 'bin' / 'ccb-npm-install.js').read_text(encoding='utf-8')
    artifact_route = text[text.index('function artifactForHost') : text.index('function installDir')]

    assert 'process.platform === "win32"' not in artifact_route
    assert 'ccb-windows' not in artifact_route.lower()
