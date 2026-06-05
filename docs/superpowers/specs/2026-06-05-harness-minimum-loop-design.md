# Harness Minimum Loop Design

## Context

Code Reuse Kit already has several harness pieces: agent-facing skills, post-commit extraction, `compound-agent` search, focused Python tests, and superpowers design/plan documents. The missing piece is a small, explicit feedback loop that lets a human or agent quickly answer three questions:

- What is this repository's map?
- Which guides and sensors keep the workflow reliable?
- Is the local installation healthy without exposing personal information?

The comparison with `deusyu/harness-engineering` suggests that this project should stay a practical tool, not become a research archive. The upgrade should therefore add a minimal navigation and diagnostics layer rather than a broad platform rewrite.

## Goals

- Add a root `AGENTS.md` that acts as a concise repository map for coding agents.
- Add `docs/harness-matrix.md` to make the project's guides, sensors, feedback loops, and privacy boundaries explicit.
- Add `scripts/doctor.py` for local health diagnostics.
- Keep diagnostics privacy-safe by default.
- Add focused tests for privacy sanitization and doctor status behavior.
- Update README files with the Harness Engineering positioning and doctor usage.

## Privacy Requirements

All new diagnostics, docs, and examples must avoid leaking personal information. This is a hard requirement.

The implementation must not print or write:

- Local usernames.
- Email addresses.
- Full home-directory paths.
- API keys, tokens, passwords, or credential-like query strings.
- Authenticated remote URLs.

When a path is useful, output it in sanitized form:

- Home-relative paths become `~/...`.
- Repository-root-relative paths are preferred when possible.
- Other absolute paths are reduced to a drive or root plus basename when needed.

When a URL is useful, output only scheme, host, and path. Query strings, fragments, and embedded credentials are removed.

## Non-Goals

- Do not rewrite the project as a Python package.
- Do not replace `compound-agent`.
- Do not change the post-commit extraction behavior in this phase.
- Do not add index garbage collection or duplicate detection yet.
- Do not commit or alter the `.claude/lessons/index.jsonl` content.
- Do not store machine-specific diagnostics in the repository.

## Approach

Build the minimum loop in three layers:

1. **Guide layer:** `AGENTS.md` and `docs/harness-matrix.md`.
2. **Sensor layer:** `scripts/doctor.py` plus unit tests.
3. **User-facing layer:** README notes that explain how to run the health check.

The doctor script should use only Python standard library modules. It should be safe to run on a machine without `ca`, Node.js, or configured hooks. Missing dependencies are reported as actionable status lines, not crashes.

## `AGENTS.md`

The root map should stay short and point outward:

- Project purpose.
- Daily workflow.
- Core scripts and what each owns.
- Verification commands.
- Privacy rule for future agent work.
- Links to design, plan, and harness matrix documents.

It should not duplicate the full README.

## `docs/harness-matrix.md`

The matrix should classify existing and new project pieces:

- Guides: README, AGENTS, skills, agent instruction prompt, installer.
- Sensors: tests, dry-run commands, doctor, py_compile checks.
- Feedback loops: commit -> hook -> extract -> learn -> search -> reuse.
- Privacy boundaries: sanitized paths, sanitized URLs, credential redaction.
- Future backlog: index audit, consistency checks, hook observability.

## `scripts/doctor.py`

The doctor should report:

- Python version.
- Git availability.
- Node.js availability.
- `ca` availability.
- Canonical code library directory.
- Lesson index existence.
- Global git hooks path.
- Post-commit hook presence and Code Reuse Kit marker.
- Reasonix and Claude configuration presence where detectable.

It should support:

- Default human-readable output.
- `--json` machine-readable output.
- `--root <path>` for tests and advanced use.

Status levels:

- `ok`: requirement is satisfied.
- `warn`: optional or recoverable issue.
- `fail`: core workflow is likely broken.

## Testing

Add tests that do not depend on a real global installation:

- Privacy sanitization for paths, home paths, emails, token-like strings, and URLs.
- Doctor status object shape.
- Doctor behavior with mocked command lookup and mocked filesystem paths.
- JSON output serializability without raw private values.

Verification commands:

- `python -m unittest tests.test_doctor -v`
- `python -m unittest tests.test_code_reuse_common -v`
- `python -m py_compile scripts\doctor.py scripts\code_reuse_common.py`
- `python scripts\doctor.py`
- `python scripts\doctor.py --json`

## Documentation

Both README files should receive a small section:

- Code Reuse Kit as a practical Harness Engineering memory and reuse layer.
- `python scripts\doctor.py` as the first diagnostic command.
- A privacy note that diagnostics sanitize local paths and credentials by default.

## Acceptance Criteria

- A new agent can read `AGENTS.md` and know where to look next.
- The harness matrix identifies at least one guide and one sensor for each critical workflow.
- `doctor.py` exits successfully even when optional tools are missing.
- `doctor.py --json` emits valid JSON.
- Tests cover privacy sanitization.
- No new document or test fixture contains a real local username, personal email address, token, or full user home path.
