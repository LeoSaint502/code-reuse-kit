import sys
import unittest
from unittest import mock

sys.path.insert(0, "scripts")

import ci_verify


class CIVerifyTests(unittest.TestCase):
    def test_quick_suite_is_subset_of_full_suite(self):
        quick = ci_verify.commands_for("quick")
        full = ci_verify.commands_for("full")

        self.assertLess(len(quick), len(full))
        for command in quick:
            self.assertIn(command, full)

    def test_unknown_suite_is_rejected(self):
        with self.assertRaises(ValueError):
            ci_verify.commands_for("everything")

    def test_run_commands_returns_first_failure_code(self):
        calls = []

        def fake_run(command):
            calls.append(command)
            return mock.Mock(returncode=7)

        code = ci_verify.run_commands([["python", "-m", "bad"], ["python", "-m", "later"]], runner=fake_run)

        self.assertEqual(code, 7)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
