#!/usr/bin/env python3
"""Fail closed when restricted patterns occur anywhere in reachable Git history."""

from __future__ import annotations

import argparse
import hashlib
import re
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
DEFAULT_MAX_PATH_BYTES = 50 * 1024 * 1024
HISTORY_RULES = tuple(
    type(rule)(
        rule.name,
        re.compile(rule.pattern.pattern, (rule.pattern.flags & ~re.UNICODE) | re.ASCII),
    )
    for rule in RULES
)


@dataclass(frozen=True)
class HistoricalFinding:
    object_id: str
    object_type: str
    path_digest: str | None
    line: int
    rule: str


@dataclass(frozen=True)
class HistoryScanResult:
    objects_scanned: int
    paths_scanned: int
    path_bytes_scanned: int
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
        operation = args[0] if args else "operation"
        raise ValueError(f"git {operation} failed with exit status {result.returncode}")
    return result.stdout


def _ensure_complete_repository(root: Path, revisions: tuple[str, ...]) -> None:
    shallow = _git(root, "rev-parse", "--is-shallow-repository").decode("ascii").strip()
    if shallow != "false":
        raise ValueError("repository is shallow; complete reachable history cannot be established")
    config = subprocess.run(
        ["git", "config", "--get-regexp", r"^(extensions\.partialClone|remote\..*\.promisor)$"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if config.returncode not in {0, 1}:
        raise ValueError("cannot determine partial-clone configuration")
    if config.returncode == 0 and config.stdout.strip():
        raise ValueError("repository uses partial/promisor cloning; complete history cannot be established")
    missing = _git(root, "rev-list", "--objects", "--missing=print", *revisions)
    if any(line.startswith(b"?") for line in missing.splitlines()):
        raise ValueError("reachable Git objects are missing locally")
    _git(root, "fsck", "--connectivity-only", "--no-dangling")


def reachable_objects(root: Path, revisions: tuple[str, ...] = ("--all",)) -> list[str]:
    _ensure_complete_repository(root, revisions)
    output = _git(root, "rev-list", "--objects", *revisions)
    objects: list[str] = []
    seen: set[str] = set()
    for raw_line in output.decode("utf-8", errors="strict").splitlines():
        object_id = raw_line.partition(" ")[0]
        if object_id in seen:
            continue
        seen.add(object_id)
        objects.append(object_id)
    if not objects:
        raise ValueError("revision set contains no reachable objects")
    return objects


def historical_paths(
    root: Path,
    revisions: tuple[str, ...],
    *,
    max_path_bytes: int = DEFAULT_MAX_PATH_BYTES,
) -> tuple[list[tuple[str, str]], int]:
    if max_path_bytes < 1:
        raise ValueError("max historical-path bytes must be positive")
    commits = _git(root, "rev-list", *revisions).decode("ascii", errors="strict").splitlines()
    seen: set[str] = set()
    paths: list[tuple[str, str]] = []
    path_bytes_scanned = 0
    for commit_id in commits:
        output = _git(
            root,
            "ls-tree",
            "--name-only",
            "-r",
            "-z",
            commit_id,
        )
        for raw_path in output.split(b"\0"):
            if not raw_path:
                continue
            path_bytes_scanned += len(raw_path)
            if path_bytes_scanned > max_path_bytes:
                raise ValueError("historical path data exceeds the scan limit")
            path = raw_path.decode("utf-8", errors="surrogateescape")
            if path in seen:
                continue
            seen.add(path)
            paths.append((commit_id, path))
    return paths, path_bytes_scanned


def verify_remote_refs(root: Path, remote: str) -> dict[str, str]:
    if not remote or remote.startswith("-"):
        raise ValueError("remote name is invalid")
    output = _git(
        root,
        "ls-remote",
        remote,
        "refs/heads/*",
        "refs/tags/*",
        "refs/pull/*/head",
        "refs/pull/*/merge",
    )
    expected: dict[str, str] = {}
    for line in output.decode("ascii", errors="strict").splitlines():
        object_id, ref = line.split("\t", 1)
        if ref.endswith("^{}"):
            continue
        if any(rule.pattern.search(ref) for rule in HISTORY_RULES):
            raise ValueError("remote exposes a restricted ref name; value redacted")
        if ref.startswith("refs/heads/"):
            local_ref = f"refs/remotes/{remote}/{ref.removeprefix('refs/heads/')}"
        elif ref.startswith("refs/tags/"):
            local_ref = ref
        elif ref.startswith("refs/pull/"):
            local_ref = f"refs/remotes/{remote}/{ref.removeprefix('refs/')}"
        else:
            raise ValueError("remote returned an unsupported ref class")
        expected[local_ref] = object_id
    if not expected:
        raise ValueError(f"remote {remote} exposes no branch or tag refs")
    for ref, expected_id in expected.items():
        try:
            actual_id = _git(root, "rev-parse", "--verify", ref).decode("ascii").strip()
        except ValueError as exc:
            ref_digest = hashlib.sha256(ref.encode("ascii")).hexdigest()
            raise ValueError(f"remote ref is not fetched locally: sha256={ref_digest}") from exc
        if actual_id != expected_id:
            ref_digest = hashlib.sha256(ref.encode("ascii")).hexdigest()
            raise ValueError(f"local ref is stale relative to remote: sha256={ref_digest}")
    return dict(sorted(expected.items()))


def scan_history(
    root: Path,
    *,
    revisions: tuple[str, ...] = ("--all",),
    max_object_bytes: int = DEFAULT_MAX_OBJECT_BYTES,
    max_path_bytes: int = DEFAULT_MAX_PATH_BYTES,
) -> HistoryScanResult:
    if max_object_bytes < 1:
        raise ValueError("max object size must be positive")
    findings: list[HistoricalFinding] = []
    bytes_scanned = 0
    objects = reachable_objects(root, revisions)
    paths, path_bytes_scanned = historical_paths(
        root, revisions, max_path_bytes=max_path_bytes
    )
    for commit_id, path in paths:
        for rule in HISTORY_RULES:
            if rule.pattern.search(path):
                path_bytes = path.encode("utf-8", errors="surrogateescape")
                findings.append(HistoricalFinding(
                    object_id=commit_id,
                    object_type="path",
                    path_digest=hashlib.sha256(path_bytes).hexdigest(),
                    line=0,
                    rule=rule.name,
                ))
    for object_id in objects:
        object_type = _git(root, "cat-file", "-t", object_id).decode("ascii").strip()
        size_text = _git(root, "cat-file", "-s", object_id).decode("ascii").strip()
        try:
            size = int(size_text)
        except ValueError as exc:
            raise ValueError(f"invalid size for Git object {object_id}") from exc
        if size > max_object_bytes:
            raise ValueError(
                f"Git object {object_id} ({object_type}, {size} bytes) exceeds the scan limit"
            )
        # Every path in every reachable tree is enumerated above. Tree payloads
        # contain only object IDs and entry names, so their size is bounded here
        # and their names are scanned through the lossless NUL-delimited walk.
        if object_type == "tree":
            continue
        if object_type not in {"blob", "commit", "tag"}:
            raise ValueError(f"unsupported reachable Git object type: {object_type}")
        payload = _git(root, "cat-file", object_type, object_id)
        if len(payload) != size:
            raise ValueError(f"Git object {object_id} changed size while being scanned")
        bytes_scanned += len(payload)
        # Latin-1 is a lossless byte-to-code-point mapping. It preserves every
        # ASCII restricted pattern without pretending arbitrary blobs are UTF-8.
        text = payload.decode("latin-1")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule in HISTORY_RULES:
                if rule.pattern.search(line):
                    findings.append(HistoricalFinding(
                        object_id=object_id,
                        object_type=object_type,
                        path_digest=None,
                        line=line_number,
                        rule=rule.name,
                    ))
    return HistoryScanResult(
        objects_scanned=len(objects),
        paths_scanned=len(paths),
        path_bytes_scanned=path_bytes_scanned,
        bytes_scanned=bytes_scanned,
        findings=tuple(findings),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--revision", action="append", dest="revisions")
    parser.add_argument("--verify-remote")
    parser.add_argument("--max-object-bytes", type=int, default=DEFAULT_MAX_OBJECT_BYTES)
    parser.add_argument("--max-path-bytes", type=int, default=DEFAULT_MAX_PATH_BYTES)
    args = parser.parse_args()
    revisions = tuple(args.revisions) if args.revisions else ("--all",)
    try:
        if args.verify_remote:
            snapshot = verify_remote_refs(args.root.resolve(), args.verify_remote)
            if not args.revisions:
                revisions = tuple(dict.fromkeys(snapshot.values()))
        result = scan_history(
            args.root.resolve(),
            revisions=revisions,
            max_object_bytes=args.max_object_bytes,
            max_path_bytes=args.max_path_bytes,
        )
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Git-history privacy scan failed closed: {exc}", file=sys.stderr)
        return 2
    if result.findings:
        for finding in result.findings:
            locator = f"<{finding.object_type}>"
            if finding.path_digest:
                locator = f"<historical-path sha256={finding.path_digest}>"
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
        f"{result.objects_scanned} object(s), {result.paths_scanned} historical path(s), "
        f"{result.path_bytes_scanned} historical path byte(s), {result.bytes_scanned} payload byte(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
