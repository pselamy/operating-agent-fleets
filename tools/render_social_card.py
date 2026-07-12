#!/usr/bin/env python3
"""Render a bounded chapter social card from the source-controlled SVG template."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "templates" / "chapter-social-card.svg"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_LINE = 28
MAX_TITLE_UNITS = 12.0
MAX_URL_UNITS = 29.0
NS = "{http://www.w3.org/2000/svg}"


class SocialCardError(ValueError):
    """A requested card cannot satisfy the bounded template contract."""


def text_units(value: str) -> float:
    """Conservative em-width estimate for the declared Inter/system fallback stack."""
    units = 0.0
    for char in value:
        if char in "MW@%&#":
            units += 1.0
        elif char in "mwQO0":
            units += 0.85
        elif char.isupper():
            units += 0.72
        elif char in "ilI1|!.,:'` ":
            units += 0.3
        else:
            units += 0.56
    return units


def render_card(template: Path, output: Path, *, chapter: int, title_lines: list[str], slug: str) -> None:
    if not 1 <= chapter <= 8:
        raise SocialCardError("chapter must be between 1 and 8")
    if not 1 <= len(title_lines) <= 3 or any(not line.strip() or len(line.strip()) > MAX_LINE for line in title_lines):
        raise SocialCardError(f"provide one to three non-empty title lines of at most {MAX_LINE} characters")
    if any(text_units(line.strip()) > MAX_TITLE_UNITS for line in title_lines):
        raise SocialCardError("title line exceeds the conservative rendered-width budget")
    if SLUG.fullmatch(slug) is None:
        raise SocialCardError("slug must be lowercase kebab case")
    url = f"selamy.dev/agent-fleets/{chapter:02d}-{slug}/"
    if text_units(url) > MAX_URL_UNITS:
        raise SocialCardError("chapter URL exceeds the conservative rendered-width budget")
    if output.resolve() == template.resolve():
        raise SocialCardError("refusing to overwrite the canonical template")
    try:
        tree = ElementTree.parse(template)
    except (OSError, ElementTree.ParseError) as exc:
        raise SocialCardError(f"cannot load social-card template: {exc}") from exc
    root = tree.getroot()
    by_id = {element.attrib.get("id"): element for element in root.iter() if element.attrib.get("id")}
    required = {"social-card-title", "social-card-desc", "chapter-label", "chapter-url", "title-line-1", "title-line-2", "title-line-3"}
    if not required.issubset(by_id):
        raise SocialCardError("template lacks required bounded text nodes")
    by_id["chapter-label"].text = f"CHAPTER {chapter:02d}"
    by_id["chapter-url"].text = url
    padded = [line.strip() for line in title_lines] + [""] * (3 - len(title_lines))
    for index, line in enumerate(padded, start=1):
        by_id[f"title-line-{index}"].text = line
    title = " ".join(line for line in padded if line)
    by_id["social-card-title"].text = f"Operating Agent Fleets chapter {chapter}: {title}"
    by_id["social-card-desc"].text = (
        f"Editorial social card for chapter {chapter}, {title}. Amber and cyan loops orbit a layered record. "
        "The motif is an editorial metaphor, not architecture; it does not represent deployed topology, "
        "peer connectivity, central orchestration, or a verified agent count."
    )
    if any("[" in (element.text or "") or "]" in (element.text or "") for element in root.iter()):
        raise SocialCardError("rendered card contains an unresolved placeholder")
    output.parent.mkdir(parents=True, exist_ok=True)
    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
    tree.write(output, encoding="utf-8", xml_declaration=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--title-line", action="append", required=True)
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()
    try:
        render_card(args.template.resolve(), args.output.resolve(), chapter=args.chapter, title_lines=args.title_line, slug=args.slug)
    except (OSError, SocialCardError) as exc:
        print(f"social-card render failed: {exc}", file=sys.stderr)
        return 1
    print(f"rendered social card: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
