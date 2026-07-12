# Disclosure policy

This repository is public. Every committed byte, branch, issue, pull request, workflow log, artifact, and deleted file must be treated as permanently discoverable.

## Default rule

Publish the minimum evidence needed to support a useful claim. A public claim may be narrower than the underlying evidence. A private source does not become publishable because an agent can access it, a file is gitignored, a value is redacted after commit, or a repository is private today.

Private operating repositories remain private by default and are not publication artifacts. Their visibility must never be changed to support this field guide.

## Allowed material

- Public repository URLs, immutable public commit or release identifiers, and public documentation.
- Public issue or pull-request URLs after a disclosure review of their text, attachments, logs, and linked context.
- Aggregated or derived statements that an authorized reviewer has approved and that cannot be used to reconstruct restricted values.
- Conceptual diagrams that omit private topology, addressing, credentials, account identifiers, and security-sensitive control details.
- Synthetic test fixtures that are unmistakably fictional and cannot collide with real identifiers.

## Forbidden material

The following must not appear in this repository or its collaboration surfaces:

- raw or lightly edited private transcripts, messages, email, tax documents, or financial records;
- local filesystem paths, private source locators, private repository URLs or names, private hostnames, addresses, ports, cluster or account identifiers, and jump-host details;
- credentials, secrets, tokens, cookies, private keys, recovery material, or authentication/session data;
- taxpayer identifiers, government identifiers, filing details, account numbers, private financial values, wallet addresses, positions, transaction identifiers, or custody details;
- private Telegram identifiers or message content;
- personal data about third parties that is not already deliberately public and necessary to the claim;
- scanner fixtures derived from real secrets or private values;
- generated images, screenshots, logs, metadata, or diagram source containing any forbidden material.

Paraphrase is not sufficient when the structure, chronology, rare wording, or combination of details could identify the restricted source.

## Bounded historical exceptions

The forbidden-material rule remains absolute for every new commit and collaboration surface. It is not a claim that the already-public Git history is clean.

The reproducible audit in `evidence/audits/git-history-privacy-2026-07-12.json` recorded 124 pre-existing findings bound to finding-set SHA-256 `7a42c274bb021a4a07b08e10bb27a0d34019a839ded490fce8517205db852566`:

- 123 private-hostname matches in automatically generated historical commit metadata; and
- one local-file-URL match in a historical synthetic validator fixture.

Subject to Patrick's second H1 decision on this exact policy revision, those finding identities—not the pattern categories generally—may be treated as a closed historical exception set. The exception means only that history is preserved despite those already-public objects. It does not mean the objects are safe, private, removed, endorsed, or evidence for a field-guide claim.

The exception boundary is fail-closed:

1. The exact historical scanner and the immutable audit replay must remain valid.
2. `tools/verify_history_exception_boundary.py` must prove that a fresh verified-remote scan reproduces the same 124 finding identities, categories, counts, and finding-set digest with no missing or additional finding. It also reports a digest of the evolving remote-ref snapshot so safe new objects and refs remain visible without changing the closed exception set.
3. The forward guard must pass for each candidate branch between immutable full commit OIDs.
4. Any new match—including the same rule or apparent value in a different object, line, or historical path—is outside the exception and returns `REVISE`.
5. No raw matched value, raw historical path, or restricted locator may be copied into an exception record, issue, log, or review artifact.
6. The public result must be described as `PASS WITH RECORDED HISTORICAL EXCEPTIONS`, never as clean history or an unqualified privacy pass.

The machine-readable proposed boundary is `evidence/audits/git-history-privacy-exceptions-2026-07-12.json`. It stores only aggregate categories and cryptographic bindings. Neither `pending_second_h1` nor `ready_for_second_h1` grants an exception by repository state alone.

The pinned historical scanner's standalone CLI emits redacted-but-actionable object/line locators for a controlled local investigator. That diagnostic stream must not be persisted to public workflow logs, issues, artifacts, or publication records. The qualified comparator calls the same scanner implementation in-process and emits only aggregate counts plus finding-set and remote-ref-set digests.

Activation sequence is fixed:

1. merge no policy proposal while it remains unapproved;
2. run the comparator against the fresh verified remote-ref set and immutable current commit; a pending or ready candidate without external attestation must report `MATCH BUT NOT EXTERNALLY AUTHORIZED`, never pass;
3. create one ready candidate whose diff from the reviewed pending policy base changes exactly the boundary record, this policy's status text, and the policy-binding test—no other path;
4. adversarially verify the ready candidate, its real pending base, ancestry, exact changed-path set, and complete diff;
5. Patrick reviews the immutable ready commit and records the exact second H1 statement outside repository-controlled state;
6. write that externally supplied statement to a physically separate attestation file bound to the ready commit SHA; never commit the attestation to this repository;
7. rerun the fresh comparator with the exact current SHA and external attestation; only the exact finding-set match, exact ready diff, and exact external decision together may emit `PASS WITH RECORDED HISTORICAL EXCEPTIONS`;
8. merge the already approved ready commit without further source change.

History rewriting is prohibited under this disposition. A future rewrite requires a separate impact inventory and explicit decision covering invalidated source pins, evidence revisions, pull requests, releases, backlinks, forks, and recovery procedures.

## Evidence states

Every material claim must use one of these states:

- **Publicly reproducible:** a reader can verify the claim from allowlisted public sources.
- **Internally corroborated; not publicly reproducible:** an authorized reviewer verified a restricted source and approved only the stated public claim.
- **Proposed:** desired behavior or design without sufficient current-state proof.
- **Historical:** true at a stated cutoff and not asserted as current.
- **Unverified:** evidence is incomplete; the claim must be narrowed or omitted.

An internally corroborated claim may expose a public-safe evidence ID and disclosure state, but never the restricted locator.

## Review requirements

Two independent questions govern publication:

1. **Factual review:** does the cited evidence support the exact wording and time scope?
2. **Disclosure review:** can the artifact expose, correlate, or help reconstruct forbidden information?

Tax, live-money, custody, agent access, private-message, and security-sensitive material requires Patrick's explicit approval of the exact public artifact. Approval of a topic, outline, earlier draft, or evidence class is not approval of a later artifact.

## Incident response

If restricted material may have entered GitHub:

1. stop publication and prevent further copying;
2. treat the value as compromised and rotate or revoke it when applicable;
3. record the affected surfaces without reproducing the value;
4. remove access through the appropriate GitHub and credential-provider procedures;
5. assess history, forks, caches, workflow logs, artifacts, and generated outputs;
6. add a regression test using synthetic data; and
7. obtain a fresh disclosure review before resuming.

Deleting the latest file is not proof that disclosure has been contained.

## Current approval status

Patrick recorded `H1 REVISE: preserve history; treat the two recorded audit categories as bounded historical exceptions; add a forward guard; do not rewrite.` The forward guard is merged. Repository state cannot activate the exception. A reviewed `ready_for_second_h1` commit plus Patrick's physically separate exact-commit attestation must pass the comparator before merge. Pending or unattested ready status grants no exception and does not authorize creating or using the confidential register, processing sensitive case material, deployment, or publication.
