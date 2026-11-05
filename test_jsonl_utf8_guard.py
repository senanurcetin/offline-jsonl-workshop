"""Network-free regression tests for the JSONL UTF-8 workshop example."""
from __future__ import annotations

import contextlib
import io
import json
import random
import re
import subprocess
import sys
import unittest
from pathlib import Path

import jsonl_utf8_guard
from jsonl_utf8_guard import DEFAULT_MAX_BYTES, JSONLValidationError, count_jsonl, iter_jsonl_records


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


def _escape_char(char, rng):
    """Spell one character as JSON \\uXXXX escapes (a surrogate pair if astral)."""
    code = ord(char)
    if code < 0x10000:
        units = [code]
    else:
        code -= 0x10000
        units = [0xD800 + (code >> 10), 0xDC00 + (code & 0x3FF)]
    return "".join(rng.choice(("\\u%04x", "\\u%04X")) % unit for unit in units)


def _has_duplicate_keys(text):
    """Independent oracle: does any JSON object in text repeat a decoded key?"""
    found = []

    def hook(pairs):
        keys = [key for key, _ in pairs]
        found.append(len(keys) != len(set(keys)))
        return dict(pairs)

    json.loads(text, object_pairs_hook=hook)
    return any(found)


class BoundaryEdgeCaseTests(unittest.TestCase):
    """Seeded boundary checks for issue #15 that complement BoundaryPropertyTests.

    Every outcome is either a record count or a JSONLValidationError; any other
    exception (for example RecursionError) fails the test. No rejection message
    may contain the SECRET marker embedded in the generated records.
    """

    SEED = 15_20261104
    SECRET = "S3CRET_MARKER"

    def outcome(self, payload, **kwargs):
        try:
            return count_jsonl(io.BytesIO(payload), **kwargs)
        except JSONLValidationError as exc:
            message = str(exc)
            self.assertNotIn(self.SECRET, message)
            return message

    def test_every_limit_around_a_multibyte_tail(self):
        rng = random.Random(self.SEED)
        for _ in range(40):
            prefix = "".join(rng.choice("ab z") for _ in range(rng.randint(0, 12)))
            char = rng.choice(("\u00e7", "\u20ac", "\U0001f680")).encode("utf-8")
            head = ('{"k":"' + self.SECRET + prefix).encode("utf-8")
            record = head + char + b'"}'
            ending = rng.choice((b"", b"\n", b"\r\n"))
            # limit-1, limit, limit+1 and every limit that falls inside the character.
            for limit in range(len(head), len(record) + 2):
                expected = 1 if limit >= len(record) else f"Line 1: exceeds {limit} UTF-8 bytes"
                self.assertEqual(self.outcome(record + ending, max_bytes=limit), expected)
            # A record cut inside the character fits the limit but is not valid UTF-8.
            for cut in range(1, len(char)):
                truncated = head + char[:cut] + b'"}'
                self.assertEqual(
                    self.outcome(truncated + ending, max_bytes=len(truncated)),
                    "Line 1: invalid UTF-8 encoding",
                )

    def test_invalid_utf8_sequences_match_strict_decoder(self):
        known_bad = (
            b"\x80", b"\xbf", b"\xc0\xaf", b"\xc1\xbf", b"\xe0\x80\xaf",
            b"\xed\xa0\x80", b"\xed\xbf\xbf", b"\xf4\x90\x80\x80", b"\xf5\x80\x80\x80",
            b"\xfe", b"\xff", b"\xe2\x82", b"\xf0\x9f\x9a",
        )
        rng = random.Random(self.SEED + 1)
        samples = list(known_bad)
        samples += [bytes(rng.randrange(0x80, 0x100) for _ in range(rng.randint(1, 4))) for _ in range(300)]
        for chunk in samples:
            payload = b'{"k":"' + self.SECRET.encode() + chunk + b'"}\n'
            try:
                payload.decode("utf-8")
            except UnicodeDecodeError:
                expected = "Line 1: invalid UTF-8 encoding"
            else:
                expected = 1
            if chunk in known_bad:
                self.assertEqual(expected, "Line 1: invalid UTF-8 encoding", chunk)
            self.assertEqual(self.outcome(payload), expected, chunk)

    def test_line_endings_and_blank_lines_keep_count_and_line_numbers(self):
        rng = random.Random(self.SEED + 2)
        blanks = (b"", b" ", b"\t", b" \t ")

        def join(lines):
            out = b""
            for index, line in enumerate(lines):
                ending = rng.choice((b"\n", b"\r\n"))
                if index == len(lines) - 1 and rng.random() < 0.5:
                    ending = b""
                out += line + ending
            return out

        for _ in range(150):
            lines, positions = [], []
            for i in range(rng.randint(1, 6)):
                lines += [rng.choice(blanks) for _ in range(rng.randint(0, 2))]
                positions.append(len(lines))
                lines.append(b'{"i":%d}' % i)
            lines += [rng.choice(blanks) for _ in range(rng.randint(0, 2))]
            self.assertEqual(self.outcome(join(lines)), len(positions))
            bad = rng.choice(positions)
            lines[bad] = b'{"i":'
            self.assertEqual(self.outcome(join(lines)), f"Line {bad + 1}: invalid JSON")

    def test_carriage_return_alone_is_not_a_record_separator(self):
        # Only LF (optionally preceded by CR) ends a record; CR-only files are one line.
        self.assertEqual(self.outcome(b'{"a":1}\r{"b":2}\r'), "Line 1: invalid JSON")
        self.assertEqual(self.outcome(b'{"a":1}\r'), 1)
        self.assertEqual(self.outcome(b"\r"), 0)
        self.assertEqual(self.outcome(b'{"a":1}\n\r'), 1)
        # A raw CR inside a string is a control character, not a line break.
        self.assertEqual(self.outcome(b'{"a":"x\ry"}\n'), "Line 1: invalid JSON")

    def test_unicode_escapes_and_surrogates_match_stdlib(self):
        rng = random.Random(self.SEED + 3)

        def units():
            kind = rng.randrange(5)
            high, low = rng.randint(0xD800, 0xDBFF), rng.randint(0xDC00, 0xDFFF)
            if kind == 0:
                return [rng.choice((rng.randint(0, 0xD7FF), rng.randint(0xE000, 0xFFFF)))]
            return ([high], [low], [high, low], [low, high])[kind - 1]

        for _ in range(300):
            parts = []
            for _ in range(rng.randint(1, 5)):
                parts.append(rng.choice(("", "a", "\u00e7")))
                parts += [rng.choice(("\\u%04x", "\\u%04X")) % unit for unit in units()]
            text = '{"v":"' + "".join(parts) + '"}'
            raw = text.encode("utf-8")
            self.assertEqual(list(iter_jsonl_records(io.BytesIO(raw + b"\n"))), [json.loads(text)])
            # The limit counts raw escape bytes (six per \\uXXXX), not decoded characters.
            self.assertEqual(self.outcome(raw, max_bytes=len(raw)), 1)
            self.assertEqual(
                self.outcome(raw, max_bytes=len(raw) - 1), f"Line 1: exceeds {len(raw) - 1} UTF-8 bytes"
            )

        for bad in ("\\u", "\\u1", "\\u12", "\\u123", "\\uGGGG", "\\x41", "\\U0001F680", "\\'", "\x00", "\x1f"):
            text = '{"v":"' + self.SECRET + bad + '"}'
            with self.assertRaises(ValueError):
                json.loads(text)
            self.assertEqual(self.outcome(text.encode("utf-8") + b"\n"), "Line 1: invalid JSON", bad)

    def test_escaped_spellings_of_a_key_collide_at_any_depth(self):
        rng = random.Random(self.SEED + 4)
        for _ in range(150):
            key = "".join(rng.choice("aZ_\u00e7\u20ac\U0001f680") for _ in range(rng.randint(1, 5)))
            spelled = "".join(_escape_char(c, rng) if rng.random() < 0.6 else c for c in key)
            depth = rng.randint(0, 6)
            for other, expected in ((spelled, "Line 1: invalid JSON"), (spelled + "x", 1)):
                inner = '{"%s":1,"%s":2}' % (key, other)
                text = '{"x":' * depth + inner + "}" * depth
                self.assertEqual(self.outcome(text.encode("utf-8") + b"\n"), expected, text)

    def test_random_nested_duplicates_match_oracle(self):
        rng = random.Random(self.SEED + 5)
        keys = ("a", self.SECRET, "\u00e7", "\U0001f680")

        def value(depth):
            roll = rng.random()
            if depth >= 3 or roll < 0.4:
                return rng.choice(("1", '"s"', "true", "null", "[]"))
            if roll < 0.7:
                return obj(depth + 1)
            return "[" + ",".join(value(depth + 1) for _ in range(rng.randint(0, 3))) + "]"

        def obj(depth):
            members = []
            for _ in range(rng.randint(0, 3)):
                key = rng.choice(keys)
                if rng.random() < 0.5:
                    key = "".join(_escape_char(c, rng) for c in key)
                members.append('"%s":%s' % (key, value(depth)))
            return "{" + ",".join(members) + "}"

        verdicts = set()
        for _ in range(400):
            text = obj(0)
            expected = "Line 1: invalid JSON" if _has_duplicate_keys(text) else 1
            verdicts.add(expected)
            self.assertEqual(self.outcome(text.encode("utf-8") + b"\n"), expected, text)
        self.assertEqual(verdicts, {1, "Line 1: invalid JSON"})

    def test_nesting_depth_around_recursion_limit_never_crashes(self):
        limit = sys.getrecursionlimit()
        depths = sorted({1, 2, 10, 100, *range(max(1, limit - 60), limit + 61, 15), 2 * limit, 30000})
        shapes = {
            "arrays": lambda d: b'{"a":' + b"[" * d + b"]" * d + b"}",
            "objects": lambda d: b'{"a":' * d + b"1" + b"}" * d,
            "mixed": lambda d: b'{"a":[' * d + b"0" + b"]}" * d,
            "duplicate_innermost": lambda d: b'{"a":' * d + b'{"k":1,"k":2}' + b"}" * d,
        }
        too_deep = "Line 1: JSON nesting is too deep"
        for name, build in shapes.items():
            shallow = "Line 1: invalid JSON" if name == "duplicate_innermost" else 1
            first_rejected = None
            for depth in depths:
                with self.subTest(shape=name, depth=depth):
                    payload = build(depth)
                    # Raise the byte limit so deep records reach the parser.
                    result = self.outcome(payload + b"\n", max_bytes=max(len(payload), DEFAULT_MAX_BYTES))
                    self.assertIn(result, (shallow, too_deep))
                    if depth <= 100:
                        self.assertEqual(result, shallow)
                    if result == too_deep and first_rejected is None:
                        first_rejected = depth
                    if first_rejected is not None:
                        self.assertEqual(result, too_deep, f"accepted after rejecting {first_rejected}")
            self.assertIsNotNone(first_rejected, name)

    def test_cli_rejections_exit_two_without_echo(self):
        script = Path(__file__).with_name("jsonl_utf8_guard.py")
        secret = self.SECRET.encode()
        # Oversize and deep-nesting CLI paths are covered by CLIExitCodeTests.
        cases = {
            "invalid_utf8": ([], b'{"k":"' + secret + b'\xed\xa0\x80"}\n'),
            "bad_escape": ([], b'{"k":"' + secret + b'\\u12"}\n'),
            "duplicate": ([], b'{"' + secret + b'":1,"' + secret + b'":2}\n'),
        }
        for name, (args, payload) in cases.items():
            with self.subTest(case=name):
                proc = subprocess.run(
                    [sys.executable, "-B", str(script), *args],
                    input=b'{"ok":1}\r\n' + payload, capture_output=True, timeout=10
                )
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertNotIn(secret, proc.stderr)
                self.assertNotIn(b"Traceback", proc.stderr)
                self.assertTrue(proc.stderr.startswith(b"Validation failed: Line 2: "), proc.stderr)


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

    def expected_version_line(self):
        return f"jsonl_utf8_guard {jsonl_utf8_guard.__version__}"

    def test_version_prints_one_line_and_exits_zero(self):
        proc = self.run_cli("--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, b"")
        lines = proc.stdout.decode("ascii").splitlines()
        self.assertEqual(lines, [self.expected_version_line()])

    def test_version_matches_pyproject(self):
        pyproject = Path(__file__).with_name("pyproject.toml")
        if not pyproject.exists():
            self.skipTest("pyproject.toml is not part of the standalone package")
        text = pyproject.read_text(encoding="utf-8")
        project = text.split("[project]", 1)[1].split("\n[", 1)[0]
        match = re.search(r'^version = "([^"]+)"$', project, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(jsonl_utf8_guard.__version__, match.group(1))

    def test_version_does_not_read_or_echo_stdin(self):
        proc = self.run_cli("--version", stdin=b'{"secret_token": "s3cr3t"}\n{oops\n')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.decode("ascii").splitlines(), [self.expected_version_line()])
        self.assertNotIn(b"s3cr3t", proc.stdout + proc.stderr)
        self.assertNotIn(b"records", proc.stdout)

    def test_version_works_without_stdin(self):
        proc = subprocess.run(
            [sys.executable, "-B", str(self.SCRIPT), "--version"],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=10
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.decode("ascii").splitlines(), [self.expected_version_line()])

    def test_version_works_with_closed_stdin(self):
        closed = io.TextIOWrapper(io.BytesIO(b'{"id":1}\n'))
        closed.close()
        out = io.StringIO()
        original_stdin = sys.stdin
        sys.stdin = closed
        try:
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
                jsonl_utf8_guard.main(["--version"])
        finally:
            sys.stdin = original_stdin
        self.assertEqual(ctx.exception.code, 0)
        self.assertEqual(out.getvalue().splitlines(), [self.expected_version_line()])

    def test_version_does_not_open_input_file(self):
        proc = self.run_cli("--input", "does-not-exist.jsonl", "--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.decode("ascii").splitlines(), [self.expected_version_line()])

    def test_version_wins_over_other_valid_options_like_argparse(self):
        for args in (("--version", "--max-bytes", "0"), ("--max-bytes", "0", "--version")):
            with self.subTest(args=args):
                proc = self.run_cli(*args, stdin=b'{"id":1}\n')
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.decode("ascii").splitlines(), [self.expected_version_line()])



if __name__ == "__main__":
    unittest.main()
