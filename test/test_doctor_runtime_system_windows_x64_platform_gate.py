from __future__ import annotations

from pathlib import Path

import cli.services.doctor_runtime.system as system_module
from cli.services.doctor_runtime.system import installation_summary

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_installation_summary_surfaces_windows_binary_arch_and_git_refs(tmp_path: Path, monkeypatch) -> None:
    install_dir = tmp_path / 'install'
    (install_dir / 'bin').mkdir(parents=True)
    _write_pe_executable(install_dir / 'bin' / 'ccb-rs-helper.exe', machine=0x8664)
    _write_pe_executable(install_dir / 'bin' / 'ccb-agent-sidebar.exe', machine=0x8664)
    _write_pe_executable(install_dir / 'bin' / 'herdr.exe', machine=0x8664)

    monkeypatch.setattr(system_module, 'find_install_dir', lambda _root: install_dir)
    monkeypatch.setattr(
        system_module,
        'get_version_info',
        lambda _dir_path: {
            'version': '8.5.2',
            'commit': 'abc1234',
            'date': '2026-04-09',
            'branch_ref': 'refs/heads/feature/windows-herdr',
            'source_ref': 'refs/tags/v8.5.2',
            'channel': 'stable',
            'platform': 'win32',
            'arch': 'x64',
            'build_time': '2026-04-09T10:11:12Z',
            'installed_at': '2026-04-09T10:15:00Z',
            'source_kind': 'source',
            'install_mode': 'source',
            'install_user_id': '1000',
            'install_user_name': 'tester',
            'root_install': False,
            'sudo_user': None,
        },
    )

    summary = installation_summary()

    assert summary['branch_ref'] == 'refs/heads/feature/windows-herdr'
    assert summary['source_ref'] == 'refs/tags/v8.5.2'
    assert summary['herdr_arch'] == 'x64'
    assert summary['helper_arch']['ccb-rs-helper'] == 'x64'
    assert summary['helper_arch']['ccb-agent-sidebar'] == 'x64'


def test_install_sh_persists_source_and_branch_admission_refs() -> None:
    text = (REPO_ROOT / 'install.sh').read_text(encoding='utf-8')

    assert 'CCB_SOURCE_REF' in text
    assert 'CCB_BRANCH_REF' in text
    assert '"source_ref": ${source_ref_json}' in text
    assert '"branch_ref": ${branch_ref_json}' in text


def _write_pe_executable(path: Path, *, machine: int) -> None:
    payload = bytearray(256)
    payload[0:2] = b'MZ'
    payload[0x3C:0x40] = (0x80).to_bytes(4, 'little')
    payload[0x80:0x84] = b'PE\x00\x00'
    payload[0x84:0x86] = machine.to_bytes(2, 'little')
    path.write_bytes(bytes(payload))
