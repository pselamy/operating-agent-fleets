# 7. Agents are a portfolio, not pets

_Evidence cutoff: 2026-07-11. Claim status: this chapter defines a reference evaluation and lifecycle protocol. It does not rank Patrick's agents, report private scorecards, assert that the protocol is deployed fleet-wide, or publish restricted fleet cases._

## Personified interfaces still require software governance

Persistent agents acquire names, voices, histories, and recognizable working styles. Personification helps an operator remember which context and mandate belong where. It can also obscure the fact that the thing being governed is a deployed software capability with credentials, memory, schedules, dependencies, cost, consumers, and consequence.

“Which agent do I like?” is therefore the wrong portfolio question. So is “Which agent sent the most messages?” A quiet capability may deliver an outcome directly into another system. A talkative capability may produce status traffic no one consumes. A generalist may look versatile because its success conditions are undefined. A specialist may look idle because its triggering work is rare but consequential.

The useful questions are:

- What bounded mandate does this capability own?
- Who consumes its outcomes?
- Which outcomes were actually consumed?
- How much steering and operating burden did they require?
- Which consequence and data boundaries does the capability cross?
- What does it provide that another capability does not?
- Do failures become durable constraints?
- Which reversible change would most improve the portfolio?

Lifecycle terms in this chapter—invest, specialize, merge or subsume, repurpose, pause, and retire—describe software investment decisions. They are not employment judgments or moral claims about a personified interface.

## Begin with mandate thickness

An evaluation is uninterpretable when the mandate is thin. “Software engineer,” “chief of staff,” or “help with real estate” names a theme, not an accountable capability.

A thick mandate specifies:

1. **Bounded problem:** the domain and decisions the capability owns.
2. **Named consumers:** humans, agents, services, or repositories that use its outputs.
3. **Inputs:** durable work sources, events, context, and required evidence.
4. **Outputs:** artifacts, decisions, actions, or state transitions.
5. **Authority:** what it may read, propose, mutate, transmit, or never do.
6. **Success conditions:** observable outcomes and acceptable latency or quality.
7. **Non-goals:** adjacent work that routes elsewhere.
8. **Operating envelope:** cost, cadence, privacy, credentials, and kill conditions.

Mandate thickness is not bureaucracy for its own sake. It supplies the denominator for every later metric. Ten accepted outcomes may be excellent for a rare incident role and meaningless for a capability expected to ship daily. Zero work may indicate underfeeding, not model weakness. Frequent intervention may reflect a vague authority boundary rather than poor reasoning.

The charter should be versioned and protected as semantic configuration. Adding one subordinate capability does not automatically redefine the primary mission. A material change to identity, mission, authority, consumers, primary outcomes, or non-goals requires an explicit decision bound to the proposed charter revision.

## Use an evidence envelope, not a universal score

Evaluate each capability within its own mandate using a common envelope. The common structure makes reviews comparable; the underlying measures remain role-specific.

### 1. Mandate thickness

Record whether the eight charter elements exist, agree across effective configuration, and map to actual work. Missing consumers or success conditions lower confidence in every outcome interpretation.

### 2. Consumed outcomes

Count only artifacts, actions, or decisions that a named consumer actually used. Preserve the consumer, time window, immutable artifact or action identity, and evidence of consumption. Messages, drafts, and task completions are not outcomes merely because they exist.

Useful role-specific examples include accepted pull requests, reconciled filings, incorporated research, resolved incidents, deployed releases, adopted recommendations, or verified external state changes. These examples are categories, not claims about Patrick's fleet.

### 3. Outcome quality

Quality can include correctness, timeliness, novelty, downstream acceptance, rework, escaped defects, and recurrence. Select measures before looking at the result. A capability should not choose whichever metric makes its latest output look strongest.

### 4. Steering burden

Record corrections, re-instructions, restarts, clarification turns, manual recovery, unnecessary approvals, and time spent resolving ambiguity. Separate necessary human authority from avoidable steering. A required human attestation is not agent failure; repeated requests caused by losing known context may be.

### 5. Operating burden

Include model and tool cost, compute, storage, alert noise, credentials, maintenance, incident response, and opportunity cost. Costs need a common reporting period but not a universal value conversion. One high-consequence capability may rationally cost more than several low-risk helpers.

### 6. Consequence-weighted risk

Describe data sensitivity, external authority, irreversibility, blast radius, custody, incident history, and the evidence required after action. Expected outcome value must not erase tail risk. A small observed loss does not prove a signer or approval design is safe.

