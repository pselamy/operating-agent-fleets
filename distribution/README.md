# Distribution packages

The canonical field guide lives at `https://selamy.dev/agent-fleets/`. Distribution artifacts summarize and link to a canonical chapter; they never become a competing source of truth.

Supported channels are:

- `linkedin_newsletter`: a condensed edition with one canonical link;
- `linkedin_post`: a short post with one public-safe visual and one closing question; and
- `medium`: optional delayed syndication that declares the canonical URL.

## Pre-H4 workflow

1. Pin the exact merged field-guide source revision and chapter source path.
2. Draft from the canonical chapter and its evidence records.
3. Keep claims narrower than or equal to the canonical source.
4. Run privacy, claim, link, visual, and channel-preview checks.
5. Compute the exact content digest.
6. Stop. This repository contract intentionally cannot represent H4 approval or publication.

The manifest is a draft registry, not an authorization or publication ledger. An editor cannot turn repository metadata into evidence that Patrick approved or published something. Before distribution can proceed, a separate design must bind a human-controlled attestation to the complete immutable release envelope: channel, content, visual and alt text, canonical target, source revision and path, evidence cutoff, and completed checks. Publication and independent live verification must be separate recorded acts. Until that verifier exists, every external action remains blocked.

H1, H2, H3, and H4 are independent. A merged chapter, deployed canonical page, valid draft, or pull-request merge does not authorize distribution.

Templates are under [`templates`](templates/). They are scaffolds, not approved posts. Real drafts belong under `distribution/packages/` and must be registered in [`manifest.json`](manifest.json).
