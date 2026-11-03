"""Network-free, fail-closed regressions for public checksum verification."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from verify_release import FILES, MANIFEST, VerificationError, verify_release


class ReleaseVerifierTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="test-release-manifest-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        source = Path(__file__).resolve().parent
        for name in FILES:
            shutil.copyfile(source / name, self.root / name)
        self._rewrite_manifest()

    def _rewrite_manifest(self, rows=None):
        if rows is None:
            rows = [
                f"{hashlib.sha256((self.root / name).read_bytes()).hexdigest()}  {name}"
                for name in sorted(FILES)
            ]
        (self.root / MANIFEST).write_bytes(("\n".join(rows) + "\n").encode("ascii"))

    def test_valid_source_and_manifest(self):
        self.assertEqual(
            verify_release(self.root),
            {"status": "ok", "files": len(FILES), "manifest": MANIFEST},
        )

    def test_changed_source_detected(self):
        with (self.root / "jsonl_utf8_guard.py").open("ab") as f:
            f.write(b"\n# deliberate edit")
        with self.assertRaisesRegex(VerificationError, "checksum mismatch"):
            verify_release(self.root)

    def test_missing_source_fails_closed(self):
        (self.root / "LICENSE").unlink()
        with self.assertRaisesRegex(VerificationError, "Missing or unsafe"):
            verify_release(self.root)

    def test_missing_manifest_fails_closed(self):
        (self.root / MANIFEST).unlink()
        with self.assertRaisesRegex(VerificationError, "manifest is missing"):
            verify_release(self.root)

    def test_duplicate_manifest_entry_fails_closed(self):
        lines = (self.root / MANIFEST).read_text(encoding="ascii").splitlines()
        lines[1] = lines[0]
        self._rewrite_manifest(lines)
        with self.assertRaisesRegex(VerificationError, "files/order mismatch"):
            verify_release(self.root)

    def test_extra_manifest_entry_fails_closed(self):
        lines = (self.root / MANIFEST).read_text(encoding="ascii").splitlines()
        self._rewrite_manifest(lines + [lines[-1]])
        with self.assertRaisesRegex(VerificationError, "missing or extra"):
            verify_release(self.root)

    def test_path_traversal_rejected_without_read(self):
        lines = (self.root / MANIFEST).read_text(encoding="ascii").splitlines()
        lines[0] = "0" * 64 + "  ../SECRET"
        self._rewrite_manifest(lines)
        with self.assertRaisesRegex(VerificationError, "invalid entry"):
            verify_release(self.root)

    def test_nonhex_digest_rejected(self):
        lines = (self.root / MANIFEST).read_text(encoding="ascii").splitlines()
        lines[0] = "z" * 64 + "  LICENSE"
        self._rewrite_manifest(lines)
        with self.assertRaisesRegex(VerificationError, "invalid entry"):
            verify_release(self.root)

    def test_reordered_manifest_fails_closed(self):
        lines = (self.root / MANIFEST).read_text(encoding="ascii").splitlines()
        lines[0], lines[1] = lines[1], lines[0]
        self._rewrite_manifest(lines)
        with self.assertRaisesRegex(VerificationError, "files/order mismatch"):
            verify_release(self.root)

    def test_crlf_manifest_rejected(self):
        path = self.root / MANIFEST
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        with self.assertRaisesRegex(VerificationError, "invalid format"):
            verify_release(self.root)

    def test_sensitive_file_payload_not_disclosed_in_cli_error(self):
        file = self.root / "README.md"
        file.write_text("MY_PRIVATE_SENTINEL_VALUE\n", encoding="utf-8")
        cmd = [
            sys.executable, "-B",
            str(Path(__file__).with_name("verify_release.py")),
            "--root", str(self.root),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("MY_PRIVATE_SENTINEL_VALUE", r.stderr)
        self.assertNotIn("MY_PRIVATE_SENTINEL_VALUE", r.stdout)

    def test_successful_cli_exposes_only_status(self):
        cmd = [
            sys.executable, "-B",
            str(Path(__file__).with_name("verify_release.py")),
            "--root", str(self.root),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["files"], len(FILES))
        self.assertNotIn(str(self.root), r.stdout)

    def test_symlink_source_is_rejected_when_supported(self):
        file = self.root / "LICENSE"
        file.unlink()
        try:
            file.symlink_to(self.root / "README.md")
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are unavailable on this host")
        with self.assertRaisesRegex(VerificationError, "Missing or unsafe"):
            verify_release(self.root)


if __name__ == "__main__":
    unittest.main()
