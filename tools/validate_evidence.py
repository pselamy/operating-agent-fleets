#!/usr/bin/env python3
"""Validate the dependency-free, JSON-compatible public evidence atlas."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "public-evidence.schema.json"
MANIFEST_PATH = ROOT / "evidence" / "manifest.yaml"


class EvidenceValidationError(ValueError):
    """Raised when an evidence record violates the public contract."""


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceValidationError(f"{path}: cannot load JSON-compatible YAML: {exc}") from exc


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceValidationError(message)


def _validate_strings(record: dict[str, object], field: str, minimum: int = 1) -> list[str]:
    value = record[field]
    _expect(isinstance(value, list), f"{field}: expected an array")
    _expect(len(value) >= minimum, f"{field}: expected at least {minimum} item(s)")
    _expect(all(isinstance(item, str) and item.strip() for item in value), f"{field}: items must be non-empty strings")
    _expect(len(value) == len(set(value)), f"{field}: duplicate items are not allowed")
    return value


def validate_record(record: object, schema: dict[str, object]) -> str:
    _expect(isinstance(record, dict), "record: expected an object")
    required = schema["required"]
    properties = schema["properties"]
    _expect(isinstance(required, list) and isinstance(properties, dict), "schema: malformed contract")

    missing = sorted(set(required) - set(record))
    unknown = sorted(set(record) - set(properties))
    _expect(not missing, f"record: missing required fields: {', '.join(missing)}")
    _expect(not unknown, f"record: unknown fields: {', '.join(unknown)}")

    evidence_id = record["id"]
    _expect(isinstance(evidence_id, str), "id: expected a string")
    id_pattern = properties["id"]["pattern"]
    _expect(re.fullmatch(id_pattern, evidence_id) is not None, f"id: invalid stable ID {evidence_id!r}")

    for field in ("title", "cutoff"):
        _expect(isinstance(record[field], str) and record[field].strip(), f"{field}: expected a non-empty string")

    for field in ("evidence_class", "lineage", "sensitivity", "status"):
        allowed = properties[field]["enum"]
        _expect(record[field] in allowed, f"{field}: {record[field]!r} is not allowed")

    try:
        dt.date.fromisoformat(record["verified_at"])
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError("verified_at: expected an ISO 8601 calendar date") from exc

    reverify_after_days = record["reverify_after_days"]
    _expect(
        isinstance(reverify_after_days, int) and not isinstance(reverify_after_days, bool),
        "reverify_after_days: expected an integer",
    )
    _expect(1 <= reverify_after_days <= 365, "reverify_after_days: expected a value from 1 through 365")

    sources = _validate_strings(record, "public_sources", minimum=0)
    for source in sources:
        parsed = urlparse(source)
        _expect(parsed.scheme == "https" and bool(parsed.netloc), f"public_sources: expected a public HTTPS URL, got {source!r}")

    evidence_class = record["evidence_class"]
    sensitivity = record["sensitivity"]
    if evidence_class == "internally_corroborated":
        _expect(sensitivity == "public_derived", "internally_corroborated: sensitivity must be public_derived")
    else:
        _expect(bool(sources), f"{evidence_class}: at least one public source is required")

    _validate_strings(record, "claims")
    _validate_strings(record, "verification_method")
    _validate_strings(record, "limitations")

    for optional in ("consumer", "outcome"):
        if optional in record:
            _expect(isinstance(record[optional], str) and record[optional].strip(), f"{optional}: expected a non-empty string")

    return evidence_id


def validate_atlas(root: Path = ROOT) -> list[str]:
    schema = load_json(root / SCHEMA_PATH.relative_to(ROOT))
    manifest = load_json(root / MANIFEST_PATH.relative_to(ROOT))
    _expect(isinstance(schema, dict), "schema: expected an object")
    _expect(isinstance(manifest, dict), "manifest: expected an object")
    _expect(set(manifest) == {"schema_version", "records"}, "manifest: expected only schema_version and records")
    _expect(manifest["schema_version"] == 1, "manifest: unsupported schema_version")

    record_paths = manifest["records"]
    _expect(isinstance(record_paths, list), "manifest.records: expected an array")
    _expect(len(record_paths) == len(set(record_paths)), "manifest.records: duplicate paths are not allowed")

    evidence_root = (root / "evidence" / "records").resolve()
    ids: list[str] = []
    for relative in record_paths:
        _expect(isinstance(relative, str) and relative, "manifest.records: paths must be non-empty strings")
        path = (root / relative).resolve()
        _expect(path.is_relative_to(evidence_root), f"manifest.records: path escapes evidence/records: {relative!r}")
        _expect(path.is_file(), f"manifest.records: missing file: {relative!r}")
        ids.append(validate_record(load_json(path), schema))

    _expect(len(ids) == len(set(ids)), "atlas: duplicate evidence IDs are not allowed")
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to validate")
    args = parser.parse_args()
    try:
        ids = validate_atlas(args.root.resolve())
    except EvidenceValidationError as exc:
        print(f"evidence validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"evidence validation passed: {len(ids)} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
