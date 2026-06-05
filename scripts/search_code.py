#!/usr/bin/env python3
"""
search_code.py - 搜索 code-reuse-kit 中的已有代码。
用法: python search_code.py "关键词" [--limit 5]
"""
import argparse
import sys

from code_reuse_common import code_library_dir, configure_utf8_stdio, find_ca, run_ca

def main():
    configure_utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("query"); ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()
    ca = find_ca()
    r = run_ca([ca, "search", args.query], cwd=code_library_dir())
    if r.returncode != 0:
        err = r.stderr.strip() or "ca search failed"
        print(err, file=sys.stderr)
        sys.exit(r.returncode)

    out = r.stdout.strip()
    if not out:
        print('No results found for "%s".' % args.query)
        return
    print()
    print('## Results for "%s"' % args.query)
    print()
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        if i >= args.limit:
            print("... (%d more results)" % (len(lines) - args.limit))
            break
        print("  - %s" % line)

if __name__ == "__main__":
    main()
