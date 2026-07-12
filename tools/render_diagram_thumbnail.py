#!/usr/bin/env python3
"""Render a source-bound, readable 1200×627 social diagram summary."""

from __future__ import annotations

import argparse
import html
import struct
import subprocess
import sys
import tempfile
import unicodedata
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = Path("/usr/bin/sips")


class ThumbnailRenderError(ValueError):
    """A diagram thumbnail cannot be rendered under the bounded contract."""


def locate_renderer(explicit: Path | None = None) -> Path:
    renderer = explicit or RENDERER
    if renderer.is_file():
        return renderer
    raise ThumbnailRenderError("the local sips image renderer is required")


def _clean(value: str, *, label: str, minimum: int = 3, maximum: int = 72) -> str:
    cleaned = " ".join(value.split())
    if not minimum <= len(cleaned) <= maximum or any(char in cleaned for char in "<>[]"):
        raise ThumbnailRenderError(f"{label} must contain {minimum}–{maximum} safe characters")
    return cleaned


def _em_width(value: str) -> float:
    width = 0.0
    for char in value:
        if unicodedata.east_asian_width(char) in {"W", "F"}:
            width += 1.0
        elif char.isspace():
            width += 0.32
        elif char.isupper():
            width += 0.72
        elif char.islower() or char.isdigit():
            width += 0.58
        else:
            width += 0.45
    return width


def _bounded(value: str, *, label: str, budget: float, minimum: int = 3, maximum: int = 72) -> str:
    cleaned = _clean(value, label=label, minimum=minimum, maximum=maximum)
    if _em_width(cleaned) > budget:
        raise ThumbnailRenderError(f"{label} exceeds its rendered-width budget")
    return cleaned


def _validate_png(path: Path) -> None:
    data = path.read_bytes() if path.is_file() else b""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ThumbnailRenderError("renderer did not produce a valid PNG")
    offset, dimensions, compressed, ended, color = 8, None, bytearray(), False, None
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ThumbnailRenderError("renderer produced a corrupt PNG")
        payload = data[offset + 8:offset + 8 + length]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != struct.unpack(">I", data[offset + 8 + length:end])[0]:
            raise ThumbnailRenderError("renderer produced a corrupt PNG")
        if kind == b"IHDR":
            if dimensions is not None or length != 13:
                raise ThumbnailRenderError("renderer produced a corrupt PNG")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if depth != 8 or color not in {2, 6} or compression or filtering or interlace:
                raise ThumbnailRenderError("renderer produced an unsupported PNG")
            dimensions = width, height
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            if length or end != len(data):
                raise ThumbnailRenderError("renderer produced a corrupt PNG")
            ended = True
            break
        offset = end
    if dimensions != (1200, 627) or not compressed or not ended or color is None:
        raise ThumbnailRenderError("renderer produced an invalid thumbnail contract")
    try:
        pixels = zlib.decompress(bytes(compressed))
    except zlib.error as exc:
        raise ThumbnailRenderError("renderer produced a corrupt PNG") from exc
    channels = 3 if color == 2 else 4
    if len(pixels) != 627 * (1 + 1200 * channels):
        raise ThumbnailRenderError("renderer produced a corrupt PNG")


def _lane_svg(lane: tuple[str, ...], y: int) -> str:
    gap, left, available = 54, 94, 1012
    width = (available - gap * (len(lane) - 1)) // len(lane)
    font_size = 18 if len(lane) == 4 else 21
    pieces: list[str] = []
    for index, step in enumerate(lane):
        x = left + index * (width + gap)
        pieces.append(f'<rect x="{x}" y="{y}" width="{width}" height="82" rx="12" fill="#ffffff" stroke="#b8c8d3" stroke-width="2"/>')
        pieces.append(f'<text x="{x + width // 2}" y="{y + 49}" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="{font_size}" font-weight="650" fill="#071426">{html.escape(step)}</text>')
        if index < len(lane) - 1:
            pieces.append(f'<text x="{x + width + 27}" y="{y + 51}" text-anchor="middle" font-size="31" font-weight="800" fill="#1685a1">→</text>')
    return "".join(pieces)


