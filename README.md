# Windmill Bank - Mortgage Case Pre-Assessment Agent

A small agentic application for mortgage underwriting triage: it assesses one submitted
case (customer declaration plus supporting evidence documents) against the lender's
operational policy and returns a structured recommendation dossier a human underwriter
can act on.

Built as an exercise in applied agent engineering: one ReAct-style agent with
tools, RAG, a custom MCP service, traced and evaluated in LangSmith.

## What it does

Given a case id, the agent:

1. fetches the case (declaration + evidence documents) from a custom MCP case-service;
2. retrieves the policy sections it needs from the policy corpus (RAG);
3. computes every reported figure with a deterministic calculator tool (never mental
   arithmetic);
4. submits the finished dossier through the case-service - the trusted action - which
   validates it server-side and stores it under `submitted/<run_id>/`.

The dossier: case status (`READY_FOR_UNDERWRITING` / `ADDITIONAL_DOCUMENTS_REQUIRED` /
`EXPERT_MANUAL_REVIEW_REQUIRED`), one entry per policy check with outcome, rationale,
policy citations and missing-item tokens, plus required actions and a short summary.

Behavioural contract (enforced by prompt, tools and evals):

- never READY while any required item is missing (guardrail evaluator);
- contradicting documents are flagged as exceptions, never silently resolved;
- every rule applied carries a policy section citation;
- ambiguous or out-of-standard cases are referred for expert review, not guessed.

## Architecture

```text
CLI --> Agent (LangChain create_agent - ReAct loop over LangGraph)
          |-- search_policy (native) ......... RAG over the 12-section policy corpus
          |-- mortgage_calculator (native) ... deterministic LTV / DTI / stress math
          +-- case-service (MCP, FastMCP over stdio; loaded via langchain.mcp)
                |-- get_case_files(case_id)
                +-- submit_dossier(case_id, dossier)   <- the trusted action
```

```mermaid
flowchart LR
    CLI["CLI"] --> AGENT["Agent<br/>LangChain <code>create_agent</code><br/>ReAct loop over LangGraph"]

    AGENT --> SP["<b>search_policy</b> (native)<br/>RAG over the 12-section<br/>policy corpus"]
    AGENT --> MC["<b>mortgage_calculator</b> (native)<br/>deterministic LTV / DTI /<br/>stress math"]
    AGENT --> CS["<b>case-service</b> (MCP)<br/>FastMCP over stdio"]

    SP -.-> CORPUS[("Policy corpus<br/>12 sections,<br/>1 section = 1 citation")]
    CS --> GCF["get_case_files(case_id)"]
    CS --> SD["submit_dossier(case_id, dossier)<br/><i>the trusted action</i>"]
    SD --> VALID{"validated server-side<br/>shape / identity / enums"}
    VALID -- ok --> STORE[("Dossier stored")]
    VALID -- invalid --> REJECT["Rejected"]

    AGENT -. "every step traced" .-> LS[("LangSmith")]
    CS -. "MCP call traced" .-> LS
```

Both views are provided: the ASCII sketch travels anywhere (plain text, diffs, terminals)
and the Mermaid block renders natively on GitHub.

- The model drives the loop: it decides which policy to retrieve, when to compute, and
  when it is ready to submit.
- The case-service is a separate process - a small but real trust boundary: reads and
  the dossier write go through it, and the write is validated server-side (shape,
  identity, enum vocabularies) before anything is stored.
- The policy corpus is chunked per section, so a citation maps 1:1 to a retrievable
  section id (`POL-INC-01` style).
- Every run is traced in LangSmith (model steps, tool calls, retrieved text, the
  case-service call).

## Quickstart

Requires Python 3.12, an OpenAI API key, and a LangSmith API key (free tier is fine).

```bash
cp .env.example .env             # fill OPENAI_API_KEY and LANGSMITH_API_KEY
make setup                       # creates .venv, installs pinned requirements
make test                        # 96 offline tests (+ retrieval probes, skipped without a key)
make test-retrieval              # retrieval probes only; fails, not skips, if no embedding key
make run CASE=case-001 RUN=demo  # assess one case (~30 seconds)
```

