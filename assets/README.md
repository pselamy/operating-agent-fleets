# Editorial visual assets

This directory contains public-safe generated editorial artwork and derived raster thumbnails. Technical diagrams remain under `diagrams/`. Manifest version 1 validates generated PNG assets; a source-controlled overlay/template contract must be added before SVG templates enter the manifest.

Every asset must be registered in [`manifest.json`](manifest.json) with:

- its intended role and media type;
- exact path, byte digest, and pixel dimensions;
- useful alternative text;
- creation method and date;
- generator/provider and exact model/version, or an explicit statement that the managed tool did not expose it;
- the complete generation prompt when generative tooling was used; and
- an explicit statement that text is absent from generated pixels or intentionally supplied by a source-controlled overlay.

Generated artwork must not contain private topology, credentials, financial identifiers, wallet or position details, private conversations, real personal data, product logos, or unsupported system claims. Titles and chapter labels belong in HTML or source-controlled SVG overlays, not generated pixels.

Conceptual artwork is not architecture evidence. Every use of the hero must retain a nearby caption explaining that its nodes, loops, gateways, and central ledger are editorial metaphors—not deployed topology, direct peer connectivity, a central orchestrator, or a verified agent count.

Run `python3 tools/validate_assets.py` after adding or changing an asset.
