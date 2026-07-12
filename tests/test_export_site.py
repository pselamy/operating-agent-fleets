from __future__ import annotations

import json
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.export_site import ROOT, ExportError, build_bundle, git_state, load_manifest, main, validate_entries


def entry(source: str, destination: str, channel: str = "preview") -> dict[str, str]:
    return {
        "source": source,
        "destination": destination,
        "channel": channel,
        "media_type": "text/markdown",
    }


class SiteExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "source"
        (self.root / "guide").mkdir(parents=True)
        (self.root / "guide" / "chapter.md").write_text("# Stable chapter\n", encoding="utf-8")
        (self.root / "guide" / "release.md").write_text("# Released chapter\n", encoding="utf-8")

    def manifest(self, entries):
        return {"schema_version": 1, "entries": entries}

    def test_repository_preview_includes_required_chapter_7_artifacts(self) -> None:
        document = load_manifest(ROOT / "export" / "site-manifest.json")
        entries = validate_entries(ROOT, document["entries"])
        chapter_7 = {
            item["source"]: item
            for item in entries
            if item["source"].startswith(("guide/07-", "diagrams/chapter-07/"))
        }
        self.assertEqual(set(chapter_7), {
            "guide/07-agent-portfolio.md",
            "diagrams/chapter-07/agent-lifecycle-state-machine.light.svg",
            "diagrams/chapter-07/agent-lifecycle-state-machine.dark.svg",
        })
        self.assertTrue(all(item["channel"] == "preview" for item in chapter_7.values()))

    def test_repository_preview_includes_exact_editorial_hero_surface(self) -> None:
        document = load_manifest(ROOT / "export" / "site-manifest.json")
        entries = validate_entries(ROOT, document["entries"])
        editorial = {
            item["source"]: item
            for item in entries
            if item["source"].startswith("assets/")
        }
        self.assertEqual(set(editorial), {
            "assets/manifest.json",
            "assets/generated/field-guide-hero.png",
        })
        self.assertTrue(all(item["channel"] == "preview" for item in editorial.values()))

    def test_preview_export_is_deterministic(self) -> None:
        manifest = self.manifest([entry("guide/chapter.md", "content/chapter.md")])
        first = Path(self.directory.name) / "first"
        second = Path(self.directory.name) / "second"
        one = build_bundle(self.root, first, channel="preview", revision="abc123", dirty=True, manifest=manifest)
        two = build_bundle(self.root, second, channel="preview", revision="abc123", dirty=True, manifest=manifest)
        self.assertEqual(one, two)
        self.assertEqual((first / "content" / "chapter.md").read_bytes(), (second / "content" / "chapter.md").read_bytes())
        self.assertEqual((first / "export-metadata.json").read_bytes(), (second / "export-metadata.json").read_bytes())

    def test_release_includes_only_release_entries(self) -> None:
        manifest = self.manifest([
            entry("guide/chapter.md", "content/chapter.md"),
            entry("guide/release.md", "content/release.md", channel="release"),
        ])
        output = Path(self.directory.name) / "release-output"
        metadata = build_bundle(self.root, output, channel="release", revision="abc123", dirty=False, manifest=manifest)
        self.assertEqual([item["destination"] for item in metadata["entries"]], ["content/release.md"])
        self.assertFalse((output / "content" / "chapter.md").exists())

    def test_release_refuses_dirty_tree(self) -> None:
        with self.assertRaisesRegex(ExportError, "clean working tree"):
            build_bundle(
                self.root,
                Path(self.directory.name) / "output",
                channel="release",
                revision="abc123",
                dirty=True,
                manifest=self.manifest([]),
            )

    def test_rejects_traversal_absolute_and_forbidden_paths(self) -> None:
        invalid = [
            entry("../restricted.md", "content/chapter.md"),
            entry("/guide/chapter.md", "content/chapter.md"),
            entry("guide/chapter.md", "../outside.md"),
            entry("guide/private/chapter.md", "content/chapter.md"),
            entry("guide/chapter.md", "static/confidential/chapter.md"),
        ]
        for candidate in invalid:
            with self.subTest(candidate=candidate), self.assertRaises(ExportError):
                validate_entries(self.root, [candidate])

    def test_rejects_symlink_source(self) -> None:
        (self.root / "guide" / "linked.md").symlink_to(self.root / "guide" / "chapter.md")
        with self.assertRaisesRegex(ExportError, "symlink"):
            validate_entries(self.root, [entry("guide/linked.md", "content/linked.md")])

    def test_rejects_duplicate_destination(self) -> None:
        with self.assertRaisesRegex(ExportError, "duplicates"):
            validate_entries(self.root, [
                entry("guide/chapter.md", "content/same.md"),
                entry("guide/release.md", "content/same.md"),
            ])

    def test_rejects_nonempty_output(self) -> None:
        output = Path(self.directory.name) / "output"
        output.mkdir()
        (output / "existing.txt").write_text("do not overwrite", encoding="utf-8")
        with self.assertRaisesRegex(ExportError, "output"):
            build_bundle(
                self.root,
                output,
                channel="preview",
                revision="abc123",
                dirty=False,
                manifest=self.manifest([]),
            )

    def test_metadata_hash_matches_emitted_bytes(self) -> None:
        output = Path(self.directory.name) / "output"
        metadata = build_bundle(
            self.root,
            output,
            channel="preview",
            revision="abc123",
            dirty=False,
            manifest=self.manifest([entry("guide/chapter.md", "content/chapter.md")]),
        )
        stored = json.loads((output / "export-metadata.json").read_text())
        self.assertEqual(stored, metadata)
        self.assertEqual(metadata["entries"][0]["bytes"], len(b"# Stable chapter\n"))

    def test_manifest_loader_accepts_contract_and_rejects_bad_shapes(self) -> None:
        export = self.root / "export"
        export.mkdir()
        path = export / "site-manifest.json"
        document = self.manifest([entry("guide/chapter.md", "content/chapter.md")])
        path.write_text(json.dumps(document), encoding="utf-8")
        self.assertEqual(load_manifest(path), document)
        for invalid in ({"schema_version": 2, "entries": []}, {"schema_version": 1}, []):
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.subTest(invalid=invalid), self.assertRaises(ExportError):
                load_manifest(path)
        path.write_text("not json", encoding="utf-8")
        with self.assertRaisesRegex(ExportError, "cannot load"):
            load_manifest(path)

    def test_rejects_unknown_fields_media_channel_root_and_missing_file(self) -> None:
        candidates = [
            {**entry("guide/chapter.md", "content/chapter.md"), "extra": True},
            {**entry("guide/chapter.md", "content/chapter.md"), "media_type": "text/html"},
            entry("guide/chapter.md", "content/chapter.md", channel="unknown"),
            entry("tools/export_site.py", "content/chapter.md"),
            entry("guide/missing.md", "content/missing.md"),
        ]
        for candidate in candidates:
            with self.subTest(candidate=candidate), self.assertRaises(ExportError):
                validate_entries(self.root, [candidate])

    def test_git_state_and_cli_preview(self) -> None:
        (self.root / "export").mkdir()
        manifest = self.manifest([entry("guide/chapter.md", "content/chapter.md")])
        (self.root / "export" / "site-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Synthetic Test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "synthetic@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "synthetic fixture"], cwd=self.root, check=True)
        revision, dirty = git_state(self.root)
        self.assertEqual(len(revision), 40)
        self.assertFalse(dirty)
        output = Path(self.directory.name) / "cli-output"
        stdout = io.StringIO()
        with mock.patch(
            "sys.argv",
            ["export_site.py", "--root", str(self.root), "--output", str(output), "--channel", "preview"],
        ), mock.patch("sys.stdout", stdout):
            self.assertEqual(main(), 0)
        self.assertEqual(json.loads(stdout.getvalue())["source_revision"], revision)

    def test_cli_failure_is_redacted_to_contract_error(self) -> None:
        output = Path(self.directory.name) / "cli-failure"
        stderr = io.StringIO()
        with mock.patch(
            "sys.argv",
            ["export_site.py", "--root", str(self.root), "--output", str(output), "--channel", "preview"],
        ), mock.patch("sys.stderr", stderr):
            self.assertEqual(main(), 1)
        self.assertIn("site export failed", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
