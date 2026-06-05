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
| `scripts/audit_index.py` | Privacy-safe index quality audit. |
| `scripts/check_consistency.py` | Privacy-safe documentation consistency check. |
| `scripts/ci_verify.py` | Local mirror of the lightweight CI verification suite. |

## Verification

Run focused checks before reporting completion:

```powershell
python -m unittest tests.test_code_reuse_common -v
python -m unittest tests.test_doctor -v
python -m unittest tests.test_audit_index -v
python -m unittest tests.test_check_consistency -v
python -m py_compile scripts\code_reuse_common.py scripts\doctor.py scripts\audit_index.py scripts\check_consistency.py
python scripts\doctor.py
python scripts\audit_index.py
python scripts\check_consistency.py
python scripts\ci_verify.py
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
