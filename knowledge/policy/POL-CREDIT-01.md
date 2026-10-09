# POL-CREDIT-01 - Credit File Markers

Windmill Bank - Underwriting Operations. Section POL-CREDIT-01. Version 1.0. Effective 2026-09-01.

- R1 The credit file report is a required item; if absent, report the token credit_report.
- R2 County Court Judgments (CCJs):
  - any unsatisfied CCJ -> EXCEPTION_FLAGGED;
  - a satisfied CCJ whose registration date is within the 24 calendar months ending on the
    assessment date (age <= 24 months) -> EXCEPTION_FLAGGED;
  - a satisfied CCJ registered more than 24 months before the assessment date -> note only.
- R3 Registered defaults: a default registered within the 12 calendar months ending on the
  assessment date (age <= 12 months) -> EXCEPTION_FLAGGED; older defaults -> note only.
- R4 When flagging, state each marker, its status and its dates in the rationale.
