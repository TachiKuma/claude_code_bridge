#!/usr/bin/env python3
"""Check that referenced translation keys exist in CCB translation files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.i18n import _key_mapping
TRANSLATION_FILE = ROOT / "lib" / "i18n" / "ccb" / "en.json"
TARGETS = (
    ROOT / "ccb",
    ROOT / "lib" / "i18n.py",
    ROOT / "lib" / "i18n_core.py",
    ROOT / "lib" / "i18n_runtime.py",
    ROOT / "lib" / "codex_comm.py",
    ROOT / "lib" / "gemini_comm.py",
    ROOT / "lib" / "opencode_comm.py",
    ROOT / "lib" / "mail" / "sender.py",
    ROOT / "lib" / "mail_tui" / "wizard.py",
    ROOT / "lib" / "web" / "app.py",
    ROOT / "lib" / "web" / "routes" / "daemons.py",
    ROOT / "lib" / "web" / "routes" / "mail.py",
    ROOT / "lib" / "web" / "templates" / "base.html",
    ROOT / "lib" / "web" / "templates" / "dashboard.html",
    ROOT / "lib" / "web" / "templates" / "mail.html",
    ROOT / "bin" / "cask",
    ROOT / "bin" / "gask",
    ROOT / "bin" / "oask",
    ROOT / "bin" / "dask",
    ROOT / "bin" / "cpend",
    ROOT / "bin" / "gpend",
    ROOT / "bin" / "opend",
)
TRANSLATION_CALL_RE = re.compile(r"""\bt\(\s*['"]([^'"]+)['"]""")


def load_translations() -> set[str]:
    with TRANSLATION_FILE.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{TRANSLATION_FILE} is not a JSON object")
    return set(data.keys())


def main() -> int:
    known_keys = load_translations()
    missing_refs: list[str] = []
    total_refs = 0

    for target in TARGETS:
        content = target.read_text(encoding="utf-8")
        matches = TRANSLATION_CALL_RE.findall(content)
        total_refs += len(matches)
        for key in matches:
            namespaced_key = _key_mapping.get(key, key)
            if namespaced_key not in known_keys:
                missing_refs.append(f"{target.relative_to(ROOT)} -> {key}")

    if missing_refs:
        print("FAIL: missing translation keys")
        for item in missing_refs:
            print(f"  {item}")
        return 1

    print(f"PASS: {total_refs} translation call(s) resolved across {len(TARGETS)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
