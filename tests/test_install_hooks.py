import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import install_hooks


class InstallHooksTests(unittest.TestCase):
    def test_build_post_commit_hook_writes_extract_log(self):
        hook = install_hooks.build_post_commit_hook(
            extract_script="/kit/scripts/extract_from_diff.py",
            code_library_dir="/kit",
            log_file="/kit/logs/extract.log",
        )

        self.assertIn("LOG_FILE=", hook)
        self.assertIn("mkdir -p", hook)
        self.assertIn(">> \"$LOG_FILE\" 2>&1", hook)
        self.assertIn("--silent", hook)
        self.assertIn("exit 0", hook)


if __name__ == "__main__":
    unittest.main()
