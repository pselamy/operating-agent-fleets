#!/usr/bin/env python3
"""Validate editorial asset identity, dimensions, provenance, and accessibility."""

from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
import zlib
from datetime import date
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    "id", "role", "path", "media_type", "sha256", "width", "height",
    "alt_text", "created_at", "provenance_type", "creation_method",
    "generation_provider", "generation_model", "prompt", "text_policy",
    "claim_status",
}
ROLES = {"field_guide_hero", "conceptual_illustration", "social_card_template", "diagram_thumbnail"}
TEXT_POLICIES = {"no_text_in_generated_pixels", "source_controlled_overlay", "not_applicable"}
ID = re.compile(r"^editorial\.[a-z][a-z0-9-]*$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
DATE = re.compile(r"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$")
ASSET_PATH = re.compile(r"^assets/(generated|templates|thumbnails)/[a-z0-9-]+\.(png|svg)$")
SVG_ELEMENTS = {
    "svg", "title", "desc", "defs", "linearGradient", "radialGradient", "stop",
    "filter", "feGaussianBlur", "feMerge", "feMergeNode", "rect", "path", "g",
    "text", "ellipse", "circle",
}
SVG_ATTRIBUTES = {
    "width", "height", "viewBox", "role", "aria-labelledby", "id", "x1", "y1",
    "x2", "y2", "offset", "stop-color", "stop-opacity", "fill-opacity", "cx", "cy", "r", "x",
    "y", "rx", "ry", "fill", "stroke", "stroke-opacity", "stroke-width",
    "stroke-linecap", "font-family", "font-size", "font-weight", "letter-spacing",
    "transform", "d", "filter", "stdDeviation", "result", "in", "text-anchor",
}


class AssetValidationError(ValueError):
    """An editorial asset violates the public visual contract."""


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssetValidationError(f"invalid PNG header: {path.name}")
    offset = 8
    dimensions: tuple[int, int] | None = None
    compressed = bytearray()
    ended = False
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise AssetValidationError(f"truncated PNG chunk: {path.name}")
        payload = data[offset + 8:offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length:end])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != expected_crc:
            raise AssetValidationError(f"invalid PNG checksum: {path.name}")
        if kind == b"IHDR":
            if dimensions is not None or length != 13:
                raise AssetValidationError(f"invalid PNG IHDR: {path.name}")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if depth != 8 or color not in {2, 6} or compression or filtering or interlace:
                raise AssetValidationError(f"unsupported PNG encoding: {path.name}")
            dimensions = (width, height)
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            if length != 0 or end != len(data):
                raise AssetValidationError(f"invalid PNG ending: {path.name}")
            ended = True
            break
        offset = end
    if dimensions is None or not compressed or not ended:
        raise AssetValidationError(f"incomplete PNG: {path.name}")
    try:
        pixels = zlib.decompress(bytes(compressed))
    except zlib.error as exc:
        raise AssetValidationError(f"invalid PNG pixel stream: {path.name}") from exc
    channels = 3 if color == 2 else 4
    if len(pixels) != dimensions[1] * (1 + dimensions[0] * channels):
        raise AssetValidationError(f"invalid PNG pixel length: {path.name}")
    return dimensions


