# Evidence classes and trust hierarchy

Evidence quality depends on what was observed, when it was observed, and whether another reader can reproduce the check. A green proxy cannot prove a different artifact.

## Trust hierarchy

Use the strongest available evidence and disclose when only a weaker class exists:

1. **Live behavior** — the real deployed or externally recorded outcome was inspected.
2. **Deployed artifact** — an immutable deployed revision, digest, package, or generated artifact was inspected.
3. **Repository artifact** — source, tests, configuration, commit history, issue, or pull request was inspected.
4. **Documentation or memory** — a durable written record was inspected but not re-verified against current behavior.
5. **Agent assertion** — an agent reported a result without independently inspected evidence.

Higher placement does not remove disclosure constraints. Live private data may be stronger evidence and still be unsuitable for publication.

## Public evidence classes

| Class | What it may prove | Typical public source | Common limitation |
| --- | --- | --- | --- |
| `live_behavior` | Reader-visible behavior at a cutoff | Public site or endpoint | Behavior may change after verification |
| `deployed_artifact` | Identity or content of a deployed build | Release, digest, package, Pages deployment | Does not alone prove runtime behavior |
| `repository_artifact` | Source, configuration, history, or review state | Commit, file, issue, pull request | Repository intent may differ from deployment |
| `documentation` | A recorded design, policy, or claim | Public documentation | May be stale or aspirational |
| `internally_corroborated` | A narrowly approved claim from restricted evidence | Public-safe evidence record only | Not publicly reproducible |

`agent_assertion` is not an acceptable public evidence class. It can identify a verification task but cannot close one.

## Lineage rules

- **Primary:** read directly from the system of record during the verification run.
- **Copied:** inherited from a prior output or cache and not independently confirmed.
- **Synthetic:** an example or fixture; never evidence of a real outcome.
- **Derived:** computed from other inputs and inherits the weakest input lineage.

Every record must state its verification method, date, cutoff, supported claims, limitations, sensitivity, and status. A claim cannot be broader, newer, or more reproducible than its evidence.

## Verification outcomes

- `verified`: sufficient evidence supports the stated claim at the cutoff.
- `limited`: evidence supports a narrower claim recorded in limitations.
- `proposed`: desired design or behavior, not current-state proof.
- `stale`: the cutoff is no longer adequate for the intended claim.
- `rejected`: evidence does not support publication of the claim.

Evidence records are versioned snapshots, not permanent truth.
