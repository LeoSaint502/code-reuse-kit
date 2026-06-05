# Harness Minimum Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal Harness Engineering feedback loop for Code Reuse Kit: an agent-readable repository map, an explicit guide/sensor matrix, a privacy-safe doctor command, focused tests, and README usage notes.

**Architecture:** Keep the change small and standard-library only. Add documentation guides at the repository root and under `docs/`, add a single diagnostic script under `scripts/`, and test privacy sanitization plus doctor status behavior without requiring a real global installation.

**Tech Stack:** Python 3 standard library, `unittest`, `subprocess`, `shutil`, `pathlib`, git, Node.js, compound-agent CLI (`ca`).

---

## File Structure

- Create `AGENTS.md`: short repository map for coding agents and privacy rules.
- Create `docs/harness-matrix.md`: guide/sensor/feedback-loop matrix for the current project.
- Create `scripts/doctor.py`: privacy-safe local health diagnostics.
- Create `tests/test_doctor.py`: focused tests for sanitization, status objects, and JSON-safe reporting.
- Modify `README.md`: Chinese Harness positioning and doctor usage note.
- Modify `README.en.md`: English Harness positioning and doctor usage note.

### Task 1: Agent Repository Map

**Files:**
- Create: `AGENTS.md`

- [ ] **Step 1: Create the root map**

Create `AGENTS.md`:

```markdown
# Code Reuse Kit Agent Map

## Purpose

Code Reuse Kit is a practical Harness Engineering memory and reuse layer for coding agents. It indexes reusable functions and classes from git history through `compound-agent`, then lets agents search before writing new code.

## Start Here

- Read `README.en.md` or `README.md` for user-facing setup and workflow.
- Read `docs/harness-matrix.md` for guides, sensors, feedback loops, and privacy boundaries.
- Read `docs/superpowers/specs/` and `docs/superpowers/plans/` for designed changes.

## Core Scripts

| Script | Responsibility |
|---|---|
| `scripts/search_code.py` | Search the canonical code reuse index. |
| `scripts/extract_from_diff.py` | Extract newly committed functions/classes and register them. |
| `scripts/backfill_code_library.py` | Manually index existing source files. |
| `scripts/install_code_library.py` | One-command installation flow. |
| `scripts/install_hooks.py` | Global post-commit hook setup. |
| `scripts/install_agent_config.py` | Agent-specific auto-archive instructions. |
| `scripts/sync.py` | Pull and rebuild the local code reuse index. |
| `scripts/doctor.py` | Privacy-safe local health diagnostics. |

## Verification

Run focused checks before reporting completion:

```powershell
python -m unittest tests.test_code_reuse_common -v
python -m unittest tests.test_doctor -v
python -m py_compile scripts\code_reuse_common.py scripts\doctor.py
python scripts\doctor.py
```

Use dry runs before writing to the code library:

```powershell
python scripts\backfill_code_library.py --dir scripts --pattern *.py --dry-run
python scripts\extract_from_diff.py --repo . --dry-run
```

## Privacy Rule

Do not print or commit personal information. Diagnostics and examples must avoid local usernames, email addresses, full home-directory paths, API keys, tokens, passwords, and authenticated remote URLs. Prefer `~/...`, repository-relative paths, and redacted URLs.

## Change Boundaries

- Keep scripts standard-library only unless a design document explicitly approves a dependency.
- Preserve existing CLI shapes unless the plan says otherwise.
- Do not modify `.claude/lessons/index.jsonl` unless the user explicitly asks to update the index.
- Do not rewrite this repository as a package during small harness upgrades.
```

- [ ] **Step 2: Review for privacy leaks**

Run:

```powershell
Select-String -Path AGENTS.md -Pattern 'Users\\|@|token|password|api[_-]?key|http.*@'
```

Expected: no matches for personal paths, emails, tokens, or authenticated URLs. The word `password` may appear only in the privacy rule.

- [ ] **Step 3: Commit**

```powershell
git add AGENTS.md
git commit -m "docs: add agent repository map"
```

### Task 2: Harness Matrix Document

**Files:**
- Create: `docs/harness-matrix.md`

- [ ] **Step 1: Create the guide/sensor matrix**

Create `docs/harness-matrix.md`:

