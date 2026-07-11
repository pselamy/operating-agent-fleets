# 6. Memory without surrendering provenance

_Evidence cutoff: 2026-07-11. Claim status: public memory-mcp repository mechanics are verified at the cited cutoff. Live deployment, consumer reachability, source freshness, authorization isolation, retrieval quality, poisoning recovery, utilization, and task-value improvement are unverified._

## Recall is not authority

An agent forgets useful context when a conversation ends. A fleet can repeat the same mistake when one role's learning never reaches another. It is tempting to solve both problems with a shared vector database and describe the result as shared cognition.

That metaphor is wrong in exactly the dangerous way. A retrieval service does not create shared cognition, shared judgment, or shared authority. It returns records selected by an algorithm. Those records may be stale, incomplete, malicious, out of scope, or derived from a source the caller is not allowed to see.

The safer objective is **fleet-scoped semantic recall over versioned memory**:

- versioned Markdown or another inspectable record remains authoritative;
- structured and keyed lookup outranks semantic similarity when identity is known;
- embeddings and vector indexes remain derived and rebuildable;
- every hit carries enough provenance to reach the source;
- domain scope is the default and fleet scope requires deliberate promotion; and
- correction means changing the authoritative record, invalidating bad derived state, and rebuilding.

This design improves discovery without asking a similarity score to decide truth.

## Three layers, three different promises

A memory subsystem should separate three layers.

### 1. Authoritative record

The authoritative layer preserves the fact, decision, procedure, or source locator in a reviewable system of record. It supports history, correction, access control, and attribution. Git-backed Markdown is one implementation. A database with immutable audit history can serve the same role.

The promise is durable provenance: a reviewer can identify who or what introduced the record, when, from which evidence, under which scope, and what later superseded it.

### 2. Structured retrieval

If the caller knows a stable identity—a memory key, decision ID, incident number, repository path, customer ID, or exact title—direct lookup should win. Structured state can also encode precedence: current policy outranks an old note; a signed decision outranks a summary; a source record outranks an embedding-generated association.

The promise is deterministic selection under explicit keys and rules.

### 3. Derived semantic recall

An embedding index helps when the caller does not know the key or vocabulary. It can associate “cancel stale CI” with a record titled “Lane-Scoped Supersession.” It can rank candidates using semantic similarity, keywords, and recency.

The promise is discovery, not correctness. A hit should be treated as a lead that points back to an authoritative record.

The public memory-mcp repository contains examples of the first and third layers: a local interface over Markdown files and a separate semantic interface with add, search, and get operations backed by an injected vector store. The pgvector implementation keys records by scope and name and blends semantic, recency, and keyword signals during search. These are repository facts, not evidence of a live or effective fleet deployment. [@evidence:artifact.memory-mcp]

## The provenance envelope

A useful retrieval hit needs more than a body and score. A durable memory record should carry:

- stable record identity;
- authoritative source repository or system;
- source path or key and immutable revision;
- authoring human or agent identity;
- creation and last-review time;
- source issue, incident, decision, or session when applicable;
- domain scope and permitted audience;
- evidence class and confidence;
- privacy classification and retention policy;
- supersedes and superseded-by links;
- embedding model and index revision as derived metadata; and
- a content digest that lets the caller detect mismatch.

The retrieval response should preserve that envelope. An agent may summarize the body for its current task, but the source identity and cutoff must survive context reduction.

The inspected public semantic record does not implement this complete contract. Its core record exposes scope, name, type, description, body, embedding, and update time; public evidence does not establish source repository, path, commit, author, evidence class, privacy class, supersession, or retention fields on every hit. That is a documented gap, not an invitation to infer provenance from naming. [@evidence:artifact.memory-mcp]

## Read flow: retrieve, resolve, verify

A semantic-memory read should be a routing sequence:

1. Authenticate the caller and derive readable scopes before retrieval.
2. Classify the task within those allowed domains.
3. Prefer current session state or a known structured key when available.
4. Query only the authorized domain scopes; add shared scope only when policy permits.
5. Treat semantic hits as candidates, not instructions.
6. Reject or quarantine hits missing provenance or failing post-retrieval policy.
7. Resolve the selected hit to its authoritative source.
8. Check revision, supersession, privacy, and time sensitivity.
9. Use the source-backed fact with an explicit cutoff.
10. Record whether the retrieval was used, ignored, stale, or wrong without logging sensitive content.

This sequence limits two failure modes. First, semantic similarity cannot silently override a keyed policy. Second, text retrieved from memory cannot acquire system-prompt authority merely because it was indexed. Retrieved instructions are untrusted content until a governing policy identifies them as current procedural authority.

## Write flow: evidence before promotion

Writing shared memory has a wider consequence surface than reading it. One bad query can mislead one task; one poisoned fleet record can mislead many future tasks.

A durable write should therefore proceed through a controlled path:

