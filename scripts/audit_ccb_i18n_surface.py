#!/usr/bin/env python3
"""Audit Mail/Web/TUI user-visible i18n surfaces for CCB."""

from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / ".planning" / "phases" / "06-ccb-i18n" / "reports"


@dataclass(frozen=True)
class Target:
    category: str
    namespace: str
    kind: str


@dataclass(frozen=True)
class Entry:
    file_path: str
    line_no: int
    text: str
    category: str
    visible: str
    namespace: str
    status: str
    note: str


TARGETS: dict[Path, Target] = {
    ROOT / "lib" / "mail_tui" / "wizard.py": Target("terminal", "ccb.mail_tui", "python"),
    ROOT / "lib" / "web" / "templates" / "dashboard.html": Target("html", "ccb.web.dashboard", "template"),
    ROOT / "lib" / "web" / "templates" / "mail.html": Target("html", "ccb.web.mail", "template"),
    ROOT / "lib" / "web" / "routes" / "daemons.py": Target("api", "ccb.web.daemon", "python"),
    ROOT / "lib" / "web" / "routes" / "mail.py": Target("api", "ccb.web.mail", "python"),
    ROOT / "lib" / "mail" / "sender.py": Target("mail", "ccb.mail.sender", "python"),
}

T_CALL_RE = re.compile(r"""t\(\s*['"]([^'"]+)['"]""")
CONSOLE_ERROR_RE = re.compile(r"""console\.error\(\s*['"]([^'"]+)['"]""")
TEXT_NODE_RE = re.compile(r">([^<{][^<]*)<")
OPTION_TEXT_RE = re.compile(r"""<option[^>]*>([^<{]+)</option>""")
SPAN_TEXT_RE = re.compile(r"""<span[^>]*>([^<{]+)</span>""")
PRINTABLE_RE = re.compile(r"[A-Za-z\u4e00-\u9fff]")

PROTOCOL_LITERALS = {
    "__main__",
    "utf-8",
    "plain",
    "alternative",
    "askd",
    "maild",
    "gmail",
    "outlook",
    "qq",
    "custom",
    "claude",
    "codex",
    "gemini",
    "opencode",
    "droid",
    "subject_prefix",
    "plus_alias",
    "on_completion",
    "application/json",
    "Content-Type",
    "Message-ID",
    "In-Reply-To",
    "References",
    "X-CCB-Thread-ID",
    "X-CCB-Provider",
}


def normalize(text: str) -> str:
    return " ".join(text.strip().split())


def is_user_visible_literal(text: str) -> bool:
    value = normalize(text)
    if not value:
        return False
    if value.startswith("ccb.") or value.startswith("/") or value.startswith("."):
        return False
    if value in PROTOCOL_LITERALS:
        return False
    if value.startswith("bg-") or value.startswith("text-") or value.startswith("grid "):
        return False
    if "{{" in value or "}}" in value or "x-text" in value or "@click" in value:
        return False
    if "http://" in value or "https://" in value:
        return False
    if value.isidentifier():
        return False
    if not PRINTABLE_RE.search(value):
        return False
    if re.fullmatch(r"[A-Za-z0-9_.:/-]+", value) and " " not in value:
        return False
    return True


