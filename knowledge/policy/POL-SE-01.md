# POL-SE-01 - Self-Employed Income Evidence

Windmill Bank - Underwriting Operations. Section POL-SE-01. Version 1.0. Effective 2026-09-01.

- R1 Required: SA302 tax calculation and HMRC tax year overview for each of the last three
  consecutive completed UK tax years (6 April to 5 April). The most recent required year is
  the most recently completed tax year.
- R2 If both documents exist for a year, that year is satisfied. If one is missing, report
  only the missing token: sa302_year_N or tax_year_overview_N; N = 1 is the most recent year.
- R3 If evidence covers fewer than three years:
  - if the declaration shows the business commenced three or more tax years before the
    assessment date: report ACTION_REQUIRED with the missing years' tokens;
  - if the business commenced fewer than three tax years before the assessment date: flag
    EXCEPTION_FLAGGED and refer for expert manual review (early-stage business outside
    standard assessment).
- R4 Evidenced annual income = average of the three years' total taxable income (SA302),
  computed to two decimal places (half-up).