def render_thumbnail(
    source: Path, output: Path, *, title: str, takeaway: str,
    lanes: tuple[tuple[str, ...], ...], renderer: Path,
) -> None:
    try:
        resolved = source.resolve(strict=True)
    except OSError as exc:
        raise ThumbnailRenderError("source diagram is missing") from exc
    if ROOT.resolve() not in resolved.parents or resolved.suffix != ".svg" or ".light." not in resolved.name:
        raise ThumbnailRenderError("source must be a repository light-theme SVG diagram")
    if output.resolve() == resolved:
        raise ThumbnailRenderError("refusing to overwrite the source diagram")
    clean_title = _bounded(title, label="title", budget=24, minimum=3, maximum=72)
    clean_takeaway = _bounded(takeaway, label="takeaway", budget=45, minimum=12, maximum=82)
    if not 1 <= len(lanes) <= 2 or any(not 2 <= len(lane) <= 4 for lane in lanes):
        raise ThumbnailRenderError("one or two lanes of two to four steps are required")
    clean_lanes = []
    for lane in lanes:
        box_width = (1012 - 54 * (len(lane) - 1)) // len(lane)
        font_size = 18 if len(lane) == 4 else 21
        budget = (box_width - 24) / font_size * 1.5
        clean_lanes.append(tuple(_bounded(step, label="step", budget=budget, minimum=2, maximum=26) for step in lane))
    clean_lanes = tuple(clean_lanes)
    y_positions = (337,) if len(clean_lanes) == 1 else (294, 392)
    lane_markup = "".join(_lane_svg(lane, y) for lane, y in zip(clean_lanes, y_positions))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="627" viewBox="0 0 1200 627">
<rect width="1200" height="627" fill="#071426"/><text x="52" y="65" font-family="Inter,Arial,sans-serif" font-size="35" font-weight="700" fill="#f7f0df">{html.escape(clean_title)}</text>
<text x="1148" y="58" text-anchor="end" font-family="Inter,Arial,sans-serif" font-size="17" font-weight="700" letter-spacing="2.4" fill="#78d5eb">OPERATING AGENT FLEETS</text>
<rect x="52" y="104" width="1096" height="448" rx="18" fill="#f8fafc"/><text x="94" y="194" font-family="Inter,Arial,sans-serif" font-size="27" font-weight="650" fill="#071426">{html.escape(clean_takeaway)}</text>
{lane_markup}<text x="52" y="597" font-family="Inter,Arial,sans-serif" font-size="15" fill="#98adbd">Editorial summary · conceptual, source-bound</text>
<text x="1148" y="597" text-anchor="end" font-family="Inter,Arial,sans-serif" font-size="15" fill="#98adbd">selamy.dev/agent-fleets/</text></svg>'''
    with tempfile.TemporaryDirectory(prefix="oaf-thumbnail-") as directory:
        source_svg = Path(directory) / "thumbnail.svg"
        rendered = Path(directory) / "thumbnail.png"
        source_svg.write_text(svg, encoding="utf-8")
        try:
            result = subprocess.run(
                [str(renderer), "-s", "format", "png", str(source_svg), "--out", str(rendered)],
                capture_output=True, text=True, timeout=15, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ThumbnailRenderError("local renderer timed out") from exc
        if result.returncode != 0:
            raise ThumbnailRenderError("local renderer failed")
        _validate_png(rendered)
        output.parent.mkdir(parents=True, exist_ok=True)
        rendered.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--takeaway", required=True)
    parser.add_argument("--lane", action="append", nargs="+", required=True)
    parser.add_argument("--renderer", type=Path)
    args = parser.parse_args()
    try:
        render_thumbnail(args.source, args.output, title=args.title, takeaway=args.takeaway,
                         lanes=tuple(tuple(lane) for lane in args.lane), renderer=locate_renderer(args.renderer))
    except (OSError, ThumbnailRenderError) as exc:
        print(f"thumbnail render failed: {exc}", file=sys.stderr)
        return 1
    print(f"rendered diagram thumbnail: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
