from __future__ import annotations

import re


ANSI_CSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ANSI_OSC_RE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")


def strip_terminal_sequences(text: str) -> str:
    cleaned = ANSI_OSC_RE.sub("", text or "")
    return ANSI_CSI_RE.sub("", cleaned)


__all__ = [
    "ANSI_CSI_RE",
    "ANSI_OSC_RE",
    "strip_terminal_sequences",
]
