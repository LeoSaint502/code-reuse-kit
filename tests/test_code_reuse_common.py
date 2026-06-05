import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import code_reuse_common as common


class CodeReuseCommonTests(unittest.TestCase):
    def test_code_library_dir_defaults_to_home_code_reuse_kit(self):
        expected = Path.home() / "code-reuse-kit"
        self.assertEqual(common.code_library_dir(), expected)

    def test_code_library_dir_honors_environment_override(self):
        old = os.environ.get("CODE_REUSE_KIT_DIR")
        try:
            os.environ["CODE_REUSE_KIT_DIR"] = r"C:\tmp\kit"
            self.assertEqual(common.code_library_dir(), Path(r"C:\tmp\kit"))
        finally:
            if old is None:
                os.environ.pop("CODE_REUSE_KIT_DIR", None)
            else:
                os.environ["CODE_REUSE_KIT_DIR"] = old

    def test_normalize_summary_compacts_whitespace(self):
        summary = "  [function] build\n\nSignature: def build(x)\n  File: a.py:7  "
        self.assertEqual(
            common.normalize_summary(summary),
            "[function] build | Signature: def build(x) | File: a.py:7",
        )

    def test_make_citation_uses_relative_posix_path_and_line(self):
        citation = common.make_citation(
            Path("C:/Users/me/project/scripts/tool.py"),
            42,
            base_dir=Path("C:/Users/me/project"),
        )
        self.assertEqual(citation, "scripts/tool.py:42")

    def test_make_citation_strips_windows_drive_when_not_relative(self):
        citation = common.make_citation(Path("C:/Users/me/tool.py"), 3)
        self.assertNotIn("C:", citation)
        self.assertTrue(citation.endswith("tool.py:3"))

    def test_add_tags_args_uses_modern_tags_flag(self):
        cmd = ["ca", "learn", "summary"]
        common.add_tags_args(cmd, ["python", "docx"])
        self.assertEqual(cmd[-2:], ["--tags", "python, docx"])

    def test_add_tags_args_skips_empty_tags(self):
        cmd = ["ca", "learn", "summary"]
        common.add_tags_args(cmd, [])
        self.assertEqual(cmd, ["ca", "learn", "summary"])

    def test_run_ca_defaults_to_code_library_cwd(self):
        old = os.environ.get("CODE_REUSE_KIT_DIR")
        try:
            os.environ["CODE_REUSE_KIT_DIR"] = str(ROOT)
            result = common.run_ca(
                [sys.executable, "-c", "import os; print(os.getcwd())"]
            )
            self.assertEqual(Path(result.stdout.strip()), ROOT)
        finally:
            if old is None:
                os.environ.pop("CODE_REUSE_KIT_DIR", None)
            else:
                os.environ["CODE_REUSE_KIT_DIR"] = old

    def test_normalize_summary_preserves_searchable_fields(self):
        raw = "\n".join([
            "[function] repair_docx",
            "Signature: def repair_docx(path)",
            "Docstring: Fix citation superscript font",
            "File: scripts/repair.py:12",
        ])
        compact = common.normalize_summary(raw)
        self.assertIn("[function] repair_docx", compact)
        self.assertIn("Signature: def repair_docx(path)", compact)
        self.assertIn("Docstring: Fix citation superscript font", compact)
        self.assertIn("File: scripts/repair.py:12", compact)
        self.assertNotIn("\n", compact)


if __name__ == "__main__":
    unittest.main()
