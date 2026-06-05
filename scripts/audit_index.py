#!/usr/bin/env python3
"""Privacy-safe audit for Code Reuse Kit lesson indexes."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from code_reuse_common import code_library_dir, configure_utf8_stdio
from doctor import sanitize_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the Code Reuse Kit JSONL index without modifying it.")
    parser.add_argument("--index", default=None, help="Path to index.jsonl. Defaults to the canonical code library index.")
    parser.add_argument("--root", default=None, help="Repository root used to resolve relative citations.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    return parser.parse_args()


def issue(level: str, code: str, line: int, message: str, detail: object | None = None) -> dict[str, str]:
    item = {"level": level, "code": code, "line": str(line), "message": message}
    if detail is not None:
        item["detail"] = str(detail)
    return item


def sanitize_issue(item: dict[str, str], *, home: Path, root: Path) -> dict[str, str]:
    return {key: sanitize_value(value, home=home, root=root) for key, value in item.items()}


def entry_id(entry: dict, fallback: int) -> str:
    raw = entry.get("id")
    return str(raw) if raw else f"line-{fallback}"


def entry_insight(entry: dict) -> str:
    raw = entry.get("insight")
    return str(raw).strip() if raw is not None else ""


def citation_path(entry: dict) -> str | None:
    citation = entry.get("citation")
    if isinstance(citation, dict):
        raw = citation.get("file")
        return str(raw) if raw else None
    if isinstance(citation, str):
        text = citation.rsplit(":", 1)[0]
        return text or None
    return None


def resolve_citation(file_value: str, *, root: Path) -> Path:
    path = Path(file_value).expanduser()
    if path.is_absolute():
        return path
    return root / path


def looks_low_quality(insight: str) -> bool:
    if len(insight) < 20:
        return True
    if "|" not in insight and not re.search(r"\b(Signature|File|Docstring):", insight):
        return True
    return False


def audit_index(*, index_path: Path, root: Path, home: Path | None = None) -> dict[str, object]:
    home = home or Path.home()
    root = root.resolve()
    index_path = index_path.expanduser()
    issues: list[dict[str, str]] = []
    active: list[tuple[int, dict]] = []
    deleted_entries = 0
    total_lines = 0
    insights: dict[str, list[int]] = defaultdict(list)

    if not index_path.exists():
        return {
            "tool": "code-reuse-kit index audit",
            "index": sanitize_value(index_path, home=home, root=root),
            "summary": {"total_lines": 0, "active_entries": 0, "deleted_entries": 0, "issues": 1},
            "issues": [
                sanitize_issue(issue("fail", "missing-index", 0, "index file does not exist", index_path), home=home, root=root)
            ],
        }

    with index_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            total_lines += 1
            text = line.strip()
            if not text:
                continue
            try:
                entry = json.loads(text)
            except json.JSONDecodeError as exc:
                issues.append(issue("fail", "malformed-json", line_no, "line is not valid JSON", exc.msg))
                continue
            if not isinstance(entry, dict):
                issues.append(issue("fail", "malformed-entry", line_no, "line JSON is not an object"))
                continue
            if entry.get("deleted"):
                deleted_entries += 1
                continue
            active.append((line_no, entry))

    for line_no, entry in active:
        insight = entry_insight(entry)
        if not insight:
            issues.append(issue("warn", "missing-insight", line_no, "entry has no insight", entry_id(entry, line_no)))
        else:
            insights[insight].append(line_no)
            if looks_low_quality(insight):
                issues.append(issue("warn", "low-quality-insight", line_no, "insight is too short or lacks searchable structure", insight))

        file_value = citation_path(entry)
        if not file_value:
            issues.append(issue("warn", "missing-citation", line_no, "entry has no citation", entry_id(entry, line_no)))
            continue
        resolved = resolve_citation(file_value, root=root)
        if not resolved.exists():
            issues.append(issue("warn", "stale-citation", line_no, "citation file does not exist", resolved))

    for insight, lines in insights.items():
        if len(lines) > 1:
            issues.append(
                issue(
                    "warn",
                    "duplicate-insight",
                    lines[0],
                    f"same insight appears on {len(lines)} active entries",
                    ", ".join(str(line) for line in lines),
                )
            )

    sanitized = [sanitize_issue(item, home=home, root=root) for item in issues]
    return {
        "tool": "code-reuse-kit index audit",
        "index": sanitize_value(index_path, home=home, root=root),
        "summary": {
            "total_lines": total_lines,
            "active_entries": len(active),
            "deleted_entries": deleted_entries,
            "issues": len(sanitized),
        },
        "issues": sanitized,
    }


def format_text(report: dict[str, object], *, max_issues: int = 50) -> str:
    summary = report["summary"]
    lines = [
        "Code Reuse Kit Index Audit",
        f"Index: {report['index']}",
        "",
        "Summary:",
        f"  total_lines: {summary['total_lines']}",
        f"  active_entries: {summary['active_entries']}",
        f"  deleted_entries: {summary['deleted_entries']}",
        f"  issues: {summary['issues']}",
        "",
    ]
    issues = report["issues"]
    if not issues:
        lines.append("No issues found.")
    else:
        lines.append("Issues:")
        displayed = issues[:max_issues]
        for item in displayed:
            detail = f" ({item['detail']})" if "detail" in item else ""
            lines.append(f"  [{item['level']}] {item['code']} line {item['line']}: {item['message']}{detail}")
        omitted = len(issues) - len(displayed)
        if omitted > 0:
            plural = "s" if omitted != 1 else ""
            lines.append(f"  ... {omitted} more issue{plural} omitted; use --json for the full report.")
    return "\n".join(lines)


def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    root = Path(args.root).resolve() if args.root else Path.cwd()
    index_path = Path(args.index).expanduser() if args.index else code_library_dir() / ".claude" / "lessons" / "index.jsonl"
    report = audit_index(index_path=index_path, root=root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
