#!/usr/bin/env python3
"""Audit Mail/Web/TUI user-visible strings for CCB i18n migration."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / ".planning" / "phases" / "06-ccb-i18n" / "reports"
TARGETS: dict[Path, tuple[str, str]] = {
    ROOT / "lib" / "mail_tui" / "wizard.py": ("terminal", "ccb.mail_tui"),
    ROOT / "lib" / "web" / "templates" / "dashboard.html": ("html", "ccb.web.dashboard"),
    ROOT / "lib" / "web" / "templates" / "mail.html": ("html", "ccb.web.mail"),
    ROOT / "lib" / "web" / "routes" / "daemons.py": ("api", "ccb.web.daemon"),
    ROOT / "lib" / "web" / "routes" / "mail.py": ("api", "ccb.web.mail"),
    ROOT / "lib" / "mail" / "sender.py": ("mail", "ccb.mail.sender"),
}

STRING_RE = re.compile(r'["\']([^"\']{8,})["\']')


def is_user_visible(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.startswith("http"):
        return False
    if stripped in {"__main__", "utf-8", "plain", "alternative"}:
        return False
    if "{" in stripped and "}" in stripped and len(stripped) < 8:
        return False
    return any(ch.isalpha() or "\u4e00" <= ch <= "\u9fff" for ch in stripped)


def collect_rows() -> list[tuple[str, int, str, str, str, str]]:
    rows: list[tuple[str, int, str, str, str, str]] = []
    for path, (category, namespace) in TARGETS.items():
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines, start=1):
            for match in STRING_RE.finditer(line):
                text = match.group(1).strip()
                if not is_user_visible(text):
                    continue
                rows.append(
                    (
                        str(path.relative_to(ROOT)).replace("\\", "/"),
                        index,
                        text.replace("|", "\\|"),
                        category,
                        "是",
                        namespace,
                    )
                )
    return rows


def write_inventory(rows: list[tuple[str, int, str, str, str, str]]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "i18n_surface_inventory.md"
    lines = [
        "# CCB i18n Surface Inventory",
        "",
        "| 文件 | 行号 | 原始文本 | 分类 | 用户可见 | 建议命名空间 |",
        "|------|------|----------|------|----------|----------------|",
    ]
    for file_path, line_no, text, category, visible, namespace in rows:
        lines.append(f"| `{file_path}` | {line_no} | {text} | {category} | {visible} | `{namespace}` |")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    rows = collect_rows()
    path = write_inventory(rows)
    print(f"Wrote {len(rows)} inventory row(s) to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
