# Site export contract

The field-guide repository is the canonical source. A website build may consume only the files listed in [`export/site-manifest.json`](../export/site-manifest.json), exported by an immutable commit or tag.

## Channels

- `preview` may include entries marked `preview` or `release`. It is for local or access-controlled review.
- `release` includes only entries explicitly marked `release`. Moving an entry to this channel is a publication decision and requires the applicable human gate.

The current manifest contains no release entries. A successful preview export is not authorization to publish.

## Boundary

Source paths are confined to public guide, documentation, evidence-record, diagram, and asset roots. Destination paths are confined to `content`, `data`, and `static`. Absolute paths, traversal, symlinks, duplicate sources or destinations, unknown fields, and forbidden path segments fail closed.

The exporter copies exact bytes without rendering or evaluating Markdown, SVG, or JSON. It emits stable metadata containing the requested channel, immutable source revision, dirty-tree flag, destination, media type, byte length, and SHA-256 digest for every file.

Private or confidential evidence is never an export source. The public repository must not contain it in the first place; the allowlist is an additional boundary, not a substitute for the disclosure and privacy gates.

## Usage

From a clean checkout at an immutable revision:

```sh
python3 tools/export_site.py --channel preview --output /tmp/operating-agent-fleets-preview
```

A release export refuses a dirty working tree. The consuming site must verify `export-metadata.json`, stage only the emitted bundle, and record the exact revision it consumed.
