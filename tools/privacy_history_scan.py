#!/usr/bin/env python3
"""Fail closed when restricted patterns occur anywhere in reachable Git history."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __package__:
    from tools.privacy_scan import RULES
else:
    sys.path.insert(0, str(ROOT))
    from tools.privacy_scan import RULES


DEFAULT_MAX_OBJECT_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class HistoricalFinding:
    object_id: str
    object_type: str
    path: str | None
    line: int
    rule: str


@dataclass(frozen=True)
class HistoryScanResult:
    objects_scanned: int
    bytes_scanned: int
    findings: tuple[HistoricalFinding, ...]


def _git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git {' '.join(args)} failed: {detail or 'unknown error'}")
    return result.stdout


def reachable_objects(root: Path, revisions: tuple[str, ...] = ("--all",)) -> list[tuple[str, str | None]]:
    output = _git(root, "rev-list", "--objects", *revisions)
    objects: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    for raw_line in output.decode("utf-8", errors="strict").splitlines():
        object_id, separator, path = raw_line.partition(" ")
        if object_id in seen:
            continue
        seen.add(object_id)
        objects.append((object_id, path if separator else None))
    if not objects:
        raise ValueError("revision set contains no reachable objects")
    return objects


def scan_history(
    root: Path,
    *,
    revisions: tuple[str, ...] = ("--all",),
    max_object_bytes: int = DEFAULT_MAX_OBJECT_BYTES,
) -> HistoryScanResult:
    if max_object_bytes < 1:
        raise ValueError("max object size must be positive")
    findings: list[HistoricalFinding] = []
    bytes_scanned = 0
    objects = reachable_objects(root, revisions)
    for object_id, path in objects:
        object_type = _git(root, "cat-file", "-t", object_id).decode("ascii").strip()
        if path is not None:
            for rule in RULES:
                if rule.pattern.search(path):
                    findings.append(HistoricalFinding(
                        object_id=object_id,
                        object_type=object_type,
                        path=path,
                        line=0,
                        rule=rule.name,
                    ))
        # Tree payloads encode object IDs plus filenames. ``rev-list --objects``
        # already exposes those filenames above; blobs, commits, and annotated
        # tags contain the history text that must be inspected.
        if object_type == "tree":
            continue
        size_text = _git(root, "cat-file", "-s", object_id).decode("ascii").strip()
        try:
            size = int(size_text)
        except ValueError as exc:
            raise ValueError(f"invalid size for Git object {object_id}") from exc
        if size > max_object_bytes:
            raise ValueError(
                f"Git object {object_id} ({object_type}, {size} bytes) exceeds the scan limit"
            )
        if object_type not in {"blob", "commit", "tag"}:
            raise ValueError(f"unsupported reachable Git object type: {object_type}")
        payload = _git(root, "cat-file", object_type, object_id)
        if len(payload) != size:
            raise ValueError(f"Git object {object_id} changed size while being scanned")
        bytes_scanned += len(payload)
        text = payload.decode("utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule in RULES:
                if rule.pattern.search(line):
                    findings.append(HistoricalFinding(
                        object_id=object_id,
                        object_type=object_type,
                        path=path,
                        line=line_number,
                        rule=rule.name,
                    ))
    return HistoryScanResult(
        objects_scanned=len(objects),
        bytes_scanned=bytes_scanned,
        findings=tuple(findings),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--revision", action="append", dest="revisions")
    parser.add_argument("--max-object-bytes", type=int, default=DEFAULT_MAX_OBJECT_BYTES)
    args = parser.parse_args()
    revisions = tuple(args.revisions) if args.revisions else ("--all",)
    try:
        result = scan_history(
            args.root.resolve(),
            revisions=revisions,
            max_object_bytes=args.max_object_bytes,
        )
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Git-history privacy scan failed closed: {exc}", file=sys.stderr)
        return 2
    if result.findings:
        for finding in result.findings:
            locator = finding.path or f"<{finding.object_type}>"
            print(
                f"{finding.object_id[:12]}:{locator}:{finding.line}: "
                f"restricted pattern: {finding.rule}",
                file=sys.stderr,
            )
        print(
            f"Git-history privacy scan failed: {len(result.findings)} finding(s); "
            "matched values are intentionally redacted",
            file=sys.stderr,
        )
        return 1
    print(
        "Git-history privacy scan passed: "
        f"{result.objects_scanned} object(s), {result.bytes_scanned} byte(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
