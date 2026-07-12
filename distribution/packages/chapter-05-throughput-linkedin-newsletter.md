<!-- PRE-H4 DRAFT — DO NOT PUBLISH -->
# “Run only the latest commit” is not a safety policy

If you operate high-throughput CI/CD, this edition gives you a way to decide which work a newer revision may supersede, which work must finish, and what evidence makes the result authoritative.

Imagine two individually green branches merging minutes apart: the second can invalidate an assumption in the first even though neither pre-merge check observed the combined state. Requiring every branch to absorb every new main-branch commit reduces that uncertainty, but it also serializes contributors behind a moving target. Relaxing the requirement accepts more integration risk and makes merged-revision detection and repair essential.

The useful question is not “Was every branch current?” It is:

> Which work becomes worthless when a newer revision exists, which work must finish once started, and what durable signal appears when integration fails?

## Define the lane before defining “latest”

A lane key is the complete identity of work competing to answer the same operational question. It must encode the purpose and target that make two jobs substitutable. For pull-request validation, that key might include repository, pull request, and check family. For a release, it might include repository, environment, and pipeline. Infrastructure mutation may need a workspace or state boundary too.

Two jobs may supersede each other only when they share that identity. A documentation change must not cancel an unrelated production repair. One pull request must not cancel another pull request’s validation.

Lane-Scoped Supersession is the reference design I recommend:

1. Supersede only within a declared lane whose work has the same purpose and target.
2. Cancel stale work only while it is side-effect-free and has no present or obtainable mutation authority.
3. Never cancel an active mutation merely because a newer revision arrived.

This is a design recommendation, not evidence that every private repository currently follows it.

## Cancellation is an authority decision

Waiting validation can usually be marked stale. Running validation may be canceled only if it is structurally incapable of mutation: no deployment, infrastructure, custody, production-write, ambient, or dynamically obtainable authority. Validation and mutation should run in separately permissioned jobs. The controller must receive an authoritative runner or process acknowledgement before treating the lane as quiescent or accepting a successor result; timeout or uncertain termination leaves the lane blocked. The canceled result remains non-authoritative.

Running mutation is different. Once a deployment, infrastructure apply, schema migration, payment, or other external action may have changed reality, a newer revision does not make the partial action harmless. Follow that operation’s designed completion, abort, or rollback protocol; do not supersede it merely because its revision is older. Queue the newer candidate after the mutation lane reaches a verified terminal state.

That boundary should exist in credentials and job structure, not in a conditional branch inside one privileged process.

## Bind authority to immutable identity

“Main” is a moving reference. Approval for one revision must not silently authorize another.

Validation should identify the exact source SHA it covers. If a trusted build produces the bytes that will change reality, preserve a verifiable link from that source SHA to the artifact digest. Authorization, execution, and post-action verification should carry that immutable identity all the way to the observed target.

If policy checks source SHA `A` but a job acts on an unlinked digest `D`, the green result does not authorize `D` or prove that `D` corresponds to `A`.

## Auto-merge consumes a queue; it does not prove safety

Auto-merge removes polling after a candidate satisfies declared checks and approval policy. It does not prove the branch is current, the checks are sufficient, or the merged revision will remain green after concurrent changes.

If branch currency is intentionally relaxed, merged-revision validation and a red-main response become compensating controls. A red episode should create durable, urgent work tied to the failing revision and check. An unrelated green result must not erase it. Red clears only when validation bound to the exact merged fix or revert passes the failed boundary again—and, where reality changed, target identity and health checks verify restoration.

## Coverage is a regression ratchet, not an integration oracle

High coverage creates more executable examples around changed behavior. When a defect escapes, a focused test can prevent the same observed behavior from silently returning.

Coverage percentages still do not establish assertion quality, realistic boundaries, concurrency behavior, deployment correctness, or compatibility with a newer main branch. Coverage helps turn a red-main repair into a permanent regression constraint; it does not make a stale branch current or prove the deployed result.

## Build systems have four capabilities to distinguish

Do not collapse every speedup into “distributed builds”:

1. **Local parallelism** schedules independent actions on one machine.
2. **CI job parallelism** runs independent jobs or matrix entries concurrently.
3. **Remote caching and Build Event Service (BES)** have separate jobs: caching reuses compatible results; BES exposes invocation evidence.
4. **Remote execution** moves actions to remote workers.

The public BuildBuddy documentation distinguishes these capabilities. A cache hit does not prove remote execution, and the public evidence does not prove a particular private configuration or quantified speedup. The canonical chapter links the inspected documentation and evidence record.

A writable shared cache is a supply-chain trust boundary; even read access may expose metadata or artifacts. Write authority, read visibility, namespaces, toolchain compatibility, event payload minimization, fallback, invalidation, and untrusted-fork behavior all need explicit policy.

## Measure useful green revisions, not activity

Measure time and cost per authoritative green revision, not job count. Useful signals include critical-path duration, queue delay, compute spent on superseded work, cold versus warm comparisons, cache-disabled counterfactuals, backend fallback, red-main frequency, repair latency, and recurrence.

Do not adopt remote execution because it exists. Pre-register the bottleneck, candidate workload, expected improvement, acceptable cost, hermeticity constraints, and rollback criteria. If local execution is not the bottleneck, remote workers add complexity without solving the measured problem.

The canonical chapter contains the supporting diagrams, source-level evidence records, detailed failure modes, claim limitations, and correction path:

https://selamy.dev/agent-fleets/05-throughput-and-supersession/

Where has canceling “old” work improved throughput in your system—and where did a newer revision reveal that the supposedly obsolete work still carried unique authority or side effects?
