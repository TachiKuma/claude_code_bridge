from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_PS1 = REPO_ROOT / 'install.ps1'


def test_install_ps1_declares_explicit_rmux_check_modes() -> None:
    text = INSTALL_PS1.read_text(encoding='utf-8')

    assert '[ValidateSet("detect_only", "warn", "fail_fast")]' in text
    assert '[string]$RmuxCheck = "warn"' in text
    assert 'Get-RmuxPackagingSupportProjection' in text
    assert 'rmux_packaging_support_projection.json' in text
    assert 'Get-RmuxPrerequisiteStatus' in text
    assert 'Show-RmuxPrerequisiteNotice -Mode $RmuxCheck' in text
    assert 'Windows Rmux support tier: $($projection.support_tier)' in text


def test_install_ps1_rmux_contract_does_not_auto_download_rmux() -> None:
    text = INSTALL_PS1.read_text(encoding='utf-8')
    rmux_section = text[text.index('function Get-RmuxPrerequisiteStatus') : text.index('function Test-PythonTomlReader')]

    assert 'Get-Command rmux' in rmux_section
    assert 'Get-Command psmux' in rmux_section
    notice_section = text[text.index('function Show-RmuxPrerequisiteNotice') : text.index('function Test-PythonTomlReader')]
    assert 'CCB will not download or install rmux automatically' in notice_section
    assert 'Invoke-WebRequest' not in rmux_section
    assert 'Invoke-RestMethod' not in rmux_section
    assert 'Start-BitsTransfer' not in rmux_section


def test_install_ps1_fail_fast_only_when_explicitly_requested() -> None:
    text = INSTALL_PS1.read_text(encoding='utf-8')

    assert 'if ($Mode -eq "fail_fast")' in text
    assert '[ERROR] Rmux prerequisite check failed and -RmuxCheck fail_fast was requested.' in text
