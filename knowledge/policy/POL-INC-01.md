# POL-INC-01 - Employed Income Evidence

Windmill Bank - Underwriting Operations. Section POL-INC-01. Version 1.0. Effective 2026-09-01.

## Evidence set

- R1 The three most recent consecutive monthly payslips are required. If a month is absent,
  report its token payslip_month_N under the employed-income check; N = 1 is the most recent
  month, N = 3 the oldest.
- R2 The employer letter must state role, employment type and gross annual salary. If the
  letter is absent, or omits any of those, it does not satisfy the requirement: report the
  token employer_letter.
- R3 If the employer letter's stated gross annual salary differs materially (more than
  5.00%) from the payslip-implied annualised income, treat the documents as contradictory
  (POL-EXC-01) and flag EXCEPTION_FLAGGED.

## Evidenced income

- R4 Evidenced annual income = average gross monthly pay across the three payslips x 12,
  computed to two decimal places (half-up).
