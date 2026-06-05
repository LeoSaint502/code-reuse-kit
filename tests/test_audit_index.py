import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audit_index


class AuditIndexTests(unittest.TestCase):
    def write_index(self, root: Path, lines: list[str]) -> Path:
        index = root / ".claude" / "lessons" / "index.jsonl"
        index.parent.mkdir(parents=True)
        index.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return index

    def test_audit_detects_malformed_stale_duplicate_and_low_quality_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "scripts" / "tool.py"
            source.parent.mkdir()
            source.write_text("def keep():\n    return True\n", encoding="utf-8")
            repeated = "[function] keep | Signature: def keep() | File: scripts/tool.py:1"
            index = self.write_index(
                root,
                [
                    json.dumps({"id": "L1", "insight": repeated, "citation": {"file": "scripts/tool.py", "line": 1}}),
                    json.dumps({"id": "L2", "insight": repeated, "citation": {"file": "scripts/tool.py", "line": 1}}),
                    json.dumps({"id": "L3", "insight": "tiny", "citation": {"file": "missing.py", "line": 1}}),
                    "{broken json",
                    json.dumps({"id": "L4", "insight": "[function] gone", "deleted": True, "citation": {"file": "missing.py", "line": 1}}),
                ],
            )

            report = audit_index.audit_index(index_path=index, root=root, home=root.parent)

        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("duplicate-insight", codes)
        self.assertIn("stale-citation", codes)
        self.assertIn("low-quality-insight", codes)
        self.assertIn("malformed-json", codes)
        self.assertEqual(report["summary"]["active_entries"], 3)
        self.assertEqual(report["summary"]["deleted_entries"], 1)

    def test_audit_report_sanitizes_private_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home" / "person"
            root = home / "code-reuse-kit"
            index = self.write_index(
                root,
                [
                    json.dumps(
                        {
                            "id": "L1",
                            "insight": "[function] leak | Signature: def leak()",
                            "citation": {"file": str(home / "private" / "secret.py"), "line": 1},
                        }
                    )
                ],
            )

            report = audit_index.audit_index(index_path=index, root=root, home=home)
            serialized = json.dumps(report, ensure_ascii=False)

        self.assertNotIn(str(home).replace("\\", "/"), serialized)
        self.assertIn("~/private/secret.py", serialized)

    def test_text_report_contains_counts_and_issue_codes(self):
        report = {
            "tool": "code-reuse-kit index audit",
            "index": ".claude/lessons/index.jsonl",
            "summary": {"total_lines": 1, "active_entries": 1, "deleted_entries": 0, "issues": 1},
            "issues": [
                {"level": "warn", "code": "missing-citation", "line": "1", "message": "entry has no citation"}
            ],
        }

        text = audit_index.format_text(report)

        self.assertIn("Code Reuse Kit Index Audit", text)
        self.assertIn("missing-citation", text)
        self.assertIn("issues: 1", text)

    def test_text_report_limits_displayed_issues(self):
        report = {
            "tool": "code-reuse-kit index audit",
            "index": ".claude/lessons/index.jsonl",
            "summary": {"total_lines": 3, "active_entries": 3, "deleted_entries": 0, "issues": 3},
            "issues": [
                {"level": "warn", "code": "issue-one", "line": "1", "message": "first"},
                {"level": "warn", "code": "issue-two", "line": "2", "message": "second"},
                {"level": "warn", "code": "issue-three", "line": "3", "message": "third"},
            ],
        }

        text = audit_index.format_text(report, max_issues=2)

        self.assertIn("issue-one", text)
        self.assertIn("issue-two", text)
        self.assertNotIn("issue-three", text)
        self.assertIn("1 more issue omitted", text)


if __name__ == "__main__":
    unittest.main()