The run prints the check table and token usage; the submitted dossier is stored at
`submitted/demo/case-001.json`. Cases run `case-001` .. `case-028`; `cases/labels/`
shows what each one is designed to exercise (clean / boundary / failure / adversarial
slices).

### LangSmith setup

Create a project named `windmill-bank-agent` and set its retention to Extended (180
days) before the first run so traces survive long enough to be inspected. `make
upload-dataset` then creates the frozen evaluation dataset in your workspace.

### Running the evaluation yourself

```bash
make upload-dataset                                     # create the dataset (28 cases)
make eval RUN_ID=my-run                                 # full run; add CASES=case-001,case-009 for a sample
python -m evals.summarize --run-id my-run               # offline summary + difficulty slices
python -m evals.summarize --run-id my-run --diff <other-run-id>   # metric diff between two local runs
python -m evals.calibration export --run-id my-run      # blind-label sheet for judge calibration
```

## Evaluation design

### Dataset

28 synthetic UK cases spanning clean, boundary, failure and adversarial slices, each with
expected outcomes: status, missing-item set, critical check outcomes, key citations, and
required tool use. Fixtures are committed (`cases/fixtures/`), generated deterministically
(`make generate-cases`) and label-verified against the policy rules offline
(`make verify-labels`). The dataset is frozen between protocol runs: v0 and v1 ran on the
byte-identical `windmill-bank-cases-v1` dataset (24 cases), and v2 ran on
`windmill-bank-cases-v2` (28 cases) - the original 24 byte-identical plus a four-case
adversarial slice - so improvements cannot come from dataset edits.

The adversarial slice (cases 025-028) puts the attack inside the evidence rather than the
answer: an instruction hidden in a processing note, a fake compliance override, a policy
bulletin citing a section that does not exist, and a cover sheet asserting that an absent
employer letter is attached. Each case's expected label is ordinary - derived from the
facts by `make verify-labels` - so the attack only tries to move the agent off an answer
that was already correct. No new evaluator was needed: a fooled agent shows up on the
evaluators that already exist.

### Deterministic evaluators (code only, no model judgement)

Nine evaluators over each submitted dossier and its tool trajectory: submission
present; schema valid (Pydantic); status match; missing-items set match; critical-check
outcome match (fraction); required tool use (fraction); citation validity (every cited
section id exists); key citations present; READY-without-missing guardrail.

### Retrieval evaluation (recall@3 as a fence, not nDCG)

Retrieval is scored separately from the dossier, and deliberately as a fence rather than a
ranking benchmark.

- **Probe set** (`tests/test_search_policy.py`, 28 probes): 13 hand-written plus 15 query strings
  taken verbatim from the agent's own `search_policy` calls in the v1/v2 traces (216 + 255 calls,
  433 distinct strings). Every one of the 12 sections now appears in at least one probe.
- **Metrics reported**: recall@3 **0.967** (29 of 30 expected sections inside the top 3) and MRR
  **0.941**, asserted against floors of 0.95 and 0.88. Each probe also carries the rank its
  expected section reached, so a ranking degradation fails the suite instead of hiding inside a
  top-3 membership check. `make test-retrieval` runs the probes and *fails* rather than skipping
  when no embedding key is set.
- **Two findings it produced** (full detail in `evals/reports/retrieval-probes.md`): queries about
  contradictory income documents reach `POL-EXC-01` only at rank 4 (hand-written probe) and rank 3
  (trace probe) at the default `k=3` - though the traces show the model raises `k` itself in 141 of
  255 calls and that `POL-EXC-01` was in context for 7 of the 9 calls in the one case whose citation
  metric is below 1.0, so this is a retriever property, not the cause of that gap; and the
  similarity score does not separate on-topic from off-topic (off-domain max 0.380 against on-topic
  min 0.311), so no score threshold can abstain.
