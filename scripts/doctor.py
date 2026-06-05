#!/usr/bin/env python3
"""Privacy-safe health diagnostics for Code Reuse Kit."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|password|secret|access[_-]?token)=([^\s&]+)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run privacy-safe Code Reuse Kit health checks.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root to inspect. Defaults to this script's parent repository.",
    )
    return parser.parse_args()


def sanitize_url(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        try:
            parsed = urlsplit(raw)
        except ValueError:
            return "<redacted-url>"
        host = parsed.hostname or ""
        netloc = host
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))

    return re.sub(r"https?://[^\s]+", replace, value)


def _path_forms(path: Path) -> list[str]:
    forms = [
        str(path).replace("\\", "/"),
        path.as_posix(),
    ]
    try:
        forms.append(str(path.resolve()).replace("\\", "/"))
        forms.append(path.resolve().as_posix())
    except OSError:
        pass
    return sorted({form.rstrip("/") for form in forms if form}, key=len, reverse=True)


def sanitize_value(value: object, *, home: Path | None = None, root: Path | None = None) -> str:
    text = str(value)
    text = sanitize_url(text)
    text = EMAIL_RE.sub("<redacted-email>", text)
    text = SECRET_RE.sub(lambda m: f"{m.group(1)}=<redacted-secret>", text)

    home = home or Path.home()

    normalized = text.replace("\\", "/")
    if root:
        for root_text in _path_forms(root):
            if normalized == root_text:
                normalized = "."
                break
            if normalized.startswith(root_text + "/"):
                normalized = normalized[len(root_text) + 1 :]
                break
    for home_text in _path_forms(home):
        if normalized == home_text:
            normalized = "~"
            break
        if normalized.startswith(home_text + "/"):
            normalized = "~/" + normalized[len(home_text) + 1 :]
            break
    return normalized


def status(name: str, level: str, message: str, detail: object | None = None) -> dict[str, str]:
    item = {"name": name, "level": level, "message": message}
    if detail is not None:
        item["detail"] = str(detail)
    return item


def run_text(cmd: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def sanitize_item(item: dict[str, str], *, home: Path, root: Path) -> dict[str, str]:
    return {key: sanitize_value(value, home=home, root=root) for key, value in item.items()}


def command_status(name: str, command: str, *, home: Path, root: Path) -> dict[str, str]:
    found = shutil.which(command)
    if found:
        return sanitize_item(status(name, "ok", "available", found), home=home, root=root)
    return status(name, "fail", f"`{command}` was not found on PATH")


def collect_report(*, root: Path, home: Path | None = None) -> dict[str, object]:
    home = home or Path.home()
    root = root.resolve()
    checks: list[dict[str, str]] = []

    checks.append(status("python", "ok", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"))
    checks.append(command_status("git", "git", home=home, root=root))
    checks.append(command_status("node", "node", home=home, root=root))
    ca_command = "ca.cmd" if os.name == "nt" else "ca"
    checks.append(command_status("compound-agent", ca_command, home=home, root=root))

    library_dir = Path(os.environ.get("CODE_REUSE_KIT_DIR", str(home / "code-reuse-kit")))
    checks.append(sanitize_item(status("code-library-dir", "ok", "resolved", library_dir), home=home, root=root))

    index_path = library_dir / ".claude" / "lessons" / "index.jsonl"
    checks.append(
        sanitize_item(
            status(
                "lesson-index",
                "ok" if index_path.exists() else "warn",
                "found" if index_path.exists() else "not found yet",
                index_path,
            ),
            home=home,
            root=root,
        )
    )

    hooks_path = run_text(["git", "config", "--global", "--get", "core.hooksPath"])
    if hooks_path:
        checks.append(sanitize_item(status("global-hooks-path", "ok", "configured", hooks_path), home=home, root=root))
        hook_file = Path(hooks_path).expanduser() / "post-commit"
        level = "ok" if hook_file.exists() else "warn"
        checks.append(
            sanitize_item(
                status("post-commit-hook", level, "found" if hook_file.exists() else "missing", hook_file),
                home=home,
                root=root,
            )
        )
    else:
        checks.append(status("global-hooks-path", "warn", "not configured"))
        checks.append(status("post-commit-hook", "warn", "cannot inspect without hooks path"))

    reasonix_candidates = [
        home / ".config" / "reasonix" / "AGENTS.md",
        home / ".reasonix" / "AGENTS.md",
    ]
    reasonix_found = next((path for path in reasonix_candidates if path.exists()), None)
    checks.append(
        sanitize_item(
            status(
                "reasonix-agents",
                "ok" if reasonix_found else "warn",
                "found" if reasonix_found else "not found",
                reasonix_found or reasonix_candidates[0],
            ),
            home=home,
            root=root,
        )
    )

    claude_path = home / ".claude" / "CLAUDE.md"
    checks.append(
        sanitize_item(
            status("claude-config", "ok" if claude_path.exists() else "warn", "found" if claude_path.exists() else "not found", claude_path),
            home=home,
            root=root,
        )
    )

    return {
        "tool": "code-reuse-kit doctor",
        "root": sanitize_value(root, home=home, root=root),
        "checks": checks,
    }


def print_text(report: dict[str, object]) -> None:
    print("Code Reuse Kit Doctor")
    print(f"Root: {report['root']}")
    print("")
    for item in report["checks"]:
        marker = {"ok": "[OK]", "warn": "[WARN]", "fail": "[FAIL]"}.get(item["level"], "[INFO]")
        line = f"{marker} {item['name']}: {item['message']}"
        if "detail" in item:
            line += f" ({item['detail']})"
        print(line)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    report = collect_report(root=root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
