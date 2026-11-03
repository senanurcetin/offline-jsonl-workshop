"""Offline regression tests for the red -> green workshop runner."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from red_green_demo import (
    BUGGY_EXPRESSION,
    CORRECT_EXPRESSION,
    DemoError,
    demonstrate,
)


class RedGreenDemoTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent
        self.source = self.root / "jsonl_utf8_guard.py"

    def test_complete_red_green_and_no_source_mutation(self):
        before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        result = demonstrate(self.root)
        self.assertEqual(result["red"], "expected regression failure")
        self.assertEqual(result["green"], "regression test passed")
        self.assertTrue(result["original_source_preserved"])
        self.assertEqual(result["network_calls"], 0)
        self.assertEqual(before, hashlib.sha256(self.source.read_bytes()).hexdigest())

    def test_requires_exactly_one_guard_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            directory.joinpath(self.source.name).write_text(
                self.source.read_text(encoding="utf-8").replace(
                    CORRECT_EXPRESSION, "# removed guard"
                ),
                encoding="utf-8",
            )
            directory.joinpath("test_jsonl_utf8_guard.py").write_text(
                (self.root / "test_jsonl_utf8_guard.py").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DemoError, "missing or ambiguous"):
                demonstrate(directory)

    def test_does_not_accept_already_broken_source(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            directory.joinpath(self.source.name).write_text(
                self.source.read_text(encoding="utf-8").replace(
                    CORRECT_EXPRESSION, BUGGY_EXPRESSION, 1
                ),
                encoding="utf-8",
            )
            directory.joinpath("test_jsonl_utf8_guard.py").write_text(
                (self.root / "test_jsonl_utf8_guard.py").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DemoError, "missing or ambiguous"):
                demonstrate(directory)

    def test_cli_summary_does_not_dump_payload(self):
        p = subprocess.run(
            [sys.executable, str(self.root / "red_green_demo.py")],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertTrue(data["original_source_preserved"])
        self.assertNotIn("🚀", p.stdout)
        self.assertNotIn("SECRET", p.stdout)


if __name__ == "__main__":
    unittest.main()
