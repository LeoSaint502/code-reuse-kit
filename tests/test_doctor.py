import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import doctor


class DoctorPrivacyTests(unittest.TestCase):
    def test_sanitize_email_token_and_url(self):
        raw = "user@example.com https://user:pass@example.test/path?token=abc#frag api_key=secret"
        safe = doctor.sanitize_value(raw, home=Path("/home/person"), root=Path("/repo"))
        self.assertNotIn("user@example.com", safe)
        self.assertNotIn("user:pass", safe)
        self.assertNotIn("token=abc", safe)
        self.assertNotIn("api_key=secret", safe)
        self.assertIn("<redacted-email>", safe)
        self.assertIn("<redacted-secret>", safe)
        self.assertIn("https://example.test/path", safe)

    def test_sanitize_home_path(self):
        safe = doctor.sanitize_value(
            "/home/person/code-reuse-kit/.claude/lessons/index.jsonl",
            home=Path("/home/person"),
            root=Path("/home/person/code-reuse-kit"),
        )
        self.assertEqual(safe, ".claude/lessons/index.jsonl")

    def test_status_serializes_to_json(self):
        item = doctor.status("git", "ok", "available", detail="/home/person/bin/git")
        payload = json.dumps(item, ensure_ascii=False)
        self.assertIn('"name": "git"', payload)
        self.assertIn('"level": "ok"', payload)

    def test_collect_report_uses_sanitized_paths(self):
        root = Path("/home/person/code-reuse-kit")
        with mock.patch("doctor.shutil.which", side_effect=lambda name: f"/home/person/bin/{name}" if name in {"git", "node", "ca"} else None):
            with mock.patch("doctor.run_text", return_value="/home/person/.git-hooks"):
                with mock.patch("doctor.Path.exists", return_value=True):
                    report = doctor.collect_report(root=root, home=Path("/home/person"))
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("/home/person", serialized)
        self.assertIn("~/", serialized)


if __name__ == "__main__":
    unittest.main()
