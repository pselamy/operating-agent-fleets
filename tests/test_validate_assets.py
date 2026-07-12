from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "tools" / "validate_assets.py"
SPEC = importlib.util.spec_from_file_location("validate_assets", MODULE_PATH)
assets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assets)


def png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    pixels = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")


class AssetValidationTests(unittest.TestCase):
    def fixture(self) -> tuple[Path, dict]:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        target = root / "assets" / "generated" / "hero.png"
        target.parent.mkdir(parents=True)
        target.write_bytes(png(2, 3))
        asset = {
            "id": "editorial.hero", "role": "conceptual_illustration",
            "path": "assets/generated/hero.png", "media_type": "image/png",
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "width": 2, "height": 3,
            "alt_text": "A useful synthetic alternative description.", "created_at": "2026-07-12",
            "provenance_type": "generated", "creation_method": "synthetic test", "generation_provider": "test provider",
            "generation_model": "test model v1", "prompt": "synthetic prompt",
            "sources": [],
            "derivation": None,
            "text_policy": "no_text_in_generated_pixels", "claim_status": "conceptual_not_evidence",
        }
        document = {"schema_version": 1, "assets": [asset]}
        self.write(root, document)
        return root, document

    @staticmethod
    def write(root: Path, document: dict) -> None:
        (root / "assets" / "manifest.json").write_text(json.dumps(document), encoding="utf-8")

    def test_repository_asset_and_valid_fixture(self) -> None:
        manifest = json.loads((assets.ROOT / "assets" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(assets.validate_assets(), len(manifest["assets"]))
        root, _ = self.fixture()
        self.assertEqual(assets.validate_assets(root), 1)

    def test_shape_identity_and_policy_fail_closed(self) -> None:
        root, document = self.fixture()
        cases = (
            (lambda value: value.update(extra=True), "must contain"),
            (lambda value: value["assets"].append(copy.deepcopy(value["assets"][0])), "duplicate ID"),
            (lambda value: value["assets"][0].update(role="avatar"), "role or policy"),
            (lambda value: value["assets"][0].update(text_policy="generated_title"), "role or policy"),
            (lambda value: value["assets"][0].update(alt_text="short"), "alt text"),
            (lambda value: value["assets"][0].update(width=True), "dimension metadata"),
            (lambda value: value["assets"][0].update(role="social_card_template"), "role-specific contract"),
        )
        for mutate, message in cases:
            candidate = copy.deepcopy(document)
            mutate(candidate)
            self.write(root, candidate)
            with self.assertRaisesRegex(assets.AssetValidationError, message):
                assets.validate_assets(root)

    def test_path_digest_dimensions_and_provenance_fail_closed(self) -> None:
        root, document = self.fixture()
        cases = (
            ("path", "private/hero.png", "path"),
            ("sha256", "0" * 64, "digest"),
            ("width", 4, "dimensions"),
            ("media_type", "image/svg+xml", "media contract"),
            ("created_at", "today", "provenance"),
            ("created_at", "2026-02-31", "creation date"),
            ("generation_model", "", "generator provenance"),
            ("prompt", "", "generator provenance"),
        )
        for field, value, message in cases:
            candidate = copy.deepcopy(document)
            candidate["assets"][0][field] = value
            self.write(root, candidate)
            with self.assertRaisesRegex(assets.AssetValidationError, message):
                assets.validate_assets(root)

    def test_unregistered_and_corrupt_pngs_fail_closed(self) -> None:
        root, document = self.fixture()
        unregistered = root / "assets" / "generated" / "extra.png"
        unregistered.write_bytes(png(1, 1))
        with self.assertRaisesRegex(assets.AssetValidationError, "manifest paths differ"):
            assets.validate_assets(root)
        unregistered.unlink()
        unsupported = root / "assets" / "generated" / "extra.webp"
        unsupported.write_bytes(b"not an allowed asset")
        with self.assertRaisesRegex(assets.AssetValidationError, "manifest paths differ"):
            assets.validate_assets(root)
        unsupported.unlink()
        target = root / document["assets"][0]["path"]
        target.write_bytes(target.read_bytes()[:-8])
        document["assets"][0]["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        self.write(root, document)
        with self.assertRaisesRegex(assets.AssetValidationError, "incomplete PNG"):
            assets.validate_assets(root)

    def test_source_controlled_svg_contract_and_active_content(self) -> None:
        root, document = self.fixture()
        target = root / "assets" / "templates" / "card.svg"
        target.parent.mkdir()
        valid = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="627" viewBox="0 0 1200 627" '
            'role="img" aria-labelledby="title desc"><title id="title">Card</title>'
            '<desc id="desc">Accessible description</desc><rect width="1200" height="627"/></svg>'
        )
        target.write_text(valid, encoding="utf-8")
        record = copy.deepcopy(document["assets"][0])
        record.update({
            "id": "editorial.card", "role": "social_card_template",
            "path": "assets/templates/card.svg", "media_type": "image/svg+xml",
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "width": 1200, "height": 627,
            "provenance_type": "source_controlled", "creation_method": "hand-authored SVG",
            "generation_provider": None, "generation_model": None, "prompt": None,
            "text_policy": "source_controlled_overlay",
        })
        document["assets"].append(record)
        self.write(root, document)
        self.assertEqual(assets.validate_assets(root), 2)
        record["generation_provider"] = "not allowed"
        self.write(root, document)
        with self.assertRaisesRegex(assets.AssetValidationError, "source-controlled provenance"):
            assets.validate_assets(root)
        record["generation_provider"] = None
        target.write_text(valid.replace("</svg>", '<script>bad()</script></svg>'), encoding="utf-8")
        record["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        self.write(root, document)
        with self.assertRaisesRegex(assets.AssetValidationError, "active content"):
            assets.validate_assets(root)
        for fragment in (
            '<animate attributeName="opacity" values="0;1"/>',
            '<rect width="1" height="1" fill="url(https://example.com/paint)"/>',
            '<rect width="1" height="1" style="fill:red"/>',
        ):
            target.write_text(valid.replace("</svg>", fragment + "</svg>"), encoding="utf-8")
            record["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
            self.write(root, document)
            with self.assertRaisesRegex(assets.AssetValidationError, "unsupported|unsafe"):
                assets.validate_assets(root)

    def test_source_controlled_provenance_and_svg_reference_fail_closed(self) -> None:
        root, document = self.fixture()
        record = document["assets"][0]
        record.update(provenance_type="source_controlled", generation_provider=None, generation_model=None, prompt=None)
        self.write(root, document)
        with self.assertRaisesRegex(assets.AssetValidationError, "role-specific contract"):
            assets.validate_assets(root)
        target = root / record["path"]
        target.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="2" height="3" viewBox="0 0 2 3" role="img" '
            'aria-labelledby="t d"><title id="t">T</title><desc id="d">D</desc><rect width="2" height="3" fill="url(https://example.com/x)"/></svg>',
            encoding="utf-8",
        )
        record.update(media_type="image/svg+xml", path="assets/generated/hero.svg", sha256=hashlib.sha256(target.read_bytes()).hexdigest(), text_policy="source_controlled_overlay")
        target.rename(root / record["path"])
        self.write(root, document)
        with self.assertRaisesRegex(assets.AssetValidationError, "unsafe reference"):
            assets.validate_assets(root)

    def test_derived_thumbnail_binds_to_immutable_source(self) -> None:
        root, document = self.fixture()
        source = root / "diagrams" / "chapter-01" / "sample.light.svg"
        source.parent.mkdir(parents=True)
        source.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")
        renderer = root / "tools" / "render_diagram_thumbnail.py"
        renderer.parent.mkdir()
        renderer.write_text("synthetic renderer", encoding="utf-8")
        target = root / "assets" / "thumbnails" / "sample.png"
        target.parent.mkdir()
        target.write_bytes(png(1200, 627))
        record = copy.deepcopy(document["assets"][0])
        record.update({
            "id": "editorial.thumbnail-sample", "role": "diagram_thumbnail",
            "path": "assets/thumbnails/sample.png", "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "width": 1200, "height": 627, "provenance_type": "derived",
            "creation_method": "bounded browser renderer", "generation_provider": None,
            "generation_model": None, "prompt": None, "text_policy": "source_controlled_overlay",
            "sources": [{"path": "diagrams/chapter-01/sample.light.svg", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}],
            "derivation": {"contract_version": 1, "renderer_path": "tools/render_diagram_thumbnail.py",
                           "renderer_sha256": hashlib.sha256(renderer.read_bytes()).hexdigest(),
                           "parameters": {"title": "Synthetic thumbnail", "takeaway": "A synthetic but valid takeaway.",
                                          "lanes": [["First step", "Second step"]]}},
        })
        document["assets"].append(record)
        self.write(root, document)
        self.assertEqual(assets.validate_assets(root), 2)

        cases = (
            (lambda item: item.update(sources=[]), "derived provenance"),
            (lambda item: item.update(generation_model="browser model"), "derived provenance"),
            (lambda item: item["sources"][0].update(sha256="0" * 64), "source digest"),
            (lambda item: item["sources"][0].update(path="private/sample.light.svg"), "source provenance"),
            (lambda item: item["sources"][0].update(path="diagrams/chapter-01/sample.dark.svg"), "light-theme SVG"),
            (lambda item: item["derivation"].update(renderer_sha256="0" * 64), "renderer provenance"),
            (lambda item: item["derivation"]["parameters"].update(lanes=[]), "derivation parameters"),
        )
        for mutate, message in cases:
            candidate = copy.deepcopy(document)
            mutate(candidate["assets"][1])
            self.write(root, candidate)
            with self.assertRaisesRegex(assets.AssetValidationError, message):
                assets.validate_assets(root)

    def test_derived_thumbnail_rejects_symlinked_source(self) -> None:
        root, document = self.fixture()
        outside = root / "outside.svg"
        outside.write_text("source", encoding="utf-8")
        source = root / "diagrams" / "chapter-01" / "sample.light.svg"
        source.parent.mkdir(parents=True)
        source.symlink_to(outside)
        renderer = root / "tools" / "render_diagram_thumbnail.py"
        renderer.parent.mkdir()
        renderer.write_text("synthetic renderer", encoding="utf-8")
        target = root / "assets" / "thumbnails" / "sample.png"
        target.parent.mkdir()
        target.write_bytes(png(1200, 627))
        record = copy.deepcopy(document["assets"][0])
        record.update({
            "id": "editorial.thumbnail-sample", "role": "diagram_thumbnail",
            "path": "assets/thumbnails/sample.png", "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "width": 1200, "height": 627, "provenance_type": "derived",
            "creation_method": "bounded browser renderer", "generation_provider": None,
            "generation_model": None, "prompt": None, "text_policy": "source_controlled_overlay",
            "sources": [{"path": "diagrams/chapter-01/sample.light.svg", "sha256": hashlib.sha256(outside.read_bytes()).hexdigest()}],
            "derivation": {"contract_version": 1, "renderer_path": "tools/render_diagram_thumbnail.py",
                           "renderer_sha256": hashlib.sha256(renderer.read_bytes()).hexdigest(),
                           "parameters": {"title": "Synthetic thumbnail", "takeaway": "A synthetic but valid takeaway.",
                                          "lanes": [["First step", "Second step"]]}},
        })
        document["assets"].append(record)
        self.write(root, document)
        with self.assertRaisesRegex(assets.AssetValidationError, "source path is unsafe"):
            assets.validate_assets(root)

    def test_loader_header_and_cli_failures(self) -> None:
        root, _ = self.fixture()
        (root / "assets" / "manifest.json").write_text("not json", encoding="utf-8")
        with self.assertRaisesRegex(assets.AssetValidationError, "cannot load"):
            assets.validate_assets(root)
        with mock.patch.object(assets, "validate_assets", return_value=2):
            self.assertEqual(assets.main(), 0)
        with mock.patch.object(assets, "validate_assets", side_effect=assets.AssetValidationError("bad")):
            self.assertEqual(assets.main(), 1)


if __name__ == "__main__":
    unittest.main()
