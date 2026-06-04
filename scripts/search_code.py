#!/usr/bin/env python3
"""
search_code.py - 搜索 code-reuse-kit 中的已有代码。
用法: python search_code.py "关键词" [--limit 5]
"""
import argparse, os, subprocess, sys

def find_ca():
    if os.name == "nt":
        for p in [os.path.expanduser("~/AppData/Roaming/npm/ca.cmd"),
                  os.path.expanduser("~/AppData/Roaming/npm/ca")]:
            if os.path.isfile(p): return p
        return "ca.cmd"
    else:
        try:
            r = subprocess.run(["which","ca"], capture_output=True, text=True, timeout=3)
            if r.returncode == 0: return r.stdout.strip().splitlines()[0]
        except: pass
        for p in ["/usr/local/bin/ca","/opt/homebrew/bin/ca"]:
            if os.path.isfile(p): return p
        return "ca"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query"); ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()
    ca = find_ca()
    r = subprocess.run([ca, "search", args.query], capture_output=True, text=False)
    out = r.stdout.decode('utf-8', errors='replace').strip()
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
