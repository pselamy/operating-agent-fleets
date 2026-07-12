# Privacy review checklist

Record the artifact, immutable revision, reviewer, review date, and result. A review applies only to the exact revision inspected.

## Automated preflight

- [ ] Secret and privacy scanner passes on the full diff and generated artifacts.
- [ ] Fetch every public branch, tag, pull-request head, and pull-request merge ref into a non-shallow, non-promisor clone, then run `python3 tools/verify_history_exception_boundary.py --remote origin`. The comparator first proves every fetched local ref equals the evolving remote ref, scans the complete ref set with Git replacement objects disabled, and compares exact finding identities/categories/counts/digest with the closed boundary. Pending status returns `MATCH BUT INACTIVE`; only active status plus an exact match returns `PASS WITH RECORDED HISTORICAL EXCEPTIONS`. Persist only the comparator's aggregate/digest output. The standalone scanner's object/line diagnostics are controlled local investigation data and must not enter public logs or artifacts.
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

A `REVISE`, mismatch, operational failure, or inactive result blocks merge or publication. Absence of a recorded result is not approval. The pending policy candidate itself requires Patrick's second H1 decision against its immutable commit and exact activation diff before activation or merge.

`PASS WITH RECORDED HISTORICAL EXCEPTIONS` is available only after the machine-readable boundary status is active and an exact full-scan finding-set comparison passes. It does not authorize sensitive-case processing, deployment, or publication.
