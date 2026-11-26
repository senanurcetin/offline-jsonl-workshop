"""Dependency-free JSONL verifier for an offline Claude Code workshop.

Measures raw UTF-8 bytes rather than the number of Unicode characters.
The command never prints or uploads input records.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, BinaryIO, Optional

# Keep in sync with [project].version in pyproject.toml (enforced by a unit test).
# A constant, not importlib.metadata, so the script also works from a clone or ZIP.
__version__ = "0.3.0"

DEFAULT_MAX_BYTES = 65_536
MAX_REPORTED_ERRORS = 100
UTF8_BOM = b"\xef\xbb\xbf"
_DRAIN_CHUNK = 4_096


class JSONLValidationError(ValueError):
    """An invalid input record, identified by its physical line number."""

    def __init__(self, line_number: int, reason: str) -> None:
        super().__init__(f"Line {line_number}: {reason}")
        self.line_number = line_number
        self.reason = reason


class _DuplicateKeyError(ValueError):
    """Raised by the object hook; deliberately carries no key or value."""


class _NonFiniteNumberError(ValueError):
    """Raised by parse_constant for NaN, Infinity and -Infinity."""


def _reject_json_constant(value: str) -> None:
    raise _NonFiniteNumberError("Non-finite JSON numbers are not supported")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous JSON object members without echoing sensitive names."""
    data: dict[str, Any] = {}
    for key, value in pairs:
        if key in data:
            raise _DuplicateKeyError("Duplicate JSON object key")
        data[key] = value
    return data


def _check_max_bytes(max_bytes: int) -> None:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
        raise ValueError("max_bytes must be a positive integer")


def _check_max_errors(max_errors: int) -> None:
    if (
        not isinstance(max_errors, int)
        or isinstance(max_errors, bool)
        or max_errors < 1
    ):
        raise ValueError("max_errors must be a positive integer")


def _strip_line_endings(raw: bytes) -> bytes:
    """Drop one trailing LF and one trailing CR, exactly as the limit expects."""
    payload = raw[:-1] if raw.endswith(b"\n") else raw
    if payload.endswith(b"\r"):
        payload = payload[:-1]
    return payload


def _check_payload(
    payload: bytes, line_number: int, max_bytes: int
) -> Optional[dict[str, Any]]:
    """Validate one physical line; ``None`` means the line is blank.

    Every rejection carries only a line number and a reason: never record
    content, key names or a file path.
    """
    if len(payload) > max_bytes:
        raise JSONLValidationError(line_number, f"exceeds {max_bytes} UTF-8 bytes")
    if not payload.strip():
        return None
    if line_number == 1 and payload.startswith(UTF8_BOM):
        raise JSONLValidationError(
            line_number, "starts with a UTF-8 byte order mark (BOM)"
        )
    if b"\r" in payload:
        raise JSONLValidationError(
            line_number,
            "contains a bare carriage return; use LF or CRLF line endings",
        )
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise JSONLValidationError(line_number, "invalid UTF-8 encoding") from exc
    try:
        data = json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except RecursionError as exc:
        raise JSONLValidationError(line_number, "JSON nesting is too deep") from exc
    except _DuplicateKeyError as exc:
        raise JSONLValidationError(
            line_number, "duplicate JSON object key"
        ) from exc
    except _NonFiniteNumberError as exc:
        raise JSONLValidationError(
            line_number, "non-finite number (NaN or Infinity) is not allowed"
        ) from exc
    except ValueError as exc:
        raise JSONLValidationError(line_number, "invalid JSON") from exc
    if not isinstance(data, dict):
        if data is None:
            kind = "null"
        elif isinstance(data, bool):
            kind = "true" if data else "false"
        elif isinstance(data, (int, float)):
            kind = "a number"
        elif isinstance(data, str):
            kind = "a string"
        else:
            kind = "an array"
        raise JSONLValidationError(line_number, f"expected a JSON object, got {kind}")
    return data


def iter_jsonl_records(
    source: BinaryIO, *, max_bytes: int = DEFAULT_MAX_BYTES
) -> Iterator[dict[str, Any]]:
    """Yield JSON objects while imposing a strict per-record byte limit.

    Bounded readline(max_bytes + 3) allows a trailing CRLF; longer records
    are rejected before their potentially sensitive content is parsed.
    """
    _check_max_bytes(max_bytes)

    line_number = 0
    while True:
        raw = source.readline(max_bytes + 3)
        if not raw:
            return
        line_number += 1
        record = _check_payload(_strip_line_endings(raw), line_number, max_bytes)
        if record is not None:
            yield record