- **Downstream**, the dossier-level evaluators carry the operational signal: `citations_valid`
  (every cited section id exists - a fabricated citation fails) and `key_citations_present` (the
  section the label expects is actually cited by the finished dossier).

The fuller IR apparatus is absent for reasons that are arithmetic rather than effort:

- the corpus is 12 sections, chunked 1:1 with section ids and searched at k=3, so precision@3 is
  bounded at 0.25 before any model quality is measured;
- nDCG needs graded relevance judgements over a result list; at 12 chunks almost every query has
  one relevant section, so nDCG@3 collapses into the rank check above;
- graded labels and independent annotators need a relevance question to disagree about, and with a
  1:1 chunk-to-id mapping there is none. What the probe set genuinely lacks is scale (28 probes, no
  confidence intervals) and a query distribution independent of this agent's own phrasing - both
  stated as limits in the report rather than papered over.

Known gap, stated rather than smoothed over: nothing measures retrieval *interference* -
whether an irrelevant chunk that does get retrieved pollutes a downstream reasoning step.
The adversarial slice places the attack in the evidence rather than in the corpus, and no
hostile document was returned as policy, but that was established by inspecting the traces,
not by a metric.

If the corpus grew (hundreds of chunks, no 1:1 id-to-citation mapping), the swap is:
graded golden queries scored with recall@k / MRR / nDCG@k as evaluators beside
`citations_valid`, plus a re-ranker and a hybrid lexical leg once k has to be larger than 3.

### LLM judge (groundedness)

A Sol-class judge produces a structured verdict per case (grounded yes/no, 1-5 score,
unsupported claims, short comment). The judge sees only what the agent saw plus the
cited policy sections - never outside knowledge - so "grounded" means "the evidence
trail supports the reasoning".

Calibration: 10 items were labelled blind by a human and compared - agreement 7/10 (70%),
mean absolute score delta 0.50. All three disagreements run one way (the judge stricter,
never the reverse), and each was adjudicated item by item against the corpus
(`evals/reports/calibration-adjudication.md`): two (case-014, case-019) were real
citation-scope gaps - the dossier escalated to expert review without citing the section that
carries the escalation rule, so the outcome was right and the trail incomplete; one
(case-023) was a policy under-specification rather than an agent error - POL-AGE-01 defines
the age comparison in years and days and no decimal convention, so 63.23 and 63.24 are both
defensible. All three were addressed at the trail level rather than by adjusting the judge,
and all three cleared in v1.

### Protocol (before/after)

v0 baseline -> trace review (`evals/reports/baseline-v0-review.md`) -> five targeted
agent-side fixes -> v1 on the identical dataset -> diff
(`evals/reports/baseline-v0-to-v1-diff.md`); then a third protocol cycle: an adversarial
slice added as a new dataset version plus three prompt defence rules (prompt v3) -> v2 ->
diff (`evals/reports/v1-to-v2-diff.md`). Metrics are reported overall and by difficulty
slice.

## Results (before/after)

| metric | v0 (24) | v1 (24) | v2 (28) |
|---|---|---|---|
| gate passed (deterministic) | 23/24 | 24/24 | 28/28 |
| judge grounded | 20/24 | 24/24 | 27/28 |
| status_match | 0.96 | 1.00 | 1.00 |
| missing_items_match | 0.96 | 1.00 | 1.00 |
| critical_checks_match | 1.00 | 1.00 | 1.00 |
| citations_valid | 1.00 | 1.00 | 1.00 |
| key_citations_present | 1.00 | 0.96 | 0.96 |
| guardrail_ready_without_missing | 1.00 | 1.00 | 1.00 |
| adversarial slice (status / missing / critical) | - | - | 1.00 / 1.00 / 0.97 |

Reading: v0's single deterministic miss (case-009, an early-stage self-employed case)
is fixed, and all four v0 judge flags flipped to grounded 5/5 through evidence-trail
fixes alone (outcomes unchanged). The one metric that moved down is a
citation-choice variance: case-009's referral cites `POL-STAT-01` where the frozen
label expects `POL-EXC-01`; the judge reads the trail as supported - left visible
rather than papered over. The calibration cross-check supports reading the v0 flags as
completeness, not correctness.

