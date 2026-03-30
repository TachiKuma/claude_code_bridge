#!/usr/bin/env python3
"""Check that CCB translation files expose the same key set."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent / "lib" / "i18n" / "ccb"
LOCALES = ("en", "zh", "xx")


def load_keys(locale_name: str) -> set[str]:
    path = BASE_DIR / f"{locale_name}.json"
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return set(data.keys())


def main() -> int:
    locale_keys = {locale_name: load_keys(locale_name) for locale_name in LOCALES}
    baseline = locale_keys["en"]
    failed = False

    for locale_name, keys in locale_keys.items():
        missing = sorted(baseline - keys)
        extra = sorted(keys - baseline)
        if missing or extra:
            failed = True
            print(f"FAIL: {locale_name}.json key mismatch")
            if missing:
                print(f"  missing: {', '.join(missing[:20])}")
            if extra:
                print(f"  extra: {', '.join(extra[:20])}")

    if failed:
        return 1

    print(f"PASS: translation key sets are consistent across {', '.join(LOCALES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
