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
from typing import Any, BinaryIO

DEFAULT_MAX_BYTES = 65_536


class JSONLValidationError(ValueError):
    """An invalid input record, identified by its physical line number."""


def _reject_json_constant(value: str) -> None:
    raise ValueError("Non-finite JSON numbers are not supported")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous JSON object members without echoing sensitive names."""
    data: dict[str, Any] = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("Duplicate JSON object key")
        data[key] = value
    return data


def iter_jsonl_records(
    source: BinaryIO, *, max_bytes: int = DEFAULT_MAX_BYTES
) -> Iterator[dict[str, Any]]:
    """Yield JSON objects while imposing a strict per-record byte limit.

    Bounded readline(max_bytes + 3) allows a trailing CRLF; longer records
    are rejected before their potentially sensitive content is parsed.
    """
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
        raise ValueError("max_bytes must be a positive integer")

    line_number = 0
    while True:
        raw = source.readline(max_bytes + 3)
        if not raw:
            return
        line_number += 1
        payload = raw[:-1] if raw.endswith(b"\n") else raw
        if payload.endswith(b"\r"):
            payload = payload[:-1]
        if len(payload) > max_bytes:
            raise JSONLValidationError(
                f"Line {line_number}: exceeds {max_bytes} UTF-8 bytes"
            )
        if not payload.strip():
            continue
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise JSONLValidationError(
                f"Line {line_number}: invalid UTF-8 encoding"
            ) from exc
        try:
            data = json.loads(
                text,
                parse_constant=_reject_json_constant,
                object_pairs_hook=_reject_duplicate_keys,
            )
        except RecursionError as exc:
            raise JSONLValidationError(
                f"Line {line_number}: JSON nesting is too deep"
            ) from exc
        except ValueError as exc:
            raise JSONLValidationError(
                f"Line {line_number}: invalid JSON"
            ) from exc
        if not isinstance(data, dict):
            raise JSONLValidationError(
                f"Line {line_number}: expected a JSON object"
            )
        yield data


def count_jsonl(source: BinaryIO, *, max_bytes: int = DEFAULT_MAX_BYTES) -> int:
    return sum(1 for _ in iter_jsonl_records(source, max_bytes=max_bytes))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Input file; omit for stdin")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    args = parser.parse_args(argv)
    try:
        if args.input is None:
            count = count_jsonl(sys.stdin.buffer, max_bytes=args.max_bytes)
        else:
            with args.input.open("rb") as source:
                count = count_jsonl(source, max_bytes=args.max_bytes)
    except (OSError, ValueError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "ok", "records": count, "max_bytes": args.max_bytes}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
