<!-- PRE-H4 DRAFT — DO NOT PUBLISH -->
## Memory retrieval is not authority

A shared vector database can improve recall. It cannot decide truth, scope, or permission.

The safer model separates three layers:

1. A versioned, reviewable record remains authoritative.
2. Structured lookup wins when the caller knows the identity.
3. Semantic search remains a derived, rebuildable discovery aid.

Every retrieved candidate should resolve back to its source, scope, cutoff, and supersession state. Writes should update the authoritative record before indexing. Corrections should change the source, invalidate or tombstone the bad derived state, rebuild, and verify the index against a source manifest.

That is the difference between fleet-scoped recall and an ungoverned “hive mind.” A memory service can be a useful typed capability; a versioned skill should still define when retrieval, persistence, promotion, or refusal is appropriate.

The chapter compares this target design with the narrower mechanics currently demonstrated by public repository evidence:

https://selamy.dev/agent-fleets/06-memory-and-provenance/

What does your memory layer do when its best-ranked answer conflicts with the source of truth?
