from __future__ import annotations

from pathlib import Path


def test_ccb_cmd_validates_python_inline_without_temp_script() -> None:
    script = Path("ccb.cmd").read_text(encoding="utf-8")

    assert "VALIDATE_CODE=" in script
    assert "-c \"%VALIDATE_CODE%\"" in script
    assert "VALIDATE_SCRIPT" not in script
    assert "_ccb_python_validate" not in script
    assert "%TEMP%" not in script
