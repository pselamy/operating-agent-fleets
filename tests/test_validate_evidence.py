from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.validate_evidence import EvidenceValidationError, ROOT, load_json, main, validate_atlas, validate_record


class EvidenceRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(ROOT / "schemas" / "public-evidence.schema.json")
        cls.valid = {
            "id": "artifact.synthetic-example",
            "title": "Synthetic public artifact",
            "evidence_class": "repository_artifact",
            "lineage": "synthetic",
            "verified_at": "2026-07-11",
            "reverify_after_days": 30,
            "cutoff": "commit example0001",
            "public_sources": ["https://example.com/public-artifact"],
            "claims": ["The synthetic artifact exists at the stated cutoff."],
            "verification_method": ["Opened the synthetic public source."],
            "limitations": ["This fixture does not describe a real artifact."],
            "sensitivity": "public",
            "status": "verified"
        }

    def test_valid_record(self) -> None:
        self.assertEqual(validate_record(self.valid, self.schema), "artifact.synthetic-example")

    def test_missing_required_field(self) -> None:
        record = copy.deepcopy(self.valid)
        del record["limitations"]
        with self.assertRaisesRegex(EvidenceValidationError, "missing required fields: limitations"):
            validate_record(record, self.schema)

    def test_unknown_field_rejected(self) -> None:
        record = copy.deepcopy(self.valid)
        record["private_source"] = "synthetic forbidden locator"
        with self.assertRaisesRegex(EvidenceValidationError, "unknown fields: private_source"):
            validate_record(record, self.schema)

    def test_non_public_source_rejected(self) -> None:
        record = copy.deepcopy(self.valid)
        record["public_sources"] = ["fi" + "le:///synthetic/private/path"]
        with self.assertRaisesRegex(EvidenceValidationError, "public HTTPS URL"):
            validate_record(record, self.schema)

    def test_reverification_window_must_be_bounded_integer(self) -> None:
        for invalid in (True, 0, 366, "30"):
            record = copy.deepcopy(self.valid)
            record["reverify_after_days"] = invalid
            with self.subTest(invalid=invalid), self.assertRaisesRegex(EvidenceValidationError, "reverify_after_days"):
                validate_record(record, self.schema)

    def test_internal_record_has_no_public_source(self) -> None:
        record = copy.deepcopy(self.valid)
        record.update({
            "id": "case.synthetic-corroboration",
            "evidence_class": "internally_corroborated",
            "lineage": "derived",
            "public_sources": [],
            "sensitivity": "public_derived",
            "status": "limited"
        })
        self.assertEqual(validate_record(record, self.schema), "case.synthetic-corroboration")


class AtlasTests(unittest.TestCase):
    def test_repository_manifest_validates(self) -> None:
        manifest = load_json(ROOT / "evidence" / "manifest.yaml")
        self.assertEqual(len(validate_atlas()), len(manifest["records"]))

    def test_manifest_path_cannot_escape_records_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "schemas").mkdir()
            (root / "evidence" / "records").mkdir(parents=True)
            (root / "schemas" / "public-evidence.schema.json").write_text(
                json.dumps(load_json(ROOT / "schemas" / "public-evidence.schema.json")), encoding="utf-8"
            )
            (root / "evidence" / "manifest.yaml").write_text(
                json.dumps({"schema_version": 1, "records": ["README.md"]}), encoding="utf-8"
            )
            (root / "README.md").write_text("synthetic", encoding="utf-8")
            with self.assertRaisesRegex(EvidenceValidationError, "path escapes"):
                validate_atlas(root)

    def test_cli_pass_and_fail(self) -> None:
        with mock.patch("sys.argv", ["validate_evidence.py", "--root", str(ROOT)]):
            self.assertEqual(main(), 0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch("sys.argv", ["validate_evidence.py", "--root", str(root)]):
                self.assertEqual(main(), 1)


if __name__ == "__main__":
    unittest.main()
