#!/usr/bin/env python3
"""
backfill_code_library.py — 一次性补录已有项目代码到代码图书馆索引。

用法：
    python backfill_code_library.py --dir /path/to/private-project/scripts
    python backfill_code_library.py --dir /path/to/private-docx-project  --pattern "_apply_polish.py"
"""
import argparse
import ast
import os
import sys
from pathlib import Path

from code_reuse_common import (
    add_tags_args,
    code_library_dir,
    configure_utf8_stdio,
    find_ca,
    make_citation,
    normalize_summary,
    run_ca,
)

# 代码图书馆根目录（ca learn 的 cwd，影响 lessons 写入位置）
CODE_LIBRARY = code_library_dir()


def parse_args():
    parser = argparse.ArgumentParser(description="补录已有代码到代码图书馆索引")
    parser.add_argument("--dir", required=True, help="扫描目录")
    parser.add_argument("--pattern", default="*.py", help="文件 glob 模式 (默认 *.py)")
    parser.add_argument("--dry-run", action="store_true", help="预览，不实际注册")
    return parser.parse_args()


def extract_functions(file_path: str):
    """从 Python 文件中提取函数和类定义。（复用 extract_from_diff.py 的逻辑）"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except SyntaxError as e:
        print(f"  [SKIP] 语法错误 {file_path}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  [SKIP] 读取失败 {file_path}: {e}", file=sys.stderr)
        return []

    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node) or ""
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            sig = f"def {node.name}({', '.join(a.arg for a in node.args.args)})"
            results.append({
                "kind": "function",
                "name": node.name,
                "signature": sig,
                "docstring": docstring[:200],
                "file": file_path,
                "line": start_line,
            })
        elif isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node) or ""
            results.append({
                "kind": "class",
                "name": node.name,
                "signature": f"class {node.name}(...):",
                "docstring": docstring[:200],
                "file": file_path,
                "line": node.lineno,
            })
    return results


def build_summary(item: dict) -> str:
    """构建 ca learn 摘要（同 extract_from_diff.py 格式）"""
    parts = [
        f"[{item['kind']}] {item['name']}",
        f"Signature: {item['signature']}",
    ]
    if item['docstring']:
        parts.append(f"Docstring: {item['docstring'][:200]}")
    parts.append(f"File: {item['file']}:{item['line']}")
    return normalize_summary("\n".join(parts))


def auto_tags(name: str, docstring: str, file_path: str) -> list:
    """自动打标签"""
    tags = set()
    ext = Path(file_path).suffix
    if ext == '.py':
        tags.add('python')
    keywords = ['test', 'api', 'auth', 'config', 'parse', 'convert',
                'validate', 'format', 'transform', 'extract', 'load',
                'save', 'export', 'import', 'create', 'delete', 'update',
                'docx', 'excel', 'word', 'pdf', 'table', 'bid']
    if docstring:
        for kw in keywords:
            if kw in docstring.lower():
                tags.add(kw)
    return sorted(tags)


def register(summary: str, tags: list, citation: str, dry_run: bool) -> bool:
    """通过 ca learn 注册到代码图书馆"""
    ca_path = find_ca()
    cmd = [ca_path, "learn", summary, "--type", "lesson", "--citation", citation]
    add_tags_args(cmd, tags)

    if dry_run:
        display_cmd = [cmd[0], "learn", "<summary>", *cmd[3:]]
        print(f"  [DRY-RUN] {' '.join(display_cmd)}")
        print(f"            {summary[:100]}...")
        return True

    result = run_ca(cmd, cwd=CODE_LIBRARY)
    if result.returncode != 0:
        print(f"  [FAIL] {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def main():
    configure_utf8_stdio()
    args = parse_args()
    scan_dir = Path(args.dir)
    if not scan_dir.is_dir():
        print(f"错误: 目录不存在 {scan_dir}", file=sys.stderr)
        sys.exit(1)

    py_files = sorted(scan_dir.glob(args.pattern))
    print(f"扫描目录: {scan_dir}")
    print(f"匹配文件: {len(py_files)} 个")
    print("=" * 60)

    total_registered = 0
    for py_file in py_files:
        items = extract_functions(str(py_file))
        if not items:
            continue

        rel_path = py_file.relative_to(scan_dir.parent) if scan_dir.parent else py_file
        print(f"\n>> {rel_path}")
        print("-" * 40)
        for item in items:
            tags = auto_tags(item["name"], item["docstring"], str(py_file))
            summary = build_summary(item)
            citation = make_citation(item["file"], item["line"], base_dir=scan_dir.parent)

            ok = register(summary, tags, citation, args.dry_run)
            if ok:
                tag_str = ", ".join(tags)
                doc_preview = f"  // {item['docstring'][:50].strip()}" if item['docstring'] else ""
                print(f"  [{item['kind']}] {item['name']}  (L{item['line']})  tags: {tag_str}{doc_preview}")
                total_registered += 1

    print("\n" + "=" * 60)
    print(f"✅ 共注册 {total_registered} 个函数/类到代码图书馆")
    print(f"   索引位置: {CODE_LIBRARY}/.claude/lessons/index.jsonl")
    print(f"   搜索: python ~/code-reuse-kit/scripts/search_code.py 关键词")
    print("=" * 60)


if __name__ == "__main__":
    main()
