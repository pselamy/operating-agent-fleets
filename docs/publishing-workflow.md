# Publishing workflow

The canonical source and public evidence records live in this repository. The canonical reading experience will live at `selamy.dev/agent-fleets/`. LinkedIn is the primary discovery and serialization channel; Medium may carry delayed syndication with a canonical link.

## Artifact flow

1. **Define the reader question.** State the claim boundary, required evidence, consequence level, and visuals before drafting.
2. **Harvest evidence.** Read the current system of record, record an evidence cutoff, and create or refresh public lineage records.
3. **Draft from records.** Link artifact claims to evidence IDs. Narrow or label claims when proof is incomplete.
4. **Validate.** Run schema, claim-link, privacy, secret, test, coverage, link, diagram, and accessibility gates as applicable.
5. **Review.** Complete factual, disclosure, adversarial, and reader-comprehension reviews on the exact revision.
6. **Preview.** Build an unpublished or access-controlled site preview from an immutable repository revision.
7. **Approve.** Record the required human signoff. Sensitive cases, production deployment, and external distribution have separate gates.
8. **Publish immutably.** The site consumes an allowlisted tagged commit or SHA; generated outputs identify their source revision.
9. **Verify the real artifact.** Open the live chapter and inspect links, diagrams, metadata, accessibility text, and canonical URL.
10. **Distribute.** Prepare channel-specific summaries that link to the canonical chapter; do not create divergent factual versions.
11. **Re-verify.** Refresh stale evidence, record corrections, and measure whether published operational claims remain true.

## Required merge evidence

A chapter or evidence change is not complete because a pull request exists or CI is green. Completion requires:

- the intended revision merged;
- required checks and approvals recorded;
- the generated or deployed artifact tied to that revision;
- the real artifact inspected; and
- any external distribution separately approved and verified.

## Human gates

- **H1 — disclosure boundary:** policy, forbidden-data rules, public schema, private-register design, and scanner limitations.
- **H2 — sensitive case reconstruction:** exact public tax artifact after factual and privacy review.
- **H3 — public launch:** exact release candidate and production deployment.
- **H4 — distribution:** each external post, newsletter, or syndication artifact.

Approval at one gate does not imply approval at another.

## Corrections

Material errors or privacy concerns stop distribution. Correct the canonical source first, preserve a public correction note when appropriate, rebuild from an immutable revision, verify the live artifact, and then update derivative channels.
