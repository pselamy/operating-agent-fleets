#!/usr/bin/env python3
"""Reject restricted data newly reachable after an explicit trusted Git base."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

if __package__:
    from tools.privacy_history_scan import ROOT, _git, scan_history
else:
    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT))
    from tools.privacy_history_scan import _git, scan_history


COMMIT_OID = re.compile(r"^[0-9a-f]{40}$", re.ASCII)


def forward_revision_range(root: Path, base: str, head: str) -> str:
    """Return a non-empty, descendant-only range safe for a forward privacy gate."""
    if COMMIT_OID.fullmatch(base) is None or COMMIT_OID.fullmatch(head) is None:
        raise ValueError("base and head must be full lowercase commit OIDs")
    for revision in (base, head):
        if _git(root, "cat-file", "-t", revision).decode("ascii").strip() != "commit":
            raise ValueError("base or head does not identify a commit")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if ancestor.returncode == 1:
        raise ValueError("base revision is not an ancestor of head")
    if ancestor.returncode != 0:
        raise ValueError("cannot establish base/head ancestry")
    revision_range = f"{base}..{head}"
    count = _git(root, "rev-list", "--count", revision_range).decode("ascii").strip()
    if not count.isdigit() or int(count) < 1:
        raise ValueError("forward revision range contains no new commits")
    return revision_range


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--max-object-bytes", type=int, default=10 * 1024 * 1024)
    parser.add_argument("--max-path-bytes", type=int, default=50 * 1024 * 1024)
    args = parser.parse_args()
    try:
        revision_range = forward_revision_range(args.root.resolve(), args.base, args.head)
        result = scan_history(
            args.root.resolve(),
            revisions=(revision_range,),
            max_object_bytes=args.max_object_bytes,
            max_path_bytes=args.max_path_bytes,
        )
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Forward Git privacy guard failed closed: {exc}", file=sys.stderr)
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
            f"Forward Git privacy guard failed: {len(result.findings)} finding(s); "
            "matched values are intentionally redacted",
            file=sys.stderr,
        )
        return 1
    print(
        "Forward Git privacy guard passed: "
        f"{result.objects_scanned} candidate-range object(s), "
        f"{result.paths_scanned} candidate-tree path observation(s), "
        f"{result.path_bytes_scanned} historical path byte(s), {result.bytes_scanned} payload byte(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