```markdown
# Harness Matrix

## Purpose

This document makes the Code Reuse Kit harness explicit. A guide tells an agent what to do. A sensor checks whether the result is healthy. The project should keep at least one guide and one sensor around each critical workflow.

## Current Guides

| Guide | Role |
|---|---|
| `AGENTS.md` | Repository map and privacy boundary. |
| `README.md` / `README.en.md` | Human setup and workflow guide. |
| `skills/code-reuse-skill.md` | Search-before-building behavior for agents. |
| `skills/code-reuse-kit-save.md` | End-of-task archive behavior. |
| `docs/agent-instructions/code-reuse-kit-save-prompt.md` | Shared prompt installed into agent configs. |
| `scripts/install_code_library.py` | Bootstrap guide encoded as an installer. |
| `scripts/install_agent_config.py` | Agent configuration guide. |

## Current Sensors

| Sensor | Checks |
|---|---|
| `tests/test_code_reuse_common.py` | Shared path, citation, tag, summary, and command behavior. |
| `scripts/doctor.py` | Local installation health without exposing private values. |
| `python -m py_compile ...` | Syntax health for command-line scripts. |
| `--dry-run` flags | Preview ingestion before writing to the code library. |
| `ca search` through `scripts/search_code.py` | Confirms indexed entries are retrievable. |

## Primary Feedback Loop

1. Human or agent writes code.
2. Git commit triggers the global post-commit hook.
3. `scripts/extract_from_diff.py` extracts reusable definitions.
4. `ca learn` records compact metadata cards.
5. A later task invokes `scripts/search_code.py`.
6. The agent reuses an existing pattern or reports that no reusable entry was found.

## Privacy Boundary

Diagnostics must sanitize:

- Home-directory paths as `~/...`.
- Repository paths as paths relative to the repository root.
- Email addresses as `<redacted-email>`.
- Credential-looking values as `<redacted-secret>`.
- Authenticated or query-bearing URLs as scheme, host, and path only.

## Minimum Loop Acceptance

- A new agent can navigate from `AGENTS.md`.
- A human can run `python scripts\doctor.py` and get actionable installation health.
- Tests prove that diagnostic output does not expose common private values.
- README files tell users where the doctor command fits.

## Later Backlog

- Index audit for stale citations and duplicate metadata cards.
- Consistency checks for README command drift.
- Hook execution log surfaced through the doctor command.
- JSON report consumption by future CI or agent review tools.
```

- [ ] **Step 2: Review for scope**

Run:

```powershell
Select-String -Path docs\harness-matrix.md -Pattern 'TODO|TBD|Users\\|@example|token=|password='
```

Expected: no `TODO` or `TBD`; no real personal information.

- [ ] **Step 3: Commit**

```powershell
git add docs/harness-matrix.md
git commit -m "docs: describe harness guide sensor matrix"
```

### Task 3: Privacy-Safe Doctor Tests

**Files:**
- Create: `tests/test_doctor.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_doctor.py`:

```python
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import doctor


class DoctorPrivacyTests(unittest.TestCase):
    def test_sanitize_email_token_and_url(self):
        raw = "user@example.com https://user:pass@example.test/path?token=abc#frag api_key=secret"
        safe = doctor.sanitize_value(raw, home=Path("/home/person"), root=Path("/repo"))
        self.assertNotIn("user@example.com", safe)
        self.assertNotIn("user:pass", safe)
        self.assertNotIn("token=abc", safe)
        self.assertNotIn("api_key=secret", safe)
        self.assertIn("<redacted-email>", safe)
        self.assertIn("<redacted-secret>", safe)
        self.assertIn("https://example.test/path", safe)

    def test_sanitize_home_path(self):
        safe = doctor.sanitize_value(
            "/home/person/code-reuse-kit/.claude/lessons/index.jsonl",
            home=Path("/home/person"),
            root=Path("/home/person/code-reuse-kit"),
        )
        self.assertEqual(safe, ".claude/lessons/index.jsonl")

    def test_status_serializes_to_json(self):
        item = doctor.status("git", "ok", "available", detail="/home/person/bin/git")
        payload = json.dumps(item, ensure_ascii=False)
        self.assertIn('"name": "git"', payload)
        self.assertIn('"level": "ok"', payload)

    def test_collect_report_uses_sanitized_paths(self):
        root = Path("/home/person/code-reuse-kit")
        with mock.patch("doctor.shutil.which", side_effect=lambda name: f"/home/person/bin/{name}" if name in {"git", "node", "ca"} else None):
            with mock.patch("doctor.run_text", return_value="/home/person/.git-hooks"):
                with mock.patch("doctor.Path.exists", return_value=True):
                    report = doctor.collect_report(root=root, home=Path("/home/person"))
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("/home/person", serialized)
        self.assertIn("~/", serialized)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m unittest tests.test_doctor -v
```

Expected: ERROR because `scripts/doctor.py` does not exist or lacks the tested functions.

- [ ] **Step 3: Commit tests**

```powershell
git add tests/test_doctor.py
git commit -m "test: cover privacy safe doctor diagnostics"
```

### Task 4: Doctor Implementation

**Files:**
- Create: `scripts/doctor.py`

- [ ] **Step 1: Implement doctor script**

Create `scripts/doctor.py`:

