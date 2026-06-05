import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_consistency


class CheckConsistencyTests(unittest.TestCase):
    def test_extracts_repo_relative_markdown_code_paths(self):
        text = "Read `scripts/tool.py`, `docs/harness-matrix.md`, and `~/code-reuse-kit/scripts/search_code.py`."

        refs = check_consistency.extract_markdown_paths(text)

        self.assertIn("scripts/tool.py", refs)
        self.assertIn("docs/harness-matrix.md", refs)
        self.assertNotIn("~/code-reuse-kit/scripts/search_code.py", refs)

    def test_report_detects_missing_markdown_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "README.en.md").write_text("Use `scripts/tool.py` and `scripts/missing.py`.\n", encoding="utf-8")

            report = check_consistency.check_consistency(root=root, docs=[root / "README.en.md"], required_scripts=[])

        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("missing-doc-reference", codes)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertIn("scripts/missing.py", serialized)

    def test_report_detects_missing_required_scripts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()

            report = check_consistency.check_consistency(
                root=root,
                docs=[],
                required_scripts=["scripts/doctor.py"],
            )

        self.assertEqual(report["summary"]["issues"], 1)
        self.assertEqual(report["issues"][0]["code"], "missing-required-script")

    def test_text_report_contains_counts_and_issue_codes(self):
        report = {
            "tool": "code-reuse-kit consistency check",
            "root": ".",
            "summary": {"documents_checked": 1, "required_scripts": 1, "issues": 1},
            "issues": [
                {
                    "level": "fail",
                    "code": "missing-required-script",
                    "path": "scripts/doctor.py",
                    "message": "required script is missing",
                }
            ],
        }

        text = check_consistency.format_text(report)

        self.assertIn("Code Reuse Kit Consistency Check", text)
        self.assertIn("missing-required-script", text)
        self.assertIn("issues: 1", text)


if __name__ == "__main__":
    unittest.main()