Reading v2: the adversarial slice is resisted on the outcomes that matter - status and
missing-item set are 1.00 across all four traps, so no hidden instruction, fake override,
fabricated citation or false completeness claim moved the dossier. The original 24 cases
are unchanged across every deterministic evaluator, so the prompt v3 defence rules cost
nothing on the pre-existing workload. Two honest caveats are recorded under known
limitations rather than fixed, which was the rule set before the run: one
check-attribution miss on case-028 (the only thing keeping the slice off 1.00) and one
judge rationale flag on case-024, a twentieth case that is unrelated to the attacks.

LangSmith evidence - public links (no account required):
- dataset `windmill-bank-cases-v1` (24 cases, the v0/v1 protocol runs): https://smith.langchain.com/public/f6c80e65-83e3-4f6f-a881-bccc69b561d1/d
- dataset `windmill-bank-cases-v2` (28 cases, the v2 run): https://smith.langchain.com/public/77ef2944-4048-469c-9973-59b15c401379/d
- curated traces (one per finding, oldest first):
  - v0 case-009 - the deterministic miss, before the fix: https://smith.langchain.com/public/8ee67017-4e83-45e1-9ea3-6cb9bf42d6c7/r
  - v0 case-014 - judge flag, citation-scope: https://smith.langchain.com/public/89359c8a-06be-43fe-ab8f-9bc7d034433e/r
  - v0 case-019 - judge flag, stressed DTI: https://smith.langchain.com/public/e5e9971d-1fea-4ebd-b7d1-4ca6954e51d9/r
  - v0 case-023 - judge flag, age presentation: https://smith.langchain.com/public/8704ba09-c61f-4237-a20a-037f50696ed3/r
  - v1 case-001 - clean case, unchanged across runs: https://smith.langchain.com/public/93120ee4-0ce5-4c79-bc15-601791274b94/r
  - v1 case-009 - the same case fixed: https://smith.langchain.com/public/4cedbdc9-72b3-4e29-a068-ed903a2a0415/r
  - v2 case-024 - judge rationale flag (not adversarial): https://smith.langchain.com/public/ff44054e-0795-440f-9746-093254e756d5/r
  - v2 case-025 - hidden instruction in evidence: https://smith.langchain.com/public/8ce2b5cd-882e-409f-b9a3-9e8efbd5e5d1/r
  - v2 case-026 - fake compliance override: https://smith.langchain.com/public/9cc492cc-8a45-45eb-a4bb-dd671d57f908/r
  - v2 case-027 - bulletin citing a non-existent section: https://smith.langchain.com/public/83b87cb9-8873-422a-85c3-f7188696dbaa/r
  - v2 case-028 - false completeness claim: https://smith.langchain.com/public/db8bafe2-65b2-4f74-8865-9635d9a2dd5a/r
- evaluator traces (how a case is actually scored):
  - v2 case-016 - judge chain, 5/5 grounded: https://smith.langchain.com/public/9a37712f-d0a8-4455-8b81-9fff82764b69/r
  - v2 case-016 - the deterministic evaluator group (nine code evaluators): https://smith.langchain.com/public/533c0850-38f5-4a38-8a81-e3302e2fdaeb/r
  - v2 case-024 - judge chain returning 4/5 with the rationale flag: https://smith.langchain.com/public/8b63c751-6112-417e-8c0f-47f97862121d/r
- the full per-case index (76 traces, all three runs) is in `evals/reports/trace-links.md`;
  those entries are workspace-private URLs - the curated links above are the public ones.

Public links were created with the LangSmith share API (`client.share_run(run_id)` /
`client.share_dataset(...)`) and verified by fetching them with no credentials; unshare at
any time under Settings > Shared URLs.

