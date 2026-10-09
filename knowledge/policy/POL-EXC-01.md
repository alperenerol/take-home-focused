# POL-EXC-01 - Contradictions, Ambiguity and Expert Referral

Windmill Bank - Underwriting Operations. Section POL-EXC-01. Version 1.0. Effective 2026-09-01.

- R1 Two required documents contradict each other when they state materially conflicting
  values for the same fact. For income figures the materiality threshold is the 5.00%
  variance defined in POL-INC-02 R2; for other facts, a conflict is material when it affects
  a check's outcome.
- R2 On a material contradiction: flag EXCEPTION_FLAGGED, list the conflicting values in the
  rationale, and refer for expert manual review. Never choose, average or harmonise the
  values.
- R3 If a contradiction prevents a check from being completed, still flag EXCEPTION_FLAGGED;
  do not fall back to guessing.
- R4 Ambiguity: where the case cannot be classified under this policy without an assumption,
  refer for expert manual review and state the reason.
- R5 Expert referrals set the dossier status EXPERT_MANUAL_REVIEW_REQUIRED (POL-STAT-01).
