from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_evidence import EvidenceValidationError, ROOT, load_json, validate_atlas, validate_record


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
        record["public_sources"] = ["file:///synthetic/private/path"]
        with self.assertRaisesRegex(EvidenceValidationError, "public HTTPS URL"):
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
        self.assertEqual(validate_atlas(), [])

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


if __name__ == "__main__":
    unittest.main()
