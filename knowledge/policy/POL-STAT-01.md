# POL-STAT-01 - Dossier Output: Checks, Statuses and Precedence

Windmill Bank - Underwriting Operations. Section POL-STAT-01. Version 1.0. Effective 2026-09-01.

## Checks

- R1 Report one entry per applicable check, each with an outcome in {PASSED, ACTION_REQUIRED,
  EXCEPTION_FLAGGED}, a rationale, the policy section ids cited, and missing_items.
  Applicable checks:
  - CHK-DOC-COMPLETE - required evidence set present (POL-DOC-01)
  - CHK-DOC-RECENCY - dated documents current (POL-DOC-02)
  - CHK-INC-EMPLOYED - employed income evidence (POL-INC-01; employed cases)
  - CHK-INC-SELFEMPLOYED - self-employed income evidence (POL-SE-01; self-employed cases)
  - CHK-INC-CONSISTENCY - declared vs evidenced income (POL-INC-02)
  - CHK-CREDIT - credit file markers (POL-CREDIT-01)
  - CHK-LTV - loan-to-value band (POL-LTV-01)
  - CHK-AFFORDABILITY - DTI and stress (POL-AFF-01)
  - CHK-TERM-AGE - term end age (POL-AGE-01)
- R2 missing_items tokens (N = 1 is the most recent): id_document, payslip_month_1,
  payslip_month_2, payslip_month_3, employer_letter, sa302_year_1, sa302_year_2, sa302_year_3,
  tax_year_overview_1, tax_year_overview_2, tax_year_overview_3, credit_report,
  declaration_correction.
- R3 Where a single check has both missing items and a flag, ACTION_REQUIRED takes precedence
  within that check; all findings remain in the rationale.

## Statuses

- R4 READY_FOR_UNDERWRITING: all applicable checks PASSED.
- R5 ADDITIONAL_DOCUMENTS_REQUIRED: at least one missing item (any check with non-empty
  missing_items). This status takes precedence even when exceptions are also present,
  because the case cannot be finalised without the missing items; exceptions remain recorded.
- R6 EXPERT_MANUAL_REVIEW_REQUIRED: no missing items, and at least one EXCEPTION_FLAGGED or
  expert-referral rule triggered.

## Required actions

- R7 required_actions[]: for ADDITIONAL_DOCUMENTS_REQUIRED, list the needed items in plain
  language; for EXPERT_MANUAL_REVIEW_REQUIRED, state the referral reasons; for
  READY_FOR_UNDERWRITING, empty.
- R8 Never output READY_FOR_UNDERWRITING when any required item is missing or any check has
  flagged an exception or refers to expert review.
