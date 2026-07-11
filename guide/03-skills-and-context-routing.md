# 3. Skills instead of a monolithic framework

_Evidence cutoff: 2026-07-11. Claim status: public repository behavior is verified at the cited cutoffs; private deployment and fleet-wide adoption are not publicly reproducible._

## The framework question is usually too broad

When several agents can retrieve context, hand work to one another, call external systems, and leave durable evidence, the obvious question is: “Which agent framework runs all of this?”

That question assumes the system must have one orchestration product at its center. It does not. A useful operating architecture can emerge from narrower pieces with explicit responsibilities:

- durable work state instead of conversational handoffs;
- skills that teach an agent how to approach a class of work;
- typed tools that let it call an external capability;
- systems of record that remain authoritative outside the model's context window;
- credentials and approvals that bound what a tool may do; and
- evidence gates that decide whether the result counts.

This is still a framework in the ordinary sense: a set of interfaces, rules, and constraints. It is not a single runtime library, graph executor, or proprietary control plane. The distinction matters because a library can standardize execution without solving authority, provenance, privacy, or proof.

Public repositories provide examples of three components consistent with this approach: a reusable skills library, a tag-pinned MCP distribution surface, and a lease-based work queue. The records establish separate artifacts, not a common deployed system or a causal claim about how they were produced. [@evidence:artifact.public-agent-skills] [@evidence:artifact.public-mcp-repositories] [@evidence:artifact.laneq]

## Two extension mechanisms, two different jobs

A useful design heuristic is a question:

> Would the agent read this to know how, or call this to do it?

If it reads the material to change how it reasons or executes with capabilities it already has, the extension is primarily a **skill**. If it calls a structured interface to reach a database, service, queue, API, or other external capability, the extension is primarily a **tool**—often exposed through MCP. The boundary is not ontological: skills can direct tool use, and tool protocols can expose resources or instructions. The heuristic identifies where the durable center of gravity belongs.

### A skill is procedural knowledge

A skill can encode a review method, a migration discipline, a debugging sequence, an evidence hierarchy, or a rule for choosing among tools. It belongs in versioned text because the artifact's value is the procedure itself.

As an authoring recommendation, a strong skill should say when to activate, when not to activate, what evidence is required, where judgment remains, and which failure modes should stop the work. It should change behavior rather than merely restate a slogan.

For example, “verify the real artifact rather than a proxy” is knowledge. It can tell an agent that a green deployment job is insufficient until the live page has been opened. There is no universal `verify_reality()` endpoint to call. The skill changes the sequence of actions performed with other tools.

### An MCP server is a callable capability

As a design recommendation, an MCP server is most useful at a system boundary. It can present typed operations and structured results for something outside the model: lease the next work item, search an approved source, query metrics, read a memory record, or request a constrained mutation. These examples describe potential tool shapes; the aggregate public MCP record does not verify each server's runtime contract.

A well-designed tool should not smuggle an operating philosophy inside a vague mega-operation. Its contract should favor clear verbs, input validation, typed errors, and safe retries where writes are involved. Credentials belong in an external secret or credential boundary, not in prose, a prompt, or committed configuration. These are prescriptive requirements, not claims that every listed public server already satisfies them.

### Hybrids are normal

Many useful capabilities can have both halves. A research skill can define source selection, lineage, and uncertainty rules while a search MCP performs authenticated retrieval. A memory skill can define what deserves durable capture while a hypothetical memory tool performs a scoped read or reviewed write. A dispatch skill can define when delegation is appropriate while a queue or dispatch tool records the handoff. These are reference-design examples, not verified properties of every public implementation.

The split should follow the read/call boundary. Turning methodology into a server creates needless code and operational surface. Leaving an authenticated API call in prose produces brittle shell recipes, untyped results, and duplicated credential handling.

## Four capability tiers

“The fleet's skills” is too imprecise to be an operating model. Capabilities have different audiences, sensitivity, and release obligations. A practical taxonomy has four tiers.

