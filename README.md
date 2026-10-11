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
make test                        # 74 offline tests
make run CASE=case-001 RUN=demo  # assess one case (~30 seconds)
```

The run prints the check table and token usage; the submitted dossier is stored at
`submitted/demo/case-001.json`. Cases run `case-001` .. `case-024`; `cases/labels/`
shows what each one is designed to exercise (clean / boundary / failure slices).

### LangSmith setup

Create a project named `windmill-bank-agent` and set its retention to Extended (180
days) before the first run so traces survive long enough to be inspected. `make
upload-dataset` then creates the frozen evaluation dataset in your workspace.

### Running the evaluation yourself

```bash
make upload-dataset                                     # create the dataset (24 cases)
make eval RUN_ID=my-run                                 # full run; add CASES=case-001,case-009 for a sample
python -m evals.summarize --run-id my-run               # offline summary + difficulty slices
python -m evals.summarize --run-id my-run --diff <other-run-id>   # metric diff between two local runs
python -m evals.calibration export --run-id my-run      # blind-label sheet for judge calibration
```

## Evaluation design

### Dataset

24 synthetic UK cases spanning clean, boundary and failure slices, each with expected
outcomes: status, missing-item set, critical check outcomes, key citations, and required
tool use. Fixtures are committed (`cases/fixtures/`), generated deterministically
(`make generate-cases`) and label-verified against the policy rules offline
(`make verify-labels`). The dataset is frozen between protocol runs - v0 and v1 ran on
the byte-identical `windmill-bank-cases-v1` dataset, so improvements cannot come from
dataset edits.

### Deterministic evaluators (code only, no model judgement)

Nine evaluators over each submitted dossier and its tool trajectory: submission
present; schema valid (Pydantic); status match; missing-items set match; critical-check
outcome match (fraction); required tool use (fraction); citation validity (every cited
section id exists); key citations present; READY-without-missing guardrail.

### LLM judge (groundedness)

A Sol-class judge produces a structured verdict per case (grounded yes/no, 1-5 score,
unsupported claims, short comment). The judge sees only what the agent saw plus the
cited policy sections - never outside knowledge - so "grounded" means "the evidence
trail supports the reasoning".

Calibration: 10 items were labelled blind by a human and compared - agreement 7/10
(70%), mean score delta 0.50. The three disagreements were citation-scope/presentation
cases where the judge applies a stricter evidence-trail standard than the human; the
result and interpretation are committed in `evals/reports/`.

### Protocol (before/after)

v0 baseline -> trace review (`evals/reports/baseline-v0-review.md`) -> five targeted
agent-side fixes -> v1 on the identical dataset -> diff
(`evals/reports/baseline-v0-to-v1-diff.md`). Metrics are reported overall and by
difficulty slice.

## Results (before/after)

| metric | v0 | v1 |
|---|---|---|
| gate passed (deterministic, 24 cases) | 23/24 | 24/24 |
| judge grounded | 20/24 | 24/24 |
| status_match | 0.96 | 1.00 |
| missing_items_match | 0.96 | 1.00 |
| critical_checks_match | 1.00 | 1.00 |
| citations_valid | 1.00 | 1.00 |
| key_citations_present | 1.00 | 0.96 |
| guardrail_ready_without_missing | 1.00 | 1.00 |

Reading: v0's single deterministic miss (case-009, an early-stage self-employed case)
is fixed, and all four v0 judge flags flipped to grounded 5/5 through evidence-trail
fixes alone (outcomes unchanged). The one metric that moved down is a
citation-choice variance: case-009's referral cites `POL-STAT-01` where the frozen
label expects `POL-EXC-01`; the judge reads the trail as supported - left visible
rather than papered over. The calibration cross-check supports reading the v0 flags as
completeness, not correctness.

LangSmith experiments (full traces, per-case):
- v0 baseline: https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071
- v1: https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3
- per-case trace links (exported backup): `evals/reports/trace-links.md`

Cost data point: ~50k tokens per case end to end (agent + judge); a full 24-case run is
~1.2M tokens, well inside single-digit dollars on the chosen models.

## Known limitations

- Corpus corners: POL-AFF-01's failure handling and the credit-referral basis are
  implicit rather than explicitly stated in the corpus; the review documents how v1
  handles them (states the derivation basis in the rationale and cites POL-STAT-01).
- Judge vs human strictness on citation completeness is known, measured (70% agreement)
  and documented - not hidden.
- case-009's citation-choice variance (above) is left visible in the diff.
- Deliberately out of scope: OCR / iXBRL / scanned PDFs (synthetic text documents
  only); multi-agent orchestration (the requirement asks for a ReAct-style agent, and a
  single agent is cleaner to evaluate); online evaluation (batch triage tool, no live
  traffic); streaming (not needed for this interaction); PII-specific handling (fully
  synthetic data).
- Retrieval is an in-memory vector store over a 12-section corpus - a deliberate
  zero-infrastructure choice that keeps citations exact; a hosted store is the swap at
  larger scale.

## Repository layout

- `src/` - agent, prompt, schemas, CLI; `tools/` (search_policy, mortgage_calculator,
  MCP wiring); `mcp_server/` (FastMCP case-service)
- `knowledge/policy/` - the 12 policy sections (markdown, stable ids)
- `cases/` - fixtures (declaration + evidence), labels, generator, label verifier
- `evals/` - dataset upload, evaluators, judge, runner, summarize/diff, calibration,
  trace links; `evals/reports/` holds the committed evidence, `evals/results/` is
  local-only (git-ignored)
- `tests/` - 74 offline tests: calculator literals + all-case label sweep, retrieval
  quality, case-service validation, a real MCP end-to-end test, schema vocabulary sync,
  strict-schema regression, dataset build, evaluators, judge prompt, runner plumbing
- `Makefile` - every common task (`make help` lists them)

All data is synthetic and self-authored; the lender (Windmill Bank) is fictional. Keys
are environment-only - `.env` is git-ignored and was never committed.
