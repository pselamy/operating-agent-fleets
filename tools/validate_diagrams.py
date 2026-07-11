#!/usr/bin/env python3
"""Validate diagram provenance, accessibility metadata, and export freshness."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "diagrams" / "manifest.json"
DIAGRAM_FIELDS = {
    "id", "title", "reader_question", "evidence_cutoff", "claim_status", "source",
    "source_sha256", "evidence_ids", "alt_text", "exports",
}
EXPORT_FIELDS = {"theme", "svg_id", "path", "sha256"}


class DiagramValidationError(ValueError):
    """A diagram artifact violates the public diagram contract."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_diagrams(root: Path = ROOT) -> int:
    try:
        manifest = json.loads((root / "diagrams" / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DiagramValidationError(f"cannot load diagram manifest: {exc}") from exc
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "renderer", "diagrams"}:
        raise DiagramValidationError("manifest must contain schema_version, renderer, and diagrams")
    if manifest["schema_version"] != 1 or not isinstance(manifest["diagrams"], list):
        raise DiagramValidationError("unsupported schema version or diagram collection")

    ids: set[str] = set()
    outputs: set[str] = set()
    for index, diagram in enumerate(manifest["diagrams"]):
        if not isinstance(diagram, dict) or set(diagram) != DIAGRAM_FIELDS:
            raise DiagramValidationError(f"diagram {index} has an invalid field set")
        if diagram["id"] in ids or not diagram["reader_question"].strip() or not diagram["alt_text"].strip():
            raise DiagramValidationError(f"diagram {index} has duplicate ID or missing reader text")
        ids.add(diagram["id"])
        source = root / diagram["source"]
        if not source.is_file() or digest(source) != diagram["source_sha256"]:
            raise DiagramValidationError(f"diagram {diagram['id']} source is missing or stale")
        source_text = source.read_text(encoding="utf-8")
        for marker in ("Reader question:", "Evidence cutoff:", "Claim status:", "accTitle:", "accDescr:"):
            if marker not in source_text:
                raise DiagramValidationError(f"diagram {diagram['id']} is missing {marker}")
        themes: set[str] = set()
        for exported in diagram["exports"]:
            if not isinstance(exported, dict) or set(exported) != EXPORT_FIELDS:
                raise DiagramValidationError(f"diagram {diagram['id']} has an invalid export")
            path = exported["path"]
            if path in outputs or exported["theme"] in themes:
                raise DiagramValidationError(f"diagram {diagram['id']} duplicates an export path or theme")
            outputs.add(path)
            themes.add(exported["theme"])
            svg = root / path
            if not svg.is_file() or digest(svg) != exported["sha256"]:
                raise DiagramValidationError(f"diagram {diagram['id']} export is missing or stale")
            text = svg.read_text(encoding="utf-8")
            for marker in ("<svg", "<title", "<desc", "aria-labelledby", "aria-roledescription"):
                if marker not in text:
                    raise DiagramValidationError(f"diagram {diagram['id']} export lacks accessible SVG metadata")
        if themes != {"light", "dark"}:
            raise DiagramValidationError(f"diagram {diagram['id']} requires light and dark exports")
    return len(ids)


def main() -> int:
    try:
        count = validate_diagrams()
    except DiagramValidationError as exc:
        print(f"diagram validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"diagram validation passed: {count} diagram(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
