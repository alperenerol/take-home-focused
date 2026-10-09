# POL-DOC-02 - Document Recency

Windmill Bank - Underwriting Operations. Section POL-DOC-02. Version 1.0. Effective 2026-09-01.

## 90-day window

- R1 A dated required document is current when its age is at most 90 calendar days:
  age_days = assessment_date - document_date; current if and only if age_days <= 90.
  Day 90 is acceptable; day 91 is not.
- R2 The window applies to: payslips, the employer letter, and the credit file report.
- R3 Undated required documents do not satisfy recency: treat them as not current and report
  the corresponding missing-item token under the recency check.

## Payslip coverage (cross-ref POL-INC-01)

- R4 Payslips must each be current individually and together cover the three most recent
  consecutive months.

## Exemptions

- R5 Self-employed SA302s and tax year overviews are exempt from the 90-day rule; they must
  instead cover the three most recent completed tax years (POL-SE-01).

## Worked boundary example

- Assessment date 2026-10-01: a document dated 2026-07-03 has age 90 days -> current; a
  document dated 2026-07-02 has age 91 days -> not current.
