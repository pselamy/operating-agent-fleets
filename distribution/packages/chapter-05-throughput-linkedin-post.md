<!-- PRE-H4 DRAFT — DO NOT PUBLISH -->
## “Run only the latest commit” is not a complete policy

The policy must first name where “latest” applies and which work is competing.

High-throughput delivery needs a lane identity: the repository, target, and check or release family whose candidates actually compete. Within that lane, newer work can supersede waiting validation. Running validation may be canceled only when it is structurally side-effect-free and termination is acknowledged.

Active mutation is different. A deployment, infrastructure apply, or other consequential operation must finish or follow a designed rollback. The newest authorized candidate waits; intermediate candidates may be skipped. The final verifier checks the real target against the exact artifact digest—not merely whether a workflow turned green.

This model permits branches that are not current with main while preserving a regression ratchet on the shared branch. It trades mandatory pre-merge currency for explicit integration detection and rapid repair; it does not pretend the risk disappeared.

The full reference design, including its BuildBuddy boundaries and evidence limitations, is here:

https://selamy.dev/agent-fleets/05-throughput-and-supersession/

Which jobs in your delivery system are genuinely safe to supersede?
