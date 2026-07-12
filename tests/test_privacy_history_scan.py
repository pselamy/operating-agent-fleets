from __future__ import annotations

import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.privacy_history_scan import main, reachable_objects, scan_history, verify_remote_refs


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
        self.assertIsNone(findings[0].path_digest)

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

    def test_shallow_repository_fails_closed(self) -> None:
        source = self.repository()
        candidate = source / "public.md"
        candidate.write_text("first\n", encoding="utf-8")
        self.commit(source)
        candidate.write_text("second\n", encoding="utf-8")
        self.commit(source)
        clone_parent = tempfile.TemporaryDirectory()
        self.addCleanup(clone_parent.cleanup)
        clone = Path(clone_parent.name) / "clone"
        subprocess.run(
            ["git", "clone", "-q", "--depth", "1", source.as_uri(), str(clone)],
            check=True,
        )
        with self.assertRaisesRegex(ValueError, "repository is shallow"):
            scan_history(clone)

    def test_remote_ref_verification_detects_unfetched_work(self) -> None:
        source = self.repository()
        candidate = source / "public.md"
        candidate.write_text("first\n", encoding="utf-8")
        self.commit(source)
        subprocess.run(["git", "tag", "-a", "v1", "-m", "safe tag"], cwd=source, check=True)
        clone_parent = tempfile.TemporaryDirectory()
        self.addCleanup(clone_parent.cleanup)
        clone = Path(clone_parent.name) / "clone"
        subprocess.run(["git", "clone", "-q", source.as_uri(), str(clone)], check=True)
        self.assertEqual(len(verify_remote_refs(clone, "origin")), 2)
        candidate.write_text("second\n", encoding="utf-8")
        self.commit(source)
        with self.assertRaisesRegex(ValueError, "stale relative to remote"):
            verify_remote_refs(clone, "origin")

    def test_same_blob_under_restricted_historical_path_is_found_and_redacted(self) -> None:
        root = self.repository()
        safe = root / "aaa.txt"
        safe.write_text("same safe payload\n", encoding="utf-8")
        self.commit(root)
        restricted_name = "service" + ".internal.txt"
        safe.rename(root / restricted_name)
        self.commit(root, "rename synthetic fixture")
        findings = scan_history(root).findings
        path_findings = [finding for finding in findings if finding.object_type == "path"]
        self.assertEqual([finding.rule for finding in path_findings], ["private hostname"])
        self.assertIsNotNone(path_findings[0].path_digest)
        stderr = io.StringIO()
        with mock.patch("sys.argv", ["privacy_history_scan.py", "--root", str(root)]), mock.patch("sys.stderr", stderr):
            self.assertEqual(main(), 1)
        self.assertNotIn(restricted_name, stderr.getvalue())
        self.assertIn("historical-path sha256=", stderr.getvalue())

    def test_merge_result_only_path_is_scanned(self) -> None:
        root = self.repository()
        (root / "base.txt").write_text("base\n", encoding="utf-8")
        self.commit(root)
        primary = subprocess.run(
            ["git", "branch", "--show-current"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        subprocess.run(["git", "checkout", "-q", "-b", "other"], cwd=root, check=True)
        (root / "other.txt").write_text("other\n", encoding="utf-8")
        self.commit(root)
        subprocess.run(["git", "checkout", "-q", primary], cwd=root, check=True)
        (root / "primary.txt").write_text("primary\n", encoding="utf-8")
        self.commit(root)
        subprocess.run(["git", "merge", "-q", "--no-commit", "other"], cwd=root, check=True)
        restricted_name = "merge-only" + ".internal.txt"
        (root / restricted_name).write_text("safe payload\n", encoding="utf-8")
        self.commit(root, "merge with synthetic resolution path")
        (root / restricted_name).unlink()
        self.commit(root, "remove synthetic resolution path")
        findings = scan_history(root).findings
        self.assertIn(("path", "private hostname"), [(item.object_type, item.rule) for item in findings])

    def test_annotated_tag_payload_is_scanned(self) -> None:
        root = self.repository()
        (root / "public.md").write_text("safe\n", encoding="utf-8")
        self.commit(root)
        synthetic = "gh" + "p_" + "A" * 24
        subprocess.run(["git", "tag", "-a", "synthetic", "-m", synthetic], cwd=root, check=True)
        findings = scan_history(root).findings
        self.assertIn(("tag", "GitHub credential"), [(item.object_type, item.rule) for item in findings])

    def test_lossless_binary_scan_and_partial_clone_guard(self) -> None:
        root = self.repository()
        candidate = root / "candidate.bin"
        candidate.write_bytes(b"\xff" + b"0x" + b"a1" * 20)
        self.commit(root)
        self.assertIn("Ethereum address", [item.rule for item in scan_history(root).findings])
        subprocess.run(["git", "config", "remote.origin.promisor", "true"], cwd=root, check=True)
        with self.assertRaisesRegex(ValueError, "partial/promisor"):
            scan_history(root)

    def test_oversized_object_and_invalid_limit_fail_closed(self) -> None:
        root = self.repository()
        (root / "public.md").write_text("safe\n", encoding="utf-8")
        self.commit(root)
        with self.assertRaisesRegex(ValueError, "scan limit"):
            scan_history(root, max_object_bytes=1)
        with self.assertRaisesRegex(ValueError, "must be positive"):
            scan_history(root, max_object_bytes=0)
        with self.assertRaisesRegex(ValueError, "historical path data"):
            scan_history(root, max_path_bytes=1)

    def test_oversized_tree_fails_closed(self) -> None:
        root = self.repository()
        for index in range(80):
            (root / f"file-{index:03d}.txt").write_text("", encoding="utf-8")
        self.commit(root)
        with self.assertRaisesRegex(ValueError, r"\(tree, [0-9]+ bytes\) exceeds"):
            scan_history(root, max_object_bytes=500)

    def test_restricted_remote_ref_name_is_redacted(self) -> None:
        source = self.repository()
        (source / "safe.txt").write_text("safe\n", encoding="utf-8")
        self.commit(source)
        restricted = "service" + ".internal"
        subprocess.run(["git", "tag", restricted], cwd=source, check=True)
        clone_parent = tempfile.TemporaryDirectory()
        self.addCleanup(clone_parent.cleanup)
        clone = Path(clone_parent.name) / "clone"
        subprocess.run(["git", "clone", "-q", source.as_uri(), str(clone)], check=True)
        with self.assertRaisesRegex(ValueError, "restricted ref name") as raised:
            verify_remote_refs(clone, "origin")
        self.assertNotIn(restricted, str(raised.exception))

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
        with mock.patch("sys.argv", ["privacy_history_scan.py", "--root", str(root), "--verify-remote=-bad"]):
            self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()