### 7. Distinctiveness and overlap

Identify capabilities another agent, worker pool, ordinary automation, or external service already provides. Overlap may improve resilience or produce routing ambiguity. Preserve it deliberately, not accidentally.

### 8. Learning velocity

Measure whether failures become versioned skills, tests, policies, fixtures, or runbooks and whether recurrence declines. Repository activity alone is insufficient. The relevant question is whether the system becomes less likely to repeat a known failure at the enforcement point.

Every envelope needs an evidence window, source lineage, confidence, limitations, and missing-data statement. Do not average these dimensions into a league-table number. A single scalar hides mandate differences and lets strong low-consequence activity offset one catastrophic boundary failure.

## Distinguish outcome, activity, and availability

Portfolio reviews often collapse three different signals:

| Signal | What it establishes | What it does not establish |
| --- | --- | --- |
| Activity | Something emitted messages, commits, jobs, or status | A consumer received value |
| Availability | The capability responded or remained schedulable | It had useful work or completed it correctly |
| Consumed outcome | A named consumer used a bounded artifact, decision, or action | The outcome was cost-effective, safe, or repeatable |

Activity is useful for diagnosing liveness and burden. It is a poor proxy for value. Availability is a prerequisite for some mandates and irrelevant during an intentional pause. Consumed outcomes are the strongest starting point, but they still require quality, cost, and risk context.

This distinction also prevents an underfed capability from being mislabeled. If no bounded work enters the system, low output says little about reasoning quality. If work enters but has no named consumer, the mandate or routing contract may be defective. If consumers repeatedly reject outputs, outcome quality or mandate fit becomes a stronger hypothesis.

## Choose among six lifecycle actions

### Invest

Invest when evidence shows consumed outcomes, acceptable burden and risk, defensible distinctiveness, and learning that compounds. Investment might mean better tools, richer durable context, more work, stronger evaluation, or lower-friction authority—not simply a larger model budget.

### Specialize

Specialize when a broad charter produces routing ambiguity but a narrower capability has clear consumers and unique value. Preserve the old charter decision and record what now routes elsewhere. Specialization is a semantic change, not a cosmetic rename.

### Merge or subsume

Merge overlapping capabilities when one accountable boundary can preserve useful outcomes with less routing and operating burden. A subsumption record needs predecessor-to-successor lineage, surviving artifacts, migrated consumers and work, transferred safety constraints, revoked credentials, retained-data disposition, and rollback or reconstruction information.

Consolidation creates survivorship bias. The surviving capability gets credit for the integrated system while abandoned alternatives and migration cost disappear from view. Evaluate the counterfactual: what would have happened if the predecessor remained independent, or if ordinary automation replaced both?

### Repurpose

Repurpose when the current mandate is weak but evidence supports a different bounded problem. Define new consumers, authority, success conditions, and non-goals before feeding work. Do not rewrite history so the old mandate appears to have succeeded at the new one.

### Pause

Pause when value is uncertain, work is absent, risk is temporarily unacceptable, or a controlled probe will produce better evidence. Pausing is not retirement. Preserve identity, state, restoration steps, and an explicit review date while reducing schedules, credentials, and noise as policy permits.

### Retire

Retire when evidence and an authorized decision show that continued operation is not justified and consumers can be migrated safely. Retirement is complete only after queued and in-flight work is dispositioned, consumers and ownership are transferred, credentials and external capabilities are revoked, retained data and memory are handled, resources are reconciled, and the applicable restore window closes or policy permits final termination.

## Falsify suspected low value with a pause/feed probe

A reversible experiment is stronger than an impression.

Pre-register:

- the capability and exact charter under test;
- the observation window and baseline;
- outcomes expected to disappear during a pause;
- safety-critical work that excludes or aborts the pause;
- queued and in-flight work handling;
- restore command, owner, objective, and verification;
- the defined backlog and named consumer for the feed phase;
- success, failure, and kill criteria; and
- evidence that will update the lifecycle decision.

The probe has two phases.

**Pause phase:** stop or narrow the capability for a bounded window. Record what breaks, what routes elsewhere, what no one notices, and which costs or alerts disappear. Abort on unexpected harm. Exercise restoration and verify service before proceeding.

**Feed phase:** provide a bounded backlog with a named consumer and pre-declared acceptance criteria. Measure consumed outcomes, quality, steering, cost, risk, distinctiveness, and learning. This distinguishes “the model or mandate cannot deliver” from “the capability had no useful work.”