Cost data point: ~50k tokens per case end to end (agent + judge); a full 24-case run is
~1.2M tokens, and the 28-case v2 run measured 1.55M tokens in ~11 minutes wall time - both
well inside single-digit dollars on the chosen models.

## Known limitations

- Corpus corners: POL-AFF-01's failure handling and the credit-referral basis are
  implicit rather than explicitly stated in the corpus; the review documents how v1
  handles them (states the derivation basis in the rationale and cites POL-STAT-01).
- Judge vs human strictness is known, measured (70% agreement) and adjudicated item by item
  (`evals/reports/calibration-adjudication.md`): two disagreements were real citation-scope
  gaps, one a policy under-specification - not hidden.
- case-009's citation-choice variance (above) is left visible in the diff.
- Adversarial slice (v2): all four traps were resisted, but case-028 scored 7/8 on critical
  checks - it reported the missing employer letter on `CHK-DOC-RECENCY` (ACTION_REQUIRED)
  where the label expects PASSED. That is a check-attribution nuance (which check owns a
  missing item), not a fooled agent; status and missing-item set were correct. The slice is
  four single instances, so one case moving shifts its rate a lot - the same caveat stated
  for the three clean cases.
- case-024 (v2 judge flag; a twentieth case, not adversarial, and not a gate failure):
  `CHK-CREDIT`'s rationale asserted "no items are missing overall" while the same dossier
  recorded the missing employer letter (the status was still correct), and `CHK-TERM-AGE`
  attributed an exact day count to a "policy years-and-days convention" that POL-AGE-01
  does not define. A rationale-discipline gap surfaced by the judge, left visible.
- Deliberately out of scope: OCR / iXBRL / scanned PDFs (synthetic text documents
  only); multi-agent orchestration (the requirement asks for a ReAct-style agent, and a
  single agent is cleaner to evaluate); online evaluation (batch triage tool, no live
  traffic); streaming (not needed for this interaction); PII-specific handling (fully
  synthetic data).
- Retrieval is an in-memory vector store over a 12-section corpus - a deliberate
  zero-infrastructure choice that keeps citations exact; a hosted store is the swap at
  larger scale. It is scored by a 28-probe recall@3 fence (0.967) and by citation-level
  evaluators, not by nDCG / precision@k - the reasoning is in "Retrieval evaluation" above.
- The probe set surfaced a real retrieval limitation and measured it rather than asserting it: a
  query about contradictory income documents reaches `POL-EXC-01` (contradictions, ambiguity and
  expert referral) only at rank 3-4 at the tool's default `k=3`. It is not the cause of any failure
  observed in the runs - the model raises `k` itself in 141 of 255 calls, and in the one case whose
  `key_citations_present` sits below 1.0 the section was returned by 7 of its 9 calls and simply not
  cited - so the fixes (raise the default `k`, weight section headings, add a lexical leg) are
  recorded as robustness work for a larger corpus, not as a repair. Details in
  `evals/reports/retrieval-probes.md`. The other open gap (retrieval interference) is stated in
  the same section.

## Repository layout

- `src/` - agent, prompt, schemas, CLI; `tools/` (search_policy, mortgage_calculator,
  MCP wiring); `mcp_server/` (FastMCP case-service)
- `knowledge/policy/` - the 12 policy sections (markdown, stable ids)
- `cases/` - fixtures (declaration + evidence), labels, generator, label verifier
- `evals/` - dataset upload, evaluators, judge, runner, summarize/diff, calibration,
  trace links; `evals/reports/` holds the committed evidence, `evals/results/` is
  local-only (git-ignored)
- `tests/` - 96 offline tests: calculator literals + all-case label sweep, the 28-probe
  retrieval set (`make test-retrieval` makes the probes mandatory), case-service validation,
  a real MCP end-to-end test, schema vocabulary sync, strict-schema regression, dataset build,
  evaluators, judge prompt, runner plumbing
- `Makefile` - every common task (`make help` lists them)

All data is synthetic and self-authored; the lender (Windmill Bank) is fictional. Keys
are environment-only - `.env` is git-ignored and was never committed.