1. Capture the candidate with source evidence and proposed scope.
2. Decide whether the material is a fact, decision, procedure, preference, hypothesis, or ephemeral observation.
3. Decline weak, duplicated, sensitive, or unauthorized material.
4. Write or update the authoritative record first.
5. Review promotion from a domain scope to a shared scope separately.
6. Commit the provenance envelope and content digest.
7. Queue indexing for that immutable source revision.
8. Verify that the derived record matches the source and contains no orphaned predecessor.

“Add memory” must not mean “write directly into pgvector and hope Markdown catches up.” At the inspected cutoff, the public shared `add` operation writes directly to its injected vector store. The Markdown indexer also upserts source files into that store, but the source does not prove that every semantic write first becomes versioned Markdown. Effective source-of-truth enforcement therefore remains unverified. [@evidence:artifact.memory-mcp]

![Flowchart showing callers authenticate and receive readable scopes before memory reads prefer structured keys or use semantic search for discovery. Selected hits resolve to versioned authoritative records and missing provenance is rejected. Writes create or update the authoritative domain record before reviewed fleet promotion and indexing. Correction changes the source, writes a minimized authoritative tombstone consumed by every rebuild, verifies deletion propagation, rebuilds the index, and compares it with the source manifest.](../diagrams/chapter-06/memory-read-write-rebuild.light.svg)

_Figure 6.1 — Semantic memory accelerates discovery while authoritative versioned records govern truth, scope, correction, and rebuild. This is a reference design; the public implementation does not yet prove the whole flow._

## Scope is an authorization question

A `group_id` column is useful namespacing. It is not authorization by itself.

The public memory-mcp semantic core validates scope strings and filters searches to requested scopes, including the shared scope by default. A caller can also request a record by scope and name. The inspected core does not demonstrate that caller identity is mapped to an allowlist of readable and writable domains. A network policy can limit which workloads reach a service, but namespace ingress alone does not decide which records each authenticated caller may access. [@evidence:artifact.memory-mcp]

A defensible scope model should be deny-by-default:

- an agent receives explicit read and write scopes;
- domain scope is the normal write target;
- shared scope requires a separate promotion authority;
- sensitive domains may forbid shared promotion entirely;
- retrieval applies row- or object-level authorization before ranking;
- embeddings, logs, metrics, and backups inherit the source sensitivity; and
- denied cross-scope queries are tested and observable without exposing content.

Search convenience must not flatten privacy boundaries. A record is not safe for fleet scope merely because several agents could benefit from it.

## Embeddings create a separate data boundary

Embedding generation processes the source text, so model location changes the disclosure surface. As a reference-design choice, a local or in-cluster model can keep source text inside an operator-controlled boundary and avoid sending it to an external model provider. That can reduce egress; it does not prove that the caller, logs, model server, vector store, or backups are properly isolated. This chapter does not assert which embedding provider or location, if any, a private deployment uses.

An external embedding provider receives the text submitted for embedding and associated request metadata under that provider's retention and processing rules. Sensitive source classes may need to forbid that path, minimize the submitted text, or use a separately approved model boundary. API credentials, request logs, error bodies, and tracing must not become secondary memory stores.

Embedding provenance should record model identity, exact version or digest where available, dimensions, preprocessing and chunking rules, normalization, and index revision. Changing a model or dimensions requires re-embedding; changing chunking or source text should also invalidate affected vectors. Even with a pinned local model, hardware kernels and numerical libraries may limit byte-for-byte reproducibility, so rebuild verification should compare record identity, dimensions, source digests, retrieval regressions, and declared tolerances rather than assuming identical floating-point arrays.

## Rebuild means more than rerunning the indexer

A derived index is rebuildable only if an operator can destroy it and reproduce an explainable result from authoritative sources.

The rebuild protocol should:

1. pin the source revisions, parser version, embedding model, dimensions, and ranking configuration;
2. create a fresh index rather than mutating the suspect one in place;
3. parse every eligible source and reject missing required provenance;
4. compare source and index manifests by identity and digest;
5. detect missing, duplicate, stale, and orphaned records;
6. run scope-isolation and retrieval regression tests;
7. atomically promote the new index revision;
8. retain a rollback pointer and destroy the quarantined index according to policy; and
9. record the rebuild evidence without copying sensitive bodies into logs.

The public indexer walks Markdown roots and idempotently upserts discovered files. An incremental pass does not, by itself, remove records whose source files disappeared. The repository documentation describes dropping and rebuilding the table, but public evidence does not demonstrate source/index manifest comparison, orphan detection, atomic cutover, or a live recovery rehearsal. [@evidence:artifact.memory-mcp]

## Correction and poisoning recovery

Shared recall needs a kill procedure before it needs sophisticated ranking.

When a record is wrong, malicious, unlawful, stale, or overexposed:

