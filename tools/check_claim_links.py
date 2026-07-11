#!/usr/bin/env python3
"""Require guide artifact links and evidence citations to resolve to the atlas."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # pragma: no cover - direct-script bootstrap
    sys.path.insert(0, str(ROOT))  # pragma: no cover

from tools.validate_evidence import EvidenceValidationError, validate_atlas


CITATION = re.compile(r"\[@evidence:([a-z][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+)\]")
GITHUB_LINK = re.compile(r"\[[^\]]+\]\(https://github\.com/[^)]+\)")


def numbered_chapters(root: Path) -> list[Path]:
    return sorted((root / "guide").glob("[0-9][0-9]-*.md"))


def check_claim_links(root: Path = ROOT) -> list[str]:
    valid_ids = set(validate_atlas(root))
    errors: list[str] = []
    for path in numbered_chapters(root):
        text = path.read_text(encoding="utf-8")
        for evidence_id in CITATION.findall(text):
            if evidence_id not in valid_ids:
                errors.append(f"{path.relative_to(root)}: unknown evidence citation {evidence_id}")
        for paragraph_number, paragraph in enumerate(re.split(r"\n\s*\n", text), start=1):
            if GITHUB_LINK.search(paragraph) and not CITATION.search(paragraph):
                errors.append(
                    f"{path.relative_to(root)}: paragraph {paragraph_number} links a GitHub artifact without an evidence citation"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        errors = check_claim_links(args.root.resolve())
    except (EvidenceValidationError, OSError) as exc:
        print(f"claim-link check failed closed: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"claim-link check failed: {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("claim-link check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
