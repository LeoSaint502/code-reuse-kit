# Code Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a system that automatically captures code written by the Reasonix agent, indexes it for reuse, and syncs across machines via Git.

**Architecture:** compound-agent (Go CLI) provides the storage/search/sync backbone; a Python script `extract_from_diff.py` parses `git diff` to extract functions/classes and registers them via `ca learn`; a `code-reuse` skill hooks into Reasonix sessions for auto-search and auto-capture.

**Tech Stack:** compound-agent (npm), Python 3.14+ (ast module), Git, Reasonix (AGENTS.md + skills)

---

### Task 1: Install compound-agent & Init Code Library

**Files:**
- Create: `~/code-library/` directory
- Create: `~/code-library/scripts/` directory
- Create: `~/code-library/lessons/index.jsonl` (created by `ca setup`)
- Create: `~/code-library/.cache/` (created by `ca setup`)

- [ ] **Step 1: Install compound-agent globally**

Run:
```bash
npm install -g compound-agent
```
Expected: Installs `ca` CLI binary globally.

- [ ] **Step 2: Create and init the code library directory**

Run:
```bash
mkdir -p ~/code-library
cd ~/code-library
ca setup
```
Expected: `ca setup` creates `.claude/` with lessons structure and hooks.

- [ ] **Step 3: Create scripts subdirectory**

Run:
```bash
mkdir -p ~/code-library/scripts
```
Expected: `~/code-library/scripts/` exists.

- [ ] **Step 4: Initialize Git repo**

Run:
```bash
cd ~/code-library
git init
git add -A
git commit -m "init: code library with compound-agent"
```
Expected: Git repo initialized, initial commit with compound-agent config files.

- [ ] **Step 5: Verify ca works**

Run:
```bash
ca --version
ca search "test"
```
Expected: `ca --version` returns version string, `ca search "test"` returns results (likely empty).

---

### Task 2: Write extract_from_diff.py

**Files:**
- Create: `~/code-library/scripts/extract_from_diff.py`

This script is the core of the system. It:
1. Runs `git diff` between the current state and a reference commit (default: HEAD~1)
2. Parses the diff to find added lines
3. Extracts function definitions and class definitions from added code
4. Extracts docstrings, imports, and file paths
5. Generates a summary for each code block
6. Calls `ca learn` to register each code block in the knowledge base

- [ ] **Step 1: Write the script scaffold**

Create `~/code-library/scripts/extract_from_diff.py`:

