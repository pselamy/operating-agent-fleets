# Editorial visual assets

This directory contains public-safe generated editorial artwork, source-controlled SVG templates, and derived raster thumbnails. Technical diagrams remain under `diagrams/`.

Every asset must be registered in [`manifest.json`](manifest.json) with:

- its intended role and media type;
- exact path, byte digest, and pixel dimensions;
- useful alternative text;
- creation method and date;
- provenance type and, for generated assets, generator/provider and exact model/version or an explicit statement that the managed tool did not expose it;
- the complete generation prompt when generative tooling was used; and
- an explicit statement that text is absent from generated pixels or intentionally supplied by a source-controlled overlay.

Generated artwork must not contain private topology, credentials, financial identifiers, wallet or position details, private conversations, real personal data, product logos, or unsupported system claims. Titles and chapter labels belong in HTML or source-controlled SVG overlays, not generated pixels.

Conceptual artwork is not architecture evidence. Every use of the hero must retain a nearby caption explaining that its nodes, loops, gateways, and central ledger are editorial metaphors—not deployed topology, direct peer connectivity, a central orchestrator, or a verified agent count.

The two-loop and mediated-coordination illustrations must also retain nearby captions that name them as editorial metaphors and direct readers to the corresponding source-controlled technical diagram for actual process or architecture claims. In particular, the mediated image must state that its example count and central arrangement are editorial composition—not fleet inventory, deployed topology, central orchestration, peer-to-peer communication, shared cognition, or a hive mind.

Run `python3 tools/validate_assets.py` after adding or changing an asset.

The chapter social card is a template, not a ready-to-publish post. Use `python3 tools/render_social_card.py` to replace its chapter label, three bounded title lines, and `[CHAPTER-SLUG]`. Each title line is limited to 28 characters; unused trailing lines become empty. The renderer rejects unresolved placeholders. A derived card must be separately registered before use; preserve the field-guide identity, chapter-specific canonical-link text, accessibility description, and visible editorial-metaphor boundary. H4 approval still applies to the exact derived distribution artifact and channel once a verifiable approval mechanism exists.