This is a **proposed governance taxonomy**. The public evidence verifies the public-fleet distribution example; it does not establish private tier inventories, promotion events between tiers, or curated-upstream consumption by a deployed fleet.

### 1. Agent-local

An agent-local skill exists because one role has a narrow responsibility or one environment has a special constraint. It should remain local while its language, activation conditions, or value are still unstable.

Local does not mean exempt from review. It means the expected consumer is one role, and wider compatibility has not been demonstrated. A local skill that proves broadly useful can be promoted; one that never changes behavior should be deleted.

### 2. Internal fleet

An internal-fleet skill captures a reusable procedure that several trusted workloads need but that contains organization-specific assumptions or private operational detail. Distribution may be shared, but publication is inappropriate.

This tier must not become a dumping ground. Private names, topology, and credentials are not what make a procedure reusable. Whenever the durable lesson can be separated from its private instance, the generic procedure should move outward and the restricted locator should remain in a private system of record.

### 3. Public fleet

A public-fleet skill is generic enough to use outside its origin environment and safe enough to publish. It needs stable naming, concise activation metadata, privacy and security review, compatibility discipline, and a versioned distribution path.

At its cutoff, the public agent-skills repository contained 97 independently named `SKILL.md` workflows, a Claude Code marketplace manifest, a documented skills-CLI path, public-safety and malicious-instruction pattern checks, public API stability checks, and a 90 percent coverage floor for repository-owned tooling. That proves an inspectable distribution and validation surface—not installation, invocation, compliance, or impact in any downstream workload. [The repository is public](https://github.com/selamy-labs/agent-skills). [@evidence:artifact.public-agent-skills]

### 4. Curated upstream

Some capabilities should not be copied at all. Mature public skills and tools can remain in their upstream projects and be pinned, reviewed, and consumed under their own licenses.

This tier prevents an internal library from becoming an unauditable mirror of the internet. Adoption should record provenance, version, license, review status, and the reason the dependency earns its place. “Available” is not the same as “approved.”

## Propagation is a release process, not telepathy

Calling a skill “fleet-wide” can imply that every agent instantly knows it. That is not a safe assumption. A procedure becomes fleet-wide only through an observable distribution chain:

1. A learning is captured as a candidate procedure.
2. The candidate is generalized, stripped of private context, and reviewed.
3. Tests or examples demonstrate that it changes behavior in the intended cases.
4. A versioned artifact is released.
5. Each consumer pins or upgrades to that version through a reviewable change.
6. Runtime or artifact evidence shows the consumer actually loaded and used it.
7. Recurrence or outcome measurements determine whether the skill helped.

The public skills repository proves steps in authoring and distribution. It does not provide a public consumer inventory. That missing proof is precisely why “the skill exists” and “the fleet enforces the skill” must remain separate statements. [@evidence:artifact.public-agent-skills]

The same rule applies to MCP. At its cutoff, the public aggregator manifest defined seven named configurations backed by six public repositories, each pinned to a Git tag. The human-facing README had drifted behind the manifest: it still described five repositories and an obsolete telemetry pin. That discrepancy is useful evidence. Versioned manifests reduce ambiguity, but they do not eliminate documentation drift; a gate must compare the two. [The corrective issue is public](https://github.com/selamy-labs/agent-mcp/issues/21). [@evidence:artifact.public-mcp-repositories]

![Flowchart showing a learning move from sourced candidate through the skill-or-tool decision, audience classification, review, versioned release, consumer upgrade, loading evidence, and outcome measurement. A separate path reviews and pins an existing upstream artifact.](../diagrams/chapter-03/skill-propagation.light.svg)

_Figure 3.1 — Skill and knowledge propagation is a release process. This is a reference design; the public evidence verifies distribution mechanics, not private adoption._

## Context routing without mind-to-mind communication

Agents do not need direct access to one another's hidden state. In a durable system, context moves through mediated, inspectable paths.

The following is a **reference design**, not an observed end-to-end deployment claim:

1. **Intent:** a work item states the outcome and evidence required.
2. **Capability selection:** a skill identifies the relevant systems of record and safe procedure.
3. **Scoped retrieval:** a typed tool queries an approved source with a bounded credential.
4. **Context reduction:** the caller receives only the material needed for the task, with source and cutoff.
5. **Execution:** the agent performs the work within its authority boundary.
6. **Durable handoff:** results, decisions, and unresolved questions return to a repository, queue, issue, or other system of record.
7. **Verification:** another check inspects the real artifact rather than trusting the caller's summary.

This pattern is **mediated coordination**, not a peer-to-peer mesh and not a hive mind. The substrate—not a model's private context window—carries the durable state.

Least-privilege retrieval is only the first privacy boundary. Sensitive tool output also needs minimization, prompt and log handling rules, retention and deletion policy, and review before it enters a wider durable handoff or public artifact. A bounded credential limits access; it does not make every returned detail safe to propagate.

![Sequence diagram showing a human placing bounded work in a durable substrate, a domain agent using a skill and typed capability, an evidence record receiving the claim, and an independent verifier accepting, narrowing, or requeuing the result after inspecting the real artifact.](../diagrams/chapter-03/mediated-collaboration.light.svg)

_Figure 3.2 — Cross-plane collaboration is mediated by durable state and evidence. The sequence is a reference design, not a claim that the complete private topology is publicly verified._

The public laneq implementation illustrates one such substrate. Its shared take operation begins an immediate SQLite transaction, selects the highest-priority eligible item in one lane, records a consumer and lease, and commits. Expired leases and explicit requeues return work to pending while incrementing a counter. CLI, MCP, and optional gRPC interfaces delegate to the same core behavior. These are repository-level facts; public evidence does not establish fleet deployment, workload volume, or exactly-once execution. [Inspect laneq](https://github.com/selamy-labs/laneq). [@evidence:artifact.laneq]

That distinction is central. Within one SQLite database, the implementation serializes eligible take operations through an immediate transaction. It does not prove that an external side effect happened once, that a worker obeyed priority, or that any private deployment is healthy. Those require idempotency, artifact evidence, runtime observation, and environment-specific controls.

## Memory is a source-routing problem before it is a vector problem

“Add memory” often becomes shorthand for “add a vector database.” Similarity search can be useful, but retrieval is not authority.

A durable knowledge design separates at least three concerns:

- **authoritative record:** the versioned fact, decision, procedure, or source locator;
- **derived recall:** an index, embedding, summary, cache, or search structure that helps find the record; and
- **access path:** the scoped tool that lets an agent retrieve or propose a change.

As a design requirement, the derived layer should be rebuildable from the authoritative layer. If an embedding index is corrupted, stale, or poisoned, the system needs a way to discard and reconstruct it without losing the actual knowledge. If a summary conflicts with the source, the source should win. This paragraph describes the desired architecture; it is not evidence that the public memory implementation enforces it.

The public MCP distribution includes a tag-pinned memory interface alongside queue, research, dispatch, telemetry, and DNS capabilities. The aggregate public record proves that the distribution entry and repository exist; it does not, by itself, verify a private memory deployment, retrieval quality, poisoning resistance, or fleet utilization. [@evidence:artifact.public-mcp-repositories]

This architecture therefore does not require a vector database as its organizing center. It can add semantic recall when measured retrieval failures justify one. The decision should follow evidence: what could not be found, how often, at what cost, with what false-retrieval risk, and whether a simpler index would suffice.

## Why not start with LangChain or LangGraph?

Not using a monolithic orchestration library is not a claim that those libraries are bad or unnecessary everywhere. It is a statement about where the hard constraints live.

In this model:

- work state lives in durable queues and repositories;
- procedural behavior lives in versioned skills;
- external capabilities live behind typed tools;
- authorization lives with credentials, policies, and human gates;
- verification lives in tests, artifact checks, and runtime evidence; and
- learning becomes a reviewed change to one of those artifacts.

A graph runtime may still be the right choice when a product needs a fine-grained, checkpointed execution DAG; repeatable branching and joins inside one request; standardized state persistence across graph nodes; or a large ecosystem of model and retriever adapters. A vector database may be justified by measured semantic-retrieval needs. A chain library may speed prototyping.

What none of them supplies automatically is the complete operating discipline: who may authorize a consequential action, which source is authoritative, whether private evidence may be disclosed, how a failure becomes a regression test, or whether a deployed outcome was inspected. Those questions survive every library choice.

## Failure modes of the composable approach

Building from smaller pieces trades framework lock-in for integration discipline. The risks are real.

### Skill sprawl

If every correction becomes a new skill, the library becomes noisy and activation becomes unpredictable. Promotion needs a utility bar: recurring problem, changed behavior, clear trigger, non-duplicative guidance, and a plausible consumer.

### Stale instructions

A skill can outlive the API, repository, or policy it references. Version pins and evidence cutoffs help, but consumers also need upgrade and deprecation paths.

### Capability disguised as prose

A skill that tells the agent to hand-build authenticated requests is a fragile tool implementation. Move structured access into an MCP server or another typed interface.

### Knowledge disguised as infrastructure

A server that only returns a methodology adds packaging, deployment, and security surface without adding capability. Keep the procedure as inspectable text.

### Overbroad tools

A typed interface can still be dangerous if one operation accepts arbitrary commands, repositories, or destinations. Narrow verbs and allowlisted targets make authority visible. They do not make every permitted action safe.

### Configuration drift

The public MCP README/manifest mismatch shows how quickly prose and machine state can diverge. Generate documentation from manifests or test them against one another. [@evidence:artifact.public-mcp-repositories]

### Memory poisoning

A writable memory interface could turn one bad inference into durable context for many later tasks. Provenance, scope, review, reversibility, and rebuildable derived indexes are therefore design requirements, not verified properties of the public distribution entry.

### Invisible non-adoption

Publishing a skill or tool creates supply, not consumption. Without a consumer inventory and live loading evidence, “fleet-wide” is an aspiration.

## A design test for your own system

Before adding another framework, server, or memory layer, ask:

1. Is this knowledge to read or a capability to call?
2. What is the authoritative system of record?
3. What is merely a derived index or cache?
4. Which credential and authority boundary governs the call?
5. Where is the durable work item and its lease or ownership state?
6. What evidence proves the real outcome?
7. How is the artifact versioned, distributed, pinned, and upgraded?
8. Which consumers demonstrably use it?
9. What private context must be removed before wider distribution?
10. What failure would cause this mechanism to be narrowed, replaced, or deleted?

If those answers are explicit, a composable architecture can stay understandable even as the number of agents and tools grows. If they are implicit, adding a graph library only moves the ambiguity.

## What transfers, and what does not

The transferable lesson is not “copy this repository layout” or “avoid a particular library.” It is to separate procedural knowledge, callable capability, durable state, authority, and evidence—and then version the interfaces between them.

The environment-specific choices in the public artifacts include `SKILL.md`, MCP, GitHub, SQLite, and particular distribution manifests. Another operator could use runbooks, an internal tool protocol, a managed queue, or a different source host and still preserve the same boundaries.

The standard is not whether the architecture looks agentic. It is whether a reader can trace how an instruction becomes behavior, how a call receives authority, how context reaches the caller, where the outcome becomes durable, and what evidence would reveal that the system failed.

## Evidence used by this chapter

- [Public agent-skills record](../evidence/records/agent-skills.yaml) [@evidence:artifact.public-agent-skills]
- [Public MCP repositories record](../evidence/records/public-mcp-repositories.yaml) [@evidence:artifact.public-mcp-repositories]
- [laneq record](../evidence/records/laneq.yaml) [@evidence:artifact.laneq]
- [Dated public-repository inventory](../evidence/records/public-repository-inventory.yaml) [@evidence:inventory.public-repositories-2026-07-11]

The inventory supplies context about the public surface only. It is not used as a proxy for impact, private fleet size, or agent contribution. [@evidence:inventory.public-repositories-2026-07-11]