```python
#!/usr/bin/env python3
"""
extract_from_diff.py — Parse git diff, extract functions/classes, register via ca learn.

Usage:
    python extract_from_diff.py --repo /path/to/project
    python extract_from_diff.py --repo /path/to/project --diff-ref HEAD~3
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
import ast
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Extract code from git diff and register in knowledge base")
    parser.add_argument("--repo", required=True, help="Path to the git repository")
    parser.add_argument("--diff-ref", default="HEAD~1", help="Git ref to diff against (default: HEAD~1)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be registered without calling ca")
    return parser.parse_args()


def run_git_diff(repo_path: str, diff_ref: str) -> str:
    """Run git diff and return the output."""
    result = subprocess.run(
        ["git", "diff", diff_ref, "--unified=0"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error running git diff: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def parse_diff(diff_output: str):
    """Parse git diff output into per-file hunks."""
    files = {}
    current_file = None

    for line in diff_output.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]  # Remove '+++ b/' prefix
            if current_file not in files:
                files[current_file] = []
        elif line.startswith("@@") and current_file:
            # New hunk
            files[current_file].append({"added_lines": [], "start_line": 0})
        elif line.startswith("+") and not line.startswith("+++") and current_file:
            if files[current_file]:
                files[current_file][-1]["added_lines"].append(line[1:])

    return files


def extract_functions_from_python(code_lines: list, file_path: str) -> list:
    """Extract function/class definitions from Python code using AST."""
    code = "\n".join(code_lines)
    results = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Try to parse at function level
        return extract_functions_regex(code_lines, file_path)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node) or ""
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            body = "\n".join(code.splitlines()[start_line-1:end_line]) if end_line > start_line else f"def {node.name}(...): ..."
            sig = f"def {node.name}({', '.join(a.arg for a in node.args.args)})"
            results.append({
                "type": "function",
                "name": node.name,
                "signature": sig,
                "docstring": docstring,
                "file": file_path,
                "line": start_line,
                "body_snippet": body,
            })
        elif isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node) or ""
            results.append({
                "type": "class",
                "name": node.name,
                "signature": f"class {node.name}(...):",
                "docstring": docstring,
                "file": file_path,
                "line": node.lineno,
                "body_snippet": "",
            })

    return results


def extract_functions_regex(code_lines: list, file_path: str) -> list:
    """Fallback: extract function/class definitions using regex."""
    code = "\n".join(code_lines)
    results = []

    patterns = [
        (r'^def\s+(\w+)\s*\(([^)]*)\)', "function"),
        (r'^async\s+def\s+(\w+)\s*\(([^)]*)\)', "async_function"),
        (r'^class\s+(\w+)\s*\(?([^:]*)\)?\s*:', "class"),
    ]

    for pattern, kind in patterns:
        for match in re.finditer(pattern, code, re.MULTILINE):
            name = match.group(1)
            args = match.group(2) if match.lastindex >= 2 else ""
            results.append({
                "type": kind,
                "name": name,
                "signature": f"{'async ' if kind == 'async_function' else ''}{'def' if 'function' in kind else 'class'} {name}({args})",
                "docstring": "",
                "file": file_path,
                "line": code[:match.start()].count("\n") + 1,
                "body_snippet": "",
            })

    return results


def extract_functions_from_general(code_lines: list, file_path: str) -> list:
    """Extract functions from JS/TS/Shell using regex."""
    code = "\n".join(code_lines)
    results = []

    # JavaScript/TypeScript functions
    patterns = [
        (r'^function\s+(\w+)\s*\(([^)]*)\)', "function"),
        (r'^const\s+(\w+)\s*=\s*(?:async\s+)?\(?([^)]*)\)?\s*=>', "arrow_function"),
        (r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', "function"),
        (r'^class\s+(\w+)\s*\{?', "class"),
    ]

    # Shell functions
    shell_patterns = [
        (r'^function\s+(\w+)\s*\{', "shell_function"),
        (r'^(\w+)\s*\(\)\s*\{', "shell_function"),
    ]

    for pattern, kind in patterns:
        for match in re.finditer(pattern, code, re.MULTILINE):
            name = match.group(1)
            args = match.group(2) if match.lastindex >= 2 else ""
            results.append({
                "type": kind,
                "name": name,
                "signature": f"{kind}: {name}({args})",
                "docstring": "",
                "file": file_path,
                "line": code[:match.start()].count("\n") + 1,
                "body_snippet": "",
            })

    ext = Path(file_path).suffix
    if ext in ('.sh', '.bash', '.zsh'):
        for pattern, kind in shell_patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                name = match.group(1)
                results.append({
                    "type": kind,
                    "name": name,
                    "signature": f"{name}()",
                    "docstring": "",
                    "file": file_path,
                    "line": code[:match.start()].count("\n") + 1,
                    "body_snippet": "",
                })

    return results


def extract_imports(code_lines: list, file_path: str) -> str:
    """Extract import statements from code lines."""
    code = "\n".join(code_lines)
    imports = []

    ext = Path(file_path).suffix

    if ext == '.py':
        for match in re.finditer(r'^(?:from\s+\S+\s+)?import\s+\S+(?:\s+as\s+\S+)?(?:\s*,\s*\S+)*', code, re.MULTILINE):
            imports.append(match.group(0).strip())
    elif ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs'):
        for match in re.finditer(r'^(?:import|export)\s+.*?(?:from\s+[\'\"][^\'\"]+[\'\"])', code, re.MULTILINE):
            imports.append(match.group(0).strip())
    elif ext in ('.sh', '.bash', '.zsh'):
        for match in re.finditer(r'^(?:source|\.)\s+\S+', code, re.MULTILINE):
            imports.append(match.group(0).strip())

    return "\n".join(imports[:20])  # Limit to 20 import lines


def extract_tags(name: str, docstring: str, file_path: str) -> list:
    """Auto-generate tags from context."""
    tags = set()
    ext = Path(file_path).suffix

    # Language tag
    lang_map = {'.py': 'python', '.js': 'javascript', '.jsx': 'react',
                '.ts': 'typescript', '.tsx': 'typescript+react',
                '.sh': 'shell', '.bash': 'shell', '.zsh': 'shell',
                '.md': 'markdown', '.yaml': 'yaml', '.yml': 'yaml',
                '.json': 'json', '.sql': 'sql'}
    if ext in lang_map:
        tags.add(lang_map[ext])

    # Tag from docstring key terms
    if docstring:
        keywords = ['test', 'api', 'auth', 'config', 'parse', 'convert',
                    'validate', 'format', 'transform', 'extract', 'load',
                    'save', 'export', 'import', 'create', 'delete', 'update']
        for kw in keywords:
            if kw in docstring.lower():
                tags.add(kw)

    # Tag from parent directory
    parent = Path(file_path).parent.name
    if parent and parent not in ('.', '..'):
        tags.add(parent)

    return sorted(tags)


def build_summary(item: dict) -> str:
    """Build a human-readable summary for ca learn."""
    parts = [f"[{item['type']}] {item['name']}"]
    if item['docstring']:
        parts.append(f"\n{item['docstring'][:200]}")
    parts.append(f"\nFile: {item['file']}:{item['line']}")
    return "".join(parts)


def register_with_ca(summary: str, tags: list, citation: str, dry_run: bool = False):
    """Call ca learn to register this code snippet."""
    tags_str = ", ".join(tags)
    cmd = [
        "ca", "learn", summary,
        "--type", "pattern",
        "--citation", citation,
    ]
    if tags_str:
        cmd.extend(["--trigger", tags_str])

    if dry_run:
        print(f"[DRY RUN] Would run: {' '.join(cmd)}")
        return

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ca learn failed: {result.stderr}", file=sys.stderr)
    else:
        print(f"Registered: {summary[:60]}...")


def main():
    args = parse_args()

    # Verify repo exists
    repo_path = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"Error: {repo_path} is not a git repository", file=sys.stderr)
        sys.exit(1)

    # Get diff
    diff_output = run_git_diff(repo_path, args.diff_ref)
    if not diff_output.strip():
        print("No changes detected in diff.")
        return

    # Parse diff
    files = parse_diff(diff_output)

    total_found = 0
    for file_path, hunks in files.items():
        ext = Path(file_path).suffix
        all_added = []
        for hunk in hunks:
            all_added.extend(hunk["added_lines"])

        if not all_added:
            continue

        # Extract code blocks
        if ext == '.py':
            items = extract_functions_from_python(all_added, file_path)
        elif ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.sh', '.bash', '.zsh'):
            items = extract_functions_from_general(all_added, file_path)
        else:
            continue  # Skip unsupported file types

        # Get imports for the file
        imports = extract_imports(all_added, file_path)

        for item in items:
            tags = extract_tags(item["name"], item["docstring"], file_path)
            summary = build_summary(item)
            citation = f"{file_path}:{item['line']}"

            if imports:
                summary += f"\nImports: {imports[:150]}"

            register_with_ca(summary, tags, citation, args.dry_run)
            total_found += 1

    print(f"\n=== Summary: {total_found} code items extracted and registered ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make the script executable**

Run:
```bash
chmod +x ~/code-library/scripts/extract_from_diff.py
```
Expected: No error.

- [ ] **Step 3: Test the script locally on this repo**

Run:
```bash
cd ~/code-library
python ~/code-library/scripts/extract_from_diff.py --repo . --dry-run
```
Expected: Script runs without error (may find no changes since initial commit).

- [ ] **Step 4: Commit**

Run:
```bash
cd ~/code-library
git add scripts/extract_from_diff.py
git commit -m "feat: add code extraction script (extract_from_diff.py)"
```
Expected: Committed.

---

### Task 3: Write search_code.py

**Files:**
- Create: `~/code-library/scripts/search_code.py`

- [ ] **Step 1: Write the script**

Create `~/code-library/scripts/search_code.py`:

```python
#!/usr/bin/env python3
"""
search_code.py — Search the code library for reusable code.

Usage:
    python search_code.py "pdf extraction"
    python search_code.py "auth middleware" --limit 5
"""

