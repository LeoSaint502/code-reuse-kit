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
| `tests/test_audit_index.py` | Index audit parsing, quality checks, and privacy sanitization. |
| `scripts/doctor.py` | Local installation health without exposing private values. |
| `scripts/audit_index.py` | JSONL index health, stale citation, duplicate, and low-quality insight checks. |
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
- A human can run `python scripts\audit_index.py` and inspect index quality without mutating the index.
- Tests prove that diagnostic output does not expose common private values.
- README files tell users where the doctor command fits.

## Later Backlog

- Consistency checks for README command drift.
- Hook execution log surfaced through the doctor command.
- JSON report consumption by future CI or agent review tools.
