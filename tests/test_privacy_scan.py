from __future__ import annotations

import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from tools.privacy_scan import main, scan_paths, tracked_text_files


class PrivacyScanTests(unittest.TestCase):
    def scan(self, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.txt"
            path.write_text(text, encoding="utf-8")
            return scan_paths([path])

    def test_safe_public_text_passes(self) -> None:
        self.assertEqual(self.scan("Public source: https://github.com/example/public\n"), [])

    def test_local_path_is_rejected(self) -> None:
        findings = self.scan("/" + "Users" + "/synthetic-person/restricted/file.txt")
        self.assertEqual([item.rule for item in findings], ["local macOS path"])

    def test_credentials_are_rejected_without_real_secret(self) -> None:
        synthetic = "gh" + "p_" + "A" * 24
        self.assertEqual([item.rule for item in self.scan(synthetic)], ["GitHub credential"])

    def test_tax_identifiers_are_rejected(self) -> None:
        synthetic = "123" + "-45-" + "6789"
        self.assertEqual([item.rule for item in self.scan(synthetic)], ["US taxpayer identifier"])

    def test_wallet_address_is_rejected(self) -> None:
        synthetic = "0x" + "a1" * 20
        self.assertEqual([item.rule for item in self.scan(synthetic)], ["Ethereum address"])

    def test_private_topology_is_rejected(self) -> None:
        synthetic = "service" + ".internal and 192" + ".168.10.4"
        self.assertEqual(
            [item.rule for item in self.scan(synthetic)],
            ["private hostname", "private IPv4 address"],
        )

    def test_telegram_locator_is_rejected(self) -> None:
        synthetic = "https://" + "t.me" + "/synthetic-channel"
        self.assertEqual([item.rule for item in self.scan(synthetic)], ["Telegram locator"])

    def test_raw_transcript_envelope_is_rejected(self) -> None:
        synthetic = "BEGIN " + "RAW TRANSCRIPT"
        self.assertEqual([item.rule for item in self.scan(synthetic)], ["raw transcript envelope"])

    def test_tracked_text_files_excludes_non_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "safe.md").write_text("safe", encoding="utf-8")
            (root / "opaque.bin").write_bytes(b"opaque")
            subprocess.run(["git", "add", "safe.md", "opaque.bin"], cwd=root, check=True)
            self.assertEqual(tracked_text_files(root), [root / "safe.md"])

    def test_cli_pass_and_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.md"
            path.write_text("safe public text", encoding="utf-8")
            with mock.patch("sys.argv", ["privacy_scan.py", str(path)]):
                self.assertEqual(main(), 0)
            path.write_text("0x" + "a1" * 20, encoding="utf-8")
            with mock.patch("sys.argv", ["privacy_scan.py", str(path)]):
                self.assertEqual(main(), 1)


if __name__ == "__main__":
    unittest.main()
