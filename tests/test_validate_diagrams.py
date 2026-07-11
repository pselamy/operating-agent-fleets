from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_diagrams import DiagramValidationError, ROOT, digest, validate_diagrams


class DiagramValidationTests(unittest.TestCase):
    def test_repository_diagrams_validate(self) -> None:
        self.assertEqual(validate_diagrams(), 2)

    def fixture(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "diagrams").mkdir()
        source = root / "diagrams" / "sample.mmd"
        source.write_text(
            "%% Reader question: Why?\n%% Evidence cutoff: 2026-07-11\n"
            "%% Claim status: reference design\nflowchart LR\n"
            "accTitle: Sample\naccDescr: Sample description\nA --> B\n",
            encoding="utf-8",
        )
        exports = []
        for theme in ("light", "dark"):
            svg = root / "diagrams" / f"sample.{theme}.svg"
            svg.write_text(
                '<svg aria-labelledby="title desc" aria-roledescription="flowchart"><title id="title">Sample</title><desc id="desc">Description</desc></svg>',
                encoding="utf-8",
            )
            exports.append({"theme": theme, "svg_id": f"sample-{theme}", "path": f"diagrams/sample.{theme}.svg", "sha256": digest(svg)})
        diagram = {
            "id": "sample.diagram",
            "title": "Sample",
            "reader_question": "Why?",
            "evidence_cutoff": "2026-07-11",
            "claim_status": "reference_design",
            "source": "diagrams/sample.mmd",
            "source_sha256": digest(source),
            "evidence_ids": ["artifact.synthetic"],
            "alt_text": "A sample accessible diagram.",
            "exports": exports,
        }
        manifest = {"schema_version": 1, "renderer": {}, "diagrams": [diagram]}
        return root, manifest

    def write_manifest(self, root: Path, manifest: dict) -> None:
        (root / "diagrams" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_valid_fixture(self) -> None:
        root, manifest = self.fixture()
        self.write_manifest(root, manifest)
        self.assertEqual(validate_diagrams(root), 1)

    def test_stale_source_and_export_fail(self) -> None:
        root, manifest = self.fixture()
        stale_source = copy.deepcopy(manifest)
        stale_source["diagrams"][0]["source_sha256"] = "0" * 64
        self.write_manifest(root, stale_source)
        with self.assertRaisesRegex(DiagramValidationError, "source is missing or stale"):
            validate_diagrams(root)
        stale_export = copy.deepcopy(manifest)
        stale_export["diagrams"][0]["exports"][0]["sha256"] = "0" * 64
        self.write_manifest(root, stale_export)
        with self.assertRaisesRegex(DiagramValidationError, "export is missing or stale"):
            validate_diagrams(root)

    def test_accessibility_marker_and_theme_failures(self) -> None:
        root, manifest = self.fixture()
        svg = root / manifest["diagrams"][0]["exports"][0]["path"]
        svg.write_text("<svg></svg>", encoding="utf-8")
        manifest["diagrams"][0]["exports"][0]["sha256"] = digest(svg)
        self.write_manifest(root, manifest)
        with self.assertRaisesRegex(DiagramValidationError, "accessible SVG metadata"):
            validate_diagrams(root)
        root, manifest = self.fixture()
        manifest["diagrams"][0]["exports"] = manifest["diagrams"][0]["exports"][:1]
        self.write_manifest(root, manifest)
        with self.assertRaisesRegex(DiagramValidationError, "light and dark"):
            validate_diagrams(root)

    def test_duplicate_id_and_export_fail(self) -> None:
        root, manifest = self.fixture()
        manifest["diagrams"].append(copy.deepcopy(manifest["diagrams"][0]))
        self.write_manifest(root, manifest)
        with self.assertRaisesRegex(DiagramValidationError, "duplicate ID"):
            validate_diagrams(root)
        root, manifest = self.fixture()
        manifest["diagrams"][0]["exports"][1]["path"] = manifest["diagrams"][0]["exports"][0]["path"]
        self.write_manifest(root, manifest)
        with self.assertRaisesRegex(DiagramValidationError, "duplicates"):
            validate_diagrams(root)


if __name__ == "__main__":
    unittest.main()
