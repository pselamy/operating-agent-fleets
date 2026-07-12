# Privacy review checklist

Record the artifact, immutable revision, reviewer, review date, and result. A review applies only to the exact revision inspected.

## Automated preflight

- [ ] Secret and privacy scanner passes on the full diff and generated artifacts.
- [ ] `python3 tools/privacy_history_scan.py --verify-remote origin` examines every reachable blob, commit, annotated tag, and historical path from fetched non-shallow branch, tag, and public pull-request refs after proving local refs match the remote; record the exact immutable ref map and result. Until the bounded-exception policy is active, any finding returns `REVISE`. After activation, only an exact reproduction of the recorded 124 finding identities and finding-set digest with no additional finding may be reported as `PASS WITH RECORDED HISTORICAL EXCEPTIONS`; never report clean history.
- [ ] Before accepting a new branch in this SHA-1 repository, `python3 tools/privacy_forward_guard.py --base <trusted-full-40-character-commit-oid> --head <candidate-full-40-character-commit-oid>` passes. The tool rejects movable refs and extended revision expressions, disables Git replacement objects for the complete validation and scan, requires a non-empty descendant range, scans commit and blob objects reachable through that range, and scans every path name in every candidate commit tree—including unchanged inherited path names. Base-reachable blob payloads are not rescanned, and annotated tag objects are outside a commit-to-commit range; the full verified-remote history audit remains mandatory for tags and historical baseline findings. This forward guard prevents recurrence on the branch candidate surface; it does not convert the full historical audit from `REVISE` to `PASS`.
- [ ] Link checker finds no private, authenticated, local, or expiring locator.
- [ ] Images, SVG source, alt text, metadata, workflow logs, and downloadable artifacts were included in the scan.

## Manual disclosure review

- [ ] Every factual claim has an evidence ID and appropriate evidence state.
- [ ] Public sources were opened and checked at the recorded cutoff.
- [ ] Internally corroborated claims reveal neither restricted locators nor reconstructable detail.
- [ ] No private repository name, URL, branch, path, hostname, address, port, cluster, account, or jump-host detail appears.
- [ ] No credential, session material, identifier, tax/financial value, wallet/position detail, or private message appears.
- [ ] Chronology, screenshots, quotations, rare phrases, and combined details cannot re-identify a private source.
- [ ] Diagrams are conceptual and omit exploitable trust-boundary details.
- [ ] Generated images contain no embedded private input and no generated text that substitutes for reviewed labels.
- [ ] Limitations and evidence cutoffs are visible to the reader.

## Consequence review

- [ ] The artifact cannot change a private repository's visibility or weaken access controls.
- [ ] The artifact does not imply autonomous tax filing, objective agent rankings, verified safety, or profitability without approved evidence.
- [ ] The artifact distinguishes standing authorization from demonstrated safety.
- [ ] Tax, live-money, custody, private-message, and security-sensitive material has Patrick's approval for this exact revision.

## Decision

- Result: `PASS` / `REVISE`
- Artifact and revision:
- Reviewer:
- Reviewed at:
- Evidence cutoff:
- Required changes or limitations:

A `REVISE` result blocks merge or publication. Absence of a recorded result is not approval.

`PASS WITH RECORDED HISTORICAL EXCEPTIONS` is available only after the machine-readable boundary status is active and an exact full-scan finding-set comparison passes. It does not authorize sensitive-case processing, deployment, or publication.
