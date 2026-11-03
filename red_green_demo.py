"""Automated offline red->green workshop demonstration.

Creates a deliberately faulty copy in a temporary directory, proves the
Unicode-byte regression catches it, and verifies the unchanged correct source.
No installation, network access, or modification of the original source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BUGGY_EXPRESSION = 'if len(payload.decode("utf-8", errors="replace")) > max_bytes:'
CORRECT_EXPRESSION = "if len(payload) > max_bytes:"
TARGET_TEST = "test_jsonl_utf8_guard.UTF8GuardTests.test_character_length_is_not_byte_length"


class DemoError(RuntimeError):
    """The red/green evidence could not be independently established."""


def _run_target(directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "-v", TARGET_TEST],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def demonstrate(directory: Path | None = None) -> dict[str, object]:
    root = directory or Path(__file__).resolve().parent
    source = root / "jsonl_utf8_guard.py"
    tests = root / "test_jsonl_utf8_guard.py"
    code = source.read_text(encoding="utf-8")
    test_code = tests.read_text(encoding="utf-8")
    if code.count(CORRECT_EXPRESSION) != 1:
        raise DemoError("Expected source guard is missing or ambiguous")
    if BUGGY_EXPRESSION in code:
        raise DemoError("Working source already contains the deliberate bug")
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix="jsonl-red-green-") as folder:
        temporary = Path(folder)
        (temporary / source.name).write_text(
            code.replace(CORRECT_EXPRESSION, BUGGY_EXPRESSION, 1),
            encoding="utf-8",
        )
        (temporary / tests.name).write_text(test_code, encoding="utf-8")

        red = _run_target(temporary)
        if red.returncode != 1 or "FAILED (failures=1)" not in red.stderr:
            raise DemoError(
                "Buggy copy did not produce the expected single regression failure"
            )

    green = _run_target(root)
    if green.returncode != 0 or "OK" not in green.stderr:
        raise DemoError("Correct source did not pass the regression test")
    if hashlib.sha256(source.read_bytes()).hexdigest() != original_hash:
        raise DemoError("Original source changed during the demonstration")

    return {
        "red": "expected regression failure",
        "green": "regression test passed",
        "original_source_preserved": True,
        "network_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        result = demonstrate()
    except (OSError, subprocess.TimeoutExpired, DemoError) as exc:
        print(f"Demo could not be verified: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
