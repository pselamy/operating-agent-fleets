from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.check_claim_links import check_claim_links, main
from tools.validate_evidence import ROOT, load_json


class ClaimLinkTests(unittest.TestCase):
    def make_root(self, chapter: str, include_record: bool) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "guide").mkdir()
        (root / "evidence" / "records").mkdir(parents=True)
        (root / "schemas").mkdir()
        (root / "guide" / "01-synthetic.md").write_text(chapter, encoding="utf-8")
        (root / "schemas" / "public-evidence.schema.json").write_text(
            json.dumps(load_json(ROOT / "schemas" / "public-evidence.schema.json")), encoding="utf-8"
        )
        records = []
        if include_record:
            relative = "evidence/records/synthetic.json"
            records.append(relative)
            (root / relative).write_text(json.dumps({
                "id": "artifact.synthetic-example",
                "title": "Synthetic example",
                "evidence_class": "repository_artifact",
                "lineage": "synthetic",
                "verified_at": "2026-07-11",
                "reverify_after_days": 30,
                "cutoff": "synthetic cutoff",
                "public_sources": ["https://example.com/public"],
                "claims": ["A synthetic public artifact exists for this test."],
                "verification_method": ["Generated fixture"],
                "limitations": ["Not a real-world claim"],
                "sensitivity": "public",
                "status": "verified"
            }), encoding="utf-8")
        (root / "evidence" / "manifest.yaml").write_text(
            json.dumps({"schema_version": 1, "records": records}), encoding="utf-8"
        )
        return root

    def test_valid_citation_passes(self) -> None:
        chapter = "[Artifact](https://github.com/example/public) [@evidence:artifact.synthetic-example]\n"
        self.assertEqual(check_claim_links(self.make_root(chapter, include_record=True)), [])

    def test_unknown_citation_fails(self) -> None:
        root = self.make_root("Claim [@evidence:artifact.missing-record]\n", include_record=False)
        self.assertIn("unknown evidence citation", check_claim_links(root)[0])

    def test_artifact_link_without_citation_fails(self) -> None:
        root = self.make_root("[Artifact](https://github.com/example/public)\n", include_record=True)
        self.assertIn("without an evidence citation", check_claim_links(root)[0])

    def test_cli_pass_and_fail(self) -> None:
        passing = self.make_root("No artifact claim.\n", include_record=False)
        with mock.patch("sys.argv", ["check_claim_links.py", "--root", str(passing)]):
            self.assertEqual(main(), 0)
        failing = self.make_root("Claim [@evidence:artifact.missing-record]\n", include_record=False)
        with mock.patch("sys.argv", ["check_claim_links.py", "--root", str(failing)]):
            self.assertEqual(main(), 1)


if __name__ == "__main__":
    unittest.main()