1. stop or narrow retrieval from the affected scope;
2. identify the authoritative record and every derived index revision containing it;
3. correct, supersede, quarantine, or delete the source under the applicable retention policy;
4. commit a minimized authoritative tombstone or revocation record that every rebuild consumes before eligible memories;
5. rebuild from reviewed source revisions;
6. verify scope, provenance, and planted negative queries;
7. rotate credentials or investigate callers if the event suggests compromise; and
8. verify propagation across vector rows, replicas, logs, backups, caches, and any revocable exported context; and
9. add a synthetic regression case for the poisoning pattern.

The tombstone is part of the authoritative control plane, not merely a vector row. It needs stable identity, precedence over older source revisions, a reason class that avoids repeating sensitive content, an effective time, and a policy-governed retention or expiry rule. Every incremental index and full rebuild must apply active tombstones before admitting records. Expiry is safe only when the underlying source, replicas, and replay paths can no longer resurrect the identity.

Deletion is also surface-specific. Removing one vector row does not prove erasure from embeddings, database replicas, logs, backups, caches, model-provider retention, or context already exported to an agent. A deletion workflow must inventory those surfaces, distinguish immediate revocation from eventual physical erasure, record exceptions and legal retention, and verify each supported propagation step. Tombstones must be minimized because a revocation record that repeats a sensitive name or body can perpetuate the disclosure it is meant to stop.

The inspected shared semantic interface has no correction, tombstone, or delete operation. That may reduce accidental deletion, but it is insufficient for poisoned or privacy-sensitive shared state. Public issue 26 tracks deletion, provenance, isolation, live health, recovery, and value evidence; until those controls are proved, effective fleet memory remains a target state. [The issue is public](https://github.com/selamy-labs/memory-mcp/issues/26). [@evidence:artifact.memory-mcp]

## Evaluate whether semantic recall earns its risk

A vector layer should answer a measured retrieval problem. Compare at least three conditions:

1. existing skills, files, indexes, and structured lookup without semantic retrieval;
2. semantic retrieval within one approved domain; and
3. semantic retrieval across approved domain plus shared scope.

An offline evaluation set should include planted factual recall, exact provenance questions, stale replacement, conflicting sources, domain-isolation negatives, prompt-injection memories, privacy-restricted records, and deletion/tombstone cases.

Measure:

- zero-result and low-score rates;
- selected versus ignored retrievals;
- stale, wrong-context, and unauthorized-hit rates;
- exact-source resolution success;
- duplicate and conflict rates;
- latency and token cost;
- task success and rework with and without retrieval;
- write, update, promotion, quarantine, and deletion counts; and
- rebuild drift and recovery time.

Instrument metadata, not sensitive bodies. A useful result is not “queries increased.” It is measurable recall improvement without unacceptable privacy, poisoning, wrong-context, latency, or cost regression.

## Start smaller than the architecture permits

The safest rollout begins with one low-risk domain and read-only retrieval. Pre-register success, safety, and kill criteria. Require source resolution for every selected hit. Expand scope only after isolation tests and value measurements pass. Add writes later, and treat shared-scope writes as higher consequence than domain reads.

Do not require memory lookup on every turn. Retrieval has latency, cost, disclosure, and distraction effects. A versioned skill or policy should define when to query, when a structured source is sufficient, when to write, when to promote, and when to decline persistence. The memory server remains the typed capability; methodology belongs in reviewable procedural knowledge. The public skills repository demonstrates a versioned distribution surface for such procedures, but not deployed memory policy or consumer compliance. [@evidence:artifact.public-agent-skills]

## A review checklist

Before calling a memory system fleet-wide, answer:

1. What source is authoritative, and can every hit resolve to an immutable revision?
2. Which fields prove author, evidence, scope, privacy, time, and supersession?
3. When does structured lookup outrank semantic recall?
4. Which caller identities may read, write, promote, correct, and delete each scope?
5. Can a direct vector-store write create durable state absent from the source?
6. Can one compromised agent establish shared truth?
7. How are retrieved instructions prevented from overriding governing policy?
8. Can the index be destroyed and rebuilt with zero unexplained drift?
9. How are orphaned, deleted, duplicated, stale, and poisoned records handled?
10. What evaluation shows semantic retrieval improves outcomes over simpler routing?

The transferable model is not a particular database. It is the separation of authoritative knowledge, deterministic identity, derived recall, scoped authority, and recovery evidence. Semantic search can make a fleet less forgetful. Provenance keeps that convenience from becoming invisible authority.

## Evidence used by this chapter

- [memory-mcp record](../evidence/records/memory-mcp.yaml) [@evidence:artifact.memory-mcp]
- [Public agent-skills record](../evidence/records/agent-skills.yaml) [@evidence:artifact.public-agent-skills]

These records establish public repository behavior at their stated cutoffs. They do not prove private deployment, adoption, live health, retrieval effectiveness, or sensitive-domain suitability.
