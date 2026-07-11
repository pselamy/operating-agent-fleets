# 5. Throughput without pretending every branch is current

_Evidence cutoff: 2026-07-11. Claim status: the public queue behavior and upstream BuildBuddy capability boundaries are verified at the cited cutoffs. Fleet-wide CI/CD conformance, private deployment details, and measured acceleration are not publicly reproducible and are not asserted here._

## Currency is not the same as safety

High-throughput development creates an uncomfortable fact: several branches can be individually reasonable and still conflict when they meet. Requiring every branch to absorb every new main-branch commit before merge reduces one kind of uncertainty, but it also serializes contributors behind a moving target. Removing that requirement increases integration risk. Neither choice removes the need to detect and repair regressions on the shared branch.

The useful question is therefore not “Was every branch current?” It is:

> Which work becomes worthless when a newer revision exists, which work must finish once started, and what durable signal appears when integration fails?

**Lane-Scoped Supersession** is a reference design for answering that question. It is not a claim that every private repository currently enforces the design. The model has three rules:

1. Supersede only within a declared lane whose work has the same purpose and target.
2. Cancel stale work only while it is side-effect-free.
3. Never cancel an active mutation merely because a newer revision arrived.

Those rules separate throughput policy from wishful thinking. A newer commit can make an older validation result irrelevant. It cannot make a half-applied deployment harmless.

## Define the lane before defining “latest”

“Run only the latest commit” is dangerously incomplete. Latest where, and for what?

A **lane** is a stable identity for work that competes to answer the same operational question. A pull request's validation lane might be `(repository, pull request, check family)`. A main-branch release lane might be `(repository, environment, release pipeline)`. A Terraform mutation lane may need an additional state or workspace boundary.

Two jobs may supersede one another only when they share that identity. A new documentation commit must not cancel an unrelated production repair. A new pull-request revision must not cancel another pull request's validation. A newer deployment candidate must wait behind an active mutation rather than interrupting it.

The public `laneq` artifact demonstrates narrower, useful mechanics for durable ownership: pending items are ordered within a lane, a take operation records a consumer and lease in an immediate SQLite transaction, and expired leases or explicit requeues return work to pending while incrementing a counter. That is repository-level evidence for lease-based work state, not proof of a deployed fleet, exactly-once side effects, or this chapter's complete supersession policy. [@evidence:artifact.laneq]

## The state transition that matters

Supersession is safest before a worker owns the job. Once work is running, the cancellation rule must depend on consequence.

| Current state | Work type | Newer revision arrives | Required behavior |
| --- | --- | --- | --- |
| Waiting | Validation | Yes | Mark stale and keep only the newest eligible revision |
| Running | Validation with no side effects and no mutation credential | Yes | Request cancellation, require termination acknowledgement, and record that the result is non-authoritative |
| Waiting | Mutation | Yes | Replace the waiting candidate if policy permits and authorization binds the replacement |
| Running | Mutation | Yes | Let it finish or execute a designed rollback; queue the newest candidate next |
| Finished | Any | Yes | Preserve evidence, but do not present the old result as proof for the new revision |

This is more precise than cancel-in-progress as a universal setting. Cancellation is not a performance option; it is an authority decision. A test process can usually be stopped. A schema migration, infrastructure apply, external payment, or deployment may already have changed reality.

Cancelable validation must be structurally incapable of mutation. It should receive no deployment, infrastructure, custody, or production-write credential. Validation and mutation need a hard job or stage boundary, not a conditional step in one credentialed process. The scheduler must observe termination before treating the lane as quiescent. At the mutation boundary, a new job must re-check policy and authorization against the immutable candidate it will act on. A cancellation request alone is not proof that the old process stopped.

