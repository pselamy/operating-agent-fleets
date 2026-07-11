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

This policy is a proposal pending Human Gate H1. It permits public-safe structural work but does not authorize processing or publishing sensitive case material.
