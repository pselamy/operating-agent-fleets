from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "tools" / "validate_distribution.py"
SPEC = importlib.util.spec_from_file_location("validate_distribution", MODULE_PATH)
distribution = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(distribution)


class DistributionValidationTests(unittest.TestCase):
    def fixture(self) -> tuple[Path, dict]:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "distribution" / "packages").mkdir(parents=True)
        (root / "guide").mkdir()
        (root / "diagrams").mkdir()
        (root / "guide" / "05-throughput.md").write_text("# Chapter\n", encoding="utf-8")
        canonical = "https://selamy.dev/agent-fleets/05-throughput/"
        content = root / "distribution" / "packages" / "chapter-05-post.md"
        content.write_text(f"{distribution.DRAFT_MARKER}\nDraft. {canonical}\n", encoding="utf-8")
        (root / "diagrams" / "visual.svg").write_text("<svg/>", encoding="utf-8")
        package = {
            "id": "chapter-05-post", "chapter": 5, "channel": "linkedin_post",
            "canonical_url": canonical, "source_revision": "a" * 40,
            "source_path": "guide/05-throughput.md",
            "content_path": "distribution/packages/chapter-05-post.md",
            "visual_path": "diagrams/visual.svg", "alt_text": "A bounded flow.",
            "visual_sha256": hashlib.sha256((root / "diagrams" / "visual.svg").read_bytes()).hexdigest(),
            "evidence_cutoff": "2026-07-11",
            "content_sha256": hashlib.sha256(content.read_bytes()).hexdigest(),
        }
        manifest = {"schema_version": 1, "packages": [package]}
        self.write(root, manifest)
        return root, manifest

    @staticmethod
    def write(root: Path, manifest: dict) -> None:
        (root / "distribution" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def validate(self, root: Path) -> int:
        return distribution.validate_distribution(root, verify_git=False)

    def test_repository_manifest_and_valid_draft(self) -> None:
        self.assertEqual(
            distribution.validate_distribution(),
            len(distribution.load_manifest()["packages"]),
        )
        root, _ = self.fixture()
        self.assertEqual(self.validate(root), 1)

    def test_authorization_or_publication_fields_fail_closed(self) -> None:
        root, manifest = self.fixture()
        for field in ("status", "h4", "external_url", "published_at"):
            candidate = copy.deepcopy(manifest)
            candidate["packages"][0][field] = "forged"
            self.write(root, candidate)
            with self.assertRaisesRegex(distribution.DistributionValidationError, "field set"):
                self.validate(root)

    def test_identity_shape_and_ownership_failures(self) -> None:
        root, manifest = self.fixture()
        cases = (
            (lambda value: value.update(extra=True), "must contain"),
            (lambda value: value["packages"].append(copy.deepcopy(value["packages"][0])), "duplicate ID"),
            (lambda value: value["packages"][0].update(channel="email"), "channel"),
            (lambda value: value["packages"][0].update(chapter=True), "chapter"),
            (lambda value: value["packages"][0].update(canonical_url="https://example.com/x"), "source or canonical"),
            (lambda value: value["packages"][0].update(canonical_url="https://selamy.dev/agent-fleets/05-other/"), "disagree"),
            (lambda value: value["packages"][0].update(canonical_url="https://selamy.dev/agent-fleets/04-throughput/"), "disagree"),
            (lambda value: value["packages"][0].update(canonical_url="https://selamy.dev/agent-fleets/throughput/"), "source or canonical"),
            (lambda value: value["packages"][0].update(source_revision="main"), "immutable"),
        )
        for mutate, message in cases:
            candidate = copy.deepcopy(manifest)
            mutate(candidate)
            self.write(root, candidate)
            with self.assertRaisesRegex(distribution.DistributionValidationError, message):
                self.validate(root)

    def test_content_visual_and_cutoff_failures(self) -> None:
        root, manifest = self.fixture()
        cases = (
            ("source_path", "README.md", "source or canonical"),
            ("content_path", "distribution/packages/missing.md", "missing package file"),
            ("visual_path", "private/visual.svg", "unsafe visual"),
            ("alt_text", "", "lacks alt text"),
            ("visual_sha256", "0" * 64, "visual digest"),
            ("evidence_cutoff", "sometime", "evidence cutoff"),
            ("content_sha256", "0" * 64, "invalid or stale"),
        )
        for field, value, message in cases:
            candidate = copy.deepcopy(manifest)
            candidate["packages"][0][field] = value
            self.write(root, candidate)
            with self.assertRaisesRegex(distribution.DistributionValidationError, message):
                self.validate(root)
        candidate = copy.deepcopy(manifest)
        candidate["packages"][0]["visual_path"] = None
        self.write(root, candidate)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "without a visual"):
            self.validate(root)
        candidate["packages"][0].update(visual_path=None, alt_text=None, visual_sha256=None)
        self.write(root, candidate)
        self.assertEqual(self.validate(root), 1)

    def test_canonical_link_and_git_source_are_verified(self) -> None:
        root, manifest = self.fixture()
        source_bytes = (root / manifest["packages"][0]["source_path"]).read_bytes()
        visual_bytes = (root / manifest["packages"][0]["visual_path"]).read_bytes()
        with mock.patch.object(distribution.subprocess, "run", side_effect=[mock.Mock(returncode=0, stdout=source_bytes), mock.Mock(returncode=0, stdout=visual_bytes)]) as invoked:
            self.assertEqual(distribution.validate_distribution(root), 1)
        verified = [call.args[0][-1] for call in invoked.call_args_list]
        self.assertEqual(verified, ["a" * 40 + ":guide/05-throughput.md", "a" * 40 + ":diagrams/visual.svg"])
        with mock.patch.object(distribution.subprocess, "run", side_effect=[mock.Mock(returncode=0, stdout=source_bytes), mock.Mock(returncode=0, stdout=b"different pinned visual")]):
            with self.assertRaisesRegex(distribution.DistributionValidationError, "blob digest differs"):
                distribution.validate_distribution(root)
        content = root / manifest["packages"][0]["content_path"]
        content.write_text(f"{distribution.DRAFT_MARKER}\nNo canonical link.\n", encoding="utf-8")
        manifest["packages"][0]["content_sha256"] = hashlib.sha256(content.read_bytes()).hexdigest()
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "exactly once"):
            self.validate(root)
        content.write_text(f"{distribution.DRAFT_MARKER}\n{manifest['packages'][0]['canonical_url']}\n{manifest['packages'][0]['canonical_url']}\n", encoding="utf-8")
        manifest["packages"][0]["content_sha256"] = hashlib.sha256(content.read_bytes()).hexdigest()
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "exactly once"):
            self.validate(root)
        content.write_text(f"Draft. {manifest['packages'][0]['canonical_url']}\n", encoding="utf-8")
        manifest["packages"][0]["content_sha256"] = hashlib.sha256(content.read_bytes()).hexdigest()
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "pre-H4 marker"):
            self.validate(root)
        with mock.patch.object(distribution.subprocess, "run", return_value=mock.Mock(returncode=1)):
            with self.assertRaisesRegex(distribution.DistributionValidationError, "does not contain"):
                distribution._verify_revision_path(root, "a" * 40, "guide/05-throughput.md")

    def test_load_and_cli_failures(self) -> None:
        root, _ = self.fixture()
        (root / "distribution" / "manifest.json").write_text("not json", encoding="utf-8")
        with self.assertRaisesRegex(distribution.DistributionValidationError, "cannot load"):
            self.validate(root)
        with mock.patch.object(distribution, "validate_distribution", return_value=2):
            self.assertEqual(distribution.main(), 0)
        with mock.patch.object(distribution, "validate_distribution", side_effect=distribution.DistributionValidationError("bad")):
            self.assertEqual(distribution.main(), 1)


if __name__ == "__main__":
    unittest.main()
