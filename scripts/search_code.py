#!/usr/bin/env python3
"""
search_code.py — 搜索 code-library 中的已有代码。

用法：
  python search_code.py "pdf 提取"
  python search_code.py "auth middleware" --limit 5
"""

import argparse
import subprocess
import sys


def find_ca() -> str:
    import os
    ca = None
    try:
        r = subprocess.run(
            ["where", "ca"] if os.name == "nt" else ["which", "ca"],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0:
            ca = r.stdout.strip().splitlines()[0]
    except Exception:
        pass
    if ca:
        return ca
    fallbacks = [
        os.path.expanduser("~\\AppData\\Roaming\\npm\\ca.cmd"),
        os.path.expanduser("~\\AppData\\Roaming\\npm\\ca"),
        "/usr/local/bin/ca",
        "/opt/homebrew/bin/ca",
    ]
    for p in fallbacks:
        if os.path.isfile(p):
            return p
    return "ca"


def parse_args():
    parser = argparse.ArgumentParser(description="搜索代码库")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--limit", type=int, default=5, help="最大结果数（默认 5）")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser.parse_args()


def main():
    args = parse_args()
    ca = find_ca()

    if ca == "ca" and not (
        subprocess.run(["ca", "--version"], capture_output=True, text=True).returncode == 0
    ):
        print("Error: 'ca' 命令未找到。请先安装 compound-agent。", file=sys.stderr)
        sys.exit(1)

    r = subprocess.run([ca, "search", args.query], capture_output=True, text=True)

    if args.format == "json":
        print(r.stdout)
        return

    output = r.stdout.strip()
    if not output:
        print(f"没有找到与 \"{args.query}\" 相关的代码。")
        return

    print(f"\n## Code Library: \"{args.query}\" 的搜索结果\n")
    lines = [l.strip() for l in output.splitlines() if l.strip()]
    count = 0
    for line in lines:
        if count >= args.limit:
            print(f"\n... 以及更多结果（共 {len(lines)} 条）")
            break
        print(f"  • {line}")
        count += 1


if __name__ == "__main__":
    main()
