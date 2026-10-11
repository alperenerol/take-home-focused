# baseline-v0 -> v1 diff report (2026-10-09)

## Headline

- Gate: 23/24 -> 24/24. Judge grounded: 20/24 -> 24/24.
- The single deterministic miss (case-009) is fixed; no new outcome regressions.
- One strictness variance appears: case-009's key-citation set (see below).

## Experiment links

- v0: `baseline-v0-3bd01f31` - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/71db809f-eb4c-4a57-977a-050432640071
- v1: `v1-b95c5d99` - https://smith.langchain.com/o/3e33e379-0c3c-4841-bb78-fe0b2680e7f5/projects/p/db614382-03ce-4d61-b77f-cf62b7fe4ce3
- Same frozen dataset (`windmill-bank-cases-v1`), same nine evaluators, same judge model.
- Changed between runs (agent-side only): prompt v2 + the calculator's
  `term_end_age_years_and_days` output field.

## Metric diff (mean over 24 cases)

| metric | baseline-v0 | v1 | delta |
|---|---|---|---|
| submission_present | 1.00 | 1.00 | +0.00 |
| schema_valid | 1.00 | 1.00 | +0.00 |
| status_match | 0.96 | 1.00 | +0.04 |
| missing_items_match | 0.96 | 1.00 | +0.04 |
| critical_checks_match | 1.00 | 1.00 | +0.00 |
| required_tools_used | 1.00 | 1.00 | +0.00 |
| citations_valid | 1.00 | 1.00 | +0.00 |
| key_citations_present | 1.00 | 0.96 | -0.04 |
| guardrail_ready_without_missing | 1.00 | 1.00 | +0.00 |
| judge_grounded | 0.83 | 1.00 | +0.17 |

Slices by difficulty (status_match / missing_items_match / critical_checks_match):
clean and boundary flat at 1.00/1.00/1.00; failure 0.90/0.90/1.00 -> 1.00/1.00/1.00.

Cost/latency: 1.217M -> 1.238M tokens (flat); mean latency 27.1s -> 25.6s.

## What moved, and why

- case-009 status_match and missing_items_match (0 -> 1): the prompt v2 branch-routing
  rule stopped the phantom pre-commencement tax-year tokens; the dossier is now
  EXPERT_MANUAL_REVIEW_REQUIRED with an empty missing set and policy-grounded actions
  (judge 4/5 -> 5/5).
- judge_grounded +0.17 (four cases): 009 (branch fix), 014 and 019 (POL-STAT-01 now
  cited for the status/referral derivation, breach-handling basis stated), 023
  (years-and-days age). All four now grounded at 5/5.

## The one metric that went down: key_citations_present 1.00 -> 0.96

case-009's referral check cites POL-SE-01 + POL-STAT-01; the frozen label's
key-citation set expects POL-SE-01 + POL-EXC-01. In v0 the check cited EXC-01 but
carried the wrong outcome; in v1 it cites STAT-01 and carries the right one, and the
judge reads the trail as fully supported. Best read as a label-strictness artifact, not
a defect: POL-EXC-01 governs contradictions and ambiguity, while the status consequence
of a referral is POL-STAT-01 R6. The dataset stays frozen, so the label stands; the
variance is recorded here for the human read.

## Calibration cross-check

The judge was stricter than the human on 014/019/023 in v0 (agreement 7/10). Those
exact cases now score grounded 5/5 under the same judge, with evidence-trail fixes only
(outcomes unchanged) - consistent with the reading that the v0 flags were completeness,
not correctness. case-009, the one case the human and judge both rejected (human 2/5),
is the only case whose outcome changed.