```python
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
    parser.add_argument("--root", default=None, help="Repository root to inspect. Defaults to this script's parent repository.")
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


def sanitize_value(value: object, *, home: Path | None = None, root: Path | None = None) -> str:
    text = str(value)
    text = sanitize_url(text)
    text = EMAIL_RE.sub("<redacted-email>", text)
    text = SECRET_RE.sub(lambda m: f"{m.group(1)}=<redacted-secret>", text)

    home = (home or Path.home()).resolve()
    root = root.resolve() if root else None

    normalized = text.replace("\\", "/")
    if root:
        root_text = str(root).replace("\\", "/")
        if normalized.startswith(root_text + "/"):
            normalized = normalized[len(root_text) + 1 :]
    home_text = str(home).replace("\\", "/")
    if normalized == home_text:
        normalized = "~"
    elif normalized.startswith(home_text + "/"):
        normalized = "~/" + normalized[len(home_text) + 1 :]
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
        checks.append(sanitize_item(status("post-commit-hook", level, "found" if hook_file.exists() else "missing", hook_file), home=home, root=root))
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
            status("reasonix-agents", "ok" if reasonix_found else "warn", "found" if reasonix_found else "not found", reasonix_found or reasonix_candidates[0]),
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
```

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m unittest tests.test_doctor -v
```

Expected: PASS.

- [ ] **Step 3: Run compile check**

Run:

```powershell
python -m py_compile scripts\doctor.py
```

Expected: no output and exit 0.

- [ ] **Step 4: Commit doctor implementation**

```powershell
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat: add privacy safe doctor diagnostics"
```

### Task 5: README Updates

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Update English README**

In `README.en.md`, add this section after "How It Works":

```markdown
## Harness Minimum Loop

Code Reuse Kit is a practical Harness Engineering component: a memory and reuse layer for coding agents. The minimum loop is:

1. Guides tell the agent where reusable code lives.
2. Hooks and ingestion scripts record reusable metadata.
3. Search retrieves prior work before new code is written.
4. Doctor diagnostics check the local harness without exposing private paths or credentials.

Run:

```bash
python scripts/doctor.py
```

For machine-readable output:

```bash
python scripts/doctor.py --json
```

Diagnostic output is privacy-safe by default: home paths, emails, credential-like values, and authenticated URLs are sanitized.
```

- [ ] **Step 2: Update Chinese README**

In `README.md`, add the matching Chinese section near the workflow explanation:

```markdown
## Harness 最小闭环

Code Reuse Kit 是一个落地型 Harness Engineering 组件：它为 coding agent 提供代码记忆与复用层。最小闭环是：

1. Guides 告诉 agent 去哪里找可复用代码。
2. Hook 和入库脚本记录可复用元数据。
3. Search 在写新代码前找回历史方案。
4. Doctor 诊断本地 harness 状态，同时避免泄露个人路径或凭据。

运行：

```bash
python scripts/doctor.py
```

机器可读输出：

```bash
python scripts/doctor.py --json
```

诊断输出默认做隐私保护：会脱敏 home 路径、邮箱、疑似凭据和值带认证信息的 URL。
```

- [ ] **Step 3: Search for accidental private data**

Run:

```powershell
Select-String -Path README.md,README.en.md -Pattern 'Users\\|api[_-]?key=|token=|password=|https?://[^/\\s]+@'
```

Expected: no matches from the new sections.

- [ ] **Step 4: Commit README updates**

```powershell
git add README.md README.en.md
git commit -m "docs: add harness minimum loop usage"
```

### Task 6: Final Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run all focused tests**

Run:

```powershell
python -m unittest tests.test_code_reuse_common -v
python -m unittest tests.test_doctor -v
```

Expected: both test modules pass.

- [ ] **Step 2: Run compile checks**

Run:

```powershell
python -m py_compile scripts\code_reuse_common.py scripts\doctor.py
```

Expected: no output and exit 0.

- [ ] **Step 3: Run doctor text output**

Run:

```powershell
python scripts\doctor.py
```

Expected: exits 0 and prints `Code Reuse Kit Doctor` with sanitized paths.

- [ ] **Step 4: Run doctor JSON output**

Run:

```powershell
python scripts\doctor.py --json
```

Expected: exits 0 and prints valid JSON with `tool`, `root`, and `checks`.

- [ ] **Step 5: Run privacy scan on changed docs and tests**

Run:

```powershell
Select-String -Path AGENTS.md,docs\harness-matrix.md,docs\superpowers\specs\2026-06-05-harness-minimum-loop-design.md,docs\superpowers\plans\2026-06-05-harness-minimum-loop-plan.md,README.md,README.en.md,tests\test_doctor.py,scripts\doctor.py -Pattern 'Users\\|user@example.com|api_key=secret|token=abc|password=|https?://[^/\s]+@'
```

Expected: only test fixture strings in `tests\test_doctor.py` may match `user@example.com`, `api_key=secret`, or `token=abc`; no real personal values appear.

- [ ] **Step 6: Inspect git status**

Run:

```powershell
git status --short
```

Expected: only intentional files from this plan are modified or added, plus any pre-existing unrelated untracked files.

---

## Self-Review

- Spec coverage: root map, harness matrix, doctor diagnostics, privacy-safe output, tests, and README updates are covered.
- Placeholder scan: no `TODO`, `TBD`, or "implement later" steps are used.
- Type consistency: `doctor.sanitize_value`, `doctor.status`, `doctor.run_text`, and `doctor.collect_report` are defined before tests rely on them.
- Privacy coverage: plan includes sanitization behavior, tests, and final scans.
