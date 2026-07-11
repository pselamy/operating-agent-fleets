#!/usr/bin/env bash
set -euo pipefail

# Renderer release: https://www.npmjs.com/package/@mermaid-js/mermaid-cli/v/11.16.0
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
python3 tools/validate_diagrams.py

jq -r '.diagrams[] | .source as $source | .exports[] | [$source, .theme, .svg_id, .path] | @tsv' diagrams/manifest.json |
while IFS=$'\t' read -r source theme svg_id expected; do
  rendered="$TMP/$(basename "$expected")"
  npx --yes @mermaid-js/mermaid-cli@11.16.0 \
    --quiet \
    --backgroundColor transparent \
    --configFile "diagrams/mermaid-${theme}.json" \
    --svgId "$svg_id" \
    --input "$source" \
    --output "$rendered"
  cmp "$expected" "$rendered" || {
    echo "diagram render differs: $expected" >&2
    exit 1
  }
done

echo "diagram render check passed"
