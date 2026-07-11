# 2. The tax filing collaboration

## Reader question

How should agent authority change with consequence, reversibility, and data sensitivity?

## Chapter contract

This chapter will use a derived, redacted reconstruction of a tax-preparation and filing collaboration to teach consequence-based authority. It will distinguish the responsibilities of Reid, Codex, and Patrick and show where human decisions were required.

The analysis will use an authority matrix covering:

- reversibility;
- consequence surface;
- data sensitivity;
- authority exercised;
- human involvement; and
- evidence required after the action.

Evidence is a required postcondition, not an autonomy level. The chapter will not claim that agents autonomously filed taxes.

## Required evidence before drafting

- A private, derived event map reviewed against the confidential source.
- A disclosure-approved public reconstruction containing no transcript excerpts.
- A reviewer record stating the permitted public claims and forbidden disclosures.
- Human factual and privacy signoff on the exact public artifact.

## Required visuals

- Tax collaboration sequence showing responsibility and decision boundaries.
- Consequence-based authority matrix.

## Generic authority matrix — reference design

The authority tool can be defined without reconstructing the sensitive case. It evaluates four inputs before any consequential action:

1. **Reversibility:** can the result be safely undone?
2. **Consequence surface:** which people, systems, money, legal duties, or external records can be affected?
3. **Data sensitivity:** which restricted data becomes readable, writable, logged, transmitted, or retained?
4. **Authority exercised:** does the operation only read and prepare, or does it mutate, authenticate, attest, transmit, or control custody?

These are not points to average. The highest applicable consequence determines the minimum authority tier. Uncertainty raises or narrows the gate; it never lowers it. A tier is selected for one operation and immutable subject. It is not assigned permanently to an agent, does not accumulate, and grants no blanket authority over later actions.

| Tier | Operation boundary | Agent authority | Human involvement | Required postcondition evidence |
| --- | --- | --- | --- | --- |
| 0 — Observe and prepare | Public or low-sensitivity read-only, simulated, or no external effect | Research, calculate, reconcile, and draft | Supplies intent and resolves material ambiguity | Sources, assumptions, and reproducible result |
| 1 — Preapproved bounded operation | Reversible local mutation, or restricted-data read within an expiring least-privilege policy | Acts only inside a preapproval bound to operation, source or target, purpose, scope, capability, retention, and rollback or revocation | Defines policy, limits, expiry, minimization, retention, and rollback boundary | Source-access record or exact revision, tests, artifact identity, and rollback/revocation proof |
| 2 — Explicit decision before operation | Material mutation; restricted-data write or transmission; or restricted read outside Tier 1 preapproval | Prepares the exact candidate; acts only after approval bound to it | Approves operation, scope, and immutable subject | Decision record, authorized source or digest, and live verification |
| 3 — Human performs decisive act | Legally binding filing or submission, identity-bound attestation, custody transfer, or another explicitly irreversible high-consequence act | Prepares, checks, and reconciles; does not perform the decisive act | Authenticates, attests, performs the binding submission, or controls custody | Receipt, observed state, reconciliation, and exception record |

Pre-action and post-action failures are different. Missing identity, provenance, scope, capability, expiry, or rollback conditions stop the action before it begins. Evidence is a postcondition, not an autonomy score: a receipt can prove that an authorized action occurred, but it cannot authorize the action after the fact. If required receipt or live verification is missing after an action, mark the result unverified, block acceptance and downstream work, and begin reconciliation or incident handling. That response cannot retroactively undo or authorize the action.

![Consequence-based authority matrix for one operation and immutable subject. Reversibility, consequence surface, data sensitivity, and authority exercised feed a pre-action contract check and highest-applicable-tier rule. Tier zero permits public or low-sensitivity read-only preparation. Tier one permits reversible local mutation or restricted-data reading within an expiring least-privilege preapproval. Tier two requires an explicit decision for material mutation, restricted-data writing or transmission, or restricted reading outside that preapproval. Tier three keeps legally binding filing or submission, identity-bound attestation, custody transfer, and explicitly irreversible high-consequence acts human-performed. Missing preconditions stop action; missing postcondition evidence marks the outcome unverified, blocks downstream work, and triggers reconciliation or incident handling.](../diagrams/chapter-02/consequence-authority-matrix.light.svg)

_Figure 2.1 — Consequence-based authority is a prescriptive decision instrument. It contains no tax-case facts and does not claim that a private deployment enforces these tiers._

## Safety and accuracy boundary

The raw transcript and its locator must never enter this repository, including gitignored paths, fixtures, commit history, issues, or pull-request discussion. No tax identifiers, financial values, filing details, private account data, or verbatim excerpts may be published. Drafting cannot begin until the disclosure boundary and confidential-register design receive explicit human approval.

_Evidence cutoff: 2026-07-11 for the generic reference design only. Drafting status: authority tool established; sensitive case reconstruction remains blocked on disclosure approval._
