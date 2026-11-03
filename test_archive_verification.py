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


if __name__ == "__main__":
    unittest.main()
