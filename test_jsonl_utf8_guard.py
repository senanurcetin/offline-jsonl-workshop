"""Network-free regression tests for the JSONL UTF-8 workshop example."""
from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

from jsonl_utf8_guard import JSONLValidationError, count_jsonl


class UTF8GuardTests(unittest.TestCase):
    def test_basic_object(self):
        self.assertEqual(count_jsonl(io.BytesIO(b'{"type":"user"}\n')), 1)

    def test_exact_byte_boundary(self):
        record = '{"text":"🚀"}'.encode("utf-8")
        self.assertEqual(count_jsonl(io.BytesIO(record + b"\n"), max_bytes=len(record)), 1)

    def test_character_length_is_not_byte_length(self):
        record = '{"text":"🚀"}'.encode("utf-8")
        self.assertGreater(len(record), len(record.decode("utf-8")))
        with self.assertRaisesRegex(JSONLValidationError, "exceeds"):
            count_jsonl(io.BytesIO(record + b"\n"), max_bytes=len(record) - 1)

    def test_crlf_excluded_from_payload_limit(self):
        record = b'{"x":true}'
        self.assertEqual(count_jsonl(io.BytesIO(record + b"\r\n"), max_bytes=len(record)), 1)

    def test_no_final_newline(self):
        self.assertEqual(count_jsonl(io.BytesIO(b'{"x":1}')), 1)

    def test_blank_lines_ignored(self):
        self.assertEqual(count_jsonl(io.BytesIO(b'\r\n\n{"x":1}\n\n')), 1)

    def test_invalid_utf8_does_not_leak_input(self):
        try:
            count_jsonl(io.BytesIO(b'{"password":"SECRET"\xff}\n'))
        except JSONLValidationError as exc:
            self.assertIn("invalid UTF-8", str(exc))
            self.assertNotIn("SECRET", str(exc))
        else:
            self.fail("Invalid UTF-8 was not rejected")

    def test_invalid_json(self):
        with self.assertRaisesRegex(JSONLValidationError, "Line 1: invalid JSON"):
            count_jsonl(io.BytesIO(b'{"x":\n'))

    def test_top_level_array_not_allowed(self):
        with self.assertRaisesRegex(JSONLValidationError, "expected a JSON object"):
            count_jsonl(io.BytesIO(b'[1,2]\n'))

    def test_non_finite_number_disallowed(self):
        with self.assertRaisesRegex(JSONLValidationError, "invalid JSON"):
            count_jsonl(io.BytesIO(b'{"x":NaN}\n'))

    def test_validate_positive_max_bytes(self):
        for bad in (0, -1, True, 1.5):
            with self.subTest(max_bytes=bad), self.assertRaises(ValueError):
                count_jsonl(io.BytesIO(b'{}\n'), max_bytes=bad)

    def test_reports_physical_line_number(self):
        with self.assertRaisesRegex(JSONLValidationError, "Line 3:"):
            count_jsonl(io.BytesIO(b'{}\n\nnot-json\n'))

    def test_chunk_size_is_bounded(self):
        class Spy(io.BytesIO):
            def __init__(self, payload):
                super().__init__(payload)
                self.sizes = []

            def readline(self, size=-1):
                self.sizes.append(size)
                return super().readline(size)

        source = Spy(b'{"x":"very very long"}\n')
        with self.assertRaises(JSONLValidationError):
            count_jsonl(source, max_bytes=5)
        self.assertEqual(source.sizes, [8])

    def test_duplicate_root_keys_are_rejected(self):
        payload = b'{"role":"viewer","role":"admin"}\n'
        with self.assertRaisesRegex(JSONLValidationError, "Line 1: invalid JSON"):
            count_jsonl(io.BytesIO(payload))

    def test_duplicate_nested_keys_are_rejected(self):
        payload = b'{"meta":{"enabled":true,"enabled":false}}\n'
        with self.assertRaisesRegex(JSONLValidationError, "Line 1: invalid JSON"):
            count_jsonl(io.BytesIO(payload))

    def test_escaped_and_literal_key_collisions_are_rejected(self):
        payload = b'{"id":1,"\\u0069d":2}\n'
        with self.assertRaisesRegex(JSONLValidationError, "Line 1: invalid JSON"):
            count_jsonl(io.BytesIO(payload))

    def test_duplicate_key_name_not_logged(self):
        payload = b'{"SECRET_KEY":1,"SECRET_KEY":2}\n'
        with self.assertRaises(JSONLValidationError) as caught:
            count_jsonl(io.BytesIO(payload))
        self.assertNotIn("SECRET_KEY", str(caught.exception))

    def test_distinct_nested_and_root_keys_still_valid(self):
        payload = b'{"id":1,"meta":{"id":2}}\n'
        self.assertEqual(count_jsonl(io.BytesIO(payload)), 1)

    def test_cli_output_never_echoes_records(self):
        script = Path(__file__).with_name("jsonl_utf8_guard.py")
        sample = Path(__file__).with_name("sample_events.jsonl")
        proc = subprocess.run(
            [sys.executable, str(script), "--input", str(sample)],
            text=True, capture_output=True, timeout=10
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["records"], 2)
        self.assertNotIn("workshop", proc.stdout)


if __name__ == "__main__":
    unittest.main()
