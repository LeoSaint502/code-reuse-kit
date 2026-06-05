# Code Reuse Kit Windows Search And Backfill Fix Design

## Context

This update fixes pain points found while using Code Reuse Kit from a project outside the library repository. A manual backfill successfully wrote reusable DOCX repair entries into the code library, and plain `ca search` could find them. The wrapper script `scripts/search_code.py` still failed from other working directories because it invoked `ca search` in the caller's project instead of the code library directory.

The same review found Windows console encoding failures, outdated `ca learn --trigger` usage, ambiguous Windows absolute-path citations, and low-quality function summaries in the manual and post-commit ingestion paths.

## Goals

- Make `scripts/search_code.py` search the canonical code library directory regardless of the caller's current working directory.
- Make `scripts/backfill_code_library.py` reliable on Windows consoles and improve the quality of registered entries.
- Update `scripts/extract_from_diff.py` with the same tags, citation, summary, and working-directory rules as backfill.
- Add troubleshooting and update notes to both README files.
- Add acknowledgements for Codex and GPT in both README files.
- Save a clean version in git and push the completed update to GitHub.

## Non-Goals

- Do not rewrite the project as a formal Python package.
- Do not change the underlying `compound-agent` storage format.
- Do not alter unrelated local files such as untracked agent configuration.
- Do not commit existing lesson index changes unless they are part of this repository's current working tree and intentionally included by the user.

## Approach

Use a small shared helper module under `scripts/` and have the three scripts call it. This keeps behavior consistent without a broad package refactor.

The helper module will provide:

- `configure_utf8_stdio()` for Windows-safe terminal output.
- `code_library_dir()` for resolving the canonical code library path.
- `find_ca()` for locating the `ca` executable consistently.
- `normalize_summary()` for converting generated summaries into compact, searchable one-line text.
- `make_citation()` for converting file paths to `file:line` citations that avoid Windows drive-colon ambiguity.
- `add_tags_args()` for using the modern `--tags` argument.

## Script Changes

### `scripts/search_code.py`

- Configure UTF-8 output at startup.
- Run `ca search` with `cwd` set to the canonical code library directory.
- Keep the existing CLI shape: positional query plus `--limit`.
- Surface `ca search` stderr when the command fails instead of silently printing no results.

### `scripts/backfill_code_library.py`

- Configure UTF-8 output at startup.
- Use the shared `find_ca()` and code library directory.
- Replace `--trigger` with `--tags`.
- Build citations from paths relative to the scanned directory's parent when possible, then append the source line.
- Build one-line summaries that retain kind, name, signature, docstring preview, file, and line.
- Preserve `--dry-run` as a safe preview that shows the command intent without writing to the library.

### `scripts/extract_from_diff.py`

- Configure UTF-8 output at startup.
- Use the shared `find_ca()` and run `ca learn` in the canonical code library directory.
- Replace `--trigger` with `--tags`.
- Build one-line summaries with signature, docstring, file, line, and imports.
- Build citations through the shared Windows-safe citation helper.
- Keep existing post-commit and `--dry-run` behavior.

## Documentation Changes

Both `README.md` and `README.en.md` will get:

- An update note for the Windows/search/backfill fixes.
- Troubleshooting for Windows console encoding, wrapper search in the wrong directory, `ca search` versus `search_code.py`, manual backfill for non-git projects, and Windows citation paths.
- Acknowledgements that include Codex and GPT.

## Testing

The implementation should be verified with:

- `python -m py_compile scripts\code_reuse_common.py scripts\search_code.py scripts\backfill_code_library.py scripts\extract_from_diff.py`
- Unit or focused script tests for summary normalization, citation generation, tag argument construction, and code library cwd handling.
- `python scripts\search_code.py "docx citation superscript font reference"`
- `python scripts\backfill_code_library.py --dir scripts --pattern *.py --dry-run`
- `python scripts\extract_from_diff.py --repo . --dry-run`

If a command depends on local `ca` state or a sample path that is not available in the current workspace, the final report must say exactly which verification could not be run and why.

## Versioning And Release

- Commit the design spec separately before implementation.
- Commit implementation and documentation changes after verification.
- Include a concise update note in the commit message or README.
- Push the resulting branch to `origin`.