def _drain_line(source: BinaryIO, raw: bytes) -> None:
    """Consume the rest of an over-long physical line without decoding it.

    Only :func:`scan_jsonl` needs this: it keeps reading after a rejected line.
    The bytes are counted in fixed-size chunks and dropped, never joined or
    decoded, so a sensitive over-long record cannot leak through the error.
    """
    if raw.endswith(b"\n"):
        return
    while True:
        rest = source.readline(_DRAIN_CHUNK)
        if not rest or rest.endswith(b"\n"):
            return


def scan_jsonl(
    source: BinaryIO,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_errors: int = MAX_REPORTED_ERRORS,
) -> tuple[int, list[tuple[int, str]], bool]:
    """Count valid records and report every invalid line, not just the first.

    Returns ``(records, errors, truncated)``; each error is a
    ``(line_number, reason)`` pair. At most ``max_errors`` pairs are collected
    and ``truncated`` says whether the input had more. Reading continues to the
    end either way so ``records`` stays exact, and an over-long line is drained
    without being decoded, exactly as the single-error path rejects it.
    """
    _check_max_bytes(max_bytes)
    _check_max_errors(max_errors)

    records = 0
    errors: list[tuple[int, str]] = []
    truncated = False
    line_number = 0
    while True:
        raw = source.readline(max_bytes + 3)
        if not raw:
            return records, errors, truncated
        line_number += 1
        payload = _strip_line_endings(raw)
        try:
            record = _check_payload(payload, line_number, max_bytes)
        except JSONLValidationError as exc:
            if not raw.endswith(b"\n") and len(raw) == max_bytes + 3:
                # The physical line continues past the bounded read: drop the
                # rest without decoding it so later lines can still be checked.
                _drain_line(source, raw)
            reason = exc.reason
        else:
            if record is not None:
                records += 1
            continue
        if len(errors) < max_errors:
            errors.append((line_number, reason))
        else:
            truncated = True


def count_jsonl(source: BinaryIO, *, max_bytes: int = DEFAULT_MAX_BYTES) -> int:
    return sum(1 for _ in iter_jsonl_records(source, max_bytes=max_bytes))


def _positive_int(value: str) -> int:
    """argparse type for --max-bytes: a base-10 integer at least 1."""
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid int value: {value!r}") from exc
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {number}")
    return number


def _ok_report(records: int, max_bytes: int) -> dict[str, Any]:
    return {"status": "ok", "records": records, "max_bytes": max_bytes}


def _invalid_report(
    records: int, errors: list[tuple[int, str]], truncated: bool, max_bytes: int
) -> dict[str, Any]:
    return {
        "status": "invalid",
        "records": records,
        "errors": [{"line": line, "reason": reason} for line, reason in errors],
        "truncated": truncated,
        "max_bytes": max_bytes,
    }


def _report_for(source: BinaryIO, args: argparse.Namespace) -> dict[str, Any]:
    """Scan one already-open source and build the JSON report."""
    if not args.report_all:
        return _ok_report(count_jsonl(source, max_bytes=args.max_bytes), args.max_bytes)
    records, errors, truncated = scan_jsonl(source, max_bytes=args.max_bytes)
    if errors:
        return _invalid_report(records, errors, truncated, args.max_bytes)
    return _ok_report(records, args.max_bytes)


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    if args.input is None or args.input == "-":
        return _report_for(sys.stdin.buffer, args)
    path = Path(args.input)
    if path.is_dir():
        raise ValueError("--input is a directory, not a file")
    with path.open("rb") as source:
        return _report_for(source, args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", help="Input file; omit or use - for stdin. Use ./- for a file named -."
    )
    parser.add_argument("--max-bytes", type=_positive_int, default=DEFAULT_MAX_BYTES)
    parser.add_argument(
        "--report-all",
        action="store_true",
        help="report every invalid line instead of stopping at the first one",
    )
    parser.add_argument(
        "--version", action="version", version=f"jsonl_utf8_guard {__version__}"
    )
    args = parser.parse_args(argv)
    try:
        report = _build_report(args)
    except (OSError, ValueError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report))
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
