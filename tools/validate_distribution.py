#!/usr/bin/env python3
"""Validate pre-H4 distribution drafts without claiming approval or publication."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from tools.validate_assets import validate_assets as validate_asset_registry
    from tools.validate_diagrams import validate_diagrams as validate_diagram_registry
except ModuleNotFoundError:  # Direct script execution puts tools/ first on sys.path.
    from validate_assets import validate_assets as validate_asset_registry
    from validate_diagrams import validate_diagrams as validate_diagram_registry


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "distribution" / "manifest.json"
PACKAGE_FIELDS = {
    "id", "chapter", "channel", "canonical_url", "source_revision",
    "source_path", "content_path", "visual_path", "alt_text",
    "visual_sha256", "evidence_cutoff", "content_sha256",
}
CHANNELS = {"linkedin_newsletter", "linkedin_post", "medium"}
ID = re.compile(r"^[a-z][a-z0-9-]*$")
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
SOURCE = re.compile(r"^guide/(?P<chapter>[0-9]{2})-(?P<slug>[a-z0-9-]+)\.md$")
CANONICAL = re.compile(r"^https://selamy\.dev/agent-fleets/(?P<chapter>[0-9]{2})-(?P<slug>[a-z0-9-]+)/$")
DATE = re.compile(r"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$")
DRAFT_MARKER = "<!-- PRE-H4 DRAFT — DO NOT PUBLISH -->"
LINKEDIN_POST_MAX_CHARACTERS = 3_000
FORBIDDEN_PUBLICATION_CLAIM = re.compile(
    r"(?:\bh4\b|"
    r"\b(?:approved|authorized)\b.{0,40}\b(?:publish(?:ed|ing)?|publication)\b|"
    r"\b(?:publish(?:ed|ing)?|publication)\b.{0,40}\b(?:approved|authorized)\b|"
    r"\b(?:now|already|successfully)\s+(?:published|live)\b|"
    r"\b(?:is|was|has\s+been|went)\s+(?:now\s+)?(?:published|live)\b|"
    r"\bready\s+to\s+publish\b|\bpublish\s+now\b)",
    re.IGNORECASE,
)
REGISTERED_VISUAL_PATH = re.compile(
    r"^(?:assets/(?:generated|templates|thumbnails)/[a-z0-9-]+\.(?:png|svg)|"
    r"diagrams/chapter-[0-9]{2}/[a-z0-9.-]+\.(?:light|dark)\.svg)$"
)


class DistributionValidationError(ValueError):
    """A draft violates the pre-H4 distribution boundary."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file(root: Path, raw: object, prefix: str) -> Path:
    if not isinstance(raw, str) or not raw.startswith(prefix):
        raise DistributionValidationError(f"path must start with {prefix}")
    path = root / raw
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise DistributionValidationError(f"missing package file: {raw}") from exc
    if path.is_symlink() or root.resolve() not in resolved.parents or not resolved.is_file():
        raise DistributionValidationError(f"unsafe package file: {raw}")
    return resolved


