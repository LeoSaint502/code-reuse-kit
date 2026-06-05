#!/usr/bin/env python3
"""Run the lightweight verification suite used by CI."""

from __future__ import annotations

import subprocess
import sys


COMMANDS = [
    [sys.executable, "-m", "unittest", "tests.test_code_reuse_common", "tests.test_doctor", "tests.test_audit_index", "tests.test_check_consistency", "tests.test_install_hooks", "-v"],
    [sys.executable, "-m", "py_compile", "scripts/code_reuse_common.py", "scripts/doctor.py", "scripts/audit_index.py", "scripts/check_consistency.py", "scripts/install_hooks.py"],
    [sys.executable, "scripts/check_consistency.py"],
]


def main() -> int:
    for cmd in COMMANDS:
        print(f">> {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
