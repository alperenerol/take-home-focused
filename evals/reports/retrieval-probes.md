# Retrieval probes - provenance, scope and findings

The retrieval step has its own probe set in `tests/test_search_policy.py`, separate from the
dossier-level evaluators. This file records where the probes came from, what they measure, and
what the measurements exposed. Reproduce with `make test-retrieval` (requires an embedding key;
fails rather than skips when the key is missing).

## Provenance

| group | n | source |
|---|---|---|
| `CURATED_PROBES` | 13 | hand-written for this suite; kept from the first version |
| `TRACE_PROBES` | 15 | verbatim `search_policy` query strings the agent produced in the v1 and v2 runs |

The trace group was extracted from the LangSmith tool runs of the two experiments
(`search_policy` calls: 216 in v1, 255 in v2; 433 distinct strings across the 471 calls). No
query string was edited - the wording, including its redundancy, is the agent's own.

Why that matters: the first version of this suite was ten hand-written probes, all of which put
their expected section at rank 1. A probe set that everything passes at rank 1 can only catch an
index that has broken, not a ranking that has degraded. Every probe now carries the rank its
expected section reached when the ceiling was recorded, so any drop fails the test.

## What the probes measure

- **Coverage** - every one of the 12 sections appears in at least one probe (was 9 of 12; the
  unprobed ones included `POL-EXC-01`, the section at the centre of the v1 citation dispute).
- **Rank ceilings** - per probe, the rank its expected section(s) reached; a regression fails.
- **Aggregate metrics** - recall@3 **0.967** (29 of 30 expected sections retrieved in the top 3)
  and MRR **0.941** over 28 probes, asserted against floors of 0.95 / 0.88.
- **Multi-topic labels** - two probes expect two sections each, taken from real queries that name
  two rules at once (e.g. stressed affordability plus the LTV band that triggers it).
- **Score overlap** - four off-domain queries record that the similarity score does not separate
  on-topic from off-topic retrieval.

## Findings

**1. Contradiction-shaped queries near-miss `POL-EXC-01`.** The curated probe "employer letter
says one salary, payslips say another - what then" ranks `POL-EXC-01` fourth (behind `POL-INC-01`,
`POL-SE-01`, `POL-INC-02`), and the trace probe for the same situation reaches it at rank 3.
At the tool's default k=3, a query phrased in income vocabulary therefore does not reliably
return the contradictions-and-referral section - the rule a case like that actually needs. This is
the same section the v1 citation dispute is about (`key_citations_present` fell to 0.96 on
case-009, which cites `POL-STAT-01` where the label expects `POL-EXC-01`). Candidate fixes, in
order of cost: raise k for contradiction-shaped queries, add a heading/section-title component to
the embedding, or move to hybrid BM25 + vector retrieval. Recorded, not fixed - the same
document-don't-fix discipline the evaluation protocol uses.

**2. The similarity score cannot abstain.** Measured top-1 similarities: off-domain max 0.380
("complaints handling procedure and how to escalate to the financial ombudsman" - real vocabulary
overlap with a bank corpus), on-topic min 0.311 ("does an exception get looked at by a human" -
colloquial phrasing for a rule the corpus states formally). One of 28 on-topic probes scores below
the worst off-domain query, so no threshold on this score separates the two. The tool returns k
sections unconditionally; the guard against acting on an irrelevant chunk lives in the prompt rule
("cite only section ids that retrieval returned") and in the dossier-level `citations_valid`
evaluator, not in a score cut-off. This is also why finding 3 is stated as an open gap.

**3. Interference is still unmeasured.** Nothing yet measures whether an irrelevant retrieved
chunk pollutes a downstream reasoning step. The adversarial slice places its attack in the
evidence rather than in the corpus, and no hostile document came back as policy, but that was
established by reading traces, not by a metric.

## Known limits of this probe set

- 28 probes is a fence, not a benchmark: no confidence intervals, and a single flip moves
  recall@3 by 3 points.
- Relevance is binary (section present within a rank ceiling) and single-author for the curated
  group; there is no graded judgement and no independent annotator, because with 12 sections
  chunked 1:1 with section ids there is no relevance question to disagree about.
- Real queries were kept verbatim, including the ones that name a section id outright
  (`... POL-STAT-01`) or pack two rules into one call. That is the agent's observed behaviour and
  therefore the right thing to probe, but it means the set encodes the current agent's phrasing
  habits rather than an independent distribution of underwriter questions.
