# POL-AGE-01 - Term and Retirement Age

Windmill Bank - Underwriting Operations. Section POL-AGE-01. Version 1.0. Effective 2026-09-01.

- R1 The mortgage term must end on or before the applicant's 75th birthday:
  term_end_date = assessment date + term months; the check passes if and only if the age at
  term_end_date is at most 75 years and 0 days.
- R2 If the term end age exceeds 75, flag EXCEPTION_FLAGGED and refer for expert manual review.
- R3 State the derived term end date and the age at term end in the rationale.
