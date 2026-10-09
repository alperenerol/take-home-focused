# Baseline v0 review - pre-assessment agent (2026-10-09)

## Run facts

- Dataset: `windmill-bank-cases-v1` (24 cases, frozen between protocol runs)
- Experiment: `baseline-v0-3bd01f31` - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071
- Models: agent `gpt-6-luna`, judge `gpt-6.1-sol` (no temperature - model family rejects it)
- Wall time ~20 min at concurrency 2; mean case latency 27.1s (min 19.3, max 45.4)
- Tokens: 1.22M total, mean 50.7k/case (min 45.0k, max 75.1k)
- Artifacts: `evals/results/baseline-v0/` - per-case records, judge caches, `links.json`
  (per-case trace URLs + stats), `summary.json`/`summary.md`, calibration sheet

## Scoreboard

Deterministic evaluators (nine, code-only): gate passed **23/24**. Every evaluator is
1.0 on 23 cases; the run's only two non-1.0 results are both case-009
(status_match 0, missing_items_match 0). submission_present, schema_valid,
required_tools_used, citations_valid, key_citations_present and the READY guardrail
are 24/24.

Judge (groundedness): grounded **20/24 (83%)**; all four flags scored 4/5.

## Findings

### F1 - case-009 (failure) - early-stage self-employed: phantom missing items, wrong status [agent defect]

The one deterministic failure, and a judge flag. POL-SE-01 R3 has two branches:
established business with fewer evidenced years -> ACTION_REQUIRED with missing tokens;
business commenced fewer than three tax years before assessment -> EXCEPTION_FLAGGED
plus expert referral. The agent used the first branch's missing-token behaviour on an
early-stage case: it reported `sa302_year_3`/`tax_year_overview_3` (a tax year that
predates the business; unobtainable) under CHK-DOC-COMPLETE, which flipped the dossier
status to ADDITIONAL_DOCUMENTS_REQUIRED (missing items take precedence) and produced an
unauthorised fallback action ("or have the underwriter confirm the appropriate evidence
treatment"). Label (EXPERT_MANUAL_REVIEW_REQUIRED, empty missing) is correct; the judge
describes the same two defects. This case also has the run's worst latency (45.4s) and
second-highest tokens (70.4k) - it searched 12 times, more than any other case.

### F2 - case-014 (failure) - credit-marker referral: outcome right, basis not cited [citation discipline]

CHK-CREDIT EXCEPTION_FLAGGED is correct (POL-CREDIT-01 R3: default registered within
12 months). The check cites only POL-CREDIT-01, whose text mandates no referral; the
referral and status consequences live in POL-STAT-01 R6/R7 (status derivation and
required-action content) with POL-EXC-01 R5 linking referrals to the status. The judge,
which by design sees only the cited sections, correctly reports the referral as
unsupported by the supplied policy. No outcome is wrong - the evidence trail is
incomplete.

### F3 - case-019 (boundary) - stressed-DTI breach: corpus gap in failure handling [corpus limitation + grounding]

Stressed DTI 45.66% exceeds the 45.00 limit (POL-AFF-01 R5), so the check fails and the
dossier flags EXCEPTION + referral (matching the label). POL-LTV-01 R4/R5, POL-AGE-01 R2,
POL-INC-02 R2 and POL-SE-01 R3 all state "breach -> EXCEPTION_FLAGGED + expert referral"
explicitly; POL-AFF-01 R4/R5 state only the pass thresholds and boundary behaviour, with
no failure-handling sentence. The judge therefore reads the flag as unsupported. The
agent and the label both apply the corpus-wide pattern; the corpus itself leaves this
corner implicit. Not fixable by the agent alone - v1 should state the derivation basis
explicitly and cite POL-STAT-01; the residual ambiguity is documented as a corpus
limitation.

### F4 - case-023 (failure) - decimal term-end age [presentation]

All outcomes correct; the judge's single note is the term-end age written as decimal
years (61.47) while POL-AGE-01 R1 frames the rule in years and days ("at most 75 years
and 0 days"). Cosmetic; cheap to align.

## Process observations

- Trajectory shape is highly uniform: get_case_files -> 7-12 search_policy calls
  (mean 9.1) -> mortgage_calculator -> submit_dossier. Zero tool errors across all
  traces; llm calls 5-11 per case.
- The agent searches more when unsure (case-009: 12 searches; both cost outliers,
  case-009 and case-017 at 70.4k/75.1k tokens, are failure/boundary cases).
- No schema violations, no guardrail violations, no invalid citation ids anywhere.

## v1 fix list (prompt-level; dataset, tools and corpus unchanged)

1. POL-SE-01 R3 branching: route early-stage cases to the referral branch; never report
   unobtainable year tokens as missing; keep them out of CHK-DOC-COMPLETE (F1).
2. Required actions must follow from cited policy text only; no invented fallback
   treatments (F1).
3. Citation discipline: cite POL-STAT-01 wherever an outcome drives the dossier status
   or a referral, and cite the section that establishes the handling (F2, F3).
4. Limit failures in sections without an explicit handling sentence: state the basis in
   the rationale (rule breach -> EXCEPTION + referral, per POL-STAT-01 R6 and the pattern
   stated in POL-LTV-01 R4/R5 and POL-AGE-01 R2) (F3).
5. Term-end age stated in years and days, matching POL-AGE-01 R1 (F4).

## Open items

- Human calibration: `evals/results/baseline-v0/calibration.md` (10 items; the four
  flagged cases lead). Label the "Your call" lines, then:
  `python -m evals.calibration compare --run-id baseline-v0`.
- Corpus limitation to carry into the final write-up: POL-AFF-01 failure handling (F3)
  and the credit-referral basis (F2) are implicit rather than stated.
