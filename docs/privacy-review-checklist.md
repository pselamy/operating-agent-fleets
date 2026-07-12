# Privacy review checklist

Record the artifact, immutable revision, reviewer, review date, and result. A review applies only to the exact revision inspected.

## Automated preflight

- [ ] Secret and privacy scanner passes on the full diff and generated artifacts.
- [ ] `python3 tools/privacy_history_scan.py --verify-remote origin` passes over every reachable blob, commit, annotated tag, and historical path from fetched non-shallow branch, tag, and public pull-request refs after proving local refs match the remote; record the exact immutable ref map and result.
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
