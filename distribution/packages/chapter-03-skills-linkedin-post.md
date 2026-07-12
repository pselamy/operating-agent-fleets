<!-- PRE-H4 DRAFT — DO NOT PUBLISH -->
## “Which agent framework?” may be the wrong first question

An agent system needs more than an orchestration runtime. It needs explicit homes for procedural knowledge, callable capabilities, durable work, authority, and evidence.

A useful boundary is:

> Would the agent read this to know how, or call this to do it?

Put review methods, stop conditions, and tool-selection rules in versioned skills. Put authenticated access to queues, databases, services, and other external systems behind narrow typed capabilities. Let skills direct tool use, but do not confuse either mechanism with authorization or proof.

For collaboration, prefer durable records over “shared cognition”: bounded work enters a system of record, a scoped capability acts, and an independent verifier checks the real artifact. That pattern can work with or without a monolithic agent framework.

The evidence-backed field-guide chapter separates the transferable design from what public repositories actually prove:

https://selamy.dev/agent-fleets/03-skills-and-context-routing/

Where has the skill/tool boundary clarified—or complicated—your agent architecture?
