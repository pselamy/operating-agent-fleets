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
        (root / "diagrams" / "chapter-05").mkdir()
        (root / "assets").mkdir()
        (root / "guide" / "05-throughput.md").write_text("# 5. Chapter\n", encoding="utf-8")
        canonical = "https://selamy.dev/agent-fleets/05-throughput/"
        content = root / "distribution" / "packages" / "chapter-05-post.md"
        content.write_text(f"{distribution.DRAFT_MARKER}\nDraft. {canonical}\nWhat do you think?\n", encoding="utf-8")
        visual_path = root / "diagrams" / "chapter-05" / "visual.light.svg"
        visual_path.write_text("<svg/>", encoding="utf-8")
        visual_digest = hashlib.sha256(visual_path.read_bytes()).hexdigest()
        (root / "assets" / "manifest.json").write_text(
            json.dumps({"schema_version": 1, "assets": []}), encoding="utf-8")
        (root / "diagrams" / "manifest.json").write_text(
            json.dumps({
                "schema_version": 1,
                "renderer": {},
                "diagrams": [{
                    "alt_text": "A bounded flow.",
                    "exports": [{"path": "diagrams/chapter-05/visual.light.svg", "sha256": visual_digest}],
                }],
            }),
            encoding="utf-8",
        )
        package = {
            "id": "chapter-05-post", "chapter": 5, "channel": "linkedin_post",
            "canonical_url": canonical, "source_revision": "a" * 40,
            "source_path": "guide/05-throughput.md",
            "content_path": "distribution/packages/chapter-05-post.md",
            "visual_path": "diagrams/chapter-05/visual.light.svg", "alt_text": "A bounded flow.",
            "visual_sha256": visual_digest,
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
        return distribution.validate_distribution(
            root, verify_git=False, validate_visual_registries=False)

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
            ("visual_path", "assets/README.md", "not registered"),
            ("alt_text", "Different alt text.", "differs from its registry"),
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
        candidate["packages"][0]["channel"] = "linkedin_newsletter"
        candidate["packages"][0]["visual_path"] = None
        self.write(root, candidate)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "without a visual"):
            self.validate(root)
        candidate["packages"][0].update(visual_path=None, alt_text=None, visual_sha256=None)
        self.write(root, candidate)
        self.assertEqual(self.validate(root), 1)

    def test_linkedin_post_channel_contract(self) -> None:
        root, manifest = self.fixture()
        content = root / manifest["packages"][0]["content_path"]
        content.write_text(
            f"{distribution.DRAFT_MARKER}\n{manifest['packages'][0]['canonical_url']}\nNo question.\n",
            encoding="utf-8",
        )
        manifest["packages"][0]["content_sha256"] = hashlib.sha256(content.read_bytes()).hexdigest()
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "exactly one visible question"):
            self.validate(root)

        content.write_text(
            f"{distribution.DRAFT_MARKER}\n{manifest['packages'][0]['canonical_url']}\n"
            + "x" * distribution.LINKEDIN_POST_MAX_CHARACTERS
            + "?\n",
            encoding="utf-8",
        )
        manifest["packages"][0]["content_sha256"] = hashlib.sha256(content.read_bytes()).hexdigest()
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "exactly one visible question"):
            self.validate(root)

        for ending in ("First? Second?", "No visible question.\n<!-- ? -->", "No visible question.\n<!-- ?"):
            content.write_text(
                f"{distribution.DRAFT_MARKER}\n{manifest['packages'][0]['canonical_url']}\n{ending}\n",
                encoding="utf-8",
            )
            manifest["packages"][0]["content_sha256"] = hashlib.sha256(content.read_bytes()).hexdigest()
            self.write(root, manifest)
            with self.assertRaisesRegex(
                    distribution.DistributionValidationError,
                    "exactly one visible question|additional HTML comment"):
                self.validate(root)

        content.write_text(
            f"{distribution.DRAFT_MARKER}\n{manifest['packages'][0]['canonical_url']}\nQuestion?\n",
            encoding="utf-8",
        )
        manifest["packages"][0].update(
            visual_path=None,
            alt_text=None,
            visual_sha256=None,
            content_sha256=hashlib.sha256(content.read_bytes()).hexdigest(),
        )
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "required visual"):
            self.validate(root)

    def test_duplicate_channel_content_and_publication_claims_fail(self) -> None:
        root, manifest = self.fixture()
        duplicate = copy.deepcopy(manifest["packages"][0])
        duplicate["id"] = "chapter-05-post-second"
        manifest["packages"].append(duplicate)
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "duplicates a chapter and channel"):
            self.validate(root)

        duplicate.update(chapter=6, source_path="guide/06-throughput.md")
        (root / "guide" / "06-throughput.md").write_text("# 6. Chapter\n", encoding="utf-8")
        duplicate["canonical_url"] = "https://selamy.dev/agent-fleets/06-throughput/"
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "reuses a content path"):
            self.validate(root)

        manifest["packages"] = [manifest["packages"][0]]
        content = root / manifest["packages"][0]["content_path"]
        for claim in (
            "H4: PASS",
            "H4 has passed",
            "Approved to publish",
            "Approved for publication",
            "Authorized for publication",
            "Patrick approved publication",
            "This has been published",
            "Now published",
            "This is live",
            "Ready to publish",
        ):
            content.write_text(
                f"{distribution.DRAFT_MARKER}\n{claim}.\n"
                f"{manifest['packages'][0]['canonical_url']}\nQuestion?\n",
                encoding="utf-8",
            )
            manifest["packages"][0]["content_sha256"] = hashlib.sha256(content.read_bytes()).hexdigest()
            self.write(root, manifest)
            with self.assertRaisesRegex(distribution.DistributionValidationError, "forbidden publication claim"):
                self.validate(root)

    def test_visual_must_be_registered_with_reviewed_alt_text(self) -> None:
        root, manifest = self.fixture()
        (root / "assets" / "README.md").write_text("not an image", encoding="utf-8")
        package = manifest["packages"][0]
        package.update(
            visual_path="assets/README.md",
            visual_sha256=hashlib.sha256((root / "assets" / "README.md").read_bytes()).hexdigest(),
            alt_text="x",
        )
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "not registered"):
            self.validate(root)

        (root / "assets" / "manifest.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(distribution.DistributionValidationError, "cannot load reviewed visual registries"):
            self.validate(root)

    def test_visual_registries_are_validated_and_paths_are_confined(self) -> None:
        root, manifest = self.fixture()
        with (mock.patch.object(distribution, "validate_asset_registry") as assets,
              mock.patch.object(distribution, "validate_diagram_registry") as diagrams):
            self.assertEqual(distribution.validate_distribution(root, verify_git=False), 1)
            assets.assert_called_once_with(root)
            diagrams.assert_called_once_with(root)

        with mock.patch.object(
                distribution, "validate_asset_registry", side_effect=ValueError("bad registry")):
            with self.assertRaisesRegex(distribution.DistributionValidationError, "registry validation failed"):
                distribution.validate_distribution(root, verify_git=False)

        private = root / "private"
        private.mkdir()
        (private / "arbitrary.png").write_bytes(b"not an image")
        digest = hashlib.sha256((private / "arbitrary.png").read_bytes()).hexdigest()
        (root / "assets" / "manifest.json").write_text(
            json.dumps({
                "schema_version": 1,
                "assets": [{"path": "private/arbitrary.png", "sha256": digest, "alt_text": "Forged."}],
            }),
            encoding="utf-8",
        )
        manifest["packages"][0].update(
            visual_path="private/arbitrary.png", visual_sha256=digest, alt_text="Forged.")
        self.write(root, manifest)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "invalid or duplicate entry"):
            self.validate(root)

    def test_medium_channel_requires_exact_delayed_import_envelope(self) -> None:
        root, manifest = self.fixture()
        package = manifest["packages"][0]
        package.update(channel="medium", visual_path=None, alt_text=None, visual_sha256=None)
        content = root / package["content_path"]

        def write_medium(value: str) -> None:
            content.write_text(value, encoding="utf-8")
            package["content_sha256"] = hashlib.sha256(content.read_bytes()).hexdigest()
            self.write(root, manifest)

        exact = distribution._medium_envelope(package, "Chapter")
        write_medium(exact)
        self.assertEqual(self.validate(root), 1)

        mutations = (
            exact.replace("Canonical title:** Chapter", "Canonical title:** Wrong title"),
            exact.replace("independently confirmed indexed with observer and timestamp", "indexable"),
            exact.replace("Stop if Patrick's exact-preview decision is absent", "Continue without a human decision"),
            exact.replace("independently retrieve the Medium page", "trust the workflow status"),
            exact + "\n# Duplicate article body\n",
            exact.replace("not the article body", "not the article body; import completed successfully"),
        )
        for candidate in mutations:
            write_medium(candidate)
            with self.assertRaisesRegex(distribution.DistributionValidationError, "delayed Medium import contract"):
                self.validate(root)

        with self.assertRaisesRegex(distribution.DistributionValidationError, "title disagrees"):
            distribution._chapter_title(b"# 6. Wrong chapter\n", 5)
        with self.assertRaisesRegex(distribution.DistributionValidationError, "UTF-8 title"):
            distribution._chapter_title(b"\xff", 5)

    def test_canonical_link_and_git_source_are_verified(self) -> None:
        root, manifest = self.fixture()
        source_bytes = (root / manifest["packages"][0]["source_path"]).read_bytes()
        visual_bytes = (root / manifest["packages"][0]["visual_path"]).read_bytes()
        with mock.patch.object(distribution.subprocess, "run", side_effect=[mock.Mock(returncode=0, stdout=source_bytes), mock.Mock(returncode=0, stdout=visual_bytes)]) as invoked:
            self.assertEqual(distribution.validate_distribution(
                root, validate_visual_registries=False), 1)
        verified = [call.args[0][-1] for call in invoked.call_args_list]
        self.assertEqual(verified, [
            "a" * 40 + ":guide/05-throughput.md",
            "a" * 40 + ":diagrams/chapter-05/visual.light.svg",
        ])
        with mock.patch.object(distribution.subprocess, "run", side_effect=[mock.Mock(returncode=0, stdout=source_bytes), mock.Mock(returncode=0, stdout=b"different pinned visual")]):
            with self.assertRaisesRegex(distribution.DistributionValidationError, "blob digest differs"):
                distribution.validate_distribution(root, validate_visual_registries=False)
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
