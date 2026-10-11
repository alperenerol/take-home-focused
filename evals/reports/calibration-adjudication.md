# Calibration disagreements - item-by-item adjudication

The v0 blind calibration (`baseline-v0-calibration.json`, `baseline-v0-review.md`) recorded
7/10 agreement between the judge and a human label, mean absolute score delta 0.50. All
three disagreements run one way: the judge said not grounded (4/5), the human said grounded
(5/5). The v0 review described them collectively as "citation-scope/presentation cases where
the judge applies a stricter evidence-trail standard than the human". This file replaces that
collective gloss with a per-item verdict, because the three items turn out not to be the same
kind of thing.

Method: for each item, the judge's stated `unsupported_claims` was checked against the
dossier's own rationale, the sections the dossier cited, and the policy corpus. The judge
sees only the evidence the agent saw plus the cited sections, so a claim that the corpus
supports but the dossier did not cite reads to the judge as unsupported - that distinction is
the whole finding here.

## case-014 - verdict: judge right (citation-scope gap)

- v0 rationale: "required exception flag and expert review"; cited `POL-CREDIT-01 R1, R3-R4` only.
- Judge: POL-CREDIT-01 R3 requires EXCEPTION_FLAGGED for a default within 12 months, but the
  supplied policy text does not require expert manual review for that flag.
- Evidence: the escalation *is* in the corpus - POL-STAT-01 R6 makes EXPERT_MANUAL_REVIEW_REQUIRED
  follow from "no missing items, and at least one EXCEPTION_FLAGGED or expert-referral rule
  triggered". The v0 dossier simply did not cite POL-STAT-01, so the judge could not see the
  rule that the rationale was applying.
- So: the answer was correct (the frozen label agrees: EXCEPTION_FLAGGED /
  EXPERT_MANUAL_REVIEW_REQUIRED), and the trail was incomplete. The judge is right on its own
  standard; the human, reading for outcome correctness, was not wrong about the outcome.
- Resolution: v1 cites `['POL-CREDIT-01', 'POL-STAT-01']` on the same check; the judge verdict
  is grounded 5/5.

## case-019 - verdict: judge right (citation-scope gap, plus a corpus corner)

- v0 rationale: "affordability therefore requires expert manual review"; cited
  `POL-AFF-01`, `POL-LTV-01`.
- Judge: POL-AFF-01 establishes the pass/fail thresholds but does not prescribe exception
  flagging or manual referral for a failure; no other cited check establishes a
  policy-supported manual-review trigger.
- Evidence: correct as stated. POL-AFF-01 R4/R5 define thresholds and R6 covers unevidenced
  income only. The mapping "rule breached -> EXCEPTION_FLAGGED" is defined in the output
  protocol (the dossier schema's outcome description), not in POL-AFF-01, and the status
  mapping is POL-STAT-01 R6 - neither of which was cited. So the escalation chain's basis was
  invisible to the judge.
- This is the documented corpus corner (POL-AFF-01's failure handling is implicit), made
  concrete: it is a property of where the rule lives, not of the agent's answer.
- Resolution: v1 cites `['POL-AFF-01', 'POL-LTV-01', 'POL-STAT-01']` and states the derivation
  basis; the judge verdict is grounded 5/5.

## case-023 - verdict: neither; a policy under-specification

- v0 rationale: "age at term end is 63.23 years"; cited `POL-AGE-01`.
- Judge: from birth 1988-07-07 and term end 2051-10-01 the age is 63 years, 2 months and 24
  days - approximately 63.24 years, not 63.23.
- Evidence: the judge's years/months/days derivation is right. The decimal is not, and cannot
  be, settled by the corpus: POL-AGE-01 R1 states the comparison in the unit "75 years and 0
  days" and R3 asks for "the age at term end" - no decimal-years convention is defined
  anywhere. Two ordinary conventions divide the same interval differently:
  - 63 years + (2 months 24 days as 84 days) / 365.25 -> 63.2324 -> 63.23
  - 63 years + (86 calendar days) / 365.25 -> 63.2354 -> 63.24
  The agent's 63.23 and the judge's 63.24 are each internally defensible, which is the defect:
  the rationale was answering in a unit the policy does not define.
- So: not a judge error and not an agent error - an under-specified protocol, which the judge
  surfaced by choosing the other convention.
- Resolution: P6a changes the output to the policy's own unit - "63 years and 86 days" - and
  the ambiguity disappears; the judge verdict is grounded 5/5.

## Reading

- Agreement is 7/10, but the disagreements are not a single phenomenon: two were real
  citation-scope gaps in the written trail (the outcomes were right, the basis was not shown),
  and one was a policy under-specification that the judge read as a defect.
- In none of the three was the judge lenient, and in none was the disagreement left standing:
  all three were addressed at the trail level, not by adjusting the judge, and all three
  cleared in v1.
- The honest summary for the submission: the judge is stricter than a human reading for
  outcome correctness, and in these three cases that strictness pointed at something real -
  an uncited rule twice, an undefined unit once.

## Artefacts

- Judge verdicts v0: `evals/results/baseline-v0/judge/case-014.json`, `case-019.json`,
  `case-023.json`; v1 equivalents under `evals/results/v1/judge/`.
- Dossiers: `evals/results/baseline-v0/cases/case-014.json` (and 019, 023); v1 equivalents.
- Corpus: `knowledge/policy/POL-STAT-01.md` (R6), `POL-CREDIT-01.md` (R3),
  `POL-AFF-01.md` (R4-R6), `POL-AGE-01.md` (R1, R3).
