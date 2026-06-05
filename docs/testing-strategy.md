# Testing Strategy

## Purpose

This document defines how Code Reuse Kit verifies its Harness Engineering loop. Tests should prove behavior without depending on the current user's machine, private paths, or live `compound-agent` state.

## Test Layers

| Layer | Command | Purpose |
|---|---|---|
| Shared helpers | `python -m unittest tests.test_code_reuse_common -v` | Path handling, citation formatting, summary normalization, tag arguments, and `ca` cwd behavior. |
| Doctor diagnostics | `python -m unittest tests.test_doctor -v` | Privacy-safe local health reporting and hook log sanitization. |
| Index audit | `python -m unittest tests.test_audit_index -v` | JSONL parsing, stale citation detection, duplicate detection, low-quality insight detection, and text output limits. |
| Consistency checks | `python -m unittest tests.test_check_consistency -v` | Markdown path extraction, missing reference detection, required-script checks, and report formatting. |
| Hook installation | `python -m unittest tests.test_install_hooks -v` | Generated post-commit hook writes an extract log without blocking commits. |
| CI orchestration | `python -m unittest tests.test_ci_verify -v` | Quick/full verification suite selection and failure propagation. |

## Verification Commands

Use the quick suite while iterating:

```powershell
python scripts\ci_verify.py --quick
```

Use the full suite before committing, pushing, or claiming completion:

```powershell
python scripts\ci_verify.py --full
```

The full suite runs:

- All unit tests.
- Syntax checks for core scripts.
- Documentation consistency checks.
- `doctor.py --json`.
- `audit_index.py`.

## Privacy Requirements

Tests and diagnostics must not require or expose:

- Local usernames.
- Email addresses.
- Full home-directory paths.
- API keys, tokens, passwords, or credential-like query values.
- Authenticated remote URLs.

Use fake fixture values only when testing redaction behavior. Those fixtures must be paired with assertions that prove the raw value is absent from the final report.

## Machine Independence

Unit tests must not require:

- A real `ca` installation.
- A real global git hook.
- A real lesson index.
- Network access.
- A specific home directory.

Use temporary directories and mocks for local state. Smoke commands may inspect the current machine, but they must sanitize output before printing.

## CI Gate

GitHub Actions runs `.github/workflows/consistency.yml` on push and pull request. The workflow calls:

```bash
python scripts/ci_verify.py --full
```

This keeps local verification and remote verification aligned.

## Known Non-Blocking Findings

`python scripts\audit_index.py` currently reports existing index quality issues in older entries. These are useful findings, not test failures. Index cleanup should be handled as a separate data-maintenance phase because it changes the user's lesson index.
