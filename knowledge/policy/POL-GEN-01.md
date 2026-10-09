# POL-GEN-01 - Scope and Assessment Principles

Windmill Bank - Underwriting Operations. Section POL-GEN-01. Version 1.0. Effective 2026-09-01.

## Purpose

This corpus defines the operational rules used to pre-assess a residential mortgage case
submission before a human underwriter reviews it. Pre-assessment produces a recommendation
dossier; it never approves lending.

## Scope

- Instrument: residential owner-occupier mortgage applications.
- Applicants: employed or self-employed.
- Inputs per case: customer declaration (income, commitments, property, term) plus supporting
  evidence documents (see POL-DOC-01).
- The assessment date is a property of the case submission; all time-based rules use it.

## Principles

- R1 Evidence discipline: apply only the rules in this corpus, and cite the section id(s)
  behind every rule you apply. Do not invent rules.
- R2 No guessing: if a fact required by a rule is not evidenced, record it as missing
  (ACTION_REQUIRED with the relevant missing-item token) instead of inferring it.
- R3 Contradictions: when two documents materially disagree, flag EXCEPTION_FLAGGED and
  refer to POL-EXC-01; never choose, average or merge the values yourself.
- R4 Escalate ambiguity: if the case cannot be assessed under this policy without an
  assumption, refer for expert manual review (POL-EXC-01).
- R5 Supplementary material: documents outside the required set never substitute for
  required evidence (POL-DOC-01).
- R6 READY gate: a case may be READY_FOR_UNDERWRITING only when every applicable check has
  passed (POL-STAT-01).

## Related sections

POL-DOC-01, POL-DOC-02, POL-INC-01, POL-INC-02, POL-SE-01, POL-CREDIT-01, POL-LTV-01,
POL-AFF-01, POL-AGE-01, POL-EXC-01, POL-STAT-01.
