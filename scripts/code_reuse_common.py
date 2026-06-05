#!/usr/bin/env python3
"""Shared helpers for Code Reuse Kit command-line scripts."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PureWindowsPath


def configure_utf8_stdio() -> None:
    """Prefer UTF-8 for script output on Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8")
            except Exception:
                pass


def code_library_dir() -> Path:
    override = os.environ.get("CODE_REUSE_KIT_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / "code-reuse-kit"


def find_ca() -> str:
    for name in ("ca", "ca.cmd"):
        found = shutil.which(name)
        if found:
            return found

    fallbacks = [
        Path.home() / "AppData" / "Roaming" / "npm" / "ca.cmd",
        Path.home() / "AppData" / "Roaming" / "npm" / "ca",
        Path("/usr/local/bin/ca"),
        Path("/opt/homebrew/bin/ca"),
    ]
    for candidate in fallbacks:
        if candidate.is_file():
            return str(candidate)

    return "ca.cmd" if os.name == "nt" else "ca"


def normalize_summary(summary: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in summary.splitlines()]
    return " | ".join(line for line in lines if line)


def _looks_like_windows_path(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", value))


def _relative_windows_path(file_path: str, base_dir: str | None) -> str | None:
    win_path = PureWindowsPath(file_path)
    if not win_path.drive:
        return None

    if base_dir and _looks_like_windows_path(base_dir):
        win_base = PureWindowsPath(base_dir)
        try:
            return win_path.relative_to(win_base).as_posix()
        except ValueError:
            pass

    return PureWindowsPath(*win_path.parts[1:]).as_posix()


def _safe_relative_path(file_path: Path, base_dir: Path | None) -> Path:
    expanded = file_path.expanduser()
    if base_dir is not None:
        try:
            return expanded.resolve().relative_to(base_dir.expanduser().resolve())
        except Exception:
            pass
    return Path(*expanded.parts[1:]) if expanded.drive else expanded


def make_citation(file_path: str | Path, line: int, base_dir: str | Path | None = None) -> str:
    path_text = str(file_path)
    base_text = str(base_dir) if base_dir is not None else None
    windows_relative = _relative_windows_path(path_text, base_text)
    if windows_relative is not None:
        return f"{windows_relative}:{line}"

    base = Path(base_dir) if base_dir is not None else None
    safe_path = _safe_relative_path(Path(file_path), base)
    return f"{safe_path.as_posix()}:{line}"


def add_tags_args(cmd: list[str], tags: list[str]) -> None:
    clean_tags = [tag.strip() for tag in tags if tag and tag.strip()]
    if clean_tags:
        cmd.extend(["--tags", ", ".join(clean_tags)])


def run_ca(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd or code_library_dir()),
        timeout=timeout,
    )
