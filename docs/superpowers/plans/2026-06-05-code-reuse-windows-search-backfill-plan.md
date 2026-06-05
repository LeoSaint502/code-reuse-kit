# Code Reuse Windows Search Backfill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Code Reuse Kit search and ingestion behavior on Windows and from non-library working directories, then document and publish the update.

**Architecture:** Add one small shared helper module in `scripts/` for `ca` discovery, UTF-8 output, canonical library cwd, summary normalization, citation formatting, and tag arguments. Update the three existing CLI scripts to call the helper while preserving their public command-line interfaces.

**Tech Stack:** Python 3 standard library, `unittest`, `subprocess`, `pathlib`, git, compound-agent CLI (`ca`).

---

## File Structure

- Create `scripts/code_reuse_common.py`: shared helpers for script behavior that must remain consistent.
- Create `tests/test_code_reuse_common.py`: unit tests for helper behavior with no external `ca` dependency.
- Modify `scripts/search_code.py`: use shared helper and run searches from the code library directory.
- Modify `scripts/backfill_code_library.py`: use shared helper, modern tags, safe citations, one-line summaries, and UTF-8 output.
- Modify `scripts/extract_from_diff.py`: use shared helper, modern tags, safe citations, one-line summaries, and library cwd for `ca learn`.
- Modify `README.md`: add Chinese update notes, troubleshooting, and Codex/GPT acknowledgements.
- Modify `README.en.md`: add English update notes, troubleshooting, and Codex/GPT acknowledgements.

### Task 1: Shared Helper Module

**Files:**
- Create: `scripts/code_reuse_common.py`
- Create: `tests/test_code_reuse_common.py`

- [ ] **Step 1: Write failing helper tests**

Create `tests/test_code_reuse_common.py`:

```python
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import code_reuse_common as common


class CodeReuseCommonTests(unittest.TestCase):
    def test_code_library_dir_defaults_to_home_code_reuse_kit(self):
        expected = Path.home() / "code-reuse-kit"
        self.assertEqual(common.code_library_dir(), expected)

    def test_code_library_dir_honors_environment_override(self):
        old = os.environ.get("CODE_REUSE_KIT_DIR")
        try:
            os.environ["CODE_REUSE_KIT_DIR"] = r"C:\tmp\kit"
            self.assertEqual(common.code_library_dir(), Path(r"C:\tmp\kit"))
        finally:
            if old is None:
                os.environ.pop("CODE_REUSE_KIT_DIR", None)
            else:
                os.environ["CODE_REUSE_KIT_DIR"] = old

    def test_normalize_summary_compacts_whitespace(self):
        summary = "  [function] build\n\nSignature: def build(x)\n  File: a.py:7  "
        self.assertEqual(
            common.normalize_summary(summary),
            "[function] build | Signature: def build(x) | File: a.py:7",
        )

    def test_make_citation_uses_relative_posix_path_and_line(self):
        citation = common.make_citation(
            Path("C:/Users/me/project/scripts/tool.py"),
            42,
            base_dir=Path("C:/Users/me/project"),
        )
        self.assertEqual(citation, "scripts/tool.py:42")

    def test_make_citation_strips_windows_drive_when_not_relative(self):
        citation = common.make_citation(Path("C:/Users/me/tool.py"), 3)
        self.assertNotIn("C:", citation)
        self.assertTrue(citation.endswith("tool.py:3"))

    def test_add_tags_args_uses_modern_tags_flag(self):
        cmd = ["ca", "learn", "summary"]
        common.add_tags_args(cmd, ["python", "docx"])
        self.assertEqual(cmd[-2:], ["--tags", "python, docx"])

    def test_add_tags_args_skips_empty_tags(self):
        cmd = ["ca", "learn", "summary"]
        common.add_tags_args(cmd, [])
        self.assertEqual(cmd, ["ca", "learn", "summary"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run helper tests and verify they fail**

Run: `python -m unittest tests.test_code_reuse_common -v`

Expected: FAIL or ERROR because `code_reuse_common` does not exist.

- [ ] **Step 3: Implement the shared helper**

Create `scripts/code_reuse_common.py`:

```python
#!/usr/bin/env python3
"""Shared helpers for Code Reuse Kit command-line scripts."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


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


def _safe_relative_path(file_path: Path, base_dir: Path | None) -> Path:
    expanded = file_path.expanduser()
    if base_dir is not None:
        try:
            return expanded.resolve().relative_to(base_dir.expanduser().resolve())
        except Exception:
            pass
    return Path(*expanded.parts[1:]) if expanded.drive else expanded


def make_citation(file_path: str | Path, line: int, base_dir: str | Path | None = None) -> str:
    base = Path(base_dir) if base_dir is not None else None
    safe_path = _safe_relative_path(Path(file_path), base)
    return f"{safe_path.as_posix()}:{line}"


def add_tags_args(cmd: list[str], tags: list[str]) -> None:
    clean_tags = [tag.strip() for tag in tags if tag and tag.strip()]
    if clean_tags:
        cmd.extend(["--tags", ", ".join(clean_tags)])


def run_ca(cmd: list[str], *, cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd or code_library_dir()),
        timeout=timeout,
    )
```

- [ ] **Step 4: Run helper tests and verify they pass**

Run: `python -m unittest tests.test_code_reuse_common -v`

Expected: all helper tests pass.

- [ ] **Step 5: Commit helper and tests**

```bash
git add scripts/code_reuse_common.py tests/test_code_reuse_common.py
git commit -m "test: cover code reuse common helpers"
```

### Task 2: Search Wrapper Fix

**Files:**
- Modify: `scripts/search_code.py`
- Test: `tests/test_code_reuse_common.py`

- [ ] **Step 1: Add failing search cwd test**

Append to `tests/test_code_reuse_common.py` inside `CodeReuseCommonTests`:

```python
    def test_run_ca_defaults_to_code_library_cwd(self):
        old = os.environ.get("CODE_REUSE_KIT_DIR")
        try:
            os.environ["CODE_REUSE_KIT_DIR"] = str(ROOT)
            result = common.run_ca(
                [sys.executable, "-c", "import os; print(os.getcwd())"]
            )
            self.assertEqual(Path(result.stdout.strip()), ROOT)
        finally:
            if old is None:
                os.environ.pop("CODE_REUSE_KIT_DIR", None)
            else:
                os.environ["CODE_REUSE_KIT_DIR"] = old
```

- [ ] **Step 2: Run the new test and verify it fails if `run_ca` cwd handling is absent**

Run: `python -m unittest tests.test_code_reuse_common.CodeReuseCommonTests.test_run_ca_defaults_to_code_library_cwd -v`

Expected: PASS if Task 1 already implemented `run_ca`; if it fails, update `run_ca` before continuing.

- [ ] **Step 3: Update `scripts/search_code.py`**

Replace local `find_ca()` and raw `subprocess.run` usage with:

```python
from code_reuse_common import code_library_dir, configure_utf8_stdio, find_ca, run_ca


def main():
    configure_utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=5)
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
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        if i >= args.limit:
            print("... (%d more results)" % (len(lines) - args.limit))
            break
        print("  - %s" % line)
```

- [ ] **Step 4: Run tests and py_compile**

Run: `python -m unittest tests.test_code_reuse_common -v`

Expected: PASS.

Run: `python -m py_compile scripts\search_code.py`

Expected: exit code 0.

- [ ] **Step 5: Commit search wrapper fix**

```bash
git add scripts/search_code.py tests/test_code_reuse_common.py
git commit -m "fix: search code library from wrapper"
```

### Task 3: Backfill Ingestion Fix

**Files:**
- Modify: `scripts/backfill_code_library.py`
- Test: `tests/test_code_reuse_common.py`

- [ ] **Step 1: Add failing summary content test**

Append to `tests/test_code_reuse_common.py` inside `CodeReuseCommonTests`:

```python
    def test_normalize_summary_preserves_searchable_fields(self):
        raw = "\n".join([
            "[function] repair_docx",
            "Signature: def repair_docx(path)",
            "Docstring: Fix citation superscript font",
            "File: scripts/repair.py:12",
        ])
        compact = common.normalize_summary(raw)
        self.assertIn("[function] repair_docx", compact)
        self.assertIn("Signature: def repair_docx(path)", compact)
        self.assertIn("Docstring: Fix citation superscript font", compact)
        self.assertIn("File: scripts/repair.py:12", compact)
        self.assertNotIn("\n", compact)
```

- [ ] **Step 2: Run the new test**

Run: `python -m unittest tests.test_code_reuse_common.CodeReuseCommonTests.test_normalize_summary_preserves_searchable_fields -v`

Expected: PASS if Task 1 normalization is correct; if it fails, adjust `normalize_summary`.

- [ ] **Step 3: Update `scripts/backfill_code_library.py` imports and startup**

Use:

```python
from code_reuse_common import (
    add_tags_args,
    code_library_dir,
    configure_utf8_stdio,
    find_ca,
    make_citation,
    normalize_summary,
    run_ca,
)

CODE_LIBRARY = code_library_dir()
```

Call `configure_utf8_stdio()` at the start of `main()`.

- [ ] **Step 4: Update backfill summary and citation**

Use:

```python
def build_summary(item: dict) -> str:
    parts = [
        f"[{item['kind']}] {item['name']}",
        f"Signature: {item['signature']}",
    ]
    if item["docstring"]:
        parts.append(f"Docstring: {item['docstring'][:200]}")
    parts.append(f"File: {item['file']}:{item['line']}")
    return normalize_summary("\n".join(parts))
```

Inside the registration loop:

```python
citation = make_citation(item["file"], item["line"], base_dir=scan_dir.parent)
```

- [ ] **Step 5: Update backfill registration**

Use:

```python
def register(summary: str, tags: list[str], citation: str, dry_run: bool) -> bool:
    ca_path = find_ca()
    tags_str = ", ".join(tags)
    cmd = [ca_path, "learn", summary, "--type", "lesson", "--citation", citation]
    add_tags_args(cmd, tags)

    if dry_run:
        print(f"  [DRY-RUN] {' '.join(cmd[:3])} \"{summary[:80]}...\"")
        return True

    result = run_ca(cmd, cwd=CODE_LIBRARY)
    if result.returncode != 0:
        print(f"  [FAIL] {result.stderr.strip()}", file=sys.stderr)
        return False
    return True
```

- [ ] **Step 6: Run tests and dry-run**

Run: `python -m unittest tests.test_code_reuse_common -v`

Expected: PASS.

Run: `python -m py_compile scripts\backfill_code_library.py`

Expected: exit code 0.

Run: `python scripts\backfill_code_library.py --dir scripts --pattern *.py --dry-run`

Expected: no UnicodeEncodeError, dry-run output includes `--tags` in command intent when tags exist, and citations are relative paths.

- [ ] **Step 7: Commit backfill fix**

```bash
git add scripts/backfill_code_library.py tests/test_code_reuse_common.py
git commit -m "fix: improve backfill ingestion on Windows"
```

### Task 4: Diff Extraction Fix

**Files:**
- Modify: `scripts/extract_from_diff.py`

- [ ] **Step 1: Reuse helper behavior as the failing contract**

Run: `python -m unittest tests.test_code_reuse_common -v`

Expected: PASS; these helper tests define the required tags, citation, summary, and cwd behavior for this task.

- [ ] **Step 2: Update `scripts/extract_from_diff.py` imports and startup**

Remove the local `find_ca()` and `_which()` helpers. Add:

```python
from code_reuse_common import (
    add_tags_args,
    code_library_dir,
    configure_utf8_stdio,
    find_ca,
    make_citation,
    normalize_summary,
    run_ca,
)
```

Call `configure_utf8_stdio()` at the start of `main()`.

- [ ] **Step 3: Update diff summary builder**

Use:

```python
def build_summary(item: dict, imports: str) -> str:
    parts = [
        f"[{item['type']}] {item['name']}",
        f"Signature: {item['signature']}",
    ]
    if item["docstring"]:
        parts.append(f"Docstring: {item['docstring'][:200]}")
    parts.append(f"File: {item['file']}:{item['line']}")
    if imports:
        parts.append(f"Imports: {imports[:200]}")
    return normalize_summary("\n".join(parts))
```

- [ ] **Step 4: Update diff registration**

Use:

```python
def register(ca: str, summary: str, tags: list[str], citation: str, dry_run: bool) -> bool:
    cmd = [ca, "learn", summary, "--type", "pattern", "--citation", citation]
    add_tags_args(cmd, tags)

    if dry_run:
        print(f"  [DRY-RUN] ca learn -> {item_type_from_summary(summary)} {name_from_summary(summary)}")
        return True

    r = run_ca(cmd, cwd=code_library_dir(), timeout=30)
    if r.returncode != 0:
        print(f"  [WARN] ca learn failed: {r.stderr.strip()[:120]}", file=sys.stderr)
        return False
    return True
```

Build citations in the main loop with:

```python
citation = make_citation(item["file"], item["line"], base_dir=repo)
```

- [ ] **Step 5: Run tests and dry-run**

Run: `python -m unittest tests.test_code_reuse_common -v`

Expected: PASS.

Run: `python -m py_compile scripts\extract_from_diff.py`

Expected: exit code 0.

Run: `python scripts\extract_from_diff.py --repo . --dry-run`

Expected: no UnicodeEncodeError and dry-run output if the latest commit contains extractable functions/classes; otherwise a clear skip/no extractable items message.

- [ ] **Step 6: Commit diff extraction fix**

```bash
git add scripts/extract_from_diff.py
git commit -m "fix: align diff extraction ingestion"
```

### Task 5: README Updates

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Add Chinese README update note and troubleshooting**

In `README.md`, add a section near the workflow/manual command area:

```markdown
## 更新说明：Windows 搜索与补录修复

- `scripts/search_code.py` 现在固定在 `~/code-reuse-kit` 中运行 `ca search`，从其他项目目录调用也会查同一个代码库。
- `scripts/backfill_code_library.py` 和 `scripts/extract_from_diff.py` 会使用 UTF-8 输出、`--tags` 标签参数、相对路径 citation，以及更完整的一行摘要。
- 非 Git 项目或历史代码可以继续用 `backfill_code_library.py --dry-run` 先预览，再正式补录。

## 故障排查

| 问题 | 处理方式 |
|------|----------|
| Windows 控制台出现 GBK/UnicodeEncodeError | 更新后脚本会自动配置 UTF-8；仍异常时先运行 `chcp 65001` 再重试。 |
| `ca search` 能搜到，但 `search_code.py` 搜不到 | 更新脚本后重试；包装脚本现在会固定到 `~/code-reuse-kit` 搜索。 |
| 当前项目不是 Git 仓库 | 使用 `python ~/code-reuse-kit/scripts/backfill_code_library.py --dir <目录>` 手动补录。 |
| Windows 路径里有 `C:\...` | 脚本会把 citation 转成相对路径，避免 `file:line` 解析被盘符冒号干扰。 |
```

In the acknowledgements section, add:

```markdown
| Codex and GPT | Implementation assistance | Helped diagnose Windows path/cwd issues, design the update, and verify script behavior. |
```

- [ ] **Step 2: Add English README update note and troubleshooting**

In `README.en.md`, add:

```markdown
## Update Notes: Windows Search And Backfill Fixes

- `scripts/search_code.py` now runs `ca search` from `~/code-reuse-kit`, so calls from other project directories search the same library.
- `scripts/backfill_code_library.py` and `scripts/extract_from_diff.py` now use UTF-8 output, `--tags`, relative-path citations, and richer one-line summaries.
- For non-git projects or existing code, use `backfill_code_library.py --dry-run` first, then run it without `--dry-run` when the preview looks right.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Windows console raises GBK/UnicodeEncodeError | Updated scripts configure UTF-8 output; if needed, run `chcp 65001` before retrying. |
| `ca search` finds entries but `search_code.py` does not | Update the wrapper and retry; it now searches from `~/code-reuse-kit`. |
| Current project is not a git repository | Run `python ~/code-reuse-kit/scripts/backfill_code_library.py --dir <directory>` to index it manually. |
| Windows `C:\...` citations parse incorrectly | Updated scripts convert citations to relative paths before appending `:line`. |
```

In the acknowledgements section, add:

```markdown
| Codex and GPT | Implementation assistance | Helped diagnose Windows path/cwd issues, design the update, and verify script behavior. |
```

- [ ] **Step 3: Review README rendering-sensitive syntax**

Run: `python - <<'PY'` is not suitable in PowerShell. Instead run:

```powershell
python -c "from pathlib import Path; [print(p, Path(p).read_text(encoding='utf-8').count('|')) for p in ['README.md','README.en.md']]"
```

Expected: command exits 0 and both files read as UTF-8.

- [ ] **Step 4: Commit README updates**

```bash
git add README.md README.en.md
git commit -m "docs: add Windows troubleshooting notes"
```

### Task 6: Final Verification And Push

**Files:**
- Verify all modified files.
- Push current branch to GitHub.

- [ ] **Step 1: Run full compile check**

Run:

```powershell
python -m py_compile scripts\code_reuse_common.py scripts\search_code.py scripts\backfill_code_library.py scripts\extract_from_diff.py
```

Expected: exit code 0.

- [ ] **Step 2: Run full unit tests**

Run:

```powershell
python -m unittest tests.test_code_reuse_common -v
```

Expected: all tests pass.

- [ ] **Step 3: Run search wrapper smoke test**

Run:

```powershell
python scripts\search_code.py "docx citation superscript font reference"
```

Expected: command exits 0. Results may depend on local `ca` index state, but the wrapper must not search from the caller's project directory.

- [ ] **Step 4: Run backfill dry-run smoke test**

Run:

```powershell
python scripts\backfill_code_library.py --dir scripts --pattern *.py --dry-run
```

Expected: command exits 0, no UnicodeEncodeError, dry-run command previews use `--tags` when tags exist.

- [ ] **Step 5: Run diff extraction dry-run smoke test**

Run:

```powershell
python scripts\extract_from_diff.py --repo . --dry-run
```

Expected: command exits 0 and reports either extracted items or that no extractable functions/classes were found.

- [ ] **Step 6: Inspect git status**

Run:

```powershell
git status --short --branch
```

Expected: only the pre-existing untracked `.agents/` remains uncommitted.

- [ ] **Step 7: Push to GitHub**

Run:

```powershell
git push origin master
```

Expected: push succeeds to `https://github.com/LeoSaint502/code-reuse-kit.git`.
