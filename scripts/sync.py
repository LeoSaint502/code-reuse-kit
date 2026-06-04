#!/usr/bin/env python3
"""
sync.py — Sync code-library with remote: git pull + rebuild index.

Usage:
    cd ~/code-library && python scripts/sync.py
"""

import os
import shutil
import subprocess
import sys

DEST = os.path.expanduser("~/code-library")


def find_ca() -> str:
    """Locate the ca executable across platforms."""
    # Try shutil.which first
    ca = shutil.which("ca")
    if ca:
        return ca
    # On Windows, try ca.cmd
    ca = shutil.which("ca.cmd")
    if ca:
        return ca
    # Fallback: common npm global locations
    fallbacks = [
        os.path.expanduser("~\\AppData\\Roaming\\npm\\ca.cmd"),
        os.path.expanduser("~\\AppData\\Roaming\\npm\\ca"),
        "/usr/local/bin/ca",
        "/opt/homebrew/bin/ca",
    ]
    for p in fallbacks:
        if os.path.isfile(p):
            return p
    return "ca"  # last resort, let subprocess fail with clear error


def run(cmd: list, cwd: str | None = None, check: bool = True):
    try:
        subprocess.run(cmd, cwd=cwd, check=check, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  [ERR] 命令失败 (exit={e.returncode})", file=sys.stderr)
        sys.exit(1)


def main():
    # Ensure stdout can handle Unicode (especially on Windows/GBK)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    elif hasattr(sys.stdout, "buffer"):
        sys.stdout = sys.stdout.buffer

    print("=== Code Library Sync ===")

    # 1. Git pull
    print(">> git pull --ff-only ...")
    run(["git", "pull", "--ff-only"], cwd=DEST)
    print("  [OK] 已拉取最新代码")

    # 2. Rebuild ca index
    ca = find_ca()
    print(f">> {ca} rebuild ...")
    run([ca, "rebuild"], cwd=DEST, check=False)
    print("  [OK] SQLite 索引已重建")

    # 3. Re-index docs
    docs_dir = os.path.join(DEST, "docs")
    if os.path.isdir(docs_dir):
        print(">> ca index-docs docs/ ...")
        run([ca, "index-docs", "docs/"], cwd=DEST, check=False)
        print("  [OK] 文档索引已更新")

    print("\n=== Sync complete ===")


if __name__ == "__main__":
    main()