import argparse
import subprocess
import sys
import shutil


def parse_args():
    parser = argparse.ArgumentParser(description="Search the code library")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
    return parser.parse_args()


def search_ca(query: str, limit: int) -> str:
    """Run ca search and return results."""
    result = subprocess.run(
        ["ca", "search", query],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ca search failed: {result.stderr}", file=sys.stderr)
        return ""
    return result.stdout


def list_all(limit: int) -> str:
    """Run ca list to get all entries."""
    result = subprocess.run(
        ["ca", "list"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ca list failed: {result.stderr}", file=sys.stderr)
        return ""
    return result.stdout


def format_results(raw_output: str, query: str, limit: int) -> str:
    """Format ca output into a clean summary for agent context injection."""
    if not raw_output.strip():
        return ""

    lines = raw_output.strip().splitlines()
    header = f"## Code Library: Results for \"{query}\"\n"
    body_lines = []

    count = 0
    for line in lines:
        if count >= limit:
            break
        if line.strip():
            body_lines.append(f"- {line.strip()}")
            count += 1

    if not body_lines:
        return ""

    body = "\n".join(body_lines)
    return f"{header}\n{body}\n"


def main():
    args = parse_args()

    if not shutil.which("ca"):
        print("Error: 'ca' command not found. Is compound-agent installed?", file=sys.stderr)
        sys.exit(1)

    raw = search_ca(args.query, args.limit)

    if args.format == "json":
        print(raw)
    else:
        output = format_results(raw, args.query, args.limit)
        if output:
            print(output)
        else:
            print(f"No results found for \"{args.query}\".")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable**

Run:
```bash
chmod +x ~/code-library/scripts/search_code.py
```
Expected: No error.

- [ ] **Step 3: Quick test**

Run:
```bash
python ~/code-library/scripts/search_code.py "test"
```
Expected: Runs without error, returns empty results (library is new).

- [ ] **Step 4: Commit**

Run:
```bash
cd ~/code-library
git add scripts/search_code.py
git commit -m "feat: add code search script (search_code.py)"
```
Expected: Committed.

---

### Task 4: Install code-reuse skill for Reasonix

**Files:**
- Create: `C:\Users\user\.codex\skills\code-reuse\SKILL.md`

- [ ] **Step 1: Create skill directory**

Run:
```bash
mkdir -p "C:\Users\user\.codex\skills\code-reuse"
```
Expected: Directory created.

- [ ] **Step 2: Write the skill file**

Create `C:\Users\user\.codex\skills\code-reuse\SKILL.md`:

```markdown
# code-reuse — 代码复用库

自动搜索和注册可复用代码，避免重复造轮子。

## 触发条件

- Reasonix 启动新任务时，自动搜索已有代码
- 用户输入包含"找已有代码"、"有没有现成的"、"别重复造轮子"等关键词时主动触发
- 任务结束时自动注册新增代码

## 行为

### 任务开始时

```python
# 自动搜索当前任务相关的已有代码
python ~/code-library/scripts/search_code.py "<任务关键词>"
```

将搜索结果中的已有代码函数签名 + 摘要注入到当前 context。

### 写代码时

如果写了一个通用的函数/类/工具，记录：
- 文件路径
- 函数/类名
- 功能描述

### 任务结束时

自动扫描 git diff 提取新增代码：

```
python ~/code-library/scripts/extract_from_diff.py --repo <项目路径>
```

如果项目不是 git 仓库，跳过。

### 跨设备同步

定期运行 `cd ~/code-library && git add -A && git commit -m "sync" && git push`

## 注意事项

- 只提取函数/类级别的代码，不提取配置片段、注释改动、空行
- 已存在的代码不会重复注册（基于 hash 去重）
- 搜索不到结果不代表没有，尝试不同关键词
```

- [ ] **Step 3: Commit code-library changes**

Run:
```bash
cd ~/code-library
git add -A
git commit -m "feat: add code-reuse skill"
```
Expected: Committed.

---

### Task 5: Update AGENTS.md rules

**Files:**
- Modify: `C:\Users\user\AppData\Roaming\reasonix\AGENTS.md`

- [ ] **Step 1: Add code reuse rules to AGENTS.md**

Append to `C:\Users\user\AppData\Roaming\reasonix\AGENTS.md`:

```markdown
## 代码复用规则

> 目标：避免重复造轮子。已经写过的代码自动入库，下次直接复用。

### 规则 1：任务开始时搜索已有代码

在开始写任何代码之前，先运行：
```
python ~/code-library/scripts/search_code.py "<任务核心关键词>"
```
如果找到了匹配的代码，优先复用而不是重新写。

### 规则 2：写代码时记录

如果写了一个可复用的函数/类/工具（不只是这一项目用的胶水代码），记录：
- 文件路径
- 函数/类名和签名
- 功能描述（在 AGENTS.md 中临时记录供任务结束使用）

### 规则 3：任务结束时自动提取

每个任务完成后（最后一条消息之前），自动运行：
```
python ~/code-library/scripts/extract_from_diff.py --repo <当前项目根目录>
```
- 如果项目不是 git 仓库，跳过
- 如果没有新增代码，跳过

### 规则 4：定期跨设备同步

每天至少一次：
```
cd ~/code-library && git add -A && git commit -m "daily sync" && git push
```
以及在其他机器上 `git pull`。

### 规则 5：相关 memory 检查

- 已存 memory 中标记为 "code-reuse" 的内容优先引用
- 使用 `remember` 工具保存常见任务的代码引用
```

- [ ] **Step 2: Commit**

Run:
```bash
cd ~/code-library
git add -A
git commit -m "docs: add code reuse rules to AGENTS.md"
```
Expected: Committed.

---

### Task 6: Git Remote Setup & Initial Push

**Files:**
- Modify: `~/code-library/.git/config`

- [ ] **Step 1: Create a GitHub repository**

Visit https://github.com/new and create a repo named `code-library` (private or public as you prefer).

- [ ] **Step 2: Add remote and push**

Run:
```bash
cd ~/code-library
git remote add origin git@github.com:<YOUR_USERNAME>/code-library.git
git push -u origin main
```
Expected: Code library pushed to GitHub.

- [ ] **Step 3: Verify setup**

Run:
```bash
cd ~/code-library && git status
```
Expected: Clean working tree, nothing to commit.

---

### Task 7: End-to-End Test

- [ ] **Step 1: Create a test utility function**

Write a small test file:

```python
# /tmp/test_reuse.py
def greet(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
```

- [ ] **Step 2: Init a test git repo**

Run:
```bash
mkdir -p /tmp/test-reuse-repo
cd /tmp/test-reuse-repo
git init
cp /tmp/test_reuse.py .
git add test_reuse.py
git commit -m "init"
```

- [ ] **Step 3: Modify and commit**

Add a new function to `test_reuse.py`:

```python
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
```

Run:
```bash
cd /tmp/test-reuse-repo
echo '\ndef multiply(a: int, b: int) -> int:\n    """Multiply two numbers."""\n    return a * b' >> test_reuse.py
git add test_reuse.py
git commit -m "add multiply function"
```

- [ ] **Step 4: Run extraction**

Run:
```bash
python ~/code-library/scripts/extract_from_diff.py --repo /tmp/test-reuse-repo
```
Expected: Output shows "Registered: [function] multiply..." and "Summary: 1 code item extracted".

- [ ] **Step 5: Search for the registered code**

Run:
```bash
python ~/code-library/scripts/search_code.py "multiply"
```
Expected: Returns the registered multiply function entry.

- [ ] **Step 6: Clean up test**

Run:
```bash
rm -rf /tmp/test-reuse-repo /tmp/test_reuse.py
```
Expected: Clean.

- [ ] **Step 7: Commit the test**

Run:
```bash
cd ~/code-library
git add -A
git commit -m "chore: finalize code library setup"
```
Expected: Committed.
