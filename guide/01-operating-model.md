# 1. From chatbot to operating system

## Reader question

What changes when agents own durable work instead of isolated prompts?

## Chapter contract

This chapter will introduce the field guide through a public-safe vignette, then define the two coupled loops that organize the rest of the book:

1. durable work becoming an evidence-backed outcome; and
2. operational experience becoming a versioned, tested constraint.

It will distinguish a **domain-agent fleet** of persistent, specialized agents from an **execution pool** of fungible workers. It will also separate transferable principles from environment-specific implementation choices.

## Required evidence before drafting

- Public lineage records for the field-guide repository, public agent skills, laneq, and the dated public-repository inventory.
- Public-safe architecture evidence for durable work, context routing, verification, and rollout.
- A reviewed record for any internally corroborated claim.

## Required visuals

- C4 system context: where the human, domain-agent fleet, execution pool, durable work substrate, and evidence systems meet.
- The two-loop model: how execution and system learning reinforce one another.

## Architecture preview — reference design

The following views establish the vocabulary for the eventual chapter without asserting an observed private topology. The public records verify only selected examples: laneq supports lease-based work mechanics; agent-skills and the MCP aggregator provide versioned distribution surfaces; memory-mcp exposes limited versioned and semantic-memory mechanisms. The operator, agent populations, boundaries, schedulers, policy evaluator, credential issuer, delivery system, telemetry, and end-to-end loops in these figures remain proposed unless a later evidence record says otherwise. [@evidence:artifact.laneq] [@evidence:artifact.public-agent-skills] [@evidence:artifact.public-mcp-repositories] [@evidence:artifact.memory-mcp]

![C4 system-context diagram showing an operator use one operating agent system, which returns evidence and outcomes and sends authorized requests to external systems of record and action. Source, delivery, knowledge, agent, worker, policy, credential, and verification components remain internal and are deferred to the container view.](../diagrams/chapter-01/system-context.light.svg)

_Figure 1.1 — System context. The operating agent system stays opaque at this level; private deployment and every neighboring-system relationship remain unverified reference design._

The container view uses illustrative component categories to show distinct boundaries and the data crossing them. It intentionally omits hostnames, endpoints, accounts, namespaces, repository identities, credentials, and network routes. Another operator could replace every category while preserving the separation of identity, work, policy, capability, source, memory, evidence, and external action.

![C4 container diagram showing separate boundaries for a local client, mediated access, a persistent agent principal, a temporary worker principal, durable work state, versioned source and delivery, scoped knowledge, authorization policy, credential custody, evidence and telemetry, and an external action target. Arrows label the caller identity, bounded context, work and lease identity, source revision, authorization decision, short-lived capability reference, external operation, and evidence crossing those boundaries.](../diagrams/chapter-01/container-trust-boundaries.light.svg)

_Figure 1.2 — Container view with trust boundaries. This is a public-safe reference design, not a map of private infrastructure._

The operating model has two coupled loops. The first converts a durable work item into a side-effect-free plan, evaluates authority before mutation, performs only the authorized action, and then verifies the result. Human-gated work waits for a recorded decision and returns for evaluation; denial stops the path until a new or materially changed work item exists. Evidence is a postcondition, never retroactive permission. The second loop converts observed failure or friction into a versioned constraint. A lesson does not feed future routing merely because it was remembered: it must survive tests and adversarial review, immutable rollout, and live enforcement proof. Recurrence measurement can then refine the constraint without bypassing review.

![Flowchart showing a work loop from durable work through routing, side-effect-free planning and validation, a consequence-based authority decision, authorized mutation or action, evidence as a postcondition, and integrated outcome. Human-gated work waits for a recorded decision and returns for evaluation; denied work stops until a new or materially changed work item exists. The outcome feeds a system-learning loop from observation through a versioned constraint, tests and adversarial review, immutable rollout, live enforcement proof, and recurrence measurement. Only proven constraints feed future routing.](../diagrams/chapter-01/two-coupled-loops.light.svg)

_Figure 1.3 — The work loop and system-learning loop reinforce one another without silently expanding authority._

## Safety and accuracy boundary

The chapter will not expose private repository contents, hostnames, network topology, credentials, private conversations, or restricted evidence locators. It will not describe coordination as a peer-to-peer mesh or hive mind. Mechanisms that are intended but not verified will be labeled **proposed**.

_Evidence cutoff: 2026-07-11 for the cited public artifacts. Drafting status: scope and architecture established; vignette and full prose remain gated._
