# Code Reuse Kit

> **Never write the same function twice.** Automatically index reusable functions/classes from your git history and search them with AI agents.

A cross-device, cross-project code reuse toolkit. It extracts functions from your **git diff** after every commit, indexes them via **compound-agent** (`ca learn`), and makes them searchable by your AI coding agent — so you never reinvent the wheel.

---

## Quick Start

### Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| [Git](https://git-scm.com/downloads) | Any recent version | `git --version` |
| [Python](https://www.python.org/downloads/) | 3.8+ | `python --version` |
| [Node.js](https://nodejs.org/) (LTS) | 18+ | `node --version` |

### One-Click Install

```bash
git clone https://github.com/LeoSaint502/code-reuse-kit.git
cd code-reuse-kit
python scripts/install_code_library.py
```

The installer automatically:
1. Installs **compound-agent** (`ca`) — the semantic search engine
2. Installs a global **post-commit hook** — extracts new functions on every `git commit`
3. Configures your AI agent (if supported) for zero-ops auto-archiving

Takes about 1-3 minutes. That's it — you're ready to go.

---

## How It Works

```
You write code -> git commit
                       |
                       v
               +----------------------+
               | post-commit hook     |  <- auto-triggers after every commit
               | extracts new funcs   |
               +----------+-----------+
                          |
                          v
               +----------------------+
               | ca learn registers   |
               | index -> index.jsonl |
               +----------+-----------+
                          |
                          v
               +----------------------+
               | git push (manual)    |
               | sync to GitHub       |
               +----------+-----------+
                          |
                          v
               +------------------------------+
               | AI agent searches before     |
               | writing new code             |
               | found -> reuse / not found -> new |
               +------------------------------+
```

### What gets indexed?

Only **metadata cards** — not the full source code:

```
[function] extract_tables     <- function name
Extract tables from docx...   <- docstring (first 200 chars)
File: scripts/extract.py:42  <- file + line number
```

No code duplication, no sensitive business logic leakage, minimal token overhead.

---

## Harness Minimum Loop

Code Reuse Kit is a practical Harness Engineering component: a memory and reuse layer for coding agents. The minimum loop is:

1. Guides tell the agent where reusable code lives.
2. Hooks and ingestion scripts record reusable metadata.
3. Search retrieves prior work before new code is written.
4. Doctor diagnostics check the local harness without exposing private paths or credentials.
5. Index audit checks stale citations, duplicate entries, and low-quality metadata without modifying the index.
6. Consistency checks catch missing local docs and scripts before they drift.
7. CI runs the lightweight verification suite on push and pull request.

Run:

```bash
python scripts/doctor.py
```

For machine-readable output:

```bash
python scripts/doctor.py --json
```

Audit index quality:

```bash
python scripts/audit_index.py
python scripts/audit_index.py --json
```

Check documentation consistency:

```bash
python scripts/check_consistency.py
python scripts/check_consistency.py --json
```

Run the same lightweight suite used by CI:

```bash
python scripts/ci_verify.py --full
```

Diagnostic output is privacy-safe by default: home paths, emails, credential-like values, and authenticated URLs are sanitized.

---

## Usage Verification

### Method 1: Search the Index

```bash
cd ~/code-reuse-kit
python scripts/search_code.py "extract"
```

Example output:
```
## Results for "extract"
  - [info] Found 8 lesson(s):
  - [L1a533985493c34a5] [function] step_extract
  - [L6ebf9a976268f828] [function] _fallback_extract_direct
```

### Method 2: Inspect the Index File

```
~/code-reuse-kit/.claude/lessons/index.jsonl
```

Each line is one function/class record (name + description + location, not the code body).

### Method 3: Check AI Agent Responses

In projects following the rules, the agent will state:
- **"Reused [xxx] from code library"** — wheel was not reinvented
- **"No reusable code found, wrote from scratch"** — genuinely new functionality

### Method 4: GitHub Sync

The index file is git-tracked and pushed to GitHub. Anyone cloning the repo gets the full index.

### Current Index Stats (as of 2025-06-04)

| Source | Entries | Description |
|--------|:-------:|-------------|
| Project 1 scripts/ | 49 | analyze_bid / extract_tables / generate_docs, etc. |
| Project 2 | 3 | _apply_polish.py functions |
| **Total** | **52** | Growing with every commit |

---

## Daily Workflow

### With Reasonix (Recommended, Zero Ops)

The `/code-reuse-kit-save` skill is auto-installed. The agent handles everything — you just tell it what to code.

### With Claude Code

Global `CLAUDE.md` is configured during installation. Zero ops — the agent auto-archives at the end of every task.

### With Cursor / Copilot / Windsurf

Run once per project:
```bash
python ~/code-reuse-kit/scripts/install_agent_config.py --project .
```

After that, the agent auto-commits and archives at the end of every task.

---

## Backfill Existing Projects

Already have a project with lots of code? Index it all at once:

```bash
python ~/code-reuse-kit/scripts/backfill_code_library.py --dir /path/to/your/project/scripts
```

Scans all `.py` files, extracts every function/class definition, and registers them in the index.

---

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

---

## Manual Commands

```bash
# Search the index
python ~/code-reuse-kit/scripts/search_code.py "keywords"

# Manually extract (usually auto-triggered by hook)
python ~/code-reuse-kit/scripts/extract_from_diff.py --repo .

# Sync with remote
cd ~/code-reuse-kit && python scripts/sync.py

# Audit index quality
python ~/code-reuse-kit/scripts/audit_index.py

# Check documentation consistency
python ~/code-reuse-kit/scripts/check_consistency.py

# Run lightweight CI verification locally
python ~/code-reuse-kit/scripts/ci_verify.py --full

# Uninstall auto-config
python ~/code-reuse-kit/scripts/install_hooks.py --uninstall

# Reinstall / update
python ~/code-reuse-kit/scripts/install_code_library.py
```

---

## Compatible AI Agents

| Agent | Archiving Method | User Effort |
|-------|:----------------:|:-----------:|
| Reasonix | `/code-reuse-kit-save` skill | Zero |
| Claude Code | Global `~/.claude/CLAUDE.md` | Zero |
| Cursor | `.cursorrules` per project | One-time config |
| GitHub Copilot | `.github/copilot-instructions.md` per project | One-time config |
| Windsurf | `.windsurfrules` per project | One-time config |
| Any git-aware tool | post-commit hook | Manual `git add + commit` |

---

## Dependencies

| Dependency | Purpose |
|------------|---------|
| Git | Clone/sync repo + post-commit hook |
| Python 3 | Run extraction / search / sync scripts |
| Node.js / npm | Install compound-agent |
| compound-agent (`ca`) | Semantic search + knowledge management |

---

## Project Structure

```
~/code-reuse-kit/
  scripts/
    extract_from_diff.py       <- Extract code from git diff -> index
    search_code.py             <- Search the index
    backfill_code_library.py   <- * Backfill existing project code
    install_code_library.py    <- One-click installer (start here)
    install_hooks.py           <- Install global git hook + scheduler
    install_agent_config.py    <- Install AI agent auto-archive rules
    doctor.py                  <- Privacy-safe local health diagnostics
    audit_index.py             <- Privacy-safe index quality audit
    check_consistency.py       <- Privacy-safe documentation consistency check
    ci_verify.py               <- Local lightweight CI verification suite
    sync.py                    <- Daily sync (git pull + rebuild index)
  skills/
    code-reuse-kit-save.md     <- Reasonix auto-archive skill
  docs/
    agent-instructions/        <- Shared prompt templates for all agents
  .claude/lessons/             <- Accumulated index entries (git-tracked)
```

---

## Acknowledgements

This project builds upon and references the following open-source projects:

### Core Foundation

| Project | Role | What We Used |
|---------|------|-------------|
| **[compound-agent](https://github.com/Nathandela/compound-agent)** | Storage + search engine | JSONL+SQLite FTS5 storage, `ca learn/list/search` command design |
| **[claudecode-kb](https://github.com/tangero/claudecode-kb)** | Organizational pattern | Knowledge base structure (`patterns/snippets/troubleshooting/memory`) |
| Codex and GPT | Implementation assistance | Helped diagnose Windows path/cwd issues, design the update, and verify script behavior. |

### Researched but Not Directly Used

| Project | Why Not Used | What We Learned |
|---------|-------------|-----------------|
| **[reza](https://github.com/swebreza/reza)** | Aims to index entire project files, not snippets | SQLite + FTS5 storage architecture |
| **[Lumen](https://github.com/Sardor-M/lumen)** | Depends on MCP tools (Reasonix incompatible) | Cross-device encrypted sync concept |
| **[Alembic](https://github.com/GxFn/Alembic)** | Heavy MCP dependency | Tree-sitter AST for code pattern extraction |
| **[claudio-codex](https://github.com/Abraxas-365/claudio-codex)** | Code structure indexer, not reuse library | Function-level indexing granularity |

### Extraction Layer

`extract_from_diff.py` uses Python's `ast` module and compound-agent's `lesson` JSONL storage format.



### Platform & AI

| Platform | Role |
|----------|------|
| **[Reasonix](https://reasonix.ai)** | AI coding agent — primary execution environment, runs the /code-reuse-kit-save skill |
| **[DeepSeek](https://deepseek.com)** | Underlying LLM — powers code extraction, analysis, and search intelligence |

---


## License

MIT
