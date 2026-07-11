#!/usr/bin/env python3
"""Build a deterministic, allowlisted site bundle from an immutable revision."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "export" / "site-manifest.json"
ALLOWED_SOURCE_ROOTS = {"guide", "docs", "evidence", "diagrams", "assets"}
ALLOWED_DESTINATION_ROOTS = {"content", "data", "static"}
FORBIDDEN_SEGMENTS = {"private", "confidential", "restricted", ".git", ".github", "work", "scratch"}
ENTRY_FIELDS = {"source", "destination", "channel", "media_type"}
CHANNELS = {"preview", "release"}
MEDIA_TYPES = {"text/markdown", "application/json", "image/svg+xml", "image/png"}


class ExportError(ValueError):
    """The export manifest or source tree violates the publication contract."""


def load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError(f"cannot load export manifest: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {"schema_version", "entries"}:
        raise ExportError("manifest must contain only schema_version and entries")
    if value["schema_version"] != 1 or not isinstance(value["entries"], list):
        raise ExportError("manifest schema_version must be 1 and entries must be an array")
    return value


def _safe_relative(raw: object, *, roots: set[str], label: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw:
        raise ExportError(f"{label} must be a non-empty string")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ExportError(f"{label} must be a normalized relative path: {raw!r}")
    if not path.parts or path.parts[0] not in roots:
        raise ExportError(f"{label} root is not allowlisted: {raw!r}")
    lowered = {part.lower() for part in path.parts}
    if lowered & FORBIDDEN_SEGMENTS:
        raise ExportError(f"{label} contains a forbidden path segment: {raw!r}")
    return path


def validate_entries(root: Path, entries: list[object]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    sources: set[str] = set()
    destinations: set[str] = set()
    for index, raw in enumerate(entries):
        if not isinstance(raw, dict) or set(raw) != ENTRY_FIELDS:
            raise ExportError(f"entry {index} must contain exactly {sorted(ENTRY_FIELDS)}")
        source = _safe_relative(raw["source"], roots=ALLOWED_SOURCE_ROOTS, label="source")
        destination = _safe_relative(
            raw["destination"], roots=ALLOWED_DESTINATION_ROOTS, label="destination"
        )
        if raw["channel"] not in CHANNELS or raw["media_type"] not in MEDIA_TYPES:
            raise ExportError(f"entry {index} has an unsupported channel or media type")
        if str(source) in sources or str(destination) in destinations:
            raise ExportError(f"entry {index} duplicates a source or destination")
        sources.add(str(source))
        destinations.add(str(destination))

        source_path = root / Path(*source.parts)
        current = root
        for part in source.parts:
            current = current / part
            if current.is_symlink():
                raise ExportError(f"source path may not traverse a symlink: {source}")
        if not source_path.is_file():
            raise ExportError(f"source is not a regular file: {source}")
        validated.append({**raw, "source": str(source), "destination": str(destination)})
    return sorted(validated, key=lambda entry: entry["destination"])


def git_state(root: Path) -> tuple[str, bool]:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
        )
    except subprocess.CalledProcessError as exc:
        raise ExportError("source root must be a readable Git checkout") from exc
    return revision, dirty


def build_bundle(
    root: Path,
    output: Path,
    *,
    channel: str,
    revision: str,
    dirty: bool,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if channel not in CHANNELS:
        raise ExportError(f"unsupported channel: {channel}")
    if channel == "release" and dirty:
        raise ExportError("release export requires a clean working tree")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ExportError("output must not exist or must be an empty directory")
    output.mkdir(parents=True, exist_ok=True)

    document = manifest or load_manifest(root / "export" / "site-manifest.json")
    entries = validate_entries(root, document["entries"])
    selected = [entry for entry in entries if channel == "preview" or entry["channel"] == "release"]
    emitted = []
    for entry in selected:
        source = root / entry["source"]
        destination = output / entry["destination"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        destination.write_bytes(data)
        emitted.append(
            {
                "source": entry["source"],
                "destination": entry["destination"],
                "channel": entry["channel"],
                "media_type": entry["media_type"],
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    metadata = {
        "schema_version": 1,
        "source_revision": revision,
        "source_dirty": dirty,
        "requested_channel": channel,
        "entries": emitted,
    }
    (output / "export-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--channel", choices=sorted(CHANNELS), default="preview")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    try:
        revision, dirty = git_state(root)
        metadata = build_bundle(root, output, channel=args.channel, revision=revision, dirty=dirty)
    except (ExportError, OSError) as exc:
        print(f"site export failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
