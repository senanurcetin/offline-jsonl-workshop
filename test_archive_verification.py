"""Tests for verifying a standalone release ZIP without extracting it."""
from __future__ import annotations

import hashlib
import io
import json
import stat
import warnings
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from verify_release import FILES, VerificationError, verify_archive

HERE = Path(__file__).resolve().parent
PREFIX = "offline-jsonl-workshop/"


def archive(entries=None):
    """Create a valid ZIP, optionally replacing its ordered list of entries."""
    if entries is None:
        manifest = "".join(
            f"{hashlib.sha256((HERE / name).read_bytes()).hexdigest()}  {name}\n"
            for name in sorted(FILES)
        ).encode("ascii")
        entries = [(PREFIX + name, (HERE / name).read_bytes()) for name in FILES]
        entries.append((PREFIX + "SHA256SUMS", manifest))
    output = io.BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        for name, data in entries:
            z.writestr(name, data)
    return output.getvalue()


class ArchiveVerificationTests(unittest.TestCase):
    def test_valid_archive_without_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workshop.zip"
            path.write_bytes(archive())
            self.assertEqual(
                verify_archive(path),
                {"status": "ok", "files": len(FILES), "manifest": "SHA256SUMS"},
            )

    def test_cli_archive_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workshop.zip"
            path.write_bytes(archive())
            result = subprocess.run(
                [sys.executable, "-B", str(HERE / "verify_release.py"), "--archive", str(path)],
                capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["files"], len(FILES))
            self.assertNotIn(str(path), result.stdout)

    def test_archive_rejects_extra_or_traversal_entries(self):
        for bad in ("../secret.txt", "offline-jsonl-workshop/../secret.txt",
                    "offline-jsonl-workshop/extra.py"):
            with self.subTest(name=bad):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "bad.zip"
                    with ZipFile(io.BytesIO(archive())) as original:
                        entries = [(i.filename, original.read(i)) for i in original.infolist()]
                    entries.append((bad, b"SECRET_VALUE"))
                    path.write_bytes(archive(entries))
                    with self.assertRaisesRegex(VerificationError, "unexpected"):
                        verify_archive(path)

    def test_archive_rejects_duplicate_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.zip"
            with ZipFile(io.BytesIO(archive())) as original:
                entries = [(i.filename, original.read(i)) for i in original.infolist()]
            entries.append(entries[0])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                path.write_bytes(archive(entries))
            with self.assertRaisesRegex(VerificationError, "duplicate"):
                verify_archive(path)

    def test_archive_rejects_missing_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.zip"
            with ZipFile(io.BytesIO(archive())) as original:
                entries = [(i.filename, original.read(i)) for i in original.infolist()]
            path.write_bytes(archive(entries[:-2] + entries[-1:]))
            with self.assertRaisesRegex(VerificationError, "missing"):
                verify_archive(path)

    def test_archive_rejects_tampered_content_and_hides_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.zip"
            with ZipFile(io.BytesIO(archive())) as original:
                entries = [(i.filename, original.read(i)) for i in original.infolist()]
            entries = [(name, b"SECRET_VALUE" if name.endswith("/README.md") else data)
                       for name, data in entries]
            path.write_bytes(archive(entries))
            with self.assertRaises(VerificationError) as caught:
                verify_archive(path)
            self.assertIn("checksum mismatch", str(caught.exception))
            self.assertNotIn("SECRET_VALUE", str(caught.exception))

    def test_archive_rejects_symlink_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "symlink.zip"
            with ZipFile(io.BytesIO(archive())) as original:
                entries = [(i.filename, original.read(i)) for i in original.infolist()]
            memory = io.BytesIO()
            with ZipFile(memory, "w", ZIP_DEFLATED) as z:
                for name, data in entries:
                    if name.endswith("/README.md"):
                        info = ZipInfo(name)
                        info.create_system = 3
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                        z.writestr(info, b"../outside")
                    else:
                        z.writestr(name, data)
            path.write_bytes(memory.getvalue())
            with self.assertRaisesRegex(VerificationError, "symlink"):
                verify_archive(path)

    def test_archive_rejects_oversized_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "oversize.zip"
            with ZipFile(io.BytesIO(archive())) as original:
                entries = [(i.filename, original.read(i)) for i in original.infolist()]
            entries = [(name, b"x" * 1_000_001 if name.endswith("/README.md") else data)
                       for name, data in entries]
            path.write_bytes(archive(entries))
            with self.assertRaisesRegex(VerificationError, "size"):
                verify_archive(path)

    def test_corrupt_and_non_zip_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "notzip.zip"
            path.write_bytes(b"not a zip SECRET_VALUE")
            with self.assertRaises(VerificationError) as caught:
                verify_archive(path)
            self.assertNotIn("SECRET_VALUE", str(caught.exception))

    def test_missing_zip_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(VerificationError):
                verify_archive(Path(tmp) / "missing.zip")


    def test_independent_archive_sha256_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.zip"
            data = archive()
            path.write_bytes(data)
            report = verify_archive(path, expected_sha256=hashlib.sha256(data).hexdigest())
            self.assertEqual(report["status"], "ok")
            self.assertTrue(report["trusted_archive_sha256_verified"])

    def test_wrong_trusted_digest_rejected_without_disclosure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.zip"
            path.write_bytes(archive())
            with self.assertRaises(VerificationError) as caught:
                verify_archive(path, expected_sha256="0" * 64)
            self.assertIn("trusted", str(caught.exception))
            self.assertNotIn(str(path), str(caught.exception))

    def test_attacker_replaces_payload_and_embedded_manifest(self):
        original_archive = archive()
        digest = hashlib.sha256(original_archive).hexdigest()
        with ZipFile(io.BytesIO(original_archive)) as original:
            entries = [(i.filename, original.read(i)) for i in original.infolist()]
        new_source = b'{"safe":false,"code":"secret"}\n'
        entries = [(name, new_source if name.endswith("/sample_events.jsonl") else data)
                   for name, data in entries]
        manifest = "".join(
            f"{hashlib.sha256(data).hexdigest()}  {name.removeprefix(PREFIX)}\n"
            for name, data in sorted(entries) if not name.endswith("/SHA256SUMS")
        ).encode("ascii")
        entries = [(name, manifest if name.endswith("/SHA256SUMS") else data)
                   for name, data in entries]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "attacker.zip"
            path.write_bytes(archive(entries))
            # Embedded manifest matches the malicious replacement's payload.
            self.assertEqual(verify_archive(path)["status"], "ok")
            # Independent checksum from the trusted earlier release rejects it.
            with self.assertRaisesRegex(VerificationError, "trusted"):
                verify_archive(path, expected_sha256=digest)

    def test_invalid_trusted_digest_fails_closed(self):
        for invalid in ("", "0" * 63, "0" * 65, "x" * 64,
                        "A" * 64, "../etc/passwd", "0" * 64 + "\nSECRET"):
            with self.subTest(value=invalid[:15]):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "ok.zip"
                    path.write_bytes(archive())
                    with self.assertRaisesRegex(VerificationError, "trusted"):
                        verify_archive(path, expected_sha256=invalid)

    def test_cli_accepts_trusted_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.zip"
            data = archive()
            path.write_bytes(data)
            r = subprocess.run([
                sys.executable, "-B", str(HERE / "verify_release.py"),
                "--archive", str(path), "--expected-archive-sha256",
                hashlib.sha256(data).hexdigest(),
            ], capture_output=True, text=True, timeout=20)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(json.loads(r.stdout)["trusted_archive_sha256_verified"])

    def test_cli_rejects_trusted_sha256_without_archive(self):
        r = subprocess.run([
            sys.executable, "-B", str(HERE / "verify_release.py"),
            "--expected-archive-sha256", "0" * 64,
        ], capture_output=True, text=True, timeout=20)
        self.assertEqual(r.returncode, 2)
        self.assertFalse(r.stdout.strip())

    def test_cli_rejects_mismatched_trusted_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.zip"
            path.write_bytes(archive())
            r = subprocess.run([
                sys.executable, "-B", str(HERE / "verify_release.py"),
                "--archive", str(path), "--expected-archive-sha256", "0" * 64,
            ], capture_output=True, text=True, timeout=20)
            self.assertEqual(r.returncode, 2)
            self.assertFalse(r.stdout.strip())
            self.assertIn("trusted", r.stderr)

    def test_bounded_archive_read_with_trusted_checksum(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.zip"
            path.write_bytes(archive())
            with patch("verify_release.MAX_ARCHIVE_BYTES", 50):
                with self.assertRaisesRegex(VerificationError, "size"):
                    verify_archive(path, expected_sha256="0" * 64)


    def test_trusted_archive_reader_never_uses_unbounded_read_bytes(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.zip"
            blob = archive()
            path.write_bytes(blob)
            digest = hashlib.sha256(blob).hexdigest()
            with patch.object(
                Path, "read_bytes",
                side_effect=AssertionError("unbounded read_bytes must not run"),
            ):
                result = verify_archive(path, expected_sha256=digest)
            self.assertTrue(result["trusted_archive_sha256_verified"])


if __name__ == "__main__":
    unittest.main()