![Timeline showing revision B arriving and superseding waiting revision A, then revision C arriving and canceling side-effect-free validation B. After B acknowledges termination, C validates. A separate mutation lane lets an earlier mutation finish, resolves C's source SHA to an authorized artifact digest, mutates that digest next, and verifies the real target.](../diagrams/chapter-05/lane-scoped-supersession.light.svg)

_Figure 5.1 — Lane-Scoped Supersession preserves the latest useful validation while serializing mutation. This is a reference design, not a fleet-conformance claim._

## Bind authority to the artifact, not the branch name

“Main” is a moving reference. Approval for one revision must not silently authorize another.

For source validation, record the exact commit SHA the result covers. If that source produces a deployable artifact, a trusted build must record a verifiable provenance link from source SHA to artifact digest. Mutation authorization should bind the artifact digest whenever bytes, an image, a package, or an infrastructure plan is what will change reality. Authorization may bind only a source SHA when the mutation consumes that exact immutable source directly and no rebuild or resolution step can change the acted-on bytes.

Carry the correct identity through authorization, execution, and post-action verification. Rebuilding after approval creates a new artifact digest and requires a new provenance and authorization decision unless a reviewed policy explicitly defines an equivalent reproducible-build rule. If policy checks source SHA `A` but a job deploys an unlinked digest `D`, a green check for `A` proves nothing about `D`.

This yields a simple invariant:

> The evidence accepted for a state-changing action must identify the authorized artifact digest—or exact immutable source when no artifact boundary exists—and preserve the provenance link between source, artifact, action, and observed target.

Branch protection, environments, concurrency groups, locks, and auto-merge are implementation mechanisms. None is evidence by itself. The public field-guide repository currently documents desired operating behavior, but public evidence does not establish fleet-wide conformance for private repositories. That gap must remain visible rather than being converted into a broad present-tense claim.

### Auto-merge is a queue consumer, not a safety proof

Auto-merge can remove human polling once a pull request satisfies its declared checks and approval policy. It does not prove the branch is current, that the declared checks are sufficient, that the merged revision will integrate cleanly with concurrent changes, or that main will remain green. In a supersession design, auto-merge consumes an eligible candidate; it does not widen the candidate's authority.

The merge record must still identify the exact revision accepted, and merged-revision validation must still run. If branch currency is intentionally relaxed, the red-main protocol is the compensating integration control. Auto-merge without revision-scoped checks and red-main response merely increases the rate at which latent incompatibilities reach the shared branch.

## Red main is an incident signal, not an embarrassment to hide

Allowing a branch to merge without first absorbing every main-branch change accepts a known integration risk. The compensating control is not optimism. It is an explicit red-main protocol.

A robust protocol should:

1. run integration validation on the merged revision;
2. create one durable, urgent repair item per red episode or first-known-failing boundary;
3. attach the failing revision, check, logs, and first known bad boundary;
4. append equivalent evidence to that episode while splitting distinct failures rather than globally deduplicating them;
5. prevent a red result from being overwritten by an unrelated green result;
6. assign ownership and a response objective;
7. restore main through a tested fix or revert; and
8. clear red only when an authoritative merged repair revision or verified revert proves restoration; and
9. convert the failure into a permanent regression constraint when feasible.

The red state is sticky and revision-scoped. A newer queued candidate, a canceled job, or an unrelated green result does not erase the incident. This is the bargain: branches may move quickly because shared-branch failure becomes durable work. Without that response path, relaxed currency is merely deferred integration cost.

## High coverage is a regression ratchet, not an integration oracle

High test coverage makes generated or human-written behavior easier to isolate and repair because changed paths are more likely to have executable examples. When a defect escapes, the repair can add a focused test so the same observed behavior cannot silently return. That is the regression ratchet.

Coverage is still a proxy. Line or branch percentages do not establish assertion quality, feature coverage, realistic boundaries, concurrency behavior, deployment correctness, or integration with a newer main branch. A high threshold is useful when it prevents untested behavior from accumulating, but it must sit beside mutation testing or test review where appropriate, contract and artifact checks, merged-revision integration tests, runtime provenance, and inspection of the real result.

The operating claim should therefore be narrow: high coverage increases the surface on which regressions can be captured and repaired. It does not make a stale branch current or turn a pre-merge green result into proof of the merged artifact.

## Validation throughput has four different levers

Build acceleration is often described as if every speedup came from the same mechanism. It does not.

### 1. Local parallelism

Bazel can schedule independent actions concurrently on one machine. The bound is the runner's CPU, memory, I/O, dependency graph, and configured resources.

### 2. Job parallelism

A CI system can run independent jobs or matrix entries concurrently. This is orchestration outside Bazel. More jobs can reduce elapsed time while increasing duplicated setup and resource consumption.

### 3. Remote cache and Build Event Service

A remote cache allows compatible invocations to reuse action results instead of recomputing them. Build Event Service ingestion supplies invocation events and a result surface for diagnosis. BuildBuddy's public source describes itself as a Bazel build-event viewer, result store, and remote cache; its documentation treats these as distinct capabilities. [@evidence:documentation.buildbuddy-capabilities]

Cache reuse is conditional. Inputs, toolchains, platforms, environment, flags, and action hermeticity affect keys and correctness. Authentication and write policy also matter: BuildBuddy documents API-key authentication and a read-only mode that disables cache uploads. Its troubleshooting material describes timeout, unavailability, eviction, and local-state mismatch failure modes. [@evidence:documentation.buildbuddy-capabilities]

### 4. Remote execution

Remote execution moves actions to remote workers. It is not implied by uploading build events or configuring a cache. BuildBuddy documents a separate Bazel `remote_executor` configuration for remote execution. [@evidence:documentation.buildbuddy-capabilities]

This distinction prevents a common evidence error: observing a cache hit and reporting “distributed execution.” The narrower claim is the honest one. The public evidence supports BuildBuddy's capability boundaries; it does not prove that Patrick's repositories enable remote execution, conform to one configuration, or achieve a quantified speedup.

![Data-flow diagram showing a source revision entering a credential-free Bazel validation job. Bazel executes eligible actions locally, queries a trust-scoped remote cache, and sends minimized build events to a separately controlled Build Event Service. Cache hits and local results feed tests; the authoritative validation result remains bound to the source SHA. Remote execution is shown as a separate disabled or experimental path, not implied by cache or event configuration.](../diagrams/chapter-05/buildbuddy-validation-flow.light.svg)

_Figure 5.2 — BuildBuddy validation data flow separates local execution, cache reuse, event observability, and optional remote execution. This is a public-safe reference design, not Patrick's private topology._

## Cache only what you can trust

A shared cache is a performance system and a supply-chain boundary. A bad writer can distribute a bad result faster than local computation would.

A defensible policy distinguishes trusted and untrusted contexts:

- trusted protected-branch jobs may receive scoped write authority;
- pull requests from forks or untrusted code should be read-only or isolated;
- secrets should be injected at runtime and masked, never committed into Bazel configuration;
- cache namespaces should separate incompatible trust, platform, or toolchain domains;
- cache read authority and tenant isolation should be scoped as deliberately as cache writes;
- Build Event Service payloads should minimize or redact command lines, repository paths, environment data, test logs, and artifact metadata before retention;
- BES and cache access should have retention, deletion, audit, and incident-response rules;
- fork and untrusted-code invocations should not inherit trusted event, cache-read, or artifact visibility;
- fallback behavior should be explicit when the backend is unavailable; and
- suspicious results need a way to bypass, quarantine, or invalidate the cache.

These are design requirements. The upstream documentation's support for separate keys and read-only cache access makes such a policy possible; it does not prove any downstream implementation follows it. [@evidence:documentation.buildbuddy-capabilities]

## Measure useful green revisions, not activity

Supersession can lower wasted compute while making dashboards look quieter. Caching can increase hit rate while leaving the critical path unchanged. Parallelism can shorten one stage while moving the bottleneck elsewhere.

Measure the system around a useful outcome:

- time from revision ready to authoritative green result;
- p50 and p95 critical-path duration;
- canceled waiting and running validation by lane;
- compute and network spent on superseded revisions;
- cold, warm, and cache-disabled comparisons;
- cache hit rate and bytes transferred, separated from wall-clock impact;
- queue delay, runner provisioning, analysis, execution, and test time;
- backend fallback and unavailable rates;
- red-main frequency, repair latency, and recurrence; and
- cost per useful green revision.

Do not adopt remote execution merely because it is available. Pre-register the suspected bottleneck, candidate workload, expected improvement, acceptable cost, hermeticity constraints, and rollback criteria. If local execution is not the measured bottleneck, remote workers add complexity without addressing the problem.

## Failure modes to design for

### Cross-lane cancellation

An overly broad concurrency key allows unrelated work to cancel each other. Include every identity component required to make work substitutable.

### Cancellation after side effects begin

A generic cancel-in-progress policy interrupts mutation. Split validation and mutation into different stages or jobs, and make the mutation stage non-cancelable once authority is exercised.

### Mutable authorization

Approval attaches to a branch or pull request while the deployed revision changes. Bind approval and evidence to an immutable SHA or digest.

### Stale green overwrites current red

An older job finishes after a newer failure and updates a shared status. Status identity must include revision; only the current authoritative revision may satisfy the gate.

### Cache poisoning or incompatibility

An untrusted writer or non-hermetic action produces a reusable but wrong result. Scope write authority, separate namespaces, inspect cache misses and anomalies, and retain a cache-bypass path.

### Metrics without counterfactuals

A warm build is declared faster without a comparable cold or cache-disabled run. Preserve the comparison method and the invocation evidence before claiming acceleration.

## A review checklist

Before calling a pipeline high-throughput, answer:

1. What is the exact lane identity?
2. Which waiting work may be superseded?
3. Which running work is side-effect-free and cancelable?
4. Where does mutation begin, and what serializes it?
5. What immutable revision or digest does authorization cover?
6. Can an old result overwrite the status of a newer revision?
7. What happens when main becomes red?
8. Which contexts may write to a shared cache?
9. Are cache, event ingestion, local parallelism, job parallelism, and remote execution reported separately?
10. Do BES and cache payload, read access, retention, deletion, and audit rules match their sensitivity?
11. Which measurement demonstrates less time or cost per useful green revision?

The transferable lesson is not “never update branches” or “always cancel CI.” It is to supersede only work that has become valueless, serialize work that changes reality, bind proof to immutable artifacts, and make integration failure durable enough to repair and learn from.

## Evidence used by this chapter

- [laneq record](../evidence/records/laneq.yaml) [@evidence:artifact.laneq]
- [BuildBuddy capability-boundary record](../evidence/records/buildbuddy-capabilities.yaml) [@evidence:documentation.buildbuddy-capabilities]

The records establish public implementation or documentation facts at their stated cutoffs. They do not expose or prove private fleet topology, configuration, invocation history, conformance, or outcomes.
