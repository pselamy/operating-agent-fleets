from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.privacy_history_scan import main, reachable_objects, scan_history


class PrivacyHistoryScanTests(unittest.TestCase):
    def repository(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "synthetic@example.test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Synthetic Test"], cwd=root, check=True)
        return root

    @staticmethod
    def commit(root: Path, message: str = "synthetic commit") -> None:
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", message], cwd=root, check=True)

    def test_safe_reachable_history_passes(self) -> None:
        root = self.repository()
        (root / "public.md").write_text("Public source: https://example.test\n", encoding="utf-8")
        self.commit(root)
        result = scan_history(root)
        self.assertGreaterEqual(result.objects_scanned, 3)
        self.assertGreater(result.bytes_scanned, 0)
        self.assertEqual(result.findings, ())

    def test_deleted_restricted_blob_still_fails(self) -> None:
        root = self.repository()
        candidate = root / "candidate.txt"
        candidate.write_text("0x" + "a1" * 20 + "\n", encoding="utf-8")
        self.commit(root)
        candidate.unlink()
        self.commit(root, "remove candidate")
        findings = scan_history(root).findings
        self.assertEqual([finding.rule for finding in findings], ["Ethereum address"])
        self.assertEqual(findings[0].path, "candidate.txt")

    def test_restricted_commit_message_fails(self) -> None:
        root = self.repository()
        (root / "public.md").write_text("safe\n", encoding="utf-8")
        synthetic = "123" + "-45-" + "6789"
        self.commit(root, f"synthetic marker {synthetic}")
        findings = scan_history(root).findings
        self.assertEqual([finding.rule for finding in findings], ["US taxpayer identifier"])
        self.assertEqual(findings[0].object_type, "commit")

    def test_revision_scope_and_empty_repository_fail_closed(self) -> None:
        root = self.repository()
        with self.assertRaisesRegex(ValueError, "no reachable objects"):
            reachable_objects(root)
        (root / "public.md").write_text("safe\n", encoding="utf-8")
        self.commit(root)
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        self.assertEqual(scan_history(root, revisions=(head,)).findings, ())

    def test_oversized_object_and_invalid_limit_fail_closed(self) -> None:
        root = self.repository()
        (root / "public.md").write_text("safe\n", encoding="utf-8")
        self.commit(root)
        with self.assertRaisesRegex(ValueError, "scan limit"):
            scan_history(root, max_object_bytes=1)
        with self.assertRaisesRegex(ValueError, "must be positive"):
            scan_history(root, max_object_bytes=0)

    def test_cli_pass_finding_and_operational_failure(self) -> None:
        root = self.repository()
        (root / "public.md").write_text("safe\n", encoding="utf-8")
        self.commit(root)
        with mock.patch("sys.argv", ["privacy_history_scan.py", "--root", str(root)]):
            self.assertEqual(main(), 0)
        synthetic = "gh" + "p_" + "A" * 24
        self.commit(root, f"synthetic {synthetic}")
        with mock.patch("sys.argv", ["privacy_history_scan.py", "--root", str(root)]):
            self.assertEqual(main(), 1)
        with mock.patch("sys.argv", ["privacy_history_scan.py", "--root", str(root), "--max-object-bytes", "0"]):
            self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()
