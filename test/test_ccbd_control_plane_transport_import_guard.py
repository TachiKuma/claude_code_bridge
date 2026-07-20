from __future__ import annotations

from pathlib import Path


def test_control_plane_af_unix_usage_stays_inside_unix_boundary() -> None:
    root = Path('lib/ccbd')
    allowed = {
        Path('lib/ccbd/control_plane_transport/unix.py'),
        Path('lib/ccbd/system.py'),
    }
    offenders: list[str] = []
    for path in root.rglob('*.py'):
        if path in allowed:
            continue
        text = path.read_text(encoding='utf-8')
        if 'AF_UNIX' in text:
            offenders.append(str(path).replace('\\', '/'))

    assert offenders == []
