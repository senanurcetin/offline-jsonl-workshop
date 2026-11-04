"""Network-free regression tests for the JSONL UTF-8 workshop example."""
from __future__ import annotations

import io
import json
import random
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
    def test_deeply_nested_json_is_rejected_not_crashed(self):
        payload = b'{"a":' + b"[" * 30000 + b"]" * 30000 + b"}\n"
        with self.assertRaises(JSONLValidationError) as ctx:
            count_jsonl(io.BytesIO(payload))
        self.assertIn("Line 1", str(ctx.exception))
        self.assertNotIn("[[[", str(ctx.exception))


class BoundaryPropertyTests(unittest.TestCase):
    """Seeded, stdlib-only randomized checks around the validator's contracts."""

    SEED = 20261104

    def test_byte_limit_is_exact_for_random_unicode(self):
        rng = random.Random(self.SEED)
        alphabet = "aZ09 \u00e7\u011f\u0131\u015f\u20ac\u4e2d\U0001f680"
        for _ in range(200):
            text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
            record = json.dumps({"k": text}, ensure_ascii=False).encode("utf-8")
            for ending in (b"", b"\n", b"\r\n"):
                self.assertEqual(count_jsonl(io.BytesIO(record + ending), max_bytes=len(record)), 1)
                with self.assertRaises(JSONLValidationError):
                    count_jsonl(io.BytesIO(record + ending), max_bytes=len(record) - 1)

    def test_random_bytes_never_escape_validation_error(self):
        rng = random.Random(self.SEED + 1)
        base = b'{"id":1,"name":"workshop","tags":["a","b"],"n":{"x":2.5}}'
        for _ in range(500):
            data = bytearray(base)
            for _ in range(rng.randint(1, 4)):
                data[rng.randrange(len(data))] = rng.randrange(256)
            payload = bytes(data) + b"\n"
            try:
                count_jsonl(io.BytesIO(payload))
            except JSONLValidationError as exc:
                self.assertNotIn("workshop", str(exc))
                self.assertLess(len(str(exc)), 80)

    def test_nesting_depth_is_accepted_or_rejected_never_crashes(self):
        for depth in (1, 50, 400, 900, 1500, 5000, 30000):
            payload = b'{"a":' + b"[" * depth + b"]" * depth + b"}\n"
            try:
                self.assertEqual(count_jsonl(io.BytesIO(payload)), 1)
            except JSONLValidationError as exc:
                self.assertIn("Line 1", str(exc))

    def test_duplicate_keys_detected_at_random_positions(self):
        rng = random.Random(self.SEED + 2)
        for _ in range(100):
            keys = [f"k{i}" for i in range(rng.randint(2, 8))]
            dup = rng.choice(keys)
            pairs = [f'"{k}":{i}' for i, k in enumerate(keys)]
            pairs.insert(rng.randint(0, len(pairs)), f'"{dup}":99')
            payload = ("{" + ",".join(pairs) + "}\n").encode()
            with self.assertRaises(JSONLValidationError):
                count_jsonl(io.BytesIO(payload))


class CLIExitCodeTests(unittest.TestCase):
    SCRIPT = Path(__file__).with_name("jsonl_utf8_guard.py")

    def run_cli(self, *args, stdin=b""):
        return subprocess.run(
            [sys.executable, "-B", str(self.SCRIPT), *args],
            input=stdin, capture_output=True, timeout=10
        )

    def test_stdin_valid_input_exits_zero(self):
        proc = self.run_cli(stdin=b'{"id":1}\n{"id":2}\n')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["records"], 2)

    def test_invalid_json_exits_two_without_echoing_record(self):
        proc = self.run_cli(stdin=b'{"secret_token": oops}\n')
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertNotIn(b"secret_token", proc.stderr)

    def test_missing_input_file_exits_two(self):
        proc = self.run_cli("--input", "does-not-exist.jsonl")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")

    def test_non_positive_max_bytes_exits_two(self):
        proc = self.run_cli("--max-bytes", "0", stdin=b'{"id":1}\n')
        self.assertEqual(proc.returncode, 2)

    def test_oversized_record_exits_two(self):
        proc = self.run_cli("--max-bytes", "8", stdin=b'{"id":123456}\n')
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")

    def test_deeply_nested_json_exits_two_without_traceback(self):
        payload = b'{"a":' + b"[" * 30000 + b"]" * 30000 + b"}\n"
        proc = self.run_cli(stdin=payload)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertNotIn(b"Traceback", proc.stderr)



if __name__ == "__main__":
    unittest.main()
