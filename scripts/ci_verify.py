#!/usr/bin/env python3
"""Run the lightweight verification suite used by CI."""

from __future__ import annotations

import subprocess
import sys


QUICK_COMMANDS = [
    [sys.executable, "-m", "unittest", "tests.test_code_reuse_common", "tests.test_doctor", "tests.test_audit_index", "tests.test_check_consistency", "tests.test_install_hooks", "tests.test_ci_verify", "-v"],
    [sys.executable, "-m", "py_compile", "scripts/code_reuse_common.py", "scripts/doctor.py", "scripts/audit_index.py", "scripts/check_consistency.py", "scripts/install_hooks.py", "scripts/ci_verify.py"],
    [sys.executable, "scripts/check_consistency.py"],
]

FULL_COMMANDS = [
    *QUICK_COMMANDS,
    [sys.executable, "scripts/doctor.py", "--json"],
    [sys.executable, "scripts/audit_index.py"],
]


def commands_for(suite: str) -> list[list[str]]:
    if suite == "quick":
        return QUICK_COMMANDS
    if suite == "full":
        return FULL_COMMANDS
    raise ValueError(f"unknown verification suite: {suite}")


def run_commands(commands: list[list[str]], *, runner=subprocess.run) -> int:
    for cmd in commands:
        print(f">> {' '.join(cmd)}")
        result = runner(cmd)
        if result.returncode != 0:
            return result.returncode
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    suite = "full"
    if argv:
        if argv[0] not in ("--quick", "--full"):
            print("usage: ci_verify.py [--quick|--full]", file=sys.stderr)
            return 2
        suite = argv[0][2:]
    try:
        commands = commands_for(suite)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return run_commands(commands)


if __name__ == "__main__":
    raise SystemExit(main())