def load_manifest(path: Path = MANIFEST) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DistributionValidationError(f"cannot load distribution manifest: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {"schema_version", "packages"}:
        raise DistributionValidationError("manifest must contain schema_version and packages")
    if value["schema_version"] != 1 or not isinstance(value["packages"], list):
        raise DistributionValidationError("unsupported schema version or package collection")
    return value


def _visual_registry(root: Path, *, validate_registries: bool = True) -> dict[str, tuple[str, str]]:
    """Return reviewed visual path -> (digest, alt text) from public manifests."""
    if validate_registries:
        try:
            validate_asset_registry(root)
            validate_diagram_registry(root)
        except ValueError as exc:
            raise DistributionValidationError("reviewed visual registry validation failed") from exc
    try:
        assets = json.loads((root / "assets" / "manifest.json").read_text(encoding="utf-8"))["assets"]
        diagrams = json.loads((root / "diagrams" / "manifest.json").read_text(encoding="utf-8"))["diagrams"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise DistributionValidationError("cannot load reviewed visual registries") from exc
    registry: dict[str, tuple[str, str]] = {}
    try:
        candidates = [(item["path"], item["sha256"], item["alt_text"]) for item in assets]
        candidates.extend(
            (exported["path"], exported["sha256"], item["alt_text"])
            for item in diagrams for exported in item["exports"]
        )
    except (KeyError, TypeError) as exc:
        raise DistributionValidationError("reviewed visual registry has an invalid shape") from exc
    for path, sha256, alt_text in candidates:
        if (not isinstance(path, str) or REGISTERED_VISUAL_PATH.fullmatch(path) is None
                or not isinstance(sha256, str) or DIGEST.fullmatch(sha256) is None
                or not isinstance(alt_text, str) or not alt_text.strip() or path in registry):
            raise DistributionValidationError("reviewed visual registry has an invalid or duplicate entry")
        registry[path] = (sha256, alt_text)
    return registry


def _verify_revision_path(root: Path, revision: str, path: str, *, expected_digest: str | None = None) -> None:
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=root, capture_output=True, check=False,
    )
    if result.returncode != 0:
        raise DistributionValidationError(f"source revision does not contain declared path: {path}")
    if expected_digest is not None and hashlib.sha256(result.stdout).hexdigest() != expected_digest:
        raise DistributionValidationError(f"source revision blob digest differs for declared path: {path}")


def validate_distribution(
    root: Path = ROOT,
    *,
    verify_git: bool = True,
    validate_visual_registries: bool = True,
) -> int:
    packages = load_manifest(root / "distribution" / "manifest.json")["packages"]
    visual_registry = _visual_registry(root, validate_registries=validate_visual_registries)
    ids: set[str] = set()
    chapter_channels: set[tuple[int, str]] = set()
    content_paths: set[str] = set()
    for index, package in enumerate(packages):
        if not isinstance(package, dict) or set(package) != PACKAGE_FIELDS:
            raise DistributionValidationError(f"package {index} has an invalid field set")
        package_id = package["id"]
        if not isinstance(package_id, str) or ID.fullmatch(package_id) is None or package_id in ids:
            raise DistributionValidationError(f"package {index} has an invalid or duplicate ID")
        ids.add(package_id)
        if package["channel"] not in CHANNELS:
            raise DistributionValidationError(f"package {package_id} has an invalid channel")
        chapter = package["chapter"]
        if not isinstance(chapter, int) or isinstance(chapter, bool) or not 1 <= chapter <= 8:
            raise DistributionValidationError(f"package {package_id} has an invalid chapter")
        chapter_channel = (chapter, package["channel"])
        if chapter_channel in chapter_channels:
            raise DistributionValidationError(f"package {package_id} duplicates a chapter and channel")
        chapter_channels.add(chapter_channel)
        source_match = SOURCE.fullmatch(package["source_path"]) if isinstance(package["source_path"], str) else None
        canonical_match = CANONICAL.fullmatch(package["canonical_url"]) if isinstance(package["canonical_url"], str) else None
        if source_match is None or canonical_match is None:
            raise DistributionValidationError(f"package {package_id} has an invalid source or canonical URL")
        if (int(source_match["chapter"]) != chapter or int(canonical_match["chapter"]) != chapter
                or source_match["slug"] != canonical_match["slug"]):
            raise DistributionValidationError(f"package {package_id} chapter, source, and canonical URL disagree")
        revision = package["source_revision"]
        if not isinstance(revision, str) or SHA.fullmatch(revision) is None:
            raise DistributionValidationError(f"package {package_id} lacks an immutable source revision")
        _file(root, package["source_path"], "guide/")
        if verify_git:
            _verify_revision_path(root, revision, package["source_path"])
        content = _file(root, package["content_path"], "distribution/packages/")
        if package["content_path"] in content_paths:
            raise DistributionValidationError(f"package {package_id} reuses a content path")
        content_paths.add(package["content_path"])
        content_text = content.read_text(encoding="utf-8")
        if not content_text.startswith(DRAFT_MARKER + "\n"):
            raise DistributionValidationError(f"package {package_id} lacks the mandatory pre-H4 marker")
        if content_text.count(package["canonical_url"]) != 1:
            raise DistributionValidationError(f"package {package_id} must contain its canonical URL exactly once")
        package_body = content_text[len(DRAFT_MARKER) + 1:]
        if "<!--" in package_body or "-->" in package_body:
            raise DistributionValidationError(f"package {package_id} contains an additional HTML comment")
        if FORBIDDEN_PUBLICATION_CLAIM.search(package_body):
            raise DistributionValidationError(f"package {package_id} contains a forbidden publication claim")
        visible_text = package_body.strip()
        if package["channel"] == "linkedin_post" and (
                len(content_text) > LINKEDIN_POST_MAX_CHARACTERS
                or visible_text.count("?") != 1 or not visible_text.endswith("?")):
            raise DistributionValidationError(
                f"package {package_id} must fit the LinkedIn limit and end with exactly one visible question")
        visual = package["visual_path"]
        if package["channel"] == "medium":
            medium_contract = (
                f"**Pinned field-guide revision:** `{revision}`",
                f"**Pinned source path:** `{package['source_path']}`",
                f"**Evidence cutoff:** {package['evidence_cutoff']}",
                "**Import mode:** Medium's canonical-URL importer; do not paste or maintain a second article copy.",
                "## Stop conditions",
                "## Import and verification procedure",
                "not the article body",
            )
            if visual is not None or any(content_text.count(marker) != 1 for marker in medium_contract):
                raise DistributionValidationError(
                    f"package {package_id} lacks the exact delayed Medium import contract")
        if package["channel"] == "linkedin_post" and visual is None:
            raise DistributionValidationError(f"package {package_id} LinkedIn post lacks its required visual")
        if visual is not None:
            if not isinstance(visual, str) or visual not in visual_registry:
                raise DistributionValidationError(f"package {package_id} visual is not registered")
            visual_file = _file(root, visual, visual.split("/", 1)[0] + "/")
            registered_digest, registered_alt = visual_registry[visual]
            if package["alt_text"] != registered_alt:
                raise DistributionValidationError(f"package {package_id} visual alt text differs from its registry")
            visual_digest = package["visual_sha256"]
            if (not isinstance(visual_digest, str) or DIGEST.fullmatch(visual_digest) is None
                    or visual_digest != registered_digest or visual_digest != digest(visual_file)):
                raise DistributionValidationError(f"package {package_id} visual digest is invalid or stale")
            if verify_git:
                _verify_revision_path(root, revision, visual, expected_digest=visual_digest)
        elif package["alt_text"] is not None or package["visual_sha256"] is not None:
            raise DistributionValidationError(f"package {package_id} has visual metadata without a visual")
        if not isinstance(package["evidence_cutoff"], str) or DATE.fullmatch(package["evidence_cutoff"]) is None:
            raise DistributionValidationError(f"package {package_id} lacks an evidence cutoff")
        content_digest = package["content_sha256"]
        if not isinstance(content_digest, str) or DIGEST.fullmatch(content_digest) is None or content_digest != digest(content):
            raise DistributionValidationError(f"package {package_id} content digest is invalid or stale")
    return len(ids)


def main() -> int:
    try:
        count = validate_distribution()
    except DistributionValidationError as exc:
        print(f"distribution validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"distribution draft validation passed: {count} package(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
