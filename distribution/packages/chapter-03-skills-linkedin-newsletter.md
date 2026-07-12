<!-- PRE-H4 DRAFT — DO NOT PUBLISH -->
# Skills or tools? The boundary matters more than the framework

If you build agent infrastructure or platforms, this edition gives you a practical way to decide where procedural knowledge, callable capabilities, durable work, authority, and evidence should live.

The usual first question is: “Which agent framework orchestrates all of this?”

That question starts one layer too high. A graph runtime can coordinate execution, but it does not automatically decide which source is authoritative, who may approve a consequential action, what private context may move between systems, or what evidence proves the real outcome.

Here is the operating model I recommend. Start with a narrower question:

> Would the agent read this to know how, or call this to do it?

## Read this to know how

A skill is durable procedural knowledge. It can encode a review method, a debugging sequence, a migration discipline, or a rule for choosing among tools.

A useful skill should make its activation conditions, required evidence, stop conditions, and decisions that remain with an agent or human explicit. “Verify the real artifact instead of trusting a proxy” is a procedure. It changes how an agent works with other capabilities; it is not naturally a standalone API.

## Call this to do it

Treat a callable capability as a tool when it crosses a system or authority boundary. It can expose a typed operation for something outside the model’s context: leasing a work item, querying an approved source, reading a scoped memory record, or requesting a constrained mutation.

Typed does not mean safe. The operation still needs narrow verbs, validated inputs, bounded credentials, explicit authority, and useful failure evidence. A vague mega-operation can hide just as much risk as an improvised shell command.

Hybrids are normal. A research skill can define source-selection and lineage rules while a search tool performs authenticated retrieval. A memory skill can define what deserves durable capture while a scoped tool performs a reviewed read or write.

## Four tiers keep skill and capability distribution honest

As a proposed governance taxonomy, skill and capability distribution needs more precision than “local” or “shared”:

1. **Agent-local** — narrow, unstable, or role-specific procedure.
2. **Internal fleet** — reusable across trusted workloads but still coupled to restricted assumptions.
3. **Publicly reusable** — generic, documented, tested, and safe outside its origin environment; “public” describes the capability’s distribution tier, not an openly accessible fleet.
4. **Curated upstream** — externally maintained capability adopted under explicit version and supply-chain policy.

Promotion is a release decision. A procedure should move outward only after its private instance has been separated from the transferable lesson and it has been tested with representative consumers outside its origin environment.

## Durable coordination should use records, not shared cognition

For durable, auditable collaboration, agents should coordinate through records rather than relying on an idea of peer-to-peer “shared cognition.” One component records a scoped work item. Another leases it for a bounded period. A skill or context router—a selector for the relevant procedure and capability—chooses the next bounded path. The result returns with source identity and limitations. An independent check inspects the real artifact, and the outcome returns to a repository, queue, issue, or other system of record.

The public `laneq` repository demonstrates a narrower part of this pattern: SQLite-backed work state, priority ordering, renewable leases, and explicit requeue behavior, which returns work for another attempt. That is repository evidence for those mechanics—not proof of a private fleet deployment, workload volume, or a guarantee that an external action happens once and only once. The canonical chapter links the inspected repository and its evidence record.

## Memory is a source-routing problem before it is a vector problem

Similarity search can improve recall, but retrieval is not authority. Keep three roles separate:

- the authoritative versioned record;
- a derived index, embedding, summary, or cache; and
- the scoped access path used to retrieve or propose a change.

The derived layer should be disposable and rebuildable. If a summary conflicts with the source, the source wins. If a writable memory surface can spread one bad inference into later work, provenance, scope, correction, and rebuild tests matter more than calling the result “shared memory.”

## When a graph runtime is still the right answer

LangGraph, LangChain, or another orchestration library can be valuable for checkpointed execution, repeatable branching and joins, standardized node state, or a mature adapter ecosystem. The boundary is simply that a runtime library does not supply the whole operating discipline: durable work state, procedural knowledge, callable capability, authority, and verification still need explicit homes and interfaces.

The canonical chapter includes the supporting diagrams, public evidence records, claim limitations, and correction path:

https://selamy.dev/agent-fleets/03-skills-and-context-routing/

Where has this boundary prevented a failure in your system—and where has a skill/tool hybrid or a different boundary worked better?