def _svg_dimensions(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise AssetValidationError(f"unsafe SVG document: {path.name}")
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        raise AssetValidationError(f"invalid SVG XML: {path.name}") from exc
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise AssetValidationError(f"invalid SVG root: {path.name}")
    try:
        width, height = int(root.attrib["width"]), int(root.attrib["height"])
    except (KeyError, ValueError) as exc:
        raise AssetValidationError(f"SVG lacks integer dimensions: {path.name}") from exc
    if root.attrib.get("viewBox") != f"0 0 {width} {height}" or root.attrib.get("role") != "img":
        raise AssetValidationError(f"SVG lacks matching viewBox or image role: {path.name}")
    labelled = set(root.attrib.get("aria-labelledby", "").split())
    found_labels: set[str] = set()
    for element in root.iter():
        local = element.tag.rsplit("}", 1)[-1]
        if local not in SVG_ELEMENTS:
            raise AssetValidationError(f"SVG contains unsupported or active content: {path.name}")
        if local in {"title", "desc"} and element.attrib.get("id") in labelled and (element.text or "").strip():
            found_labels.add(local)
        for name, value in element.attrib.items():
            attribute = name.rsplit("}", 1)[-1].lower()
            if attribute not in {item.lower() for item in SVG_ATTRIBUTES}:
                raise AssetValidationError(f"SVG contains an unsupported attribute: {path.name}")
            lowered = value.lower().replace(" ", "")
            urls = re.findall(r"url\(([^)]+)\)", lowered)
            if any(not target.startswith("#") for target in urls) or any(token in lowered for token in ("javascript:", "data:", "http:", "https:", "@import")):
                raise AssetValidationError(f"SVG contains an unsafe reference or handler: {path.name}")
    if found_labels != {"title", "desc"}:
        raise AssetValidationError(f"SVG lacks accessible title and description: {path.name}")
    return width, height


def validate_assets(root: Path = ROOT) -> int:
    try:
        document = json.loads((root / "assets" / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetValidationError(f"cannot load asset manifest: {exc}") from exc
    if not isinstance(document, dict) or set(document) != {"schema_version", "assets"}:
        raise AssetValidationError("manifest must contain schema_version and assets")
    if document["schema_version"] != 1 or not isinstance(document["assets"], list):
        raise AssetValidationError("unsupported asset manifest")

    ids: set[str] = set()
    paths: set[str] = set()
    for index, asset in enumerate(document["assets"]):
        if not isinstance(asset, dict) or set(asset) != FIELDS:
            raise AssetValidationError(f"asset {index} has an invalid field set")
        asset_id = asset["id"]
        if not isinstance(asset_id, str) or ID.fullmatch(asset_id) is None or asset_id in ids:
            raise AssetValidationError(f"asset {index} has an invalid or duplicate ID")
        ids.add(asset_id)
        raw_path = asset["path"]
        if not isinstance(raw_path, str) or ASSET_PATH.fullmatch(raw_path) is None or raw_path in paths:
            raise AssetValidationError(f"asset {asset_id} has an invalid or duplicate path")
        paths.add(raw_path)
        path = root / raw_path
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise AssetValidationError(f"asset {asset_id} is missing") from exc
        if path.is_symlink() or root.resolve() not in resolved.parents or not resolved.is_file():
            raise AssetValidationError(f"asset {asset_id} path is unsafe")
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if not isinstance(asset["sha256"], str) or DIGEST.fullmatch(asset["sha256"]) is None or asset["sha256"] != actual_digest:
            raise AssetValidationError(f"asset {asset_id} digest is invalid or stale")
        media_contract = {".png": "image/png", ".svg": "image/svg+xml"}
        if media_contract.get(path.suffix) != asset["media_type"]:
            raise AssetValidationError(f"asset {asset_id} uses an unsupported media contract")
        if any(not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 7680 for value in (asset["width"], asset["height"])):
            raise AssetValidationError(f"asset {asset_id} has invalid dimension metadata")
        actual_dimensions = _png_dimensions(path) if path.suffix == ".png" else _svg_dimensions(path)
        if actual_dimensions != (asset["width"], asset["height"]):
            raise AssetValidationError(f"asset {asset_id} dimensions are stale")
        if asset["role"] not in ROLES or asset["text_policy"] not in TEXT_POLICIES or asset["claim_status"] != "conceptual_not_evidence":
            raise AssetValidationError(f"asset {asset_id} has invalid role or policy")
        role_contracts = {
            "field_guide_hero": ("assets/generated/", ".png", "generated", (1536, 1024)),
            "social_card_template": ("assets/templates/", ".svg", "source_controlled", (1200, 627)),
            "diagram_thumbnail": ("assets/thumbnails/", ".png", "generated", (1200, 627)),
        }
        if asset["role"] in role_contracts:
            prefix, suffix, provenance, dimensions = role_contracts[asset["role"]]
            if not raw_path.startswith(prefix) or path.suffix != suffix or asset["provenance_type"] != provenance or actual_dimensions != dimensions:
                raise AssetValidationError(f"asset {asset_id} violates its role-specific contract")
        elif asset["role"] == "conceptual_illustration" and (path.suffix != ".png" or asset["provenance_type"] != "generated"):
            raise AssetValidationError(f"asset {asset_id} violates its role-specific contract")
        if not isinstance(asset["alt_text"], str) or len(asset["alt_text"].strip()) < 20:
            raise AssetValidationError(f"asset {asset_id} lacks useful alt text")
        if not isinstance(asset["created_at"], str) or DATE.fullmatch(asset["created_at"]) is None:
            raise AssetValidationError(f"asset {asset_id} lacks creation provenance")
        try:
            date.fromisoformat(asset["created_at"])
        except ValueError as exc:
            raise AssetValidationError(f"asset {asset_id} has an invalid creation date") from exc
        if not isinstance(asset["creation_method"], str) or len(asset["creation_method"].strip()) < 3:
            raise AssetValidationError(f"asset {asset_id} lacks creation provenance")
        if asset["provenance_type"] == "generated":
            for field, minimum in (("generation_provider", 2), ("generation_model", 3), ("prompt", 1)):
                if not isinstance(asset[field], str) or len(asset[field].strip()) < minimum:
                    raise AssetValidationError(f"asset {asset_id} lacks generator provenance")
        elif asset["provenance_type"] == "source_controlled":
            if any(asset[field] is not None for field in ("generation_provider", "generation_model", "prompt")) or asset["text_policy"] != "source_controlled_overlay":
                raise AssetValidationError(f"asset {asset_id} has invalid source-controlled provenance")
        else:
            raise AssetValidationError(f"asset {asset_id} has invalid provenance type")
    discovered = {
        str(path.relative_to(root))
        for directory in (root / "assets" / "generated", root / "assets" / "templates", root / "assets" / "thumbnails")
        if directory.exists()
        for path in directory.rglob("*")
        if path.is_file()
    }
    if discovered != paths:
        raise AssetValidationError("asset directories and manifest paths differ")
    return len(ids)


def main() -> int:
    try:
        count = validate_assets()
    except AssetValidationError as exc:
        print(f"asset validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"asset validation passed: {count} asset(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
