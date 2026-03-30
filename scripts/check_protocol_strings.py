#!/usr/bin/env python3
"""
check_protocol_strings.py - Check translation files for protocol strings.

Compares translation values against .planning/protocol_whitelist.json whitelist.
This is the first layer of protocol protection: CI value check.

Usage:
    python scripts/check_protocol_strings.py [--values] [--code] [--whitelist PATH] [--translations PATH]

Exit codes:
    0 - Check passed
    1 - Violations found
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Set, List, Dict, Any


DEFAULT_WHITELIST = Path(__file__).parent.parent / ".planning" / "protocol_whitelist.json"
DEFAULT_TRANSLATION_DIR = Path(__file__).parent.parent / "lib" / "i18n"


def load_whitelist(path: Path) -> Set[str]:
    """Load protocol string whitelist from JSON file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    strings: Set[str] = set()
    for category, items in data.get("categories", {}).items():
        strings.update(items)
    return strings


def check_translation_file(file_path: Path, whitelist: Set[str]) -> List[Dict[str, str]]:
    """Check a single translation file's values against the whitelist."""
    errors: List[Dict[str, str]] = []
    try:
        with open(file_path, encoding="utf-8") as f:
            translations = json.load(f)
    except json.JSONDecodeError as e:
        return [{"type": "parse_error", "file": str(file_path), "error": str(e)}]

    for key, value in translations.items():
        if isinstance(value, str) and value in whitelist:
            errors.append({
                "type": "protocol_value",
                "file": str(file_path),
                "key": key,
                "value": value,
                "reason": "Protocol string should not be a translation value",
            })
    return errors


def scan_translation_values(translation_dir: Path, whitelist: Set[str]) -> List[Dict[str, str]]:
    """Scan all JSON files in translation directory."""
    all_errors: List[Dict[str, str]] = []
    if not translation_dir.exists():
        return all_errors
    for json_file in sorted(translation_dir.rglob("*.json")):
        errors = check_translation_file(json_file, whitelist)
        all_errors.extend(errors)
    return all_errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Check protocol strings in translation files")
    parser.add_argument("--values", action="store_true", default=True,
                        help="Check translation values (default)")
    parser.add_argument("--whitelist", type=Path, default=DEFAULT_WHITELIST,
                        help="Path to protocol whitelist JSON")
    parser.add_argument("--translations", type=Path, default=DEFAULT_TRANSLATION_DIR,
                        help="Path to translation directory")
    args = parser.parse_args()

    # 1. Load whitelist
    try:
        whitelist = load_whitelist(args.whitelist)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FAIL: Cannot load whitelist: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(whitelist)} protocol strings from whitelist")

    # 2. Check translation values
    if args.values:
        errors = scan_translation_values(args.translations, whitelist)
        if errors:
            print(f"\nFAIL: Found {len(errors)} protocol string violation(s):")
            for err in errors:
                if err.get("type") == "protocol_value":
                    print(f"  {err['file']}: key '{err['key']}' has protocol value '{err['value']}'")
                else:
                    print(f"  {err['file']}: {err.get('error', err.get('reason', 'unknown'))}")
            sys.exit(1)
        else:
            file_count = len(list(args.translations.rglob("*.json"))) if args.translations.exists() else 0
            print(f"PASS: No protocol strings found in {file_count} translation file(s)")

    sys.exit(0)


if __name__ == "__main__":
    main()