def get_call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = get_call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def iter_string_literals(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        fragments = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                fragments.append(value.value)
        return ["".join(fragments)] if fragments else []
    return []


def add_entry(entries: dict[tuple[str, int, str, str], Entry], entry: Entry) -> None:
    key = (entry.file_path, entry.line_no, entry.text, entry.status)
    entries.setdefault(key, entry)


def scan_python(path: Path, target: Target, entries: dict[tuple[str, int, str, str], Entry]) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    rel_path = str(path.relative_to(ROOT)).replace("\\", "/")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        call_name = get_call_name(node.func)
        if call_name == "t" and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                add_entry(
                    entries,
                    Entry(
                        file_path=rel_path,
                        line_no=node.lineno,
                        text=arg.value,
                        category=target.category,
                        visible="是",
                        namespace=target.namespace,
                        status="translated-key",
                        note="t()",
                    ),
                )
            continue

        if call_name not in {
            "print",
            "input",
            "getpass.getpass",
            "ValueError",
            "ConnectionError",
            "RuntimeError",
        }:
            continue

        for arg in node.args:
            for literal in iter_string_literals(arg):
                if not is_user_visible_literal(literal):
                    continue
                add_entry(
                    entries,
                    Entry(
                        file_path=rel_path,
                        line_no=node.lineno,
                        text=normalize(literal),
                        category=target.category,
                        visible="是",
                        namespace=target.namespace,
                        status="hardcoded",
                        note=call_name,
                    ),
                )


def scan_template(path: Path, target: Target, entries: dict[tuple[str, int, str, str], Entry]) -> None:
    rel_path = str(path.relative_to(ROOT)).replace("\\", "/")
    lines = path.read_text(encoding="utf-8").splitlines()

    for line_no, line in enumerate(lines, start=1):
        for match in T_CALL_RE.finditer(line):
            add_entry(
                entries,
                Entry(
                    file_path=rel_path,
                    line_no=line_no,
                    text=match.group(1),
                    category=target.category,
                    visible="是",
                    namespace=target.namespace,
                    status="translated-key",
                    note="template t()",
                ),
            )

        for pattern, note in (
            (CONSOLE_ERROR_RE, "console.error"),
            (OPTION_TEXT_RE, "option text"),
            (SPAN_TEXT_RE, "inline text"),
            (TEXT_NODE_RE, "text node"),
        ):
            for match in pattern.finditer(line):
                literal = normalize(match.group(1))
                if not is_user_visible_literal(literal):
                    continue
                add_entry(
                    entries,
                    Entry(
                        file_path=rel_path,
                        line_no=line_no,
                        text=literal,
                        category=target.category,
                        visible="是",
                        namespace=target.namespace,
                        status="hardcoded",
                        note=note,
                    ),
                )


def collect_entries() -> list[Entry]:
    entries: dict[tuple[str, int, str, str], Entry] = {}
    for path, target in TARGETS.items():
        if target.kind == "python":
            scan_python(path, target, entries)
        else:
            scan_template(path, target, entries)
    return sorted(entries.values(), key=lambda item: (item.file_path, item.line_no, item.status, item.text))


def build_inventory(entries: list[Entry]) -> str:
    status_counts = Counter(entry.status for entry in entries)
    file_counts = Counter(entry.file_path for entry in entries)
    hardcoded_counts = Counter(entry.file_path for entry in entries if entry.status == "hardcoded")

    lines = [
        "# CCB i18n Surface Inventory",
        "",
        "## Summary",
        "",
        f"- 总条目: {len(entries)}",
        f"- 已接入翻译 key: {status_counts.get('translated-key', 0)}",
        f"- 剩余硬编码 surface: {status_counts.get('hardcoded', 0)}",
        "",
        "## File Breakdown",
        "",
        "| 文件 | 条目数 | 硬编码数 |",
        "|------|--------|----------|",
    ]
    for file_path in sorted(file_counts):
        lines.append(f"| `{file_path}` | {file_counts[file_path]} | {hardcoded_counts.get(file_path, 0)} |")

    lines.extend(
        [
            "",
            "## Inventory",
            "",
            "| 文件路径 | 行号 | 原始文本 | 分类 | 用户可见 | 建议命名空间 | 现状 | 备注 |",
            "|----------|------|----------|------|----------|----------------|------|------|",
        ]
    )
    for entry in entries:
        text = entry.text.replace("|", "\\|")
        note = entry.note.replace("|", "\\|")
        lines.append(
            f"| `{entry.file_path}` | {entry.line_no} | {text} | {entry.category} | {entry.visible} | "
            f"`{entry.namespace}` | {entry.status} | {note} |"
        )
    return "\n".join(lines) + "\n"


def write_inventory(entries: list[Entry]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "i18n_surface_inventory.md"
    report_path.write_text(build_inventory(entries), encoding="utf-8")
    return report_path


def main() -> int:
    entries = collect_entries()
    path = write_inventory(entries)
    status_counts = Counter(entry.status for entry in entries)
    print(
        "Wrote "
        f"{len(entries)} surface row(s) "
        f"({status_counts.get('translated-key', 0)} translated / {status_counts.get('hardcoded', 0)} hardcoded) "
        f"to {path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
