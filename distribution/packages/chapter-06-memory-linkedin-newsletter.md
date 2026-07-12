<!-- PRE-H4 DRAFT — DO NOT PUBLISH -->
# Memory is useful only while retrieval remains subordinate to truth

If you are adding memory to an agent system, this edition gives you a way to decide whether the design preserves authoritative sources, scoped access, correction, and recovery—or merely makes derived text easier to retrieve.

An agent forgets useful context when a conversation ends. Multiple agents can repeat the same mistake when one role’s learning never reaches another. It is tempting to solve both problems with a shared vector database and describe the result as shared cognition.

That metaphor grants the retrieval layer too much authority. A search service returns records selected by an algorithm. Those records may be stale, incomplete, malicious, out of scope, or derived from a source the caller is not allowed to see.

The safer objective is semantic recall over versioned memory: improve discovery without asking similarity to decide truth.

## Three layers, three different promises

Treat memory as three separable layers:

1. **Authoritative record** — the claim, decision, procedure, or source locator in a reviewable system of record with history, correction, access control, and attribution.
2. **Structured retrieval** — deterministic selection when the caller knows a stable key or explicit precedence rule. Deterministic selection is not automatically true or current; the selected record still needs source, revision, and supersession checks.
3. **Derived semantic recall** — an embedding or hybrid index that discovers candidates when the caller does not know the source’s key or vocabulary.

The semantic hit is a lead, not a fact. It should point back to an immutable authoritative revision—a version that cannot change in place—before use.

The public `memory-mcp` repository demonstrates narrower mechanics: a Markdown-facing interface, a separate semantic interface backed by an injected vector store, scoped record keys, and search that combines semantic, recency, and keyword signals. Those are repository facts—not evidence of live deployment, retrieval quality, source freshness, authorization isolation, poisoning recovery, or task-value improvement. The canonical chapter links the inspected repository and evidence record.

## A hit needs a provenance envelope

A useful retrieval result needs more than a body and score. It should preserve stable record identity, authoritative source and immutable revision, author, reviewer, review decision and time, scope, permitted audience, evidence class, privacy classification, supersession, retention, source digest (a content hash), and the derived model/index identity.

The inspected public semantic record does not implement that complete contract. Its fields do not publicly establish source repository, path, commit, author, evidence class, privacy class, supersession, or retention for every hit. That is a documented gap, not a reason to infer provenance from naming.

## Read flow: retrieve, resolve, verify

A defensible semantic read follows an authority sequence:

1. Authenticate the caller and derive readable scopes before retrieval.
2. Prefer a current structured key when one is known.
3. Search only approved scopes and treat hits as candidates.
4. Reject or quarantine candidates missing required provenance.
5. Resolve the selected candidate to its authoritative source.
6. Verify revision, supersession, privacy, and time cutoff.
7. Use source-backed context while preserving source identity.

Retrieved instructions remain untrusted content unless governing policy identifies the resolved source as current procedural authority. Similarity must not silently outrank a keyed policy or signed decision.

## Write flow: source before index

One bad query can mislead one task. One poisoned shared record can mislead many later tasks.

A durable write should capture source evidence and proposed scope, decline weak or unauthorized material, update the authoritative domain record first, review any promotion to shared scope separately, then index the immutable revision and verify source-to-index identity.

“Add memory” must not mean “write directly to the vector store and hope the source catches up.” At the inspected cutoff, the public shared add operation writes to its injected vector store; the repository does not prove that every semantic write first becomes versioned Markdown. Source-of-truth enforcement remains a target state.

## Scope is authorization, not a namespace string

A scope or group column helps organize records. It does not prove that caller identity maps to allowed read, write, promotion, correction, and deletion operations.

A deny-by-default model should grant explicit domain scopes, keep domain write as the default, require separate authority for shared promotion, apply per-record authorization before ranking, and make embeddings, logs, metrics, and backups inherit the source’s sensitivity.

Search convenience must not flatten privacy boundaries. A record is not safe for wider scope merely because several agents could benefit from it.

## Embeddings create another data boundary

Embedding generation processes source text. A local model can reduce external egress, but it does not prove isolation of callers, logs, model servers, vector stores, or backups. An external provider receives submitted text and request metadata under its own processing rules.

Record embedding-model identity, version or digest, dimensions, preprocessing, chunking, normalization, and index revision. Rebuild verification should compare record identity, source digests, dimensions, retrieval regressions, and declared numerical tolerances rather than assuming byte-identical vectors across hardware and libraries.

## Recovery starts with the source, not the bad vector row

A rebuild is credible only if the derived index can be destroyed and reconstructed from pinned authoritative sources with explainable results.

When memory is wrong, stale, malicious, or overexposed:

- narrow retrieval from the affected scope;
- correct, supersede, quarantine, or delete the source under policy;
- commit a minimized authoritative tombstone—a durable revocation or supersession record—that outranks the older identity;
- verify deletion or revocation across supported surfaces;
- build a fresh index from pinned sources and active tombstones;
- compare source and index manifests—the expected inventories of record identities and content digests—and run isolation regressions; and
- promote the new index only when identities, digests, orphan checks, scope-isolation tests, and retrieval regressions have no unexplained difference outside declared numerical tolerances.

Deleting one vector row does not prove erasure from replicas, logs, backups, caches, provider retention, or context already exported to an agent. Recovery must distinguish immediate revocation from eventual physical deletion and record unsupported surfaces honestly.

The inspected public interface does not prove this complete recovery flow. That limitation is central to the design, not a footnote.

## Make semantic recall earn its risk

Start with one low-risk domain and read-only retrieval. Compare structured lookup without semantic search, semantic search within one domain, and carefully approved broader scope. Measure exact-source resolution, stale and unauthorized hits, task success, rework, latency, cost, rebuild drift, and recovery time.

Do not require memory lookup on every turn. Retrieval adds latency, disclosure, and distraction risk. Expand scope and writes only after isolation tests, source-resolution checks, and value measurements pass.

The canonical chapter contains the supporting read/write/rebuild diagram, repository evidence records, detailed provenance and recovery requirements, current implementation gaps, and correction path:

https://selamy.dev/agent-fleets/06-memory-and-provenance/

Where has semantic recall solved a real retrieval failure in your system—and where has a simpler structured index, stricter scope, or deliberate forgetting produced a safer result?
