#!/usr/bin/env python3
"""
extract_from_diff.py — 从 git diff 中提取新增函数/类，自动入库。

工作方式：
  1. 解析 git diff（HEAD 与上一 commit 对比）
  2. 识别新增的函数、类定义
  3. 提取签名、docstring、import 依赖
  4. 调用 ca learn 注册到知识库

完全自动流程（配合 git post-commit hook）：
  git commit 后自动触发，无需手动操作。

用法：
  python extract_from_diff.py --repo /path/to/project
  python extract_from_diff.py --repo . --dry-run    # 预览不改库
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
import ast
from pathlib import Path

# ── ca 命令定位（兼容 Windows / Linux / macOS） ──────────────────────────

def find_ca() -> str:
    ca = _which("ca")
    if ca:
        return ca
    ca = _which("ca.cmd")
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
    return "ca"  # last resort, let subprocess fail with clear error


def _which(cmd: str) -> str | None:
    """shutil.which 替代：兼容各种环境"""
    try:
        r = subprocess.run(
            ["where", cmd] if os.name == "nt" else ["which", cmd],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0:
            return r.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


# ── 参数解析 ────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="从 git diff 提取代码并入库"
    )
    parser.add_argument("--repo", required=True,
                        help="目标 git 仓库路径")
    parser.add_argument("--diff-ref", default=None,
                        help="对比的 git ref（默认自动：有 parent 用 HEAD~1，否则用 4b825dc）")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅预览，不调用 ca learn")
    parser.add_argument("--silent", action="store_true",
                        help="静默模式，只在有提取结果时输出")
    return parser.parse_args()


# ── Git 操作 ────────────────────────────────────────────────────────────

def _git(*args: str, cwd: str) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[WARN] git {' '.join(args)} 失败: {r.stderr.strip()}", file=sys.stderr)
        return ""
    return r.stdout


def has_parent(repo_path: str) -> bool:
    """检查 HEAD 是否有 parent commit（不是第一次提交）"""
    out = _git("rev-parse", "HEAD~1", cwd=repo_path)
    return bool(out.strip())


def get_diff(repo_path: str, diff_ref: str | None) -> str:
    """获取 git diff 输出。自动选择对比 ref。"""
    if diff_ref is None:
        diff_ref = "HEAD~1" if has_parent(repo_path) else "4b825dc"
    # --unified=0: 不输出上下文，只输出新增/删除行
    out = _git("diff", diff_ref, "--unified=0", cwd=repo_path)
    return out


def get_diff_stat(repo_path: str) -> str:
    """获取 --stat 用于判断是否有变更"""
    ref = "HEAD~1" if has_parent(repo_path) else "4b825dc"
    return _git("diff", ref, "--stat", cwd=repo_path)


# ── Diff 解析 ────────────────────────────────────────────────────────────

def parse_diff(diff_output: str) -> dict[str, list[dict]]:
    """解析 git diff 输出为 { 文件路径: [{added_lines, start_line}] }"""
    files: dict[str, list[dict]] = {}
    current_file = None

    for line in diff_output.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]  # 去掉 '+++ b/'
            if current_file not in files:
                files[current_file] = []
        elif line.startswith("@@"):
            # 新 hunk
            if current_file:
                files[current_file].append({"added_lines": [], "start_line": _parse_hunk_line(line)})
        elif line.startswith("+") and not line.startswith("+++") and current_file:
            if files[current_file]:
                files[current_file][-1]["added_lines"].append(line[1:])

    return files


def _parse_hunk_line(hunk_header: str) -> int:
    """从 @@ -a,b +c,d @@ 中提取目标起始行号 c"""
    m = re.search(r'\+(\d+)', hunk_header)
    return int(m.group(1)) if m else 0


# ── 代码提取 ────────────────────────────────────────────────────────────

def extract_items(file_path: str, added_lines: list[str]) -> list[dict]:
    """根据文件后缀选择解析方式，提取函数/类定义"""
    ext = Path(file_path).suffix
    code = "\n".join(added_lines)

    if ext == ".py":
        return _extract_python(code, file_path)
    elif ext in (".js", ".jsx", ".ts", ".tsx", ".mjs"):
        return _extract_js_ts(code, file_path)
    elif ext in (".sh", ".bash", ".zsh"):
        return _extract_shell(code, file_path)
    return []


def _extract_python(code: str, file_path: str) -> list[dict]:
    """用 AST 提取 Python 函数/类"""
    results = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return _extract_python_regex(code, file_path)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node) or ""
            results.append({
                "type": "function",
                "name": node.name,
                "signature": _py_sig(node),
                "docstring": doc,
                "file": file_path,
                "line": node.lineno,
            })
        elif isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node) or ""
            results.append({
                "type": "class",
                "name": node.name,
                "signature": f"class {node.name}",
                "docstring": doc,
                "file": file_path,
                "line": node.lineno,
            })
    return results


def _py_sig(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """生成函数签名字符串"""
    args = []
    for a in node.args.args:
        args.append(a.arg)
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}def {node.name}({', '.join(args)})"


def _extract_python_regex(code: str, file_path: str) -> list[dict]:
    """AST 失败时的正则 fallback"""
    results = []
    for m in re.finditer(r'^(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)', code, re.MULTILINE):
        results.append({
            "type": "function",
            "name": m.group(1),
            "signature": m.group(0).strip(),
            "docstring": "",
            "file": file_path,
            "line": code[:m.start()].count("\n") + 1,
        })
    for m in re.finditer(r'^class\s+(\w+)', code, re.MULTILINE):
        results.append({
            "type": "class",
            "name": m.group(1),
            "signature": f"class {m.group(1)}",
            "docstring": "",
            "file": file_path,
            "line": code[:m.start()].count("\n") + 1,
        })
    return results


def _extract_js_ts(code: str, file_path: str) -> list[dict]:
    """正则提取 JS/TS 函数/类"""
    results = []
    patterns = [
        (r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', "function"),
        (r'const\s+(\w+)\s*=\s*(?:async\s+)?(?:\(?[^)]*\)?\s*=>)', "arrow_function"),
        (r'(?:export\s+)?class\s+(\w+)', "class"),
    ]
    for pat, kind in patterns:
        for m in re.finditer(pat, code, re.MULTILINE):
            results.append({
                "type": kind,
                "name": m.group(1),
                "signature": m.group(0).strip(),
                "docstring": "",
                "file": file_path,
                "line": code[:m.start()].count("\n") + 1,
            })
    return results


def _extract_shell(code: str, file_path: str) -> list[dict]:
    """正则提取 shell 函数"""
    results = []
    for m in re.finditer(r'^(?:function\s+)?(\w+)\s*\(\s*\)\s*\{', code, re.MULTILINE):
        results.append({
            "type": "shell_function",
            "name": m.group(1),
            "signature": f"{m.group(1)}()",
            "docstring": "",
            "file": file_path,
            "line": code[:m.start()].count("\n") + 1,
        })
    return results


# ── import / 标签 ──────────────────────────────────────────────────────

def extract_imports(added_lines: list[str], file_path: str) -> str:
    """提取 import 语句"""
    code = "\n".join(added_lines)
    ext = Path(file_path).suffix
    imports = []

    patterns = []
    if ext == ".py":
        patterns = [r'^(?:from\s+\S+\s+)?import\s+\S+(?:\s+as\s+\S+)?']
    elif ext in (".js", ".jsx", ".ts", ".tsx", ".mjs"):
        patterns = [r'^(?:import|export)\s+.*?(?:from\s+[\'\"][^\'\"]+[\'\"])']
    elif ext in (".sh", ".bash", ".zsh"):
        patterns = [r'^(?:source|\.)\s+\S+']

    for pat in patterns:
        for m in re.finditer(pat, code, re.MULTILINE):
            imports.append(m.group(0).strip())

    return "\n".join(imports[:15])


def extract_tags(name: str, docstring: str, file_path: str) -> list[str]:
    """自动生成标签"""
    tags = set()
    ext = Path(file_path).suffix
    lang_map = {
        ".py": "python", ".js": "javascript", ".jsx": "react",
        ".ts": "typescript", ".tsx": "typescript+react",
        ".sh": "shell", ".bash": "shell", ".zsh": "shell",
        ".md": "markdown", ".yaml": "yaml", ".yml": "yaml",
        ".json": "json", ".sql": "sql",
    }
    if ext in lang_map:
        tags.add(lang_map[ext])

    if docstring:
        keywords = [
            "test", "api", "auth", "config", "parse", "convert",
            "validate", "format", "transform", "extract", "load",
            "save", "export", "import", "create", "delete", "update",
            "search", "merge", "sort", "filter", "map",
        ]
        for kw in keywords:
            if kw in docstring.lower():
                tags.add(kw)

    return sorted(tags)


# ── ca learn 注册 ─────────────────────────────────────────────────────

def build_summary(item: dict, imports: str) -> str:
    """构建传给 ca learn 的摘要文本"""
    parts = [
        f"[{item['type']}] {item['name']}",
        f"\n签名: {item['signature']}",
    ]
    if item["docstring"]:
        parts.append(f"\n说明: {item['docstring'][:200]}")
    parts.append(f"\n文件: {item['file']}:{item['line']}")
    if imports:
        parts.append(f"\n依赖: {imports[:200]}")
    return "".join(parts)


def register(ca: str, summary: str, tags: list[str], citation: str, dry_run: bool) -> bool:
    """调用 ca learn 注册一个代码条目"""
    cmd = [
        ca, "learn", summary,
        "--type", "pattern",
        "--citation", citation,
    ]
    if tags:
        cmd.extend(["--trigger", ", ".join(tags)])

    if dry_run:
        print(f"  [模拟] ca learn → {item_type_from_summary(summary)} {name_from_summary(summary)}")
        return True

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"  [WARN] ca learn 失败: {r.stderr.strip()[:120]}", file=sys.stderr)
        return False
    return True


def item_type_from_summary(s: str) -> str:
    m = re.match(r'^\[(\w+)\]', s)
    return m.group(1) if m else "?"


def name_from_summary(s: str) -> str:
    m = re.match(r'^\[\w+\]\s+(\S+)', s)
    return m.group(1) if m else "?"


# ── 主流程 ──────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    repo = os.path.abspath(args.repo)

    # 检查 git 仓库
    git_dir = os.path.join(repo, ".git")
    if not os.path.isdir(git_dir):
        if not args.silent:
            print(f"[SKIP] {repo} 不是 git 仓库")
        return

    # 检查 diff
    stat = get_diff_stat(repo)
    if not stat.strip():
        if not args.silent:
            print(f"[SKIP] {repo} 没有新增变更")
        return

    # 解析 diff
    diff = get_diff(repo, args.diff_ref)
    if not diff.strip():
        if not args.silent:
            print(f"[SKIP] {repo} diff 为空")
        return

    files = parse_diff(diff)
    total = 0
    ca = find_ca()

    report_lines = []

    for file_path, hunks in files.items():
        all_added = []
        for hunk in hunks:
            all_added.extend(hunk["added_lines"])
        if not all_added:
            continue

        items = extract_items(file_path, all_added)
        if not items:
            continue

        imports = extract_imports(all_added, file_path)

        for item in items:
            tags = extract_tags(item["name"], item["docstring"], file_path)
            summary = build_summary(item, imports)
            citation = f"{item['file']}:{item['line']}"
            ok = register(ca, summary, tags, citation, args.dry_run)
            if ok:
                report_lines.append(f"  ✓ [{item['type']}] {item['name']}  ← {citation}")
                total += 1

    # 输出报告
    if report_lines:
        mode = " [模拟]" if args.dry_run else ""
        print(f"\n{'='*50}")
        print(f"  Code Library 提取报告{mode}")
        print(f"{'='*50}")
        for l in report_lines:
            print(l)
        print(f"{'='*50}")
        print(f"  共 {total} 个代码片段已{'模拟提取' if args.dry_run else '入库'}")
        print(f"{'='*50}\n")
    elif not args.silent:
        print(f"[OK] 未发现可提取的新增函数/类")


if __name__ == "__main__":
    main()
