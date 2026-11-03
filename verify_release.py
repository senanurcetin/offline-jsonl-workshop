"""Verify the published SHA256SUMS manifest without Git, network or packages.

For a cloned repository or extracted workshop ZIP. Hashes are compared only
for explicitly listed workshop files; untrusted manifest paths are rejected.
Input file contents and secret-looking metadata are never printed.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import io
import json
import re
import stat
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

FILES = (
    "LICENSE",
    "README.md",
    "WORKSHOP_RUNBOOK_TR_EN.md",
    "jsonl_utf8_guard.py",
    "red_green_demo.py",
    "sample_events.jsonl",
    "test_jsonl_utf8_guard.py",
    "test_red_green_demo.py",
    "test_archive_verification.py",
    "test_verify_release.py",
    "verify_release.py",
)
MANIFEST = "SHA256SUMS"
MAX_SOURCE_BYTES = 1_000_000
MAX_MANIFEST_BYTES = 8_192
MAX_ARCHIVE_BYTES = 16_000_000
ZIP_PREFIX = "offline-jsonl-workshop/"
ENTRY = re.compile(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)")


class VerificationError(ValueError):
    """The release manifest or a source file failed verification."""


def _source_bytes(root: Path, filename: str) -> bytes:
    target = root / filename
    if target.is_symlink() or not target.is_file():
        raise VerificationError(f"Missing or unsafe source file: {filename}")
    if target.resolve().parent != root:
        raise VerificationError(f"Source file escapes release directory: {filename}")
    if target.stat().st_size > MAX_SOURCE_BYTES:
        raise VerificationError(f"Source file exceeds size limit: {filename}")
    data = target.read_bytes()
    if len(data) > MAX_SOURCE_BYTES:
        raise VerificationError(f"Source file exceeds size limit: {filename}")
    return data


def _manifest_entries(raw: bytes) -> list[tuple[str, str]]:
    """Parse fixed sorted source names and SHA-256 digests (no untrusted paths)."""
    if len(raw) > MAX_MANIFEST_BYTES or b"\r" in raw:
        raise VerificationError("Release checksum manifest has an invalid format")
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise VerificationError("Release checksum manifest must be ASCII") from exc
    if not raw.endswith(b"\n") or len(lines) != len(FILES):
        raise VerificationError("Release checksum manifest has missing or extra entries")
    parsed: list[tuple[str, str]] = []
    for line in lines:
        match = ENTRY.fullmatch(line)
        if match is None:
            raise VerificationError("Release checksum manifest has an invalid entry")
        parsed.append((match.group(2), match.group(1)))
    if [name for name, _ in parsed] != sorted(FILES):
        raise VerificationError("Release checksum manifest files/order mismatch")
    return parsed


def verify_release(root: Path) -> dict[str, object]:
    """Verify all expected files and reject extras or ambiguous manifest rows."""
    if root.is_symlink() or not root.is_dir():
        raise VerificationError("Release directory is missing or unsafe")
    directory = root.resolve()
    manifest = directory / MANIFEST
    if manifest.is_symlink() or not manifest.is_file():
        raise VerificationError("Release checksum manifest is missing or unsafe")
    if manifest.stat().st_size > MAX_MANIFEST_BYTES:
        raise VerificationError("Release checksum manifest exceeds size limit")
    raw = manifest.read_bytes()
    parsed = _manifest_entries(raw)
    for filename, digest in parsed:
        actual = hashlib.sha256(_source_bytes(directory, filename)).hexdigest()
        if actual != digest:
            raise VerificationError(f"Source checksum mismatch: {filename}")
    return {"status": "ok", "files": len(FILES), "manifest": MANIFEST}


def verify_archive(
    path: Path, expected_sha256: str | None = None
) -> dict[str, object]:
    """Verify ZIP sources and optionally a separately trusted whole-file hash."""
    if expected_sha256 is not None and (
        not isinstance(expected_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
    ):
        raise VerificationError("Invalid trusted archive SHA-256 format")
    if path.is_symlink() or not path.is_file():
        raise VerificationError("Missing or unsafe ZIP archive")
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise VerificationError("ZIP archive exceeds size limit")
    # Bound source bytes and hash exactly the bytes later parsed by ZipFile.
    with path.open("rb") as stream:
        raw_archive = stream.read(MAX_ARCHIVE_BYTES + 1)
    if len(raw_archive) > MAX_ARCHIVE_BYTES:
        raise VerificationError("ZIP archive exceeds size limit")
    if expected_sha256 is not None and not hmac.compare_digest(
        hashlib.sha256(raw_archive).hexdigest(), expected_sha256
    ):
        raise VerificationError("ZIP archive does not match trusted SHA-256")
    expected = {ZIP_PREFIX + name for name in (*FILES, MANIFEST)}
    try:
        with ZipFile(io.BytesIO(raw_archive), "r") as package:
            members = package.infolist()
            names = [member.filename for member in members]
            if len(names) != len(set(names)):
                raise VerificationError("ZIP archive has duplicate entries")
            if set(names) - expected:
                raise VerificationError("ZIP archive has unexpected entries")
            if expected - set(names):
                raise VerificationError("ZIP archive has missing entries")
            data: dict[str, bytes] = {}
            for member in members:
                if member.flag_bits & 1:
                    raise VerificationError("ZIP archive contains encrypted members")
                if stat.S_ISLNK(member.external_attr >> 16):
                    raise VerificationError("ZIP archive contains a symlink member")
                name = member.filename.removeprefix(ZIP_PREFIX)
                limit = MAX_MANIFEST_BYTES if name == MANIFEST else MAX_SOURCE_BYTES
                if member.file_size > limit:
                    raise VerificationError(f"ZIP member exceeds size limit: {name}")
                with package.open(member, "r") as stream:
                    blob = stream.read(limit + 1)
                if len(blob) > limit:
                    raise VerificationError(f"ZIP member exceeds size limit: {name}")
                data[name] = blob
            for filename, expected_hash in _manifest_entries(data[MANIFEST]):
                actual = hashlib.sha256(data[filename]).hexdigest()
                if actual != expected_hash:
                    raise VerificationError(f"Source checksum mismatch: {filename}")
    except (BadZipFile, RuntimeError, EOFError, OSError, NotImplementedError) as exc:
        raise VerificationError("ZIP archive cannot be verified") from exc
    result: dict[str, object] = {"status": "ok", "files": len(FILES), "manifest": MANIFEST}
    if expected_sha256 is not None:
        result["trusted_archive_sha256_verified"] = True
    return result


def read_trusted_sha256_sidecar(sidecar: Path, archive_path: Path) -> str:
    """Parse a separately trusted sha256sum-style file for this exact ZIP."""
    if sidecar.is_symlink() or not sidecar.is_file():
        raise VerificationError("Trusted SHA-256 sidecar is missing or unsafe")
    with sidecar.open("rb") as stream:
        raw = stream.read(257)
    if len(raw) > 256:
        raise VerificationError("Trusted SHA-256 sidecar exceeds size limit")
    match = re.fullmatch(rb"([0-9a-f]{64})  ([A-Za-z0-9_.-]+\.zip)\r?\n", raw)
    if match is None:
        raise VerificationError("Trusted SHA-256 sidecar has invalid format")
    if match.group(2).decode("ascii") != archive_path.name:
        raise VerificationError("Trusted SHA-256 sidecar filename mismatch")
    return match.group(1).decode("ascii")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--root", type=Path,
        help="Directory containing SHA256SUMS and workshop source files",
    )
    source.add_argument(
        "--archive", type=Path,
        help="Validate a standalone workshop ZIP without extracting it",
    )
    trusted = parser.add_mutually_exclusive_group()
    trusted.add_argument(
        "--expected-archive-sha256", type=str,
        help="Independently trusted SHA-256 digest of the entire ZIP (requires --archive)",
    )
    trusted.add_argument(
        "--trusted-sha256-file", type=Path,
        help="Explicitly trusted SHA-256 sidecar file for the ZIP (requires --archive)",
    )
    args = parser.parse_args(argv)
    if args.archive is None and (
        args.expected_archive_sha256 is not None or args.trusted_sha256_file is not None
    ):
        parser.error("A trusted archive SHA-256 requires --archive")
    try:
        expected_hash = args.expected_archive_sha256
        if args.trusted_sha256_file is not None:
            expected_hash = read_trusted_sha256_sidecar(
                args.trusted_sha256_file, args.archive
            )
        result = (
            verify_archive(args.archive, expected_sha256=expected_hash)
            if args.archive is not None
            else verify_release(args.root or Path(__file__).resolve().parent)
        )
    except (VerificationError, OSError) as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
