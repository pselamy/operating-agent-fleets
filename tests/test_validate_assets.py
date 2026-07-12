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
            "id": "editorial.hero", "role": "field_guide_hero",
            "path": "assets/generated/hero.png", "media_type": "image/png",
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "width": 2, "height": 3,
            "alt_text": "A useful synthetic alternative description.", "created_at": "2026-07-12",
            "creation_method": "synthetic test", "generation_provider": "test provider",
            "generation_model": "test model v1", "prompt": "synthetic prompt",
            "text_policy": "no_text_in_generated_pixels", "claim_status": "conceptual_not_evidence",
        }
        document = {"schema_version": 1, "assets": [asset]}
        self.write(root, document)
        return root, document

    @staticmethod
    def write(root: Path, document: dict) -> None:
        (root / "assets" / "manifest.json").write_text(json.dumps(document), encoding="utf-8")

    def test_repository_asset_and_valid_fixture(self) -> None:
        self.assertEqual(assets.validate_assets(), 1)
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
            ("prompt", "", "prompt"),
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
