from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.privacy_forward_guard import forward_revision_range, main
from tools.privacy_history_scan import scan_history


class PrivacyForwardGuardTests(unittest.TestCase):
    def repository(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "synthetic@example.test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Synthetic Test"], cwd=root, check=True)
        return root

    @staticmethod
    def commit(root: Path, message: str) -> str:
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", message], cwd=root, check=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()

    def test_safe_range_passes_and_restricted_metadata_fails(self) -> None:
        root = self.repository()
        (root / "public.md").write_text("baseline\n", encoding="utf-8")
        base = self.commit(root, "baseline")
        (root / "public.md").write_text("safe candidate\n", encoding="utf-8")
        safe_head = self.commit(root, "safe candidate")
        revision_range = forward_revision_range(root, base, safe_head)
        self.assertEqual(revision_range, f"{base}..{safe_head}")
        self.assertEqual(scan_history(root, revisions=(revision_range,)).findings, ())
        with mock.patch("sys.argv", [
            "privacy_forward_guard.py", "--root", str(root), "--base", base, "--head", safe_head,
        ]):
            self.assertEqual(main(), 0)

        subprocess.run(
            ["git", "config", "user.email", "operator@workstation" + ".local"],
            cwd=root,
            check=True,
        )
        restricted_head = self.commit(root, "new commit with restricted metadata")
        with mock.patch("sys.argv", [
            "privacy_forward_guard.py", "--root", str(root),
            "--base", safe_head, "--head", restricted_head,
        ]):
            self.assertEqual(main(), 1)

    def test_scope_failures_are_closed(self) -> None:
        root = self.repository()
        (root / "public.md").write_text("baseline\n", encoding="utf-8")
        head = self.commit(root, "baseline")
        with self.assertRaisesRegex(ValueError, "no new commits"):
            forward_revision_range(root, head, head)
        with self.assertRaisesRegex(ValueError, "invalid"):
            forward_revision_range(root, "--all", head)

        subprocess.run(["git", "checkout", "-q", "--orphan", "unrelated"], cwd=root, check=True)
        subprocess.run(["git", "rm", "-q", "-rf", "."], cwd=root, check=True)
        (root / "other.md").write_text("unrelated\n", encoding="utf-8")
        unrelated = self.commit(root, "unrelated root")
        with self.assertRaisesRegex(ValueError, "not an ancestor"):
            forward_revision_range(root, head, unrelated)
        with mock.patch("sys.argv", [
            "privacy_forward_guard.py", "--root", str(root),
            "--base", head, "--head", unrelated,
        ]):
            self.assertEqual(main(), 2)

    def test_invalid_limits_fail_without_raw_findings(self) -> None:
        root = self.repository()
        (root / "public.md").write_text("baseline\n", encoding="utf-8")
        base = self.commit(root, "baseline")
        head = self.commit(root, "candidate")
        with mock.patch("sys.argv", [
            "privacy_forward_guard.py", "--root", str(root), "--base", base, "--head", head,
            "--max-object-bytes", "0",
        ]):
            self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()
