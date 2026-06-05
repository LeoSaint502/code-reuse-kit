#!/usr/bin/env python3
"""Privacy-safe consistency checks for Code Reuse Kit docs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from code_reuse_common import configure_utf8_stdio
from doctor import sanitize_value


DEFAULT_DOCS = [
    "AGENTS.md",
    "README.md",
    "README.en.md",
    "docs/harness-matrix.md",
]

DEFAULT_REQUIRED_SCRIPTS = [
    "scripts/search_code.py",
    "scripts/extract_from_diff.py",
    "scripts/backfill_code_library.py",
    "scripts/install_code_library.py",
    "scripts/install_hooks.py",
    "scripts/install_agent_config.py",
    "scripts/sync.py",
    "scripts/doctor.py",
    "scripts/audit_index.py",
    "scripts/check_consistency.py",
    "scripts/ci_verify.py",
]

CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
LOCAL_PATH_RE = re.compile(
    r"^(?:AGENTS\.md|README(?:\.en)?\.md|docs/[\w./-]+|scripts/[\w./-]+|tests/[\w./-]+|skills/[\w./-]+)$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Code Reuse Kit documentation consistency.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    parser.add_argument("--root", default=None, help="Repository root. Defaults to the current working directory.")
    return parser.parse_args()


def extract_markdown_paths(text: str) -> list[str]:
    refs: list[str] = []
    for match in CODE_SPAN_RE.finditer(text):
        value = match.group(1).strip().replace("\\", "/")
        value = value.rstrip(".,:;")
        if LOCAL_PATH_RE.match(value):
            refs.append(value)
    return sorted(set(refs))


def issue(level: str, code: str, path: str, message: str, source: str | None = None) -> dict[str, str]:
    item = {"level": level, "code": code, "path": path, "message": message}
    if source:
        item["source"] = source
    return item


def sanitize_issue(item: dict[str, str], *, home: Path, root: Path) -> dict[str, str]:
    return {key: sanitize_value(value, home=home, root=root) for key, value in item.items()}


def check_consistency(
    *,
    root: Path,
    docs: list[Path] | None = None,
    required_scripts: list[str] | None = None,
    home: Path | None = None,
) -> dict[str, object]:
    home = home or Path.home()
    root = root.resolve()
    doc_paths = docs if docs is not None else [root / path for path in DEFAULT_DOCS]
    scripts = required_scripts if required_scripts is not None else DEFAULT_REQUIRED_SCRIPTS
    issues: list[dict[str, str]] = []

    for script in scripts:
        if not (root / script).exists():
            issues.append(issue("fail", "missing-required-script", script, "required script is missing"))

    for doc in doc_paths:
        doc_path = doc if doc.is_absolute() else root / doc
        doc_label = sanitize_value(doc_path, home=home, root=root)
        if not doc_path.exists():
            issues.append(issue("fail", "missing-document", doc_label, "document is missing"))
            continue
        text = doc_path.read_text(encoding="utf-8")
        for ref in extract_markdown_paths(text):
            if not (root / ref).exists():
                issues.append(issue("fail", "missing-doc-reference", ref, "document references a missing local path", doc_label))

    sanitized = [sanitize_issue(item, home=home, root=root) for item in issues]
    return {
        "tool": "code-reuse-kit consistency check",
        "root": sanitize_value(root, home=home, root=root),
        "summary": {
            "documents_checked": len(doc_paths),
            "required_scripts": len(scripts),
            "issues": len(sanitized),
        },
        "issues": sanitized,
    }


def format_text(report: dict[str, object]) -> str:
    summary = report["summary"]
    lines = [
        "Code Reuse Kit Consistency Check",
        f"Root: {report['root']}",
        "",
        "Summary:",
        f"  documents_checked: {summary['documents_checked']}",
        f"  required_scripts: {summary['required_scripts']}",
        f"  issues: {summary['issues']}",
        "",
    ]
    issues = report["issues"]
    if not issues:
        lines.append("No issues found.")
    else:
        lines.append("Issues:")
        for item in issues:
            source = f" from {item['source']}" if "source" in item else ""
            lines.append(f"  [{item['level']}] {item['code']}: {item['path']}{source} - {item['message']}")
    return "\n".join(lines)


def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    root = Path(args.root).resolve() if args.root else Path.cwd()
    report = check_consistency(root=root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_text(report))
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