Some capabilities must not be paused because they own safety monitoring, legal deadlines, custody, or irrecoverable state. Record that exclusion as evidence; do not silently treat an unrun probe as success.

## Carry the decision through implementation

A signed lifecycle decision should identify:

- decision type and owner;
- immutable evidence window and limitations;
- affected charter revision and deployed capability identities;
- implementation issue or change record;
- consumer, work, data, memory, credential, and resource obligations;
- rollback, restore, or reconstruction path;
- verification observer and postconditions; and
- scheduled and event-triggered reassessment.

The decision type must survive into execution. A generic “change ready” state loses the obligations that distinguish a specialization from a merge, pause, or retirement. Implementation evidence should prove the selected action, not merely that some configuration changed.

![State machine showing a deployed capability move from a versioned charter through bounded observation and mandate-specific evidence review. Weak evidence returns to observation. Suspected low value enters a reversible probe: unsafe pauses record an exclusion, while allowed pauses support emergency abort, exercise restoration, verify service recovery, and then feed defined work. Sufficient evidence reaches a human-signed choice to invest, specialize, merge or subsume, repurpose, pause, or retire, with the chosen type retained through implementation. Only retirement enters terminal cleanup, which verifies consumer and work migration, queue disposition, credential revocation, retained data and memory handling, ownership transfer, and the applicable restore window.](../diagrams/chapter-07/agent-lifecycle-state-machine.light.svg)

_Figure 7.1 — A lifecycle decision is an evidence-bound, human-owned transition with action-specific obligations. The diagram is a reference design, not a report of decisions about Patrick's agents._

## Reassess on time and on semantic change

Use both scheduled and event-triggered reviews. A 30-day check can verify that a change stabilized. A 60-day review can measure early outcomes. A 90-day review can decide whether the evidence supports continued investment. The exact cadence should follow mandate frequency and consequence rather than becoming ritual.

Trigger an immediate review when:

- the primary charter or consumer changes;
- a capability gains sensitive data or external authority;
- a material incident occurs;
- another capability creates substantial overlap;
- operating burden changes sharply;
- a key input or consumer disappears;
- the model, tool boundary, or memory architecture changes materially; or
- live behavior contradicts the declared charter.

Reassessment returns the capability to observation. It does not permit silent retirement. A terminal transition requires an explicit retirement decision and verified cleanup contract.

## What this chapter deliberately withholds

The complete chapter plan calls for named fleet cases: a consolidation lineage, mandate-thickness hypotheses, demonstrated outcomes, and an inadvertent charter-drift example. Those cases are not included in this revision because their restricted evidence, counterfactual limitations, and applicable disclosure reviews are not yet represented in the public atlas.

No relative ranking is offered. No pause/feed probe result is claimed. No private message volume is treated as value. No restricted high-consequence safety or outcome claim is introduced. These omissions are evidence boundaries, not conclusions about the agents.

The public repository inventory is useful context for why artifact counts require care: repository existence and creation time do not establish usefulness, originality, adoption, maintained quality, or attributed agent contribution. [@evidence:inventory.public-repositories-2026-07-11]

## A portfolio review checklist

1. Is the mandate thick enough to evaluate?
2. Who consumes each claimed outcome?
3. What immutable evidence proves consumption?
4. Are quality measures role-specific and pre-declared?
5. Is necessary human authority separated from avoidable steering?
6. What operating burden and consequence surface accompany the outcome?
7. Which overlap is deliberate, and which creates ambiguity?
8. Did failures become constraints, and did recurrence decline?
9. Would a reversible pause/feed probe falsify the current hypothesis?
10. Does the lifecycle decision preserve lineage, consumers, work, data, memory, credentials, and rollback?
11. Was the selected decision verified at the real enforcement point?
12. What scheduled or semantic event triggers reassessment?

The transferable lesson is to govern agents as a portfolio of accountable software capabilities. Thick mandates make evidence interpretable. Consumed outcomes outrank activity. Risk and operating burden remain visible. Reversible probes replace intuition with falsification. Human-owned lifecycle decisions preserve lineage and recovery. Personification can make the interface usable; it must not make the operating discipline sentimental.

## Evidence used by this chapter

- [Dated public-repository inventory](../evidence/records/public-repository-inventory.yaml) [@evidence:inventory.public-repositories-2026-07-11]

The inventory supports only its bounded repository-count and timestamp claims and explicitly does not measure value or agent contribution. The lifecycle protocol and diagram are proposed reference designs. Named private-fleet cases remain withheld.
